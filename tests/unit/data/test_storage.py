from unittest import mock

import boto3
import botocore
import json
import os
import unittest
from botocore.exceptions import ClientError, BotoCoreError
from datetime import date
from decimal import Decimal
from moto import mock_s3
# TODO: make this moto import work locally
from mypy_boto3_s3.service_resource import Object  # Used by moto to correctly mock object store requests
from pathlib import Path
from s3fs import S3FileSystem
from shapely.geometry import box
from time import time
from unittest.mock import Mock

from clean_air.data.storage import AURNSiteDataStoreException, DataStoreException, AURNSite, AURNSiteDataStore, \
    create_aurn_datastore, S3FSMetadataStore, S3FSDataSetStore, create_dataset_store, create_metadata_store
from clean_air.data.exceptions import CleanAirFrameworkException
from clean_air.data.models import Metadata, DataSet
from clean_air.data.serialisation import MetadataJsonSerialiser
from edr_server.core.models.extents import Extents, SpatialExtent

os.environ["MOTO_S3_CUSTOM_ENDPOINTS"] = "https://caf-o.s3-ext.jc.rl.ac.uk"


@mock_s3
class BaseAURNSiteDataStoreTest(unittest.TestCase):
    """SETUP and TEARDOWN all tests relating to the AURN data"""

    AURN_BUCKET_NAME = "aurn"
    AURN_FILE_KEY = "AURN_Site_Information.csv"
    TEST_ENDPOINT_URL = "https://caf-o.s3-ext.jc.rl.ac.uk"

    TEST_AURN_DATA = "\n".join(['Code,Name,Type,Latitude,Longitude,Date_Opened,Date_Closed,Species',
        'ABD,Aberdeen,URBAN_BACKGROUND,57.15736000,-2.094278000,19990918,0,"CO,NO,NO2,NOx,O3,PM10,PM2p5,SO2,nvPM10,nvPM2p5,vPM10,vPM2p5"',
        # nopep8 - wrapping would ruin readability
        'ABD7,Aberdeen_Union_St_Roadside,URBAN_TRAFFIC,57.14455500,-2.106472000,20080101,0,"NO,NO2,NOx"',
        'ABD8,Aberdeen_Wellington_Road,URBAN_TRAFFIC,57.13388800,-2.094198000,20160209,0,"NO,NO2,NOx"'])

    EXPECTED_AURNSITES = {
        "ABD": AURNSite(
            "Aberdeen", "ABD", "URBAN_BACKGROUND", Decimal("57.15736000"), Decimal("-2.094278000"),
            date(1999, 9, 18), None,
            ["CO", "NO", "NO2", "NOx", "O3", "PM10", "PM2p5", "SO2", "nvPM10", "nvPM2p5", "vPM10", "vPM2p5"]),
        "ABD7": AURNSite(
            "Aberdeen_Union_St_Roadside", "ABD7", "URBAN_TRAFFIC", Decimal("57.14455500"), Decimal("-2.106472000"),
            date(2008, 1, 1), None, ["NO", "NO2", "NOx"]
        ),
        "ABD8": AURNSite(
            "Aberdeen_Wellington_Road", "ABD8", "URBAN_TRAFFIC", Decimal("57.13388800"), Decimal("-2.094198000"),
            date(2016, 2, 9), None, ["NO", "NO2", "NOx"]
        )}

    def setUp(self) -> None:
        self.s3 = boto3.resource('s3', endpoint_url=self.TEST_ENDPOINT_URL)
        self.test_bucket = self.s3.Bucket(self.AURN_BUCKET_NAME)
        self.test_bucket.create()
        self.test_bucket.put_object(Key=self.AURN_FILE_KEY, Body=self.TEST_AURN_DATA.encode('utf-8'))

        self.datastore = AURNSiteDataStore(self.test_bucket.Object(self.AURN_FILE_KEY))

    def tearDown(self) -> None:
        self.test_bucket.objects.delete()
        self.test_bucket.delete()


class TestExceptions(unittest.TestCase):
    """
    Tests related to custom exception classes defined for storage.py.
    Mainly testing they form the expected hierarchy
    """

    def test_DataStoreException_is_subclass_of_CleanAirFrameworkException(self):
        """
        GIVEN an instance of a DataStoreException,
        WHEN checked for system hierarchy,
        THEN the instance is a subclass of a CleanAirFrameworkException.
        """
        self.assertTrue(issubclass(DataStoreException, CleanAirFrameworkException))

    def test_AURNSiteDataStoreException_is_subclass_of_DataStoreException(self):
        """
        GIVEN an instance of an AURNDataStoreException,
        WHEN checked for system hierarchy,
        THEN the instance is a subclass of a DataStoreException.
        """
        self.assertTrue(issubclass(AURNSiteDataStoreException, DataStoreException))


