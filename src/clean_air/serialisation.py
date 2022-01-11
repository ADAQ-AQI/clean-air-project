from abc import ABC, abstractmethod
from typing import Generic, TypeVar

import pyproj
import shapely.wkt
import yaml

from .models import Metadata, DataType

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

    def serialise(self, obj: Metadata) -> str:
        return yaml.safe_dump(
            {
                "dataset_name": obj.dataset_name,
                "extent": obj.extent.wkt,
                "description": obj.description,
                "crs": obj.crs.to_wkt(),
                "data_type": obj.data_type.value,
                "contacts": [],  # TODO
            }
        )

    def deserialise(self, serialised_obj: str) -> Metadata:
        obj_dict = yaml.safe_load(serialised_obj)
        obj_dict["extent"] = shapely.wkt.loads(obj_dict["extent"])
        obj_dict["crs"] = pyproj.CRS.from_wkt(obj_dict["crs"])
        obj_dict["data_type"] = DataType(obj_dict["data_type"])
        return Metadata(**obj_dict)
