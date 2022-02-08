import string
import unittest

import pyproj
import pytest
from shapely.geometry import box

from clean_air.models import Metadata, DataType, ContactDetails, TemporalExtent, Extent, Duration


class MetadataTest(unittest.TestCase):
    SPECIAL_CHARS = string.whitespace + string.punctuation.replace("_", "")

    @staticmethod
    def sanitise_id(id_str: str):
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
        test_extent = Extent(box(-1, -1, 1, 1), TemporalExtent())
        m = Metadata(test_dataset_name, test_extent)

        self.assertEqual(test_dataset_name, m.title)
        self.assertEqual(self.sanitise_id(test_dataset_name), m.id)
        self.assertEqual(test_extent, m.extent)
        self.assertEqual([], m.keywords)
        self.assertEqual(DataType.OTHER, m.data_type)
        self.assertEqual("", m.description)
        self.assertEqual([], m.contacts)
        self.assertEqual(pyproj.CRS("EPSG:4326"), m.crs)

    def test_init(self):
        test_dataset_name = "Hey! This~is_one_str@ng£ DaTaSet |\\|ame"
        test_extent = Extent(box(-1, -1, 1, 1), TemporalExtent())
        test_keywords = ["one", "two", "three"]
        test_crs = pyproj.CRS("EPSG:4269")
        test_data_type = DataType.OBS_STATIONARY
        test_description = "This is a test"
        test_contacts = [ContactDetails("Mr", "John", "West", "johnwest@example.com")]

        m = Metadata(
            test_dataset_name, test_extent, test_crs, test_description, test_keywords, test_data_type, test_contacts)

        self.assertEqual(test_dataset_name, m.title)
        self.assertEqual(self.sanitise_id(test_dataset_name), m.id)
        self.assertEqual(test_extent, m.extent)
        self.assertEqual(test_keywords, m.keywords)
        self.assertEqual(test_data_type, m.data_type)
        self.assertEqual(test_description, m.description)
        self.assertEqual(test_contacts, m.contacts)
        self.assertEqual(test_crs, m.crs)


@pytest.mark.parametrize("dur_obj,str_dur", [
    (Duration(3, 6, 0, 4, 12, 30, 5), "P3Y6M4DT12H30M5S"),
    (Duration(1, 2, 0, 10, 2, 30), "P1Y2M10DT2H30M"),
    (Duration(seconds=0), "PT0S"),
    (Duration(days=0), "P0D"),
    (Duration(days=23, hours=23), "P23DT23H"),
    (Duration(4), "P4Y"),
    (Duration(months=1), "P1M"),
    (Duration(minutes=1), "PT1M"),
    (Duration(0.5), "P0.5Y"),
    (Duration(0.5), "P0,5Y"),
    (Duration(hours=36), "PT36H"),
    (Duration(days=1, hours=12), "P1DT12H"),
    (Duration(days=2.3, hours=2.3), "P2.3DT2.3H"),
    (Duration(weeks=4), "P4W"),
    (Duration(weeks=1.5), "P1.5W"),
])
def test_duration_str_conversion_valid(dur_obj: Duration, str_dur: str):
    """Can we convert back and forth between a Duration object and its ISO8601 string representation correctly?"""
    # TODO: assert str(dur_obj) == str_dur
    assert Duration.parse_str(str_dur) == dur_obj


@pytest.mark.parametrize("invalid_str_dur", [
    "P3Y6M4W4DT12H30M5S",  # Can't have weeks (W) with anything else
    "3Y6M4W4DT12H30M5S",  # Must have a leading P
    "P3Y6M4W4D12H30M5S",  # T separator is required between Y/M/W/D and H/M/S parts
    "P-1D",  # Negatives not allowed
    "P3S6M4HT12D30M5Y",  # In the spec, order matters, so I won't take on the complexity of figuring it out
    "",  # Empty string is not a valid representation
    # And now for some bad input values for good measure
    None,
    -1,
    ["P3Y6M4W4DT12H30M5S"],
    ["P", "3Y", "6M", "4W", "4D", "T", "12H", "30M", "5S"]
])
def test_duration_str_conversion_invalid(invalid_str_dur: str):
    """Can we convert back and forth between a Duration object and its ISO8601 string representation correctly?"""
    with pytest.raises(ValueError):
        Duration.parse_str(invalid_str_dur)
