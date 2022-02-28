import string
import unittest
from datetime import datetime, timedelta

import pyproj
import pytest
from dateutil.tz import UTC, tzoffset
from shapely.geometry import box

from clean_air.models import Metadata, DataType, ContactDetails, TemporalExtent, Extent, Duration, DateTimeInterval


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
        d = Duration(seconds=1.1, minutes=2.2, hours=3.3, days=4.4, months=5, years=6)

        self.assertEqual(1.1, d.seconds)
        self.assertEqual(2.2, d.minutes)
        self.assertEqual(3.3, d.hours)
        self.assertEqual(4.4, d.days)
        self.assertEqual(5, d.months)  # Floats not allowed here
        self.assertEqual(6, d.years)  # Floats not allowed here

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
        d = Duration(6, 5, 4.4, 3.3, 2.2, 1.1)

        self.assertEqual(1.1, d.seconds)
        self.assertEqual(2.2, d.minutes)
        self.assertEqual(3.3, d.hours)
        self.assertEqual(4.4, d.days)
        self.assertEqual(5, d.months)  # Floats not allowed here
        self.assertEqual(6, d.years)  # Floats not allowed here

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
        d = Duration(0, 0, 0.0, 0.0, 0.0, 0.0)

        self.assertEqual(0.0, d.seconds)
        self.assertIsInstance(d.seconds, float)
        self.assertEqual(0.0, d.minutes)
        self.assertIsInstance(d.minutes, float)
        self.assertEqual(0.0, d.hours)
        self.assertIsInstance(d.hours, float)
        self.assertEqual(0.0, d.days)
        self.assertIsInstance(d.days, float)
        self.assertEqual(0, d.months)
        self.assertIsInstance(d.months, int)
        self.assertEqual(0, d.years)
        self.assertIsInstance(d.years, int)

        d = Duration(weeks=0.0)
        self.assertEqual(0.0, d.weeks)
        self.assertIsInstance(d.weeks, float)

    def test_init_at_least_one_value_set(self):
        """GIVEN no arguments are given WHEN a Duration is created THEN a ValueError is raised"""
        self.assertRaises(ValueError, Duration)

    def test_init_float_years_rejected(self):
        """
        GIVEN `years` is a flot WHEN a Duration is created THEN a ValueError is raised

        (Decimal years and months are ambiguous, so not supported)
        """
        self.assertRaises(ValueError, Duration, years=0.5)

    def test_init_float_months_rejected(self):
        """
        GIVEN `months` is a flot WHEN a Duration is created THEN a ValueError is raised

        (Decimal years and months are ambiguous, so not supported)
        """
        self.assertRaises(ValueError, Duration, months=0.5)


