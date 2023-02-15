import unittest
from clean_air.base.serialisation import MetadataJsonSerialiser
from edr_server.core.models.metadata import CollectionMetadata
from edr_server.core.models.extents import Extents, SpatialExtent
from shapely.geometry import box

class TestMetadataJsonSerialiser(unittest.TestCase):
	"Basic testing of MetadataJsonSerialiser properties"

	def setUp(self) -> None:
		self.metadata = CollectionMetadata(
			f"an ID", f"test dataset", "A Test", [], Extents(SpatialExtent(box(-1, -1, 1, 1))), [])
		self.string = r"""{"links": [], "id": "an ID", "title": "test dataset", "description": "A Test", 
		"keywords": [], "extent": {}, "output_formats": []}"""

	def test_serialise(self):
		"""
		GIVEN a CollectionMetadata object
		WHEN MetadataJsonSerialiser.serialise is called
		THEN the metadata is encoded to a string
		"""
		encoded = MetadataJsonSerialiser().serialise(self.metadata)
		assert isinstance(encoded, str)

	def test_deserialise(self):
		"""
		GIVEN a valid string
		WHEN MetadataJsonSerialiser.deserialise is called
		THEN the metadata is converted to a CollectionMetadata object
		"""
		decoded = MetadataJsonSerialiser().deserialise(self.string)
		assert isinstance(decoded, CollectionMetadata)
