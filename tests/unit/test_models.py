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


class DateTimeIntervalTest(unittest.TestCase):

    def test_constant_inifinite_recurrences(self):
        """Verify that DateTimeInterval.INFINITE_RECURRENCES is set to the correct value"""
        self.assertEqual(-1, DateTimeInterval.INFINITE_RECURRENCES)

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

    def test_start_property_inference(self):
        """
        GIVEN a DateTimeInterval created with end and duration parameters
        WHEN start property is accessed
        THEN the correct start date is returned
        """
        d = Duration(weeks=1)
        end = datetime(2022, 1, 8)
        expected_start = datetime(2022, 1, 1)
        dti = DateTimeInterval(end=end, duration=d)

        self.assertEqual(expected_start, dti.start)

    def test_start_property_inference_with_recurrence(self):
        """
        GIVEN a DateTimeInterval created with end, duration, and recurrences parameters
        WHEN start property is accessed
        THEN the correct start date is returned
        """
        d = Duration(weeks=1)
        recurrences = 40
        end = datetime(2022, 1, 8)
        expected_start = end - (timedelta(weeks=1) * recurrences)
        dti = DateTimeInterval(end=end, duration=d, recurrences=recurrences)

        self.assertEqual(expected_start, dti.start)

    def test_start_property_inference_with_recurrences_zero(self):
        """
        GIVEN a DateTimeInterval created with end and duration parameters
        AND recurrences=0
        WHEN start property is accessed
        THEN the correct start date is returned
        """
        d = Duration(weeks=1)
        end = datetime(2022, 1, 8)
        expected_start = datetime(2022, 1, 1)
        dti = DateTimeInterval(end=end, duration=d, recurrences=0)

        self.assertEqual(expected_start, dti.start)

    def test_start_property_inference_with_recurrence_infinite(self):
        """
        GIVEN a DateTimeInterval created with end, duration, and recurrences parameters
        AND recurrences are infinite (recurrences=-1)
        WHEN start property is accessed
        THEN None is returned
        """
        dti = DateTimeInterval(end=datetime(2022, 1, 8), duration=Duration(weeks=1), recurrences=-1)

        self.assertIsNone(dti.start)

    def test_end_property_inference(self):
        """
        GIVEN a DateTimeInterval created with start and duration parameters
        WHEN end property is accessed
        THEN the correct end date is returned
        """
        d = Duration(weeks=1)
        start = datetime(2022, 1, 8)
        expected_end = datetime(2022, 1, 15)
        dti = DateTimeInterval(start=start, duration=d)

        self.assertEqual(expected_end, dti.end)

    def test_end_property_inference_with_recurrence(self):
        """
        GIVEN a DateTimeInterval created with start, duration, & recurrence parameters
        WHEN end property is accessed
        THEN the correct end date is returned
        """
        d = Duration(weeks=1)
        recurrence = 5
        start = datetime(2022, 1, 8)
        expected_end = start + (timedelta(weeks=1) * recurrence)
        dti = DateTimeInterval(start=start, duration=d, recurrences=recurrence)

        self.assertEqual(expected_end, dti.end)

    def test_end_property_inference_with_recurrence_zero(self):
        """
        GIVEN a DateTimeInterval created with start and duration parameters
        AND recurrence=0
        WHEN end property is accessed
        THEN the correct end date is returned
        """
        d = Duration(weeks=1)
        start = datetime(2022, 1, 8)
        expected_end = datetime(2022, 1, 15)
        dti = DateTimeInterval(start=start, duration=d, recurrences=0)

        self.assertEqual(expected_end, dti.end)

    def test_end_property_inference_with_recurrence_infinite(self):
        """
        GIVEN a DateTimeInterval created with start, duration, and recurrences parameters
        AND recurrences are infinite (recurrences=-1)
        WHEN end property is accessed
        THEN None is returned
        """
        dti = DateTimeInterval(start=datetime(2022, 1, 8), duration=Duration(weeks=1), recurrences=-1)
        self.assertIsNone(dti.end)

    def test_duration_property_inference(self):
        """
        GIVEN a DateTimeInterval created with start and end date parameters
        WHEN duration property is accessed
        THEN the correct Duration is returned
        """
        start = datetime(2010, 2, 1, 12, 30, 15)
        end = datetime(2013, 1, 12, 9, 15, 3)
        expected_duration = Duration(years=2, days=345, hours=20, minutes=44, seconds=48)

        dti = DateTimeInterval(start, end)

        self.assertEqual(expected_duration, dti.duration)

    def test_duration_property_inference_with_recurrence(self):
        """
        GIVEN a DateTimeInterval created with start, end, & recurrence parameters
        WHEN duration property is accessed
        THEN the correct duration is returned
        """
        start = datetime(2010, 2, 1, 12, 30, 15)
        end = datetime(2013, 1, 12, 9, 15, 3)
        recurrence = 5
        expected_duration = Duration.from_timedelta((end - start) * recurrence)

        dti = DateTimeInterval(start, end, recurrences=recurrence)

        self.assertEqual(expected_duration, dti.duration)


    def test_duration_property_inference_with_recurrence_zero(self):
        """
        GIVEN a DateTimeInterval created with start and end parameters
        AND recurrence=0
        WHEN duration property is accessed
        THEN the correct duration is returned
        """
        start = datetime(2010, 2, 1, 12, 30, 15)
        end = datetime(2013, 1, 12, 9, 15, 3)
        expected_duration = Duration(years=2, days=345, hours=20, minutes=44, seconds=48)

        dti = DateTimeInterval(start, end, recurrences=0)

        self.assertEqual(expected_duration, dti.duration)

    def test_duration_property_inference_with_recurrence_infinite(self):
        """
        GIVEN a DateTimeInterval created with start, end, and recurrences parameters
        AND recurrences are infinite (recurrences=-1)
        WHEN duration property is accessed
        THEN None is returned
        """
        dti = DateTimeInterval(start=datetime(2022, 1, 8), end=datetime(2022, 1, 9), recurrences=-1)
        self.assertIsNone(dti.duration)

    def test_duration_only_properties_are_none(self):
        """
        WHEN a DateTimeInterval created with just a duration parameter
        THEN start property is None
        AND end property is None
        """

        d = Duration(weeks=1)
        dti = DateTimeInterval(duration=d)

        self.assertIsNone(dti.start)
        self.assertIsNone(dti.end)

    def test_duration_only_properties_are_none_with_recurrence(self):
        """
        WHEN a DateTimeInterval created with just a duration parameter
        AND a recurrences is a positive integer
        THEN start property is None
        AND end property is None
        """

        d = Duration(weeks=1)
        dti = DateTimeInterval(duration=d, recurrences=5)

        self.assertIsNone(dti.start)
        self.assertIsNone(dti.end)

    def test_duration_only_properties_are_none_with_recurrence_zero(self):
        """
        WHEN a DateTimeInterval created with just a duration parameter
        AND a recurrences is zero
        THEN start property is None
        AND end property is None
        """

        d = Duration(weeks=1)
        dti = DateTimeInterval(duration=d, recurrences=0)

        self.assertIsNone(dti.start)
        self.assertIsNone(dti.end)

    def test_duration_only_properties_are_none_with_recurrence_infinite(self):
        """
        WHEN a DateTimeInterval created with just a duration parameter
        AND recurrences are infinite (recurrences=-1)
        THEN start property is None
        AND end property is None
        """

        d = Duration(weeks=1)
        dti = DateTimeInterval(duration=d, recurrences=-1)

        self.assertIsNone(dti.start)
        self.assertIsNone(dti.end)

    def test_recurrences(self):
        """
        GIVEN a DateTimeInterval created with recurrences specified
        THEN the recurrences property gives the value the instance was created with
        """
        expected_recurrences = 7
        dti = DateTimeInterval(duration=Duration(1), recurrences=expected_recurrences)
        self.assertEqual(expected_recurrences, dti.recurrences)

    def test_recurrences_default(self):
        """
        GIVEN a DateTimeInterval created without providing a value for recurrences
        THEN the recurrences property returns 0
        """
        dti = DateTimeInterval(duration=Duration(1))
        self.assertEqual(0, dti.recurrences)

    def test_recurrences_inifite(self):
        """
        GIVEN a DateTimeInterval created with infinite (-1) recurrences specified
        THEN the recurrences property gives the value the instance was created with
        """
        expected_recurrences = -1
        dti = DateTimeInterval(duration=Duration(1), recurrences=expected_recurrences)
        self.assertEqual(expected_recurrences, dti.recurrences)

    def test_recurrences_non_recurrence_implied(self):
        """
        GIVEN a DateTimeInterval created with recurrences=None
        THEN the recurrences property returns 0
        """
        dti = DateTimeInterval(duration=Duration(1), recurrences=None)
        self.assertEqual(0, dti.recurrences)

    def test_recurrences_non_recurrence_explicit(self):
        """
        GIVEN a DateTimeInterval created with recurrences=0
        THEN the recurrences property returns 0
        """
        dti = DateTimeInterval(duration=Duration(1), recurrences=0)
        self.assertEqual(0, dti.recurrences)


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
