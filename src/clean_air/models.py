import dataclasses
import re
import string
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from functools import total_ordering
from pathlib import Path
from typing import List

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
@dataclass(frozen=True)
class Duration:
    """
    Represents an ISO8601 compliant time duration
    (as described by https://en.wikipedia.org/wiki/ISO_8601#Durations)

    It's important to remember that:
    * the number of hours in a day (although almost always 24) is not constant due to daylight savings time adjustments
      and leap seconds,
    * different months have different number of days, so P1M in the context of different dates will represent a
      different number of days

    This means that the same duration applied to different dates can result in different amounts of time being
    added/removed.
    For arithmetic between Duration instances, we've decided it's ok to treat days as 24 hours long, but not to assume
    months are 30 days long, so P20D + P20D would result in P40D and not P1M10D.

    Considering the python timedelta class, it treats days as being 24 hours long, so we view this as acceptable too.

    This class doesn't support the combined date and time representation format (e.g. P0003-06-04T12:30:05)
    """

    # Used for string parsing
    # I feel I should apologise for what follows, but also assure it could be a lot worse
    # Regex for matching a single field, parameterised to accept the match group name and unit character
    _FLOAT_REGEX_FMT = r"(?:(?P<{}>\d+(?:\.\d+)?){})?"
    _PARSER = re.compile("".join([
        "^P",
        _FLOAT_REGEX_FMT.format("years", "Y"),
        _FLOAT_REGEX_FMT.format("months", "M"),
        # _FLOAT_REGEX_FMT.format("weeks", "W"),
        _FLOAT_REGEX_FMT.format("days", "D"),
        "(?:T",  # T is required if any of the following fields are present
        _FLOAT_REGEX_FMT.format("hours", "H"),
        _FLOAT_REGEX_FMT.format("minutes", "M"),
        _FLOAT_REGEX_FMT.format("seconds", "S"),
        ")?",
    ]), re.ASCII)
    # If weeks are used, no other fields can be used. Couldn't get that 'or' logic working with a single regex, and
    # using 2 separate ones is probably clearer anyway
    _WEEK_PARSER = re.compile(r"^P(?P<weeks>\d+(?:\.\d+)?)W$", re.ASCII)

    years: float = 0
    months: float = 0
    weeks: float = 0
    days: float = 0
    hours: float = 0
    minutes: float = 0
    seconds: float = 0

    # TODO: We could add arithmetic between timedeltas, Durations, and datetimes etc, but until there's a need for it
    #       I won't

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

    @staticmethod
    def parse_str(str_dur: str) -> "Duration":
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
