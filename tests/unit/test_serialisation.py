import unittest

import yaml
from shapely.geometry import box

from clean_air.models import Metadata, DataType, Extent, TemporalExtent
from clean_air.serialisation import MetadataYamlSerialiser


class MetadataYamlSerialiserTest(unittest.TestCase):

    def setUp(self) -> None:
        self.serialiser = MetadataYamlSerialiser()
        self.test_metadata = Metadata(
            title="Test",
            extent=Extent(box(-1, -1, 1, 1), TemporalExtent()),
            description="test description",
            keywords=["a", "b", "c"],
            data_type=DataType.MODEL_GRIDDED,
            contacts=[],
        )

    def get_expected_yaml(self, m: Metadata) -> str:
        return yaml.dump({
            "title": m.title,
            "extent": {
                "spatial": m.extent.spatial.wkt,
                "temporal": "2022-02-02T00:00:00,2022-02-03T00:00:00"  # Subject to change
            },
            "description": m.description,
            "keywords": m.keywords,
            "crs": m.crs.to_wkt(),
            "data_type": str(m.data_type.value),
            "contacts": m.contacts
        })

    def test_serialise(self):
        expected_yaml = self.get_expected_yaml(self.test_metadata)
        actual = self.serialiser.serialise(self.test_metadata)
        self.assertEqual(expected_yaml, actual)

    def test_deserialise(self):
        test_yaml = self.get_expected_yaml(self.test_metadata)
        actual = self.serialiser.deserialise(test_yaml)

        self.assertEqual(self.test_metadata, actual)