@mock_s3
class TestAURNSiteDataStoreCreation(BaseAURNSiteDataStoreTest):
    """Tests to check creation of AURN Site Data Store objects"""
    def setUp(self) -> None:
        """SETUP variables for all tests"""
        # Workaround for https://github.com/spulec/moto/issues/4797
        super().setUp()

    def tearDown(self) -> None:
        """TEARDOWN variables for all tests"""
        # Workaround for https://github.com/spulec/moto/issues/4797
        super().tearDown()

    def test_non_default_args(self):
        """
        GIVEN a valid bucket name,
        WHEN a bucket is created,
        THEN it will have the expected bucket name, data path, endpoint URL and signature version.
        """
        expected_bucket_name = "test_bucket"
        expected_data_file_path = "made/up/path/file.csv"
        expected_endpoint_url = self.TEST_ENDPOINT_URL

        bucket = self.s3.Bucket(expected_bucket_name)
        bucket.create()
        try:
            bucket.put_object(Key=expected_data_file_path, Body=self.TEST_AURN_DATA.encode('utf-8'))
            actual = create_aurn_datastore(
                bucket_name=expected_bucket_name, data_file_path=expected_data_file_path,
                endpoint_url=expected_endpoint_url, anon=False
            )

            self.assertEqual(expected_bucket_name, actual.data_file.bucket_name)
            self.assertEqual(expected_data_file_path, actual.data_file.key)
            self.assertEqual(expected_endpoint_url, actual.data_file.meta.client.meta.endpoint_url)
            self.assertEqual("s3v4", actual.data_file.meta.client.meta.config.signature_version)
        finally:
            bucket.objects.delete()
            bucket.delete()

    def test_default_args(self):
        """
        GIVEN no inputs (i.e. using only default arguments),
        WHEN a bucket is created using create_aurn_datastore(),
        THEN it will have the expected bucket name, data path, endpoint URL and signature version.
        """
        actual = create_aurn_datastore()

        self.assertEqual("aurn", actual.data_file.bucket_name)
        self.assertEqual("AURN_Site_Information.csv", actual.data_file.key)
        self.assertEqual("https://caf-o.s3-ext.jc.rl.ac.uk", actual.data_file.meta.client.meta.endpoint_url)
        self.assertEqual(botocore.UNSIGNED, actual.data_file.meta.client.meta.config.signature_version)

    def test_bucket_doesnt_exist(self):
        """
        GIVEN a bucket name that doesn't exist
        WHEN create_aurn_datastore() is called
        THEN an AURNSiteDataStoreException is raised
        """
        self.assertRaises(
            AURNSiteDataStoreException, create_aurn_datastore, bucket_name="doesnt-exist")


