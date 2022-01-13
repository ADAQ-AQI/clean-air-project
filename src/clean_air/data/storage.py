"""Data access code for stored data"""
import csv
import logging
import shutil
import tempfile
import weakref
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, date
from decimal import Decimal
from pathlib import Path
from typing import TypeVar, Generic, Iterable, Callable, List, Optional

import boto3
import botocore.exceptions
from botocore import UNSIGNED
from botocore.config import Config
from mypy_boto3_s3.service_resource import Object
from s3fs import S3FileSystem

from ..exceptions import CleanAirFrameworkException
from ..models import DataSet, Metadata
from ..serialisation import MetadataYamlSerialiser, MetadataSerialiser

LOGGER = logging.getLogger(__name__)
T = TypeVar('T')


class DataStoreException(CleanAirFrameworkException):
    """Base exception for errors relating to the underlying storage and interacting with it"""


class AURNSiteDataStoreException(DataStoreException):
    """Exceptions related to accessing the AURN site data"""


class AbstractDataStore(ABC, Generic[T]):
    """Interface for ObjectStore implementations to define what methods should be available"""

    @abstractmethod
    def all(self, force_reload=False) -> Iterable[T]:
        """
        Returns all items listed in the underlying data file.
        The data is cached, so repeated access doesn't result in multiple calls to the object store

        :param force_reload: If True, reloads the data from the object store (caching it in the process).
                             If False, uses cached data in preference to fetching data from the object store
        """

    @abstractmethod
    def filter(self, filter_expr: Callable[[T], bool]) -> Iterable[T]:
        """
        Return only the items that evaluate to True based on the supplied test

        :param filter_expr: A function/lambda that returns True/False depending on whether a given item matches the
                            filter
        """

    @abstractmethod
    def get(self, item_id) -> T:
        """Return a single item based on its ID"""

    @abstractmethod
    def get_batch(self, item_ids: Iterable) -> Iterable[T]:
        """Return multiple items based on a list of item IDs"""

    @abstractmethod
    def put(self, item: T) -> None:
        """Create or update a single item in the underlying data store"""

    @abstractmethod
    def put_batch(self, items: Iterable[T]) -> None:
        """Create or update multiple items in the underlying data store"""


class JasminEndpointUrls:
    """
    JASMIN object store endpoint URLs.
    Internal is for use within the JASMIN scientific computing environment
    External is for use from other locations
    """
    # noinspection HttpUrlsUsage
    INTERNAL = "http://caf-o.s3.jc.rl.ac.uk"
    EXTERNAL = "https://caf-o.s3-ext.jc.rl.ac.uk"


@dataclass
class AURNSite:
    """Data about a specific AURN site"""
    name: str  # The site's human readable name (with underscores instead of spaces)
    code: str  # Alphanumeric site code
    type: str  # Site Environment Type Classification
    latitude: Decimal  # Latitude in decimal degrees
    longitude: Decimal  # Longitude in decimal degrees
    opened: date  # Date the site was opened
    closed: Optional[date]  # Date the site was closed (None if it's still open)
    species: List[str]  # The chemical species recorded at the site


