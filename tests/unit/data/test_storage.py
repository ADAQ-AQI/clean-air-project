import json
import os
import unittest
from datetime import date
from decimal import Decimal
from unittest import mock

import boto3
import botocore
from botocore.exceptions import ClientError, BotoCoreError
from moto import mock_s3
from mypy_boto3_s3.service_resource import Object

from clean_air.data.storage import AURNSiteDataStoreException, DataStoreException, AURNSite, AURNSiteDataStore, \
    create_aurn_datastore
from clean_air.exceptions import CleanAirFrameworkException

# Used by moto to correctly mock object store requests
os.environ["MOTO_S3_CUSTOM_ENDPOINTS"] = "https://caf-o.s3-ext.jc.rl.ac.uk"


class ExceptionsTest(unittest.TestCase):
    """
    Tests related to custom exception classes defined for storage.py.
    Mainly testing they form the expected hierarchy
    """

    def test_DataStoreException_is_subclass_of_CleanAirFrameworkException(self):
        self.assertTrue(issubclass(DataStoreException, CleanAirFrameworkException))

    def test_AURNSiteDataStoreException_is_subclass_of_DataStoreException(self):
        self.assertTrue(issubclass(AURNSiteDataStoreException, DataStoreException))


@mock_s3
class BaseAURNSiteDataStoreTest(unittest.TestCase):
    """Common test setup/tear down for tests relating to the AURN data"""

    AURN_BUCKET_NAME = "aurn"
    AURN_FILE_KEY = "AURN_Site_Information.csv"
    TEST_ENDPOINT_URL = "https://caf-o.s3-ext.jc.rl.ac.uk"

    TEST_AURN_DATA = "\n".join([
        'Code,Name,Type,Latitude,Longitude,Date_Opened,Date_Closed,Species',
        'ABD,Aberdeen,URBAN_BACKGROUND,57.15736000,-2.094278000,19990918,0,"CO,NO,NO2,NOx,O3,PM10,PM2p5,SO2,nvPM10,nvPM2p5,vPM10,vPM2p5"',  # nopep8 - wrapping would ruin readability
        'ABD7,Aberdeen_Union_St_Roadside,URBAN_TRAFFIC,57.14455500,-2.106472000,20080101,0,"NO,NO2,NOx"',
        'ABD8,Aberdeen_Wellington_Road,URBAN_TRAFFIC,57.13388800,-2.094198000,20160209,0,"NO,NO2,NOx"',
    ])

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
        ),
    }

    def setUp(self) -> None:
        self.s3 = boto3.resource('s3', endpoint_url=self.TEST_ENDPOINT_URL)
        self.test_bucket = self.s3.Bucket(self.AURN_BUCKET_NAME)
        self.test_bucket.create()
        self.test_bucket.put_object(Key=self.AURN_FILE_KEY, Body=self.TEST_AURN_DATA.encode('utf-8'))

        self.datastore = AURNSiteDataStore(self.test_bucket.Object(self.AURN_FILE_KEY))

    def tearDown(self) -> None:
        self.test_bucket.objects.delete()
        self.test_bucket.delete()


@mock_s3
class CreateAURNSiteDataStoreTest(BaseAURNSiteDataStoreTest):

    def test_non_default_args(self):
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
class AURNSiteDataStoreTest(BaseAURNSiteDataStoreTest):
    """Tests AURNSiteDataStore"""

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
