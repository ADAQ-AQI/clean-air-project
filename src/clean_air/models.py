import dataclasses
import string
from dataclasses import dataclass
from enum import Enum
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


@dataclass
class Metadata:
    dataset_name: str
    extent: shapely.geometry.Polygon
    crs: pyproj.CRS = pyproj.CRS("EPSG:4326")
    description: str = ""
    data_type: DataType = DataType.OTHER
    contacts: List[ContactDetails] = dataclasses.field(default_factory=list)

    @property
    def id(self):
        return self.dataset_name.lower().replace(string.punctuation, "_")


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
        return self.metadata.dataset_name if self.metadata else ""

    @property
    def id(self):
        return self.metadata.id if self.metadata else None
