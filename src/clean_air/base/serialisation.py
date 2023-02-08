import json
from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from edr_server.core.models.metadata import CollectionMetadata
from edr_server.core.serialisation import EdrJsonEncoder
from .models import Metadata

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


class MetadataJsonSerialiser(Serialiser[Metadata, str]):

    def __init__(self):
        self._encoder = EdrJsonEncoder()

    def serialise(self, obj: CollectionMetadata) -> str:
        return self._encoder.encode(obj)

    def deserialise(self, serialised_obj: str) -> CollectionMetadata:
        json_dict = json.loads(serialised_obj)
        return CollectionMetadata.from_json(json_dict)
