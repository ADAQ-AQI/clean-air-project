import dataclasses
import math
import re
import string
import warnings
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from functools import total_ordering
from pathlib import Path
from typing import List, Optional, Union, Tuple

import dateutil.parser
import pyproj
import shapely.geometry


class DataType(Enum):
    MODEL_GRIDDED = "model_gridded"
    MODEL_NONGRIDDED = "model_nongridded"
    OBS_STATIONARY = "obs_stationary"
    OBS_MOBILE = "obs_mobile"
    OTHER = "other"


@dataclass
class ContactDetails:
    title: str = ""
    first_name: str = ""
    surname: str = ""
    email_address: str = ""
    affiliation: str = ""


@total_ordering
class Duration:
    """
    Represents an ISO8601 compliant time duration
    (as described by https://en.wikipedia.org/wiki/ISO_8601#Durations)
    This class doesn't support the combined date and time representation format (e.g. P0003-06-04T12:30:05)

    Negative values are not part of the ISO8601 spec, and thus are not supported

    It's important to remember that:
    * the number of hours in a day (although almost always 24) is not constant due to daylight savings time adjustments
      and leap seconds,
    * different months have different number of days, so P1M in the context of different dates will represent a
      different number of days

    This means that the same duration applied to different dates can result in different amounts of time being
    added/removed.

    We've decided to try and be consistent with the behaviour of python's timedelta as much as possible, but note that
    the timedelta class doesn't support weeks, months, or years. Presumably to avoid issues arising from ambiguity
    caused by different calendars.

    We've also taken the decision that Durations will be naive: they won't try to take into account differences caused
    by calendars.

    For arithmetic between Duration instances, we've decided that because:
    * python's timedelta assumes days are always 24 hours long, we will also assume that
    * the length of months vary, we can't assume 1 month == 30 days.
      * hence, we won't convert from days->months or months->days, so
        * P20D + P20D would result in P40D and not P1M10D.
        * P1M would not be converted to P30D
      * we won't allow decimal fractions for months or years (since decimal fractions in years means we have to deal
        with fractions of a month)

    For the addition/subtraction of Durations from datetimes, because we'd be adding/removing time from a known
    reference point, we would be able to take into account the length of months, daylight savings time, etc

    Considering the python timedelta class, it treats days as being 24 hours long, so we view this as acceptable too.
    """
    # This class is intended to be read-only. Similar to timedelta, most operations that would cause a change should
    # return a new instance. Here are some things that we could implement, but haven't needed as yet:

    # TODO: .replace() method to create a copy of the Duration with the given fields replaced with the supplied values
    # TODO: .remove() method to create a copy of the Duration with the given fields removed

    # These regexes are for parsing and extracting the values from ISO 8601 duration strings
    # I feel I should apologise for what follows, but also assure it could be a lot worse...
    # Regex for matching a single field, parameterised to accept the match group name and unit character
    _FLOAT_REGEX_FMT = r"(?:(?P<{}>\d+(?:\.\d+)?){})?"
    # Regex for parsing and extracting most of an ISO 8601 duration string
    _PARSER = re.compile("".join([
        "^P",
        _FLOAT_REGEX_FMT.format("years", "Y"),
        _FLOAT_REGEX_FMT.format("months", "M"),
        _FLOAT_REGEX_FMT.format("days", "D"),
        "(?:T",  # T is required if any of the following fields are present
        _FLOAT_REGEX_FMT.format("hours", "H"),
        _FLOAT_REGEX_FMT.format("minutes", "M"),
        _FLOAT_REGEX_FMT.format("seconds", "S"),
        ")?",
    ]), re.ASCII)
    # Regex for parsing and extracting the special case of weeks, which can't be combined with any of the other fields
    _WEEK_PARSER = re.compile(r"^P(?P<weeks>\d+(?:\.\d+)?)W$", re.ASCII)

    def __init__(
            self,
            years: Optional[int] = None,
            months: Optional[int] = None,
            days: Optional[float] = None,
            hours: Optional[float] = None,
            minutes: Optional[float] = None,
            seconds: Optional[float] = None,
            *,  # Prevent weeks from being specified by positional argument, because it's invalid to combine weeks
            # with other arguments
            weeks: Optional[float] = None,
    ):
        # Remember that float implies int as well, so either can be stored, and its type matters for reconstructing
        # parsed strings that match the original input (with the caveat that we don't store which decimal separator
        # was used, as that seems too esoteric and fiddly for the uses this code was written for)

        args = [years, months, days, hours, minutes, seconds, weeks]
        if all(arg is None for arg in args):
            raise ValueError("At least one argument must be supplied")
        if any(arg < 0 for arg in args if arg is not None):
            raise ValueError(f"Arguments cannot be less than 0! arguments={args!r}")

        if weeks is not None and any(v is not None for v in args[:-1]):
            # If we allowed this, we couldn't generate a valid ISO 8601 string
            raise ValueError("'weeks' cannot be combined with any other arguments")

        if years and not isinstance(years, int):
            raise ValueError(
                "'years' must be an int because non-integer years and months are ambiguous and not currently supported"
            )
        if months and not isinstance(months, int):
            raise ValueError(
                "'months' must be an int because non-integer years and months are ambiguous and not currently supported"
            )
        self._years = years
        self._months = months
        self._days = days
        self._hours = hours
        self._minutes = minutes
        self._seconds = seconds
        self._weeks = weeks

    @property
    def years(self) -> float:
        return self._years if self._years is not None else 0

    @property
    def months(self) -> float:
        return self._months if self._months is not None else 0

    @property
    def days(self) -> float:
        return self._days if self._days is not None else 0

    @property
    def hours(self) -> float:
        return self._hours if self._hours is not None else 0

    @property
    def minutes(self) -> float:
        return self._minutes if self._minutes is not None else 0

    @property
    def seconds(self) -> float:
        return self._seconds if self._seconds is not None else 0

    @property
    def weeks(self) -> float:
        return self._weeks if self._weeks is not None else 0

    @staticmethod
    def _get_months_seconds(dur: "Duration") -> (int, int):
        months = dur.months if dur.months else 0
        months += dur.years * 12 if dur.years else 0

        seconds = dur.seconds if dur.seconds else 0
        seconds += dur.hours * 3600 if dur.hours else 0
        seconds += dur.days * 86400 if dur.days else 0
        seconds += dur.weeks * 604800 if dur.weeks else 0

        return months, seconds

    def __eq__(self, other):
        # Required for @total_ordering to provide a full suite of rich comparison operators
        return Duration._get_months_seconds(self) == Duration._get_months_seconds(other)

    def __lt__(self, other):
        # Required for @total_ordering to provide a full suite of rich comparison operators
        return Duration._get_months_seconds(self) < Duration._get_months_seconds(other)

    def _add_durations(self, other: "Duration") -> "Duration":
        kwargs = {}

        if self._weeks and other._weeks:
            kwargs["weeks"] = self.weeks + other.weeks
        elif self._weeks or other._weeks:
            # When adding weeks to a duration that doesn't use weeks,
            # the weeks must be converted to years, months, days, etc (remembering that weeks can be a float, like 1.75)
            _WEEKS_IN_YEAR = 52
            _DAYS_IN_WEEK = 7
            _HOURS_IN_DAY = 24
            _MINS_IN_HOUR = 60
            _SECS_IN_MIN = 60

            # Work out which of the 2 durations has the weeks value, and store that value
            weeks = self._weeks if self._weeks else other._weeks
            dur = other if self._weeks else self  # The Duration that doesn't have a "weeks" value

            # Get starting values for fields from the Duration that doesn't have weeks
            kwargs = {
                "years": dur._years,
                "months": dur._months,
                "days": dur._days,
                "hours": dur._hours,
                "minutes": dur._minutes,
                "seconds": dur._seconds
            }

            # Convert the weeks value to years/months/days/hours/minutes/seconds
            if weeks >= _WEEKS_IN_YEAR:
                years = math.floor(weeks / _WEEKS_IN_YEAR)
                weeks -= years * _WEEKS_IN_YEAR
            else:
                years = None
            # ignore months, because months aren't a consistent length and so the conversion is ambiguous

            partial_days, days = math.modf(weeks * _DAYS_IN_WEEK)
            partial_hours, hours = math.modf(partial_days * _HOURS_IN_DAY)
            partial_minutes, minutes = math.modf(partial_hours * _MINS_IN_HOUR)
            seconds = round(partial_minutes * _SECS_IN_MIN)

            # Add the converted year/month/day/hours/minutes/seconds values to the starting values
            if years:
                kwargs["years"] = kwargs["years"] + years if kwargs["years"] else years
            if days:
                kwargs["days"] = kwargs["days"] + days if kwargs["days"] else days
            if hours:
                kwargs["hours"] = kwargs["hours"] + hours if kwargs["hours"] else hours
            if minutes:
                kwargs["minutes"] = kwargs["minutes"] + minutes if kwargs["minutes"] else minutes
            if seconds:
                kwargs["seconds"] = kwargs["seconds"] + seconds if kwargs["seconds"] else seconds

        else:
            # Straight-forward case of combining the values from two Durations that don't use weeks
            # We don't normalise values, so don't care whether they "rollover" (e.g. a value of 26 hours is fine,
            # we don't attempt to convert it to 1 day & 2 hours)

            # We check the private attributes, because they distinguish between an explicit 0 and unset
            # We add using the public properties because it simplifies the operation
            # because any Nones get converted to 0
            if self._years is not None or other._years is not None:
                kwargs["years"] = self.years + other.years

            if self._months is not None or other._months is not None:
                kwargs["months"] = self.months + other.months

            if self._days is not None or other._days is not None:
                kwargs["days"] = self.days + other.days

            if self._hours is not None or other._hours is not None:
                kwargs["hours"] = self.hours + other.hours

            if self._minutes is not None or other._minutes is not None:
                kwargs["minutes"] = self.minutes + other.minutes

            if self._seconds is not None or other._seconds is not None:
                kwargs["seconds"] = self.seconds + other.seconds

        return Duration(**kwargs)

    def __add__(self, other):
        if isinstance(other, Duration):
            return self._add_durations(other)

        return NotImplemented

    def __radd__(self, other):
        return NotImplemented

    def __str__(self) -> str:
        """
        Create an ISO 8601  string representation compliant with these rules:
        https://en.wikipedia.org/wiki/ISO_8601#Durations
        """
        if self._weeks is not None:
            return f"P{self._weeks}W"

        # Work out which things we need to include. None indicates unset/not included/omitted, so filter out the Nones
        pre_t_fields = [f for f in [(self._years, "Y"), (self._months, "M"), (self._days, "D")] if f[0] is not None]
        post_t_fields = [
            f for f in [(self._hours, "H"), (self._minutes, "M"), (self._seconds, "S")] if f[0] is not None]

        str_parts = ["P"] + [f"{val}{unit}" for val, unit in pre_t_fields]

        if post_t_fields:
            str_parts.extend("T")
            str_parts.extend(f"{val}{unit}" for val, unit in post_t_fields)

        return "".join(str_parts)

    def __repr__(self):
        if self._weeks is not None:
            args_str = f"weeks={self._weeks!r}"
        else:
            args_list = []
            for attr in ["years", "months", "days", "hours", "minutes", "seconds"]:
                attr_val = getattr(self, f"_{attr}")  # Check private, internal attribute, not public property
                if attr_val is not None:
                    args_list.append(f"{attr}={attr_val!r}")
            args_str = ", ".join(args_list)

        return f"Duration({args_str})"

    @staticmethod
    def parse_str(str_dur: str) -> "Duration":
        """
        Convert a valid ISO 8601 Duration string to a Duration object.
        The combined date and time representation format (e.g. P0003-06-04T12:30:05)
        """
        # Considering the best way to parse this, generally the string is made up a series of pairs. Each pair
        # has a character that identifies the unit and a value. The value can be multiple characters. Additionally,
        # there is a preceding P and potentially a T mid-string to indicate transition from years/months/weeks/days to
        # hours/minutes/seconds.

        # As a result, a loop based method that examines 1 character at a time is going to get complex, as we need to
        # track state such as whether we've seen a T character, which unit we're processing, and collecting values that
        # span multiple characters across loop iterations.

        # Therefore, I think a regex approach will be the lesser of the available evils and yield the clearest and
        # easiest to maintain code.

        try:
            # Substituting "," for "." simplifies the regex and subsequent conversion from str to int/float
            clean_dur_str = str_dur.replace(",", ".").strip()
        except AttributeError as e:
            raise ValueError(f"{str_dur!r} doesn't appear to be a string: {e}")

        parsed_str = Duration._PARSER.fullmatch(clean_dur_str) or Duration._WEEK_PARSER.fullmatch(clean_dur_str)
        if parsed_str is None:
            raise ValueError(f"Unable to parse {str_dur!r}; Probably because it's invalid")

        kwargs = {
            k: float(v) if "." in v else int(v)
            for k, v in parsed_str.groupdict().items()
            if v is not None  # Filter out non-matches
        }
        return Duration(**kwargs)


