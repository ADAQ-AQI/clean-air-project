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


class DurationTest(unittest.TestCase):

    def test_init_defaults(self):
        """GIVEN no arguments are passed WHEN a Duration is created THEN values default to 0"""
        d = Duration(weeks=1)  # We have to supply at least 1 value

        self.assertEqual(0, d.seconds)
        self.assertEqual(0, d.minutes)
        self.assertEqual(0, d.hours)
        self.assertEqual(0, d.days)
        self.assertEqual(0, d.months)
        self.assertEqual(0, d.years)

        d = Duration(years=1)  # Now check the default value for weeks
        self.assertEqual(0, d.weeks)

    def test_init_kwargs_ints(self):
        """WHEN a Duration is created using keyword arguments and integer values THEN the correct values are stored"""
        d = Duration(seconds=1, minutes=2, hours=3, days=4, months=5, years=6)

        self.assertEqual(1, d.seconds)
        self.assertEqual(2, d.minutes)
        self.assertEqual(3, d.hours)
        self.assertEqual(4, d.days)
        self.assertEqual(5, d.months)
        self.assertEqual(6, d.years)

        self.assertEqual(0, d.weeks)  # "weeks" cannot be combined with other args

    def test_init_kwargs_floats(self):
        """WHEN a Duration is created using keyword arguments and float values THEN the correct values are stored"""
        d = Duration(seconds=1.1, minutes=2.2, hours=3.3, days=4.4, months=5.5, years=6.6)

        self.assertEqual(1.1, d.seconds)
        self.assertEqual(2.2, d.minutes)
        self.assertEqual(3.3, d.hours)
        self.assertEqual(4.4, d.days)
        self.assertEqual(5.5, d.months)
        self.assertEqual(6.6, d.years)

        self.assertEqual(0, d.weeks)  # "weeks" cannot be combined with other args

    def test_init_positionals_ints(self):
        """
        WHEN a Duration is created using positional arguments and integer values THEN the correct values are stored
        """
        d = Duration(6, 5, 4, 3, 2, 1)

        self.assertEqual(1, d.seconds)
        self.assertEqual(2, d.minutes)
        self.assertEqual(3, d.hours)
        self.assertEqual(4, d.days)
        self.assertEqual(5, d.months)
        self.assertEqual(6, d.years)

        self.assertEqual(0, d.weeks)  # "weeks" cannot be combined with other args

    def test_init_positionals_floats(self):
        """WHEN a Duration is created using positional arguments and float values THEN the correct values are stored"""
        d = Duration(6.6, 5.5, 4.4, 3.3, 2.2, 1.1)

        self.assertEqual(1.1, d.seconds)
        self.assertEqual(2.2, d.minutes)
        self.assertEqual(3.3, d.hours)
        self.assertEqual(4.4, d.days)
        self.assertEqual(5.5, d.months)
        self.assertEqual(6.6, d.years)

        self.assertEqual(0, d.weeks)  # "weeks" cannot be combined with other args

    def test_init_weeks_int(self):
        """GIVEN weeks=1 WHEN a Duration is created THEN correct values are stored"""
        d = Duration(weeks=1)

        self.assertEqual(1, d.weeks)  # "weeks" cannot be combined with other args

        self.assertEqual(0, d.seconds)
        self.assertEqual(0, d.minutes)
        self.assertEqual(0, d.hours)
        self.assertEqual(0, d.days)
        self.assertEqual(0, d.months)
        self.assertEqual(0, d.years)

    def test_init_weeks_float(self):
        """GIVEN weeks=1 WHEN a Duration is created THEN correct values are stored"""
        d = Duration(weeks=1.1)

        self.assertEqual(1.1, d.weeks)  # "weeks" cannot be combined with other args

        self.assertEqual(0, d.seconds)
        self.assertEqual(0, d.minutes)
        self.assertEqual(0, d.hours)
        self.assertEqual(0, d.days)
        self.assertEqual(0, d.months)
        self.assertEqual(0, d.years)

    def test_init_negative_values(self):
        """GIVEN a negative value WHEN a Duration is created THEN a ValueError is raised"""
        # Negative values aren't allowed by ISO 8601
        self.assertRaises(ValueError, Duration, -1, 2, 3, 4, 5, 6)
        self.assertRaises(ValueError, Duration, 1, -2, 3, 4, 5, 6)
        self.assertRaises(ValueError, Duration, 1, 2, -3, 4, 5, 6)
        self.assertRaises(ValueError, Duration, 1, 2, 3, -4, 5, 6)
        self.assertRaises(ValueError, Duration, 1, 2, 3, 4, -5, 6)
        self.assertRaises(ValueError, Duration, 1, 2, 3, 4, 5, -6)
        self.assertRaises(ValueError, Duration, weeks=-7)

    def test_init_0_floats(self):
        """GIVEN a values of 0.0 WHEN a Duration is created THEN 0.0 is stored"""
        d = Duration(0.0, 0.0, 0.0, 0.0, 0.0, 0.0)

        self.assertEqual(0.0, d.seconds)
        self.assertIsInstance(d.seconds, float)
        self.assertEqual(0.0, d.minutes)
        self.assertIsInstance(d.minutes, float)
        self.assertEqual(0.0, d.hours)
        self.assertIsInstance(d.hours, float)
        self.assertEqual(0.0, d.days)
        self.assertIsInstance(d.days, float)
        self.assertEqual(0.0, d.months)
        self.assertIsInstance(d.months, float)
        self.assertEqual(0.0, d.years)
        self.assertIsInstance(d.years, float)

        d = Duration(weeks=0.0)
        self.assertEqual(0.0, d.weeks)
        self.assertIsInstance(d.weeks, float)

    def test_init_at_least_one_value_set(self):
        """GIVEN no arguments are given WHEN a Duration is create THEN a ValueError is raised"""
        self.assertRaises(ValueError, Duration)