DURATION_ADDITION_TEST_CASES = [
    (Duration(1), Duration(1), Duration(2)),
    (Duration(1, 2, 3, 4, 5, 6), Duration(6, 5, 4, 3, 2, 1), Duration(7, 7, 7, 7, 7, 7)),
    (Duration(weeks=1), Duration(weeks=2), Duration(weeks=3)),
    # Weeks are converted to days when combined with anything other than weeks
    (Duration(1, 2, 3, 4, 5, 6), Duration(weeks=1), Duration(1, 2, 10, 4, 5, 6)),
    # Fractional amounts
    (Duration(days=0.5), Duration(days=0.5), Duration(days=1)),
    (Duration(hours=0.5), Duration(hours=0.5), Duration(hours=1)),
    (Duration(minutes=0.5), Duration(minutes=0.5), Duration(minutes=1)),
    (Duration(seconds=0.5), Duration(seconds=0.5), Duration(seconds=1)),
    (Duration(weeks=0.5), Duration(weeks=0.5), Duration(weeks=1)),
    (Duration(weeks=0.5), Duration(1, 2, 3, 4, 5, 6), Duration(1, 2, 6, 16, 5, 6)),

    # Overflowing fields
    # we don't normalise fields, e.g. convert 26 hours to 1 day 2 hours, so just test things add up correctly
    (Duration(months=6), Duration(months=7), Duration(months=13)),
    (Duration(days=10), Duration(days=25), Duration(days=35)),
    (Duration(hours=20), Duration(hours=20), Duration(hours=40)),
    (Duration(minutes=59), Duration(minutes=59), Duration(minutes=118)),
    (Duration(seconds=59), Duration(seconds=59), Duration(seconds=118)),
    (Duration(weeks=123), Duration(weeks=321), Duration(weeks=444)),

    # DATETIME TEST CASES
    (Duration(1, 2, 3, 4, 5, 6), datetime(2003, 1, 1, 2, 3, 4), datetime(2004, 3, 4, 6, 8, 10)),

    (Duration(months=6), datetime(2003, 1, 1, 2, 3, 4), datetime(2003, 7, 1, 2, 3, 4)),
    (Duration(days=1), datetime(2003, 1, 1, 2, 3, 4), datetime(2003, 1, 2, 2, 3, 4)),
    (Duration(hours=12), datetime(2003, 1, 1, 2, 3, 4), datetime(2003, 1, 1, 14, 3, 4)),
    (Duration(minutes=50), datetime(2003, 1, 1, 2, 3, 4), datetime(2003, 1, 1, 2, 53, 4)),
    (Duration(seconds=30), datetime(2003, 1, 1, 2, 3, 4), datetime(2003, 1, 1, 2, 3, 34)),
    (Duration(weeks=1), datetime(2003, 1, 1, 2, 3, 4), datetime(2003, 1, 8, 2, 3, 4)),

    (Duration(months=25), datetime(2003, 1, 1, 2, 3, 4), datetime(2005, 2, 1, 2, 3, 4)),
    (Duration(days=400), datetime(2003, 1, 1, 2, 3, 4), datetime(2004, 2, 5, 2, 3, 4)),
    (Duration(hours=36), datetime(2003, 1, 1, 2, 3, 4), datetime(2003, 1, 2, 14, 3, 4)),
    (Duration(minutes=120), datetime(2003, 1, 1, 2, 3, 4), datetime(2003, 1, 1, 4, 3, 4)),
    (Duration(seconds=120), datetime(2003, 1, 1, 2, 3, 4), datetime(2003, 1, 1, 2, 5, 4)),
    (Duration(weeks=123), datetime(2003, 1, 1, 2, 3, 4), datetime(2005, 5, 11, 2, 3, 4)),

    (Duration(days=0.5), datetime(2003, 1, 1, 2, 3, 4), datetime(2003, 1, 1, 14, 3, 4)),
    (Duration(hours=0.5), datetime(2003, 1, 1, 2, 3, 4), datetime(2003, 1, 1, 2, 33, 4)),
    (Duration(minutes=0.5), datetime(2003, 1, 1, 2, 3, 4), datetime(2003, 1, 1, 2, 3, 34)),
    (Duration(seconds=0.5), datetime(2003, 1, 1, 2, 3, 4), datetime(2003, 1, 1, 2, 3, 4, 500000)),
    (Duration(weeks=0.5), datetime(2003, 1, 1, 2, 3, 4), datetime(2003, 1, 4, 14, 3, 4)),

    # TIMEDELTA TEST CASES
    (Duration(1, 2, 3, 4, 5, 6), timedelta(weeks=1, days=2, hours=3, minutes=4, seconds=5),
     Duration(1, 2, 12, 7, 9, 11)),
    (Duration(weeks=1), timedelta(weeks=1, days=2, hours=3, minutes=4, seconds=5),
     Duration(days=16, hours=3, minutes=4, seconds=5)),

    (Duration(1, 2, 3, 4, 5, 6), timedelta(weeks=1), Duration(1, 2, 10, 4, 5, 6)),
    (Duration(1, 2, 3, 4, 5, 6), timedelta(days=1), Duration(1, 2, 4, 4, 5, 6)),
    (Duration(1, 2, 3, 4, 5, 6), timedelta(hours=1), Duration(1, 2, 3, 5, 5, 6)),
    (Duration(1, 2, 3, 4, 5, 6), timedelta(minutes=1), Duration(1, 2, 3, 4, 6, 6)),
    (Duration(1, 2, 3, 4, 5, 6), timedelta(seconds=1), Duration(1, 2, 3, 4, 5, 7)),
    (Duration(1, 2, 3, 4, 5, 6), timedelta(milliseconds=500), Duration(1, 2, 3, 4, 5, 6)),
    (Duration(1, 2, 3, 4, 5, 6), timedelta(milliseconds=499), Duration(1, 2, 3, 4, 5, 6)),
    (Duration(1, 2, 3, 4, 5, 6), timedelta(microseconds=500000), Duration(1, 2, 3, 4, 5, 6)),
    (Duration(1, 2, 3, 4, 5, 6), timedelta(microseconds=499999), Duration(1, 2, 3, 4, 5, 6)),

    (Duration(years=1), timedelta(weeks=1), Duration(years=1, days=7)),
    (Duration(months=25), timedelta(weeks=1), Duration(months=25, days=7)),
    (Duration(days=400), timedelta(days=1), Duration(days=401)),
    (Duration(hours=36), timedelta(hours=35), Duration(hours=71)),
    (Duration(minutes=120), timedelta(minutes=66), Duration(hours=3, minutes=6)),
    (Duration(seconds=120), timedelta(seconds=321), Duration(minutes=7, seconds=21)),
    (Duration(seconds=1), timedelta(milliseconds=2000), Duration(seconds=3)),
    (Duration(seconds=1), timedelta(milliseconds=1499), Duration(seconds=2)),
    (Duration(seconds=1), timedelta(milliseconds=1500), Duration(seconds=2)),
    (Duration(seconds=1), timedelta(microseconds=1000000), Duration(seconds=2)),
    (Duration(seconds=1), timedelta(microseconds=500000), Duration(seconds=1)),
    (Duration(seconds=1), timedelta(microseconds=490000), Duration(seconds=1)),

    (Duration(weeks=1), timedelta(weeks=1), Duration(weeks=2)),
    (Duration(weeks=1), timedelta(days=1), Duration(days=8)),
    (Duration(weeks=1), timedelta(hours=35), Duration(days=8, hours=11)),
    (Duration(weeks=1), timedelta(minutes=66), Duration(days=7, hours=1, minutes=6)),
    (Duration(weeks=1), timedelta(seconds=321), Duration(days=7, minutes=5, seconds=21)),
    (Duration(weeks=1), timedelta(milliseconds=2000), Duration(days=7, seconds=2)),
    (Duration(weeks=1), timedelta(milliseconds=1499), Duration(days=7, seconds=1)),
    (Duration(weeks=1), timedelta(milliseconds=1500), Duration(days=7, seconds=1)),
    (Duration(weeks=1), timedelta(microseconds=1000000), Duration(days=7, seconds=1)),
    (Duration(weeks=1), timedelta(microseconds=500000), Duration(days=7)),
    (Duration(weeks=1), timedelta(microseconds=490000), Duration(weeks=1)),

    (Duration(days=0.5), timedelta(weeks=1), Duration(days=7.5)),
    (Duration(hours=0.5), timedelta(weeks=1), Duration(days=7, hours=0.5)),
    (Duration(minutes=0.5), timedelta(weeks=1), Duration(days=7, minutes=0.5)),
    (Duration(seconds=0.5), timedelta(weeks=1), Duration(days=7, seconds=0.5)),
    (Duration(weeks=0.5), timedelta(weeks=1), Duration(weeks=1.5)),
]