class AURNSiteDataStore(AbstractDataStore[AURNSite]):
    """
    Encapsulates storage and access of Automatic Urban and Rural Network (AURN) site data.
    What is AURN? Refer to https://uk-air.defra.gov.uk/networks/network-info?view=aurn

    Provides methods to get all data, some data, and write new data
    """

    def __init__(self, aurn_data_file_obj: Object) -> None:

        self._data_file = aurn_data_file_obj
        self._cached_data = None

    @property
    def data_file(self) -> Object:
        """Returns the Object storing the raw data on the object store"""
        return self._data_file

    def __eq__(self, other):
        return isinstance(other, AURNSiteDataStore) and self._data_file.e_tag == other._data_file.e_tag

    def all(self, force_reload=False) -> Iterable[AURNSite]:
        """
        Returns all sites listed in the AURN site data file.
        The data is cached, so repeated access doesn't result in multiple calls to the object store

        :param force_reload: If True, reloads the site data from the object store (caching it in the process).
                             If False, uses cached data in preference to fetching data from the object store
        """
        if not self._cached_data or force_reload:
            try:
                obj = self._data_file.get()
            except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as ex:
                # Despite ClientError inheriting from BotoCoreError, both must be handled due to internal botocore
                # shenanigans that I can't fully explain to do with dynamically generated exception classes
                raise AURNSiteDataStoreException from ex

            if not obj["ContentLength"]:
                raise AURNSiteDataStoreException(f"{self._data_file.key} contains no data")

            binary_data = obj["Body"].read()
            data = binary_data.decode("utf-8").splitlines()
            # We expect the CSV file to have a header row:
            # Code,Name,Type,Latitude,Longitude,Date_Opened,Date_Closed,Species
            reader = csv.DictReader(data)
            results = []
            for row in reader:
                try:
                    results.append(
                        AURNSite(
                            name=row["Name"],
                            code=row["Code"],
                            type=row["Type"],
                            latitude=Decimal(row["Latitude"]),
                            longitude=Decimal(row["Longitude"]),
                            opened=datetime.strptime(row["Date_Opened"], "%Y%m%d").date(),
                            closed=datetime.strptime(
                                row["Date_Closed"], "%Y%m%d").date() if int(row["Date_Closed"]) else None,
                            species=row["Species"].split(",")
                        )
                    )
                except KeyError as ex:
                    raise AURNSiteDataStoreException("Data doesn't match expected CSV schema") from ex

            self._cached_data = results
            if not self._cached_data:
                raise AURNSiteDataStoreException(f"{self._data_file.key} contained data, but it was not parseable")

        return self._cached_data

    def filter(self, filter_func: Callable[[AURNSite], bool]) -> Iterable[AURNSite]:
        raise NotImplementedError()

    def get(self, item_id) -> AURNSite:
        raise NotImplementedError()

    def get_batch(self, item_ids: Iterable[str]) -> Iterable[AURNSite]:
        raise NotImplementedError()

    def put(self, item: AURNSite) -> None:
        raise NotImplementedError()

    def put_batch(self, items: Iterable[AURNSite]) -> None:
        raise NotImplementedError()


class BaseS3FSDataStore:
    """Common functionality for S3FS-based datastores"""

    def __init__(self, fs: S3FileSystem, storage_bucket_name: str = "caf-data", cache_dir: Optional[Path] = None):
        self._storage_bucket_name = storage_bucket_name
        self._fs = fs

        if cache_dir:
            self._cache_dir = Path(cache_dir)
            # For now, our "cache" is just a directory where we download files too.
            # There's no upper limit on disk usage, so just ensure it's cleaned up on exit
            weakref.finalize(self._cache_dir, shutil.rmtree, self._cache_dir)
        else:
            # We don't need to access this, just need to stop it being garbage collected before the DataStore instance,
            # so ensure we hold a reference to it
            self.__tmp_dir = tempfile.TemporaryDirectory()
            self._cache_dir = Path(self.__tmp_dir.name)

    def available_datasets(self) -> List[str]:
        """Returns a list of dataset names that are available"""
        return [s.split("/", 1)[1] for s in self._fs.ls(self._storage_bucket_name, detail=False)]