@pytest.mark.parametrize("attr_name", ["seconds", "minutes", "hours", "days", "months", "years", "weeks"])
def test_duration_attrs_read_only(attr_name):
    """Test that attributes are read-only"""
    d = Duration(2, 3, 4, 5, 6, 7)
    pytest.raises(AttributeError, setattr, d, attr_name, 1)


@pytest.mark.parametrize("incompatible_kwarg", ["seconds", "minutes", "hours", "days", "months", "years"])
def test_duration_init_weeks_mutually_exclusive(incompatible_kwarg):
    """
    GIVEN weeks keyword argument is specified
    AND another keyword argument is specified
    WHEN Duration is created
    THEN ValueError is raised

    Put differently, if you use the weeks keyword argument, you can't use any of the other ones. This test will test
    what happens when you use 'weeks' along with each of the other keyword arguments.
    """
    # 0 is treated as a value for the purposes of this behaviour, as None is how we represent "not specified".
    # A 0 value will show up in the serialised string representation, whereas a None will not
    pytest.raises(ValueError, Duration, **{"weeks": 0, incompatible_kwarg: 0})


DURATION_STR_CONVERSION_TEST_CASES = [
    (Duration(3, 6, 4, 12, 30, 5), "P3Y6M4DT12H30M5S"),
    (Duration(1, 2, 10, 2, 30), "P1Y2M10DT2H30M"),
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
    (Duration(weeks=1.5), "P1,5W"),
    (Duration(weeks=0), "P0W"),
    (Duration(weeks=0.0), "P0.0W"),
]


@pytest.mark.parametrize("dur_obj,str_dur", DURATION_STR_CONVERSION_TEST_CASES)
def test_duration_parse_str_valid(dur_obj: Duration, str_dur: str):
    """Can we convert a valid ISO8601 duration string to a Duration object?"""
    assert Duration.parse_str(str_dur) == dur_obj


@pytest.mark.parametrize("dur_obj,str_dur", DURATION_STR_CONVERSION_TEST_CASES)
def test_duration_str_valid(dur_obj: Duration, str_dur: str):
    """Can a Duration object to a valid ISO8601 string ?"""
    # commas are valid as a separator, but we will always serialise using periods
    assert str(dur_obj) == str_dur.replace(",", ".")


@pytest.mark.parametrize(
    "invalid_str_dur", [
        "P3Y6M4W4DT12H30M5S",  # Can't have weeks (W) with anything else
        "3Y6M4W4DT12H30M5S",  # Must have a leading P
        "P3Y6M4W4D12H30M5S",  # T separator is required between Y/M/W/D and H/M/S parts
        "P-1D",  # Negatives not allowed
        "P3S6M4HT12D30M5Y",  # In the spec, order matters, so I won't take on the complexity of figuring it out
        # And now for some bad input values for good measure
        None,
        -1,
        ["P3Y6M4W4DT12H30M5S"],
        ["P", "3Y", "6M", "4W", "4D", "T", "12H", "30M", "5S"],
        "",  # Empty string is not a valid representation
    ],
    ids=lambda val: f"invalid_str_{val!r}"  # Fixes a test report issue due to empty string case
)
def test_duration_str_conversion_invalid(invalid_str_dur: str):
    """Can we convert back and forth between a Duration object and its ISO8601 string representation correctly?"""
    pytest.raises(ValueError, Duration.parse_str, invalid_str_dur)