@pytest.mark.parametrize("left_operand,right_operand,expected_result", DURATION_ADDITION_TEST_CASES, ids=repr)
def test_duration__add__(left_operand, right_operand, expected_result):
    """
    GIVEN operands A and B WHEN B is added to A THEN the expected result is returned.
    i.e. it tests what happens when we do `a_duration + an_object`.
    This tests the addition (`__add__`) method
    """
    assert left_operand + right_operand == expected_result


@pytest.mark.parametrize(
    # For these tests, we want to switch the transpose the operands from our common test cases, so that
    "left_operand,right_operand,expected_result", [(b, a, res) for a, b, res in DURATION_ADDITION_TEST_CASES], ids=repr)
def test_duration__radd__(left_operand, right_operand, expected_result):
    """
    GIVEN operands A and B WHEN A is added to B THEN the expected result is returned.
    i.e. it tests what happens when we do `an_object + a_duration`.
    This tests the reflected addition (`__radd__`) method
    """
    assert left_operand + right_operand == expected_result


# TODO implement __sub__ and __rsub__


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
    (Duration(days=0.5), "P0.5D"),
    (Duration(days=0.5), "P0,5D"),
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
    """Can we convert a Duration object to a valid ISO8601 string?"""
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
    """
    GIVEN an invalid string WHEN converting the string to a Duration object is attempted THEN a ValueError is raised
    """
    pytest.raises(ValueError, Duration.parse_str, invalid_str_dur)