@mock_s3
class TestAURNSiteDataStore(BaseAURNSiteDataStoreTest):
    """Tests AURNSiteDataStore"""

    def setUp(self) -> None:
        # Workaround for https://github.com/spulec/moto/issues/4797
        super().setUp()

    def tearDown(self) -> None:
        # Workaround for https://github.com/spulec/moto/issues/4797
        super().tearDown()

    def test_all(self):
        """
        GIVEN a valid bucket holding a CSV file of AURN site data with the expected filename
        AND our code has permission to access that file
        WHEN all() is called
        THEN an Iterable of dictionaries is returned
        """
        expected = self.EXPECTED_AURNSITES.values()
        actual = self.datastore.all()

        self.assertCountEqual(expected, actual)

    def test_all_bucket_doesnt_exist(self):
        """
        GIVEN the AURNDataStore instance is configured with a bucket that doesn't exist
        WHEN all() is called
        THEN an AURNSiteDataStoreException is raised
        """

        ds = AURNSiteDataStore(self.s3.Bucket("doesnt-exist").Object(self.AURN_FILE_KEY))
        self.assertRaises(AURNSiteDataStoreException, ds.all)

    def test_all_bucket_name_invalid(self):
        """
        GIVEN the AURNDataStore instance is configured with an invalid bucket name
        WHEN all() is called
        THEN an AURNSiteDataStoreException is raised
        """
        ds = AURNSiteDataStore(self.s3.Bucket("invalid name !£$%^&*()").Object(self.AURN_FILE_KEY))
        self.assertRaises(AURNSiteDataStoreException, ds.all)

    def test_all_clienterror_handled(self):
        """
        WHEN all() is called
        AND a boto ClientError (or a subclass of it) is raised
        THEN an AURNSiteDataStoreException is raised
        """
        mock_object = mock.Mock(spec=Object, name="my_mock_object")
        mock_object.get.side_effect = ClientError(error_response={}, operation_name="get")

        ds = AURNSiteDataStore(mock_object)
        self.assertRaises(AURNSiteDataStoreException, ds.all)

    def test_all_botocoreerror_handled(self):
        """
        WHEN all() is called
        AND a boto BotoCoreError (or a subclass of it) is raised
        THEN an AURNSiteDataStoreException is raised
        """
        mock_object = mock.Mock(spec=Object, name="my_mock_object")
        mock_object.get.side_effect = BotoCoreError

        ds = AURNSiteDataStore(mock_object)
        self.assertRaises(AURNSiteDataStoreException, ds.all)

    def test_all_file_doesnt_exist(self):
        """
        GIVEN our code doesn't have permission to access the bucket
        WHEN all() is called
        THEN an AURNSiteDataStoreException is raised
        """
        self.test_bucket.Object(self.AURN_FILE_KEY).delete()
        self.assertRaises(AURNSiteDataStoreException, self.datastore.all)

    def test_all_empty_file(self):
        """
        GIVEN the data file exists in the expected bucket
        AND the data file is empty
        WHEN all() is called
        THEN an AURNSiteDataStoreException is raised
        """
        self.test_bucket.put_object(Key=self.AURN_FILE_KEY, Body=b"")
        self.assertRaises(AURNSiteDataStoreException, self.datastore.all)

    def test_all_non_csv_data(self):
        """
        GIVEN the data in the data file is not in CSV format
        WHEN all() is called
        THEN an AURNSiteDataStoreException is raised
        """
        test_file_contents = json.dumps({
            "key1": "value1",
            "key2": None,
        }).encode("utf-8")
        self.test_bucket.put_object(Key=self.AURN_FILE_KEY, Body=test_file_contents)
        self.assertRaises(AURNSiteDataStoreException, self.datastore.all)

    def test_all_incorrect_csv(self):
        """
        GIVEN the data in the data file is not formatted in the expected CSV schema
        WHEN all() is called
        THEN an AURNSiteDataStoreException is raised
        """
        test_file_contents = "\n".join([
            "Field1,Field2,Field3",
            "spam,eggs,spam",
            "ham,jam,ham",
            '"portabello mushroom","dauphinoise potatoes","lobster thermador"'
        ]).encode("utf-8")
        self.test_bucket.put_object(Key=self.AURN_FILE_KEY, Body=test_file_contents)
        self.assertRaises(AURNSiteDataStoreException, self.datastore.all)

    def test_all_force_reload(self):
        """
        GIVEN all() has been called once already (and the result has been cached)
        WHEN all(force_reload=True) is called
        THEN the cached data is discarded
        AND the data is re-downloaded from the object store
        """

        object_mock = mock.Mock(spec=Object)
        object_mock.key = self.AURN_FILE_KEY
        object_mock.get.side_effect = lambda: self.test_bucket.Object(self.AURN_FILE_KEY).get()
        ds = AURNSiteDataStore(object_mock)

        expected_object_store_access_count = 3
        for c in range(expected_object_store_access_count):
            ds.all(force_reload=True)

        # noinspection PyUnresolvedReferences
        self.assertEqual(expected_object_store_access_count, ds.data_file.get.call_count)

    def test_all_force_reload_defaults_false(self):
        """
        GIVEN force_reload is not passed as an argument to all()
        WHEN all() is called multiple times
        THEN the object store is accessed only once
        (i.e. the data is cached after the first call for use in subsequent calls)
        """
        object_mock = mock.Mock(spec=Object)
        object_mock.get.return_value = self.test_bucket.Object(self.AURN_FILE_KEY).get()
        ds = AURNSiteDataStore(object_mock)

        for c in range(3):
            ds.all()

        # noinspection PyUnresolvedReferences
        ds.data_file.get.assert_called_once()

    def test_all_data_cached(self):
        """
        GIVEN all() has been called once already
        WHEN all() is called again
        THEN data from the first call is returned
        AND the object store is not called
        (i.e. the data is cached after the first call for use in subsequent calls)
        """
        object_mock = mock.Mock(spec=Object)
        object_mock.get.return_value = self.test_bucket.Object(self.AURN_FILE_KEY).get()
        ds = AURNSiteDataStore(object_mock)

        for c in range(3):
            ds.all(force_reload=False)

        # noinspection PyUnresolvedReferences
        ds.data_file.get.assert_called_once()