@dataclass
class DateTimeInterval:
    """
    Represents an ISO 8601 compliant time interval
    (as described by https://en.wikipedia.org/wiki/ISO_8601#Time_intervals)

    An ISO 8601 compliant time interval can be one of the following:
    * a start and end datetime
    * a start datetime and a duration
    * a duration and an end datetime
    * a duration

    Optionally, interval can recur:
    * a set number of times (recurrences=N where N is the number of times to recur)
    * infinitely (recurrences=-1)
    * or not at all (recurrences=None)

    In our implementation, recurrences=0 is semantically the same as recurrences=None (i.e. no repetition, but generates
     a different string representation in line with the standard):
    * When recurrences=None, the `R[n]/` part of the string representation is omitted
    * When recurrences=0, `R0/` is prefixed to the string representation to explicitly indicate 0 repetitions
    """

    def __init__(
            self,
            start: Optional[datetime] = None,
            end: Optional[datetime] = None,
            duration: Optional[Duration] = None,
            recurrences: Optional[int] = None
    ):
        """
        :param start: The beginning of the interval. Can be combined with `end` or `duration`, but not both at the same
                      time. Must come before `end` if 'end' is given.
        :param end: The end of the interval. Can be combined with `end` or `duration`, but not both at the same time.
                    Must come after `start` if 'start' is given.
        :param duration: Indicates the span of time covered by this interval. Can be supplied on its own, or with a
                         `start` or `end` (but not both at the same time). If supplied on its own, it won't be possible
                         to calculate the bounds of this interval.
        """
        if start and end and start > end:
            raise ValueError("start datetime cannot be after end datetime")

        if start and end and duration:
            raise ValueError("Cannot set start, end, and duration together. It's not a valid combination")
        if start and not (end or duration):
            raise ValueError("start cannot be specified on its own. Please provide either and end date or a duration")
        if end and not (start or duration):
            raise ValueError("end cannot be specified on its own. Please provide either and end date or a duration")
        if recurrences is not None and recurrences < -1:
            raise ValueError("recurrences cannot be less than -1")

        self.start = start
        self.end = end
        self.duration = duration
        self.recurrences = recurrences

    def __str__(self) -> str:
        """
        Converts the object to the ISO 8601 string representation of this interval

        The generated string will be based off the arguments passed to the __init__ method. For example, if the object
         was created with `start` and `end` dates, expect the `<start>/<end>` version. Whereas if `end` and `duration` were
         passed, expect `<duration>/<end>`.

        Because there are many flavours of valid ISO string, calling this method on an object created by parsing an ISO
        string isn't guaranteed to re-create the original input. The resulting string will be equivalent, but may not be
        identical.
        """
        parts = []
        if self.recurrences is not None:
            parts.append(f"R{self.recurrences}")

        if self.duration:
            if self.start:
                parts.append(self.start.isoformat(timespec="seconds"))
                parts.append(str(self.duration))
            elif self.end:
                parts.append(str(self.duration))
                parts.append(self.end.isoformat(timespec="seconds"))
            else:
                parts.append(str(self.duration))
        else:
            parts.append(self.start.isoformat(timespec="seconds"))
            parts.append(self.end.isoformat(timespec="seconds"))

        return "/".join(parts)

    @staticmethod
    def parse_str(str_dti: str) -> "DateTimeInterval":
        """
        Convert a valid ISO 8601 time interval string into a DateTimeInterval object

        The implementation is based on the description of ISO 8601 time intervals here:
        https://en.wikipedia.org/wiki/ISO_8601#Time_intervals

        As such, the supported representations are:
        * <start>/<end>
        * <start>/<duration>
        * <duration>/<end>
        * <duration>
        The optional recurrence prefix `R[n]/` is also supported.

        Where <start> & <end> are valid ISO 8601 datetime strings, and <duration> is a valid ISO 8601 duration string.
        Once split into the individual elements, parsing is provided by `dateutil.parser.isoparse` for `datetime`s and
        `Duration.parse_str` for durations. Refer to the respective documentation for the limitations of these parsers.

        Concise datetime representations, such as "2007-12-14T13:30/15:30", "2008-02-15/03-14", and
        "2007-11-13T09:00/15T17:00", are not supported. (TODO: add support)
        """

        start, end, duration, recurrences = None, None, None, None

        parts = str_dti.split("/")
        for p in parts:
            if p.startswith("R"):
                recurrences = int(p[1:])
            elif p.startswith("P"):
                duration = Duration.parse_str(p)
            else:
                if duration or start:
                    end = dateutil.parser.isoparse(p)
                else:
                    start = dateutil.parser.isoparse(p)

        return DateTimeInterval(start, end, duration, recurrences)