class DateTimeIntervalTest(unittest.TestCase):

    def test_init_end_date_before_start_date(self):
        """GIVEN end date is before start date WHEN a DateTimeInterval is created THEN a ValueError is raised"""
        start_date = datetime.now()
        end_date = start_date - timedelta(days=1)

        self.assertRaises(ValueError, DateTimeInterval, start_date, end_date)

    def test_init_recurrences_less_than_minus_1(self):
        """GIVEN recurrences is less than -1 WHEN a DateTimeInterval is created THEN a ValueError is raised"""
        start_date = datetime.now()
        end_date = start_date + timedelta(days=1)

        # recurrences must be >= -1, so -2 is invalid
        self.assertRaises(ValueError, DateTimeInterval, start_date, end_date, recurrences=-2)

    def test_init_all_fields_set(self):
        """
        GIVEN start_date, end_date, and duration are provided
        WHEN a DateTimeInterval is created
        THEN a ValueError is raised

        The only valid combinations are:
        * start date & end date
        * start date & duration
        * duration & end date
        * duration only
        So everything else is not allowed
        """
        self.assertRaises(ValueError, DateTimeInterval, datetime.now(), datetime.now(), Duration(1))

    def test_init_only_start_date_set(self):
        """
        GIVEN only start_date is provided
        WHEN a DateTimeInterval is created
        THEN a ValueError is raised
        """
        self.assertRaises(ValueError, DateTimeInterval, datetime.now())

    def test_init_only_end_date_set(self):
        """
        GIVEN only end_date is provided
        WHEN a DateTimeInterval is created
        THEN a ValueError is raised
        """
        self.assertRaises(ValueError, DateTimeInterval, end=datetime.now())

    def test_init_only_duration_set(self):
        """
        GIVEN only duration is provided
        WHEN a DateTimeInterval is created
        THEN the correct DateTimeInterval is created
        """
        duration = Duration(1, 2, 3, 4)

        dti = DateTimeInterval(duration=duration)

        self.assertIsNone(dti.start)
        self.assertIsNone(dti.end)
        self.assertEqual(duration, dti.duration)

    @pytest.mark.skip("TODO")
    def test_start_property_inference(self):
        """
        GIVEN a DateTimeInterval created with end and duration parameters
        WHEN start property is accessed
        THEN the correct start date is returned
        """
        # TODO - write implementation so this test will pass
        d = Duration(weeks=1)
        end = datetime(2022, 1, 8)
        expected_start = datetime(2022, 1, 1)
        dti = DateTimeInterval(end=end, duration=d)

        self.assertEqual(expected_start, dti.start)

    def test_start_property_inference_duration_only(self):
        """
        GIVEN a DateTimeInterval created with just a duration parameter
        WHEN start property is accessed
        THEN None is returned
        """

        d = Duration(weeks=1)
        dti = DateTimeInterval(duration=d)

        self.assertIsNone(dti.start)

    @pytest.mark.skip("TODO")
    def test_end_property_inference(self):
        """
        GIVEN a DateTimeInterval created with start and duration parameters
        WHEN end property is accessed
        THEN the correct end date is returned
        """
        # TODO - write implementation so this test will pass
        d = Duration(weeks=1)
        start = datetime(2022, 1, 8)
        expected_end = datetime(2022, 1, 16)
        dti = DateTimeInterval(start=start, duration=d)

        self.assertEqual(expected_end, dti.start)

    def test_end_property_inference_duration_only(self):
        """
        GIVEN a DateTimeInterval created with just a duration parameter
        WHEN end property is accessed
        THEN None is returned
        """

        d = Duration(weeks=1)
        dti = DateTimeInterval(duration=d)

        self.assertIsNone(dti.end)

    @pytest.mark.skip("TODO")
    def test_duration_property_inference(self):
        """
        GIVEN a DateTimeInterval created with start and end date parameters
        WHEN duration property is accessed
        THEN the correct Duration is returned
        """
        # TODO - write implementation so this test will pass
        start = datetime(2010, 2, 1, 12, 30, 15)
        end = datetime(2013, 1, 12, 9, 15, 3)
        expected_duration = Duration(2, 11, 10, 20, 44, 48)

        dti = DateTimeInterval(start, end)

        self.assertEqual(expected_duration, dti.duration)