class TestDataSetStore(unittest.TestCase):

    def setUp(self) -> None:
        self.mock_fs = Mock(spec=S3FileSystem)
        self.mock_fs.anon = False
        self.mock_storage_bucket_name = "test_bucket"

        test_metadata = Metadata(
            f"{time()}", f"test dataset-{time()}", "A Test", [], Extents(SpatialExtent(box(-1, -1, 1, 1))), [])

        self.mock_metadata_store = Mock(spec=S3FSMetadataStore)
        self.mock_metadata_store.get.return_value = test_metadata

        self.dataset_store = S3FSDataSetStore(self.mock_fs, self.mock_metadata_store, self.mock_storage_bucket_name)

        # This is a little bit circular, but makes it easier to set up tests for download operations
        # later, since the paths will match
        data_dir = Path(self.dataset_store._cache_dir) / Path(test_metadata.id)
        data_files = [data_dir / p for p in [Path("test-file.csv")]]
        self.test_dataset = DataSet(data_files, test_metadata)

    def test_available_datasets(self):
        """
        GIVEN a set of datasets readily available in the storage bucket,
        WHEN available_datasets is called,
        THEN a complete list of datasets that exist in the storage bucket is returned.
        """
        expected_datasets = ["dataset1", "dataset2", "dataset3"]
        self.mock_fs.ls.return_value = [f"{self.mock_storage_bucket_name}/{ds}" for ds in expected_datasets]

        actual_datasets = self.dataset_store.available_datasets()
        self.assertEqual(expected_datasets, actual_datasets)

    def test_get(self):
        """
        GIVEN a valid ID for a dataset that exists on the object store
        WHEN get is called
        THEN that dataset is returned
        """

        def mock_get(_s3_key: str, local_dir: str, **_kwargs):
            """Mocks S3FileSystem.get"""
            local_dir = Path(local_dir)
            # S3FileSystem.get won't create the target dir if it doesn't exist
            for datafile in self.test_dataset.files:
                (local_dir / Path(datafile)).touch()

        self.mock_fs.get.side_effect = mock_get

        self.mock_metadata_store.get.return_value = self.test_dataset.metadata

        actual = self.dataset_store.get(self.test_dataset.id)

        self.assertEqual(self.test_dataset, actual)
        self.mock_metadata_store.get.assert_called_with(self.test_dataset.id)
        self.mock_fs.get.assert_called_with(
            f"{self.mock_storage_bucket_name}/{self.test_dataset.id}/",
            f"{self.dataset_store._cache_dir}/{self.test_dataset.id}",
            recursive=True
        )

    def test_get_invalid_id(self):
        """
        GIVEN a dataset ID that doesn't exist
        WHEN get is called with that ID
        THEN a DataStoreException is raised
        """
        self.mock_fs.get.side_effect = PermissionError
        self.assertRaises(DataStoreException, self.dataset_store.get, self.test_dataset.id)

    def test_put(self):
        """
        GIVEN a valid Metadata instance
        WHEN it is passed to put
        THEN S3FileSystem.put is called with the path to a temporary file
        AND the temporary file contains the correctly serialised form of the Metadata
        AND the s3 key is correct
        """
        base_s3_key = f"{self.mock_storage_bucket_name}/{self.test_dataset.id}/"
        expected_uploads = [
            unittest.mock.call(str(datafile), base_s3_key + datafile.name)
            for datafile in self.test_dataset.files
        ]

        self.dataset_store.put(self.test_dataset)

        self.mock_metadata_store.put.assert_called_once_with(self.test_dataset.metadata)
        self.assertEqual(expected_uploads, self.mock_fs.put.mock_calls)

    def test_put_readonly_credentials(self):
        """
        GIVEN the credentials in use are read only
        WHEN put is called
        THEN a DataStoreException is raised
        """
        self.mock_fs.put.side_effect = PermissionError
        self.assertRaises(DataStoreException, self.dataset_store.put, self.test_dataset)

    def test_put_anonymous(self):
        """
        GIVEN the underlying S3FileSystem was created in anonymous mode
        WHEN put is called
        THEN a DataStoreException is raised
        """
        self.mock_fs.anon = True
        self.assertRaises(DataStoreException, self.dataset_store.put, self.test_dataset)


