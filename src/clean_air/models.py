import dataclasses
import re
import string
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from functools import total_ordering
from pathlib import Path
from typing import List, Optional

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

    It's important to remember that:
    * the number of hours in a day (although almost always 24) is not constant due to daylight savings time adjustments
      and leap seconds,
    * different months have different number of days, so P1M in the context of different dates will represent a
      different number of days

    his means that the same duration applied to different dates can result in different amounts of time being
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
        * P1.5M would not be converted to P1M15D

    For the addition/subtraction of Durations from datetimes, because we'd be adding/removing time from a known
    reference point, we would be able to take into account the length of months, daylight savings time, etc

    Considering the python timedelta class, it treats days as being 24 hours long, so we view this as acceptable too.
    """
    # This class is intended to be read-only. Similar to timedelta, most operations that would cause a change should
    # return a new instance. Here are some things that we could implement, but haven't needed as yet:

    # TODO: .replace() method to create a copy of the Duration with the given fields replaced with the supplied values
    # TODO: .remove() method to create a copy of the Duration with the given fields removed
    # TODO: Implement __add__ and __sub__ with support for Duration, timedelta, and datetime instances

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
            years: Optional[float] = None,
            months: Optional[float] = None,
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

    def __str__(self) -> str:
        """Create an ISO 8601 compliant string representation"""
        if self._weeks is not None:
            return f"P{self._weeks}W"

        s = "P"
        if self._years is not None:
            s += f"{self._years}Y"
        if self._months is not None:
            s += f"{self._months}M"
        if self._days is not None:
            s += f"{self._days}D"

        if any(v is not None for v in [self._hours, self._minutes, self._seconds]):
            s += "T"
            if self._hours is not None:
                s += f"{self._hours}H"
            if self._minutes is not None:
                s += f"{self._minutes}M"
            if self._seconds is not None:
                s += f"{self._seconds}S"

        return s

    def __repr__(self):
        if self._weeks is not None:
            args_str = f"weeks={self._weeks!r}"
        else:
            args_str = ", ".join(
                f"{attr}={getattr(self, attr)!r}"
                for attr in ["years", "months", "days", "hours", "minutes", "seconds"]
                if getattr(self, attr) is not None
            )

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
class TemporalExtent:
    """"""

    _dt: datetime = datetime(2022, 2, 2)

    @property
    def interval(self) -> (datetime, datetime):
        """Returns the earliest and latest datetimes covered by the extent"""
        # Conceptually, an open-ended interval is possible, in which case None is used
        # In the Clean Air Framework or EDR, we don't expect to use that case, but it is supported
        # stubbed implementation, pending full implementation in another PR
        return self._dt, self._dt


@dataclass
class Extent:
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