class S3FSDataSetStore(BaseS3FSDataStore):
    """Encapsulates access to stored data sets"""

    # TODO? Some ideas for enhancements
    # - Lazy loading of data

    def __init__(self, fs: S3FileSystem, metadata_store: "S3FSMetadataStore", storage_bucket_name: str = "caf-data",
                 cache_dir: Optional[Path] = None):

        self._metadata_store = metadata_store
        super().__init__(fs=fs, storage_bucket_name=storage_bucket_name, cache_dir=cache_dir)

    @staticmethod
    def _get_datafile_paths(path: Path, recurse=True) -> List[Path]:
        """

        """
        datafile_paths = []
        for p in path.iterdir():
            if p.is_file() and p.suffix != ".metadata":
                datafile_paths.append(p)
            elif p.is_dir() and recurse:
                datafile_paths.extend(S3FSDataSetStore._get_datafile_paths(p))

        return datafile_paths

    def _generate_s3_key(self, dataset_id: str) -> str:
        return f"{self._storage_bucket_name}/{dataset_id}/"

    def _generate_cache_dir_path(self, dataset_id: str) -> Path:
        return (self._cache_dir / Path(dataset_id)).absolute()

    def get(self, dataset_id: str) -> DataSet:
        # TODO don't redownload if in cache? maybe add refresh/reload option
        # TODO, lazy loading, some kind of closure or DataSet subclass (LazyLoadingS3DataSet?)?
        s3_key = self._generate_s3_key(dataset_id)
        cache_dir_path = self._generate_cache_dir_path(dataset_id)

        cache_dir_path.mkdir(parents=True, exist_ok=True)
        try:
            metadata = self._metadata_store.get(dataset_id)
            self._fs.get(s3_key, str(cache_dir_path), recursive=True)
        except PermissionError:
            msg = f"PermissionError when accessing {s3_key}."
            msg += " Object may not exist, or you may have incorrect/misconfigured credentials"
            raise DataStoreException(msg)
        datafile_paths = self._get_datafile_paths(cache_dir_path)

        # Load Metadata
        return DataSet(files=datafile_paths, metadata=metadata)

    def put(self, item: DataSet) -> None:
        if self._fs.anon:
            raise DataStoreException("Cannot perform write operations in anonymous mode. "
                                     "Please provide credentials with write permissions")

        if not item.metadata:
            raise DataStoreException("metadata is required in order to persist datasets")

        self._metadata_store.put(item.metadata)

        for filename in item.files:
            key = self._generate_s3_key(item.id) + filename.name
            LOGGER.debug(f"Uploading datafile: {filename} to {key}")
            try:
                self._fs.put(str(filename), key)
            except PermissionError:
                raise DataStoreException(
                    f"You do not have permission to upload to s3://{key}."
                    " Please check your credentials are correct or contact the system administrator")


class S3FSMetadataStore(BaseS3FSDataStore):
    """Encapsulates access to stored metadata"""

    def __init__(self, fs: S3FileSystem, storage_bucket_name: str = "caf-data", cache_dir: Optional[Path] = None,
                 metadata_serialiser: Optional[MetadataSerialiser] = None):
        self._metadata_serialiser = metadata_serialiser if metadata_serialiser else MetadataYamlSerialiser()
        super().__init__(fs=fs, storage_bucket_name=storage_bucket_name, cache_dir=cache_dir)

    def _to_s3_key(self, dataset_id: str) -> str:
        return f"{self._storage_bucket_name}/{dataset_id}/{dataset_id}.metadata"

    def _to_cached_file_path(self, dataset_id: str) -> Path:
        return (self._cache_dir / Path(dataset_id) / Path(f"{dataset_id}.metadata")).absolute()

    def get(self, dataset_id: str) -> Metadata:
        metadata_key = self._to_s3_key(dataset_id)
        cached_metadata_file = self._to_cached_file_path(dataset_id)

        cached_metadata_file.parent.mkdir(parents=True, exist_ok=True)
        try:
            self._fs.get(metadata_key, str(cached_metadata_file))
        except PermissionError:
            msg = f"PermissionError when accessing {metadata_key}."
            msg += " Object may not exist, or you may have incorrect/misconfigured credentials"
            raise DataStoreException(msg)

        # Load Metadata
        with cached_metadata_file.open() as md_file:
            return self._metadata_serialiser.deserialise(md_file.read())

    def put(self, item: Metadata) -> None:
        if self._fs.anon:
            raise DataStoreException("Cannot perform write operations in anonymous mode. "
                                     "Please provide credentials with write permissions")

        with tempfile.NamedTemporaryFile() as tmp_metadata:
            tmp_metadata.write(self._metadata_serialiser.serialise(item).encode("utf-8"))
            tmp_metadata.flush()
            key = self._to_s3_key(item.id)
            LOGGER.debug(f"Uploading metadata from {tmp_metadata.name} to {key}")
            try:
                self._fs.put(tmp_metadata.name, key)
            except PermissionError:
                raise DataStoreException(
                    f"You do not have permission to upload to s3://{key}."
                    " Please check your credentials are correct or contact the system administrator")