class TestMetadataStore(unittest.TestCase):

    def setUp(self) -> None:
        self.mock_fs = Mock(spec=S3FileSystem)
        self.mock_fs.anon = False
        self.mock_storage_bucket_name = "test_bucket"
        self.test_metadata = Metadata(
            f"{time()}", f"test dataset-{time()}", "A Test", [], Extents(SpatialExtent(box(-1, -1, 1, 1))), [])

        self.metadata_store = S3FSMetadataStore(self.mock_fs, self.mock_storage_bucket_name)

    def test_available_datasets(self):
        """
        GIVEN a set of datasets readily available in the storage bucket,
        WHEN available_datasets is called,
        THEN a complete list of datasets that exist in the storage bucket is returned.
        """

        expected_datasets = ["dataset1", "dataset2", "dataset3"]
        self.mock_fs.ls.return_value = [f"{self.mock_storage_bucket_name}/{ds}" for ds in expected_datasets]

        actual_datasets = self.metadata_store.available_datasets()
        self.assertEqual(expected_datasets, actual_datasets)

    def test_get(self):
        """
        GIVEN a valid ID for a dataset that exists on the object store
        WHEN get is called
        THEN the metadata for that dataset is returned
        """
        serialiser = MetadataJsonSerialiser()

        def mock_get(_s3_key: str, download_path: str, _recursive=False):
            """Mocks S3FileSystem.get"""
            download_path = Path(download_path)
            # Note that S3FileSystem.get won't create the target dir if it doesn't exist
            with open(download_path, "w") as f:
                f.write(serialiser.serialise(self.test_metadata))

        self.mock_fs.get.side_effect = mock_get

        actual = self.metadata_store.get(self.test_metadata.id)

        self.assertEqual(self.test_metadata, actual)

    def test_get_invalid_id(self):
        """
        GIVEN a dataset ID that doesn't exist
        WHEN get is called with that ID
        THEN a DataStoreException is raised
        """
        self.mock_fs.get.side_effect = PermissionError
        self.assertRaises(DataStoreException, self.metadata_store.get, self.test_metadata.id)

    def test_put(self):
        """
        GIVEN a valid Metadata instance
        WHEN it is passed to put
        THEN S3FileSystem.put is called with the path to a temporary file
        AND the temporary file contains the correctly serialised form of the Metadata
        AND the s3 key is correct
        """
        serialiser = MetadataJsonSerialiser()
        expected_upload = serialiser.serialise(self.test_metadata)
        expected_s3_key = f"{self.mock_storage_bucket_name}/{self.test_metadata.id}/{self.test_metadata.id}.metadata"

        actual_upload = None

        def mock_put(file_path: str, _s3_key: str, _recursive=False):
            nonlocal actual_upload
            file_path = Path(file_path)
            with open(file_path) as f:
                actual_upload = f.read()

        self.mock_fs.put.side_effect = mock_put

        self.metadata_store.put(self.test_metadata)

        self.assertEqual(expected_upload, actual_upload)
        self.mock_fs.put.assert_called_with(mock.ANY, expected_s3_key)

    def test_put_readonly_credentials(self):
        """
        GIVEN the credentials in use are read only
        WHEN put is called
        THEN a DataStoreException is raised
        """
        self.mock_fs.put.side_effect = PermissionError
        self.assertRaises(DataStoreException, self.metadata_store.put, self.test_metadata)

    def test_put_anonymous(self):
        """
        GIVEN the underlying S3FileSystem was created in anonymous mode
        WHEN put is called
        THEN a DataStoreException is raised
        """
        self.mock_fs.anon = True
        self.assertRaises(DataStoreException, self.metadata_store.put, self.test_metadata)

    def test_create_dataset_store(self):
        """
        GIVEN a mock storage bucket name
        WHEN create_dataset_store is called
        THEN a S3DataSetStore object is returned
        """
        store = create_dataset_store(self.mock_storage_bucket_name)
        assert isinstance(store, S3FSDataSetStore)

    def test_create_metadata_store(self):
        """
        GIVEN a mock storage bucket name
        WHEN create_metadata_store is called
        THEN a S3MetadataStore object is returned
        """
        store = create_metadata_store(self.mock_storage_bucket_name)
        assert isinstance(store, S3FSMetadataStore)
