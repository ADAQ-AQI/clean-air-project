import unittest

import yaml
from shapely.geometry import box

from clean_air.models import Metadata, DataType
from clean_air.serialisation import MetadataYamlSerialiser


class MetadataYamlSerialiserTest(unittest.TestCase):

    def setUp(self) -> None:
        self.serialiser = MetadataYamlSerialiser()
        self.test_metadata = Metadata(
            dataset_name="Test",
            extent=box(-1, -1, 1, 1),
            description="test description",
            data_type=DataType.MODEL_GRIDDED,
            contacts=[]
        )

    def get_expected_yaml(self, m: Metadata) -> str:
        return yaml.dump({
            "dataset_name": m.dataset_name,
            "extent": m.extent.wkt,
            "description": m.description,
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