@pytest.mark.parametrize("str_dti, dti_obj", [
    # start/end interval tests
    ("2022-01-01T00:00:00Z/2022-01-01T12:00:00Z",
     DateTimeInterval(datetime(2022, 1, 1, tzinfo=UTC), datetime(2022, 1, 1, 12, tzinfo=UTC))),
    ("2022-01-01T00:00:00+00:00/2022-01-01T12:00:00+00:00",
     DateTimeInterval(datetime(2022, 1, 1, tzinfo=UTC), datetime(2022, 1, 1, 12, tzinfo=UTC))),
    # start/end interval tests - non UTC timezones
    ("2022-01-01T00:00:00+01:00/2022-01-01T12:00:00+01:00",
     DateTimeInterval(
         datetime(2022, 1, 1, tzinfo=tzoffset("", 3600)), datetime(2022, 1, 1, 12, tzinfo=tzoffset("", 3600)))
     ),
    ("2022-01-01T00:00:00-00:30/2022-01-01T12:00:00-00:30",
     DateTimeInterval(
         datetime(2022, 1, 1, tzinfo=tzoffset("", -1800)), datetime(2022, 1, 1, 12, tzinfo=tzoffset("", -1800)))),
    ("2022-01-01T00:00:00+0030/2022-01-01T12:00:00+0030",
     DateTimeInterval(
         datetime(2022, 1, 1, tzinfo=tzoffset("", 1800)), datetime(2022, 1, 1, 12, tzinfo=tzoffset("", 1800)))),
    ("2022-01-01T00:00:00-0030/2022-01-01T12:00:00-0030",
     DateTimeInterval(
         datetime(2022, 1, 1, tzinfo=tzoffset("", -1800)), datetime(2022, 1, 1, 12, tzinfo=tzoffset("", -1800)))),
    ("2022-01-01T00:00:00+12/2022-01-01T12:00:00+12",
     DateTimeInterval(
         datetime(2022, 1, 1, tzinfo=tzoffset("", 3600 * 12)),
         datetime(2022, 1, 1, 12, tzinfo=tzoffset("", 3600 * 12)))),
    ("2022-01-01T00:00:00-11/2022-01-01T12:00:00-11",
     DateTimeInterval(
         datetime(2022, 1, 1, tzinfo=tzoffset("", 3600 * -11)),
         datetime(2022, 1, 1, 12, tzinfo=tzoffset("", 3600 * -11)))),

    # start/duration tests
    ("2007-03-01T13:00:00Z/P1Y2M10DT2H30M",
     DateTimeInterval(datetime(2007, 3, 1, 13, tzinfo=UTC), duration=Duration(1, 2, 10, 2, 30))),

    # duration/end tests
    ("P1Y2M10DT2H30M/2008-05-11T15:30:00Z",
     DateTimeInterval(duration=Duration(1, 2, 10, 2, 30), end=datetime(2008, 5, 11, 15, 30, tzinfo=UTC))),

    # duration only tests
    ("P1Y2M10DT2H30M", DateTimeInterval(duration=Duration(1, 2, 10, 2, 30))),

    # Repeating interval tests
    ("R2/2022-01-01T00:00:00Z/2022-01-01T12:00:00Z",
     DateTimeInterval(datetime(2022, 1, 1, tzinfo=UTC), datetime(2022, 1, 1, 12, tzinfo=UTC), recurrences=2)),
    ("R5/2008-03-01T13:00:00Z/P1Y2M10DT2H30M",
     DateTimeInterval(datetime(2008, 3, 1, 13, tzinfo=UTC), duration=Duration(1, 2, 10, 2, 30), recurrences=5)),
    ("R0/P1Y2M10DT2H30M", DateTimeInterval(duration=Duration(1, 2, 10, 2, 30), recurrences=0)),
    ("R-1/P1Y2M10DT2H30M", DateTimeInterval(duration=Duration(1, 2, 10, 2, 30), recurrences=-1)),
])
def test_datetimeinterval_parse_str_valid(str_dti: str, dti_obj: DateTimeInterval):
    """Can we convert a valid ISO8601 duration string to a Duration object?"""
    # There are minor but important differences between these test cases and the object->str test cases, as the __str__
    # method uses a specific ISO compliant format and doesn't support generating all the different valid ISO flavours.
    # Which is why these test cases aren't shared like the equivalent Duration tests.

    assert DateTimeInterval.parse_str(str_dti) == dti_obj


@pytest.mark.parametrize("str_dti", [
    # Technically having -00:00 as the timezone offset is invalid, as should be +00:00. However, the dateutil library
    # handles this, and I don't think it's important enough to make it fail, so I've just left it here commented out
    # to acknowledge its validity as a test case and why we're not testing it
    # "2022-01-01T00:00:00-00:00/2022-01-01T12:00:00-00:00",
    "R-2/2022-01-01T00:00:00Z/2022-01-01T12:00:00Z"
])
def test_datetimeinterval_parse_str_invalid(str_dti: str):
    pytest.raises(ValueError, DateTimeInterval.parse_str, str_dti)