@dataclass
class TemporalExtent:
    """
    The specific times and time ranges covered by a dataset
    A temporal extent can be made up of one or more DateTimeIntervals, one or more specific datetimes, or a
    combination of both
    """
    values: List[Union[datetime, DateTimeInterval]] = dataclasses.field(default_factory=list)

    @property
    def interval(self) -> Tuple[Optional[datetime], Optional[datetime]]:
        warnings.warn("Renamed to 'bounds' to avoid confusion with a list of DateTimeIntervals", DeprecationWarning)
        return self.bounds

    @property
    def bounds(self) -> Tuple[Optional[datetime], Optional[datetime]]:
        """
        Returns the earliest and latest datetimes covered by the extent.

        None indicates an open-ended interval, such as where a duration repeats indefinitely. The lower bound, upper
        bound, or both lower & and upper bounds can be open, depending on the extent being represented.
        """
        # TODO test and implement
        return datetime(2022, 2, 2), datetime(2022, 2, 3)  # stubbed implementation


@dataclass
class Extent:
    """A struct-like container for the geographic area and time range(s) covered by a dataset"""
    spatial: shapely.geometry.Polygon
    temporal: TemporalExtent


@dataclass
class Metadata:
    title: str
    extent: Extent
    crs: pyproj.CRS = pyproj.CRS("EPSG:4326")
    description: str = ""
    keywords: List[str] = dataclasses.field(default_factory=list)
    data_type: DataType = DataType.OTHER
    contacts: List[ContactDetails] = dataclasses.field(default_factory=list)

    @property
    def id(self):
        id_str = self.title
        for c in string.punctuation.replace("_", ""):
            if c in id_str:
                id_str = id_str.replace(c, "")
        for c in string.whitespace:
            if c in id_str:
                id_str = id_str.replace(c, "_")
        return id_str.lower()


# Assume 1 metadata file for whole dataset, and metadata is consistent across files
# All files are same filetype
# All files are netcdf4
@dataclass
class DataSet:
    """"""

    files: List[Path] = None
    metadata: Metadata = None

    @property
    def name(self):
        return self.metadata.title if self.metadata else ""

    @property
    def id(self):
        return self.metadata.id if self.metadata else None
