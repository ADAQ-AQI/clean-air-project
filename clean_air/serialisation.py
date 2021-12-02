from abc import ABC, abstractmethod
from typing import Generic, TypeVar

import yaml

from .models import MetaData

DeserialisedType = TypeVar("DeserialisedType")
SerialisedType = TypeVar("SerialisedType")


class Serialiser(Generic[DeserialisedType, SerialisedType], ABC):

    @abstractmethod
    def serialise(self, obj: DeserialisedType) -> SerialisedType:
        """Converts an object to its serialised form"""

    @abstractmethod
    def deserialise(self, serialised_obj: SerialisedType) -> DeserialisedType:
        """Converts from the serialised form to the deserialised object"""


class MetaDataSerialiser(Serialiser[MetaData, SerialisedType], ABC):
    """
    Base class for MetaData Serialisers.
    Constrains the `DeserialisedType` to `MetaData`, whilst leaving `SerialisedType` generic.
    Useful for when you want to indicate you want a serialiser that's compatible with `MetaData` objects, but don't care
    what serialisation format is used
    """


class MetaDataYamlSerialiser(Serialiser[MetaData, str]):

    def serialise(self, obj: MetaData) -> str:
        return yaml.safe_dump({"dataset_name": obj.dataset_name})

    def deserialise(self, serialised_obj: str) -> MetaData:
        return MetaData(**yaml.safe_load(serialised_obj))