def create_aurn_datastore(
        bucket_name: str = "aurn", data_file_path: str = "AURN_Site_Information.csv",
        endpoint_url: str = JasminEndpointUrls.EXTERNAL,
        anon: bool = True) -> AURNSiteDataStore:
    """
    Return an AURNSiteDatastore instance configured with the given information

    :param bucket_name: Name of the bucket storing the AURN site data CSV file
    :param data_file_path: Object key of the AURN site data CSV file
    :param endpoint_url: the object store service endpoint URL. Changes depending on whether accessing data from inside
        or outside JASMIN, or using data stored on another AWS S3 compatible object store
    :param anon: Whether to use anonymous access or credentials. anon=True is required for write access
    """

    s3_args = {"endpoint_url": endpoint_url}
    if anon:
        s3_args["config"] = Config(signature_version=UNSIGNED)

    s3 = boto3.resource("s3", **s3_args)
    bucket = s3.Bucket(bucket_name)
    data_file_obj = bucket.Object(data_file_path)
    try:
        s3.meta.client.head_bucket(Bucket=bucket.name)
        # data_file_obj.load()  # This fails, not clear why, permissions? It uses Head Object API call under the hood
    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as ex:
        raise AURNSiteDataStoreException(
            "Unable to create AURNSiteDataStore. Error when accessing object store") from ex
    return AURNSiteDataStore(data_file_obj)


def create_dataset_store(
        storage_bucket_name="caf-data", local_storage_path: Optional[Path] = None,
        endpoint_url: str = JasminEndpointUrls.EXTERNAL,
        anon: bool = True) -> S3FSDataSetStore:
    """
    Return an `S3FSDataSetStore` instance configured with the given information

    :param storage_bucket_name: Name of the bucket where datasets are stored
    :param local_storage_path: Path to a writeable directory to store local copies of dataset files
    :param endpoint_url: the object store service endpoint URL. Changes depending on whether accessing data from inside
        or outside JASMIN, or using data stored on another AWS S3 compatible object store
    :param anon: Whether to use anonymous access or credentials. anon=True is required for write access
    """

    client_kwargs = {"endpoint_url": endpoint_url}
    fs = S3FileSystem(anon=anon, client_kwargs=client_kwargs)
    meta_store = create_metadata_store(storage_bucket_name, local_storage_path, endpoint_url, anon)
    return S3FSDataSetStore(fs, meta_store, storage_bucket_name, cache_dir=local_storage_path)


def create_metadata_store(
        storage_bucket_name="caf-data", local_storage_path: Optional[Path] = None,
        endpoint_url: str = JasminEndpointUrls.EXTERNAL,
        anon: bool = True) -> S3FSMetadataStore:
    """
    Return an `S3FSDataSetStore` instance configured with the given information

    :param storage_bucket_name: Name of the bucket where datasets are stored
    :param local_storage_path: Path to a writeable directory to store local copies of dataset files
    :param endpoint_url: the object store service endpoint URL. Changes depending on whether accessing data from inside
        or outside JASMIN, or using data stored on another AWS S3 compatible object store
    :param anon: Whether to use anonymous access or credentials. anon=True is required for write access
    """
    fs = S3FileSystem(anon=anon, client_kwargs={"endpoint_url": endpoint_url})
    return S3FSMetadataStore(fs, storage_bucket_name, cache_dir=local_storage_path)
