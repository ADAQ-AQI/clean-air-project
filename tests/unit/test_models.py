import re
import string
import unittest

import pyproj
from shapely.geometry import box

from clean_air.models import Metadata, DataType, ContactDetails


class MetadataTest(unittest.TestCase):
    SPECIAL_CHARS = string.whitespace + string.punctuation.replace("_", "")

    def sanitise_id(self, id_str: str):
        # An interesting SO answer comparing the performance of several ways of doing this for different inputs:
        # https://stackoverflow.com/a/27086669
        for c in string.punctuation.replace("_", ""):
            if c in id_str:
                id_str = id_str.replace(c, "")
        for c in string.whitespace:
            if c in id_str:
                id_str = id_str.replace(c, "_")
        return id_str.lower()

    def test_init_defaults(self):
        test_dataset_name = "MOASA Flight M270"
        test_extent = box(-1, -1, 1, 1)
        m = Metadata(test_dataset_name, test_extent)

        self.assertEqual(test_dataset_name, m.title)
        self.assertEqual(self.sanitise_id(test_dataset_name), m.id)
        self.assertEqual(test_extent, m.extent)
        self.assertEqual(DataType.OTHER, m.data_type)
        self.assertEqual("", m.description)
        self.assertEqual([], m.contacts)
        self.assertEqual(pyproj.CRS("EPSG:4326"), m.crs)

    def test_init(self):
        test_dataset_name = "Hey! This~is_one_str@ng£ DaTaSet |\\|ame"
        test_extent = box(-1, -1, 1, 1)
        test_crs = pyproj.CRS("EPSG:4269")
        test_data_type = DataType.OBS_STATIONARY
        test_description = "This is a test"
        test_contacts = [ContactDetails("Mr", "John", "West", "johnwest@example.com")]

        m = Metadata(test_dataset_name, test_extent, test_crs, test_description, test_data_type, test_contacts)

        self.assertEqual(test_dataset_name, m.title)
        self.assertEqual(self.sanitise_id(test_dataset_name), m.id)
        self.assertEqual(test_extent, m.extent)
        self.assertEqual(test_data_type, m.data_type)
        self.assertEqual(test_description, m.description)
        self.assertEqual(test_contacts, m.contacts)
        self.assertEqual(test_crs, m.crs)
