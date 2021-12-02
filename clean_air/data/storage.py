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
from typing import TypeVar, Generic, Iterable, Callable, List, Optional, Union

import boto3
import botocore.exceptions
from botocore import UNSIGNED
from botocore.config import Config
from mypy_boto3_s3.service_resource import Object
from s3fs import S3FileSystem

from ..exceptions import CleanAirFrameworkException
from ..models import DataSet, MetaData
from ..serialisation import MetaDataYamlSerialiser, MetaDataSerialiser

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


def create_aurn_datastore(bucket_name="aurn", data_file_path="AURN_Site_Information.csv",
                          endpoint_url=JasminEndpointUrls.EXTERNAL, anon=True):
    """
    Return an AURNSiteDatastore instance configured with the given information

    :param bucket_name: Name of the bucket storing the AURN site data CSV file
    :param data_file_path: Object key of the AURN site data CSV file
    :param endpoint_url: the object store service endpoint URL. Changes depending on whether accessing data from inside
        or outside JASMIN, or using data stored on another AWS S3 compatible object store
    :param anon: Whether to use anonymous access or credentials. anon=True is required for write access
    """

    if anon:
        s3 = boto3.resource("s3", endpoint_url=endpoint_url, config=Config(signature_version=UNSIGNED))
    else:
        s3 = boto3.resource("s3", endpoint_url=endpoint_url)
    bucket = s3.Bucket(bucket_name)
    data_file_obj = bucket.Object(data_file_path)
    try:
        s3.meta.client.head_bucket(Bucket=bucket.name)
        # data_file_obj.load()  # This fails, not clear why, permissions? It uses Head Object API call under the hood
    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as ex:
        raise AURNSiteDataStoreException(
            "Unable to create AURNSiteDataStore. Error when accessing object store") from ex
    return AURNSiteDataStore(data_file_obj)


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

    def filter(self, filter_expr: Callable[[AURNSite], bool]) -> Iterable[AURNSite]:
        raise NotImplementedError()

    def get(self, item_id) -> AURNSite:
        raise NotImplementedError()

    def get_batch(self, item_ids: Iterable[str]) -> Iterable[AURNSite]:
        raise NotImplementedError()

    def put(self, item: AURNSite) -> None:
        raise NotImplementedError()

    def put_batch(self, items: Iterable[AURNSite]) -> None:
        raise NotImplementedError()


def create_dataset_store(storage_bucket_name="caf-data", local_storage_path: Optional[Path] = None,
                         endpoint_url=JasminEndpointUrls.EXTERNAL, anon=True) -> "S3FSDataSetStore":
    """
    Return an AURNSiteDatastore instance configured with the given information

    :param storage_bucket_name: Name of the bucket where datasets are stored
    :param local_storage_path: Path to a writeable directory to store local copies of dataset files
    :param endpoint_url: the object store service endpoint URL. Changes depending on whether accessing data from inside
        or outside JASMIN, or using data stored on another AWS S3 compatible object store
    :param anon: Whether to use anonymous access or credentials. anon=True is required for write access
    """

    client_kwargs = {"endpoint_url": endpoint_url}
    fs = S3FileSystem(anon=anon, client_kwargs=client_kwargs)
    return S3FSDataSetStore(fs, storage_bucket_name, cache_dir=local_storage_path)


class S3FSDataSetStore:
    """Encapsulates access to stored data sets"""

    def __init__(self, fs: S3FileSystem, storage_bucket_name: str = "caf-data", cache_dir: Optional[Path] = None,
                 metadata_serialiser: Optional[MetaDataSerialiser] = None):
        self._storage_bucket_name = storage_bucket_name
        self._fs = fs
        self._metadata_serialiser = metadata_serialiser if metadata_serialiser else MetaDataYamlSerialiser()

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

    @staticmethod
    def _get_file_paths(path: Path, include_datafiles=True, include_metadata=False, recurse=True) -> List[Path]:
        """
        Recursively gets file paths. Can include/exclude datafiles and metadata files using optional args.
        Assumes anything that's not a metadata file is a data file
        """
        datafile_paths = []
        for p in path.iterdir():
            if recurse and p.is_dir():
                datafile_paths.extend(S3FSDataSetStore._get_file_paths(p))
            else:
                is_metadata_file = bool(p.suffix == ".metadata")
                if (is_metadata_file and include_metadata) or (not is_metadata_file and include_datafiles):
                    datafile_paths.append(p)
        return datafile_paths

    def _generate_s3_key(self, obj: Union[DataSet, MetaData]) -> str:
        if isinstance(obj, MetaData):
            return f"{self._storage_bucket_name}/{obj.dataset_name}/{obj.dataset_name}.metadata"
        if isinstance(obj, DataSet):
            return f"{self._storage_bucket_name}/{obj.metadata.dataset_name}/"

    def available_datasets(self) -> List[str]:
        """Returns a list of dataset names that are available"""
        return [s.split("/", 1)[1] for s in self._fs.ls(self._storage_bucket_name, detail=False)]

    def get(self, dataset_id: str) -> DataSet:
        # TODO don't redownload if in cache? maybe add refresh/reload option
        # TODO, lazy loading, some kind of closure or DataSet subclass (LazyLoadingS3DataSet?)?
        s3_key = f"{self._storage_bucket_name}/{dataset_id}"
        cache_dir = (self._cache_dir / Path(dataset_id)).absolute()
        self._fs.get(s3_key, str(cache_dir), recursive=True)

        datafile_paths = self._get_file_paths(cache_dir)

        # Load Metadata
        metadata_path = self._get_file_paths(
            cache_dir, include_datafiles=False, include_metadata=True, recurse=False)[0]  # we only expect 1 file
        with metadata_path.open() as md_file:
            metadata = self._metadata_serialiser.deserialise(md_file.read())

        return DataSet(files=datafile_paths, metadata=metadata)

    def put(self, item: DataSet) -> None:
        for filename in item.files:
            key = self._generate_s3_key(item) + filename.name
            LOGGER.debug(f"Uploading datafile: {filename} to {key}")
            self._fs.put(str(filename), key)

        with tempfile.NamedTemporaryFile() as tmp_metadata:
            tmp_metadata.write(self._metadata_serialiser.serialise(item.metadata).encode("utf-8"))
            tmp_metadata.flush()
            key = self._generate_s3_key(item.metadata)
            LOGGER.debug(f"Uploading metadata to {key}")
            self._fs.put(tmp_metadata.name, key)