@pytest.mark.parametrize("dti_obj,str_dti", [
    # start/end interval tests
    (DateTimeInterval(datetime(2022, 1, 1, tzinfo=UTC), datetime(2022, 1, 1, 12, tzinfo=UTC)),
     "2022-01-01T00:00:00+00:00/2022-01-01T12:00:00+00:00"),
    (DateTimeInterval(datetime(2022, 1, 1, tzinfo=UTC), datetime(2022, 1, 1, 12, tzinfo=UTC)),
     "2022-01-01T00:00:00+00:00/2022-01-01T12:00:00+00:00"),
    # microseconds are ignored
    (DateTimeInterval(datetime(2022, 1, 1, 3, 4, 5, microsecond=6, tzinfo=UTC),
                      datetime(2022, 1, 1, 12, 1, 2, microsecond=3, tzinfo=UTC)),
     "2022-01-01T03:04:05+00:00/2022-01-01T12:01:02+00:00"),
    # start/end interval tests - non UTC timezones
    (DateTimeInterval(
        datetime(2022, 1, 1, tzinfo=tzoffset("", 3600)), datetime(2022, 1, 1, 12, tzinfo=tzoffset("", 3600))),
     "2022-01-01T00:00:00+01:00/2022-01-01T12:00:00+01:00"),
    (DateTimeInterval(
        datetime(2022, 1, 1, tzinfo=tzoffset("", -1800)), datetime(2022, 1, 1, 12, tzinfo=tzoffset("", -1800))),
     "2022-01-01T00:00:00-00:30/2022-01-01T12:00:00-00:30"),
    (DateTimeInterval(
        datetime(2022, 1, 1, tzinfo=tzoffset("", 1800)), datetime(2022, 1, 1, 12, tzinfo=tzoffset("", 1800))),
     "2022-01-01T00:00:00+00:30/2022-01-01T12:00:00+00:30"),
    (DateTimeInterval(
        datetime(2022, 1, 1, tzinfo=tzoffset("", -1800)), datetime(2022, 1, 1, 12, tzinfo=tzoffset("", -1800))),
     "2022-01-01T00:00:00-00:30/2022-01-01T12:00:00-00:30"),
    (DateTimeInterval(datetime(2022, 1, 1, tzinfo=tzoffset("", 3600 * 12)),
                      datetime(2022, 1, 1, 12, tzinfo=tzoffset("", 3600 * 12))),
     "2022-01-01T00:00:00+12:00/2022-01-01T12:00:00+12:00"),
    (DateTimeInterval(datetime(2022, 1, 1, tzinfo=tzoffset("", 3600 * -11)),
                      datetime(2022, 1, 1, 12, tzinfo=tzoffset("", 3600 * -11))),
     "2022-01-01T00:00:00-11:00/2022-01-01T12:00:00-11:00"),

    # start/duration tests
    (DateTimeInterval(datetime(2007, 3, 1, 13, tzinfo=UTC), duration=Duration(1, 2, 10, 2, 30)),
     "2007-03-01T13:00:00+00:00/P1Y2M10DT2H30M"),

    # duration/end tests
    (DateTimeInterval(duration=Duration(1, 2, 10, 2, 30), end=datetime(2008, 5, 11, 15, 30, tzinfo=UTC)),
     "P1Y2M10DT2H30M/2008-05-11T15:30:00+00:00"),

    # duration only tests
    (DateTimeInterval(duration=Duration(1, 2, 10, 2, 30)), "P1Y2M10DT2H30M"),

    # Repeating interval tests
    (DateTimeInterval(datetime(2022, 1, 1, tzinfo=UTC), datetime(2022, 1, 1, 12, tzinfo=UTC), recurrences=2),
     "R2/2022-01-01T00:00:00+00:00/2022-01-01T12:00:00+00:00"),
    (DateTimeInterval(datetime(2008, 3, 1, 13, tzinfo=UTC), duration=Duration(1, 2, 10, 2, 30), recurrences=5),
     "R5/2008-03-01T13:00:00+00:00/P1Y2M10DT2H30M"),
    (DateTimeInterval(duration=Duration(1, 2, 10, 2, 30), recurrences=0), "R0/P1Y2M10DT2H30M"),
    (DateTimeInterval(duration=Duration(1, 2, 10, 2, 30), recurrences=-1), "R-1/P1Y2M10DT2H30M"),
])
def test_datetimeinterval_str_valid(dti_obj: DateTimeInterval, str_dti: str, ):
    """Can we convert a Duration object to a valid ISO8601 string?"""
    # commas are valid as a separator, but we will always serialise using periods
    assert str(dti_obj) == str_dti
