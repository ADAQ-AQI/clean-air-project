from abc import ABC, abstractmethod
from typing import Generic, TypeVar

import dateutil.parser
import pyproj
import shapely.wkt
import yaml

from .models import Metadata, DataType, Extent, TemporalExtent, DateTimeInterval

DeserialisedType = TypeVar("DeserialisedType")
SerialisedType = TypeVar("SerialisedType")


class Serialiser(Generic[DeserialisedType, SerialisedType], ABC):

    @abstractmethod
    def serialise(self, obj: DeserialisedType) -> SerialisedType:
        """Converts an object to its serialised form"""

    @abstractmethod
    def deserialise(self, serialised_obj: SerialisedType) -> DeserialisedType:
        """Converts from the serialised form to the deserialised object"""


class MetadataSerialiser(Serialiser[Metadata, SerialisedType], ABC):
    """
    Base class for Metadata Serialisers.
    Constrains the `DeserialisedType` to `MetaData`, whilst leaving `SerialisedType` generic.
    Useful for when you want to indicate you want a serialiser that's compatible with `MetaData` objects, but don't care
    what serialisation format is used
    """


class MetadataYamlSerialiser(Serialiser[Metadata, str]):

    @staticmethod
    def _serialise_extent(extent: Extent) -> dict:
        return {
            "spatial": extent.spatial.wkt,
            "temporal": MetadataYamlSerialiser._serialise_temporal_extent(extent.temporal)
        }

    @staticmethod
    def _serialise_temporal_extent(val: TemporalExtent) -> dict:
        return {
            "values": [dt.isoformat() for dt in val.values],
            "intervals": [str(dti) for dti in val.intervals]
        }

    @staticmethod
    def _deserialise_temporal_extent(serialised_temporal_extent: dict) -> TemporalExtent:

        values = [dateutil.parser.isoparse(str_dt) for str_dt in serialised_temporal_extent["values"]]
        intervals = [DateTimeInterval.parse_str(str_dti) for str_dti in serialised_temporal_extent["intervals"]]
        return TemporalExtent(values, intervals)

    @staticmethod
    def _deserialise_extent(extent_dict: dict) -> Extent:
        spatial_extent = shapely.wkt.loads(extent_dict["spatial"])
        temporal_extent = MetadataYamlSerialiser._deserialise_temporal_extent(extent_dict["temporal"])
        return Extent(spatial_extent, temporal_extent)

    def serialise(self, obj: Metadata) -> str:
        return yaml.safe_dump(
            {
                "title": obj.title,
                "extent": MetadataYamlSerialiser._serialise_extent(obj.extent),
                "description": obj.description,
                "keywords": obj.keywords,
                "crs": obj.crs.to_wkt(),
                "data_type": obj.data_type.value,
                "contacts": [],  # TODO
            }
        )

    def deserialise(self, serialised_obj: str) -> Metadata:
        obj_dict = yaml.safe_load(serialised_obj)
        for old_title_key in ["name", "dataset_name"]:
            # Backwards compatibility with previous versions
            if old_title_key in obj_dict:
                obj_dict["title"] = obj_dict[old_title_key]
                del obj_dict[old_title_key]

        # Partial implementation, full implementation to follow in another PR
        if isinstance(obj_dict["extent"], str):
            # Backwards compatibility with a previous version, to be phased out eventually
            obj_dict["extent"] = Extent(shapely.wkt.loads(obj_dict["extent"]), TemporalExtent())
        else:
            obj_dict["extent"] = MetadataYamlSerialiser._deserialise_extent(obj_dict["extent"])

        obj_dict["crs"] = pyproj.CRS.from_wkt(obj_dict["crs"])
        obj_dict["data_type"] = DataType(obj_dict["data_type"])
        return Metadata(**obj_dict)
