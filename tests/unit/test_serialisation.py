import unittest
from datetime import datetime

import yaml
from shapely.geometry import box

from clean_air.models import Metadata, DataType, Extent, TemporalExtent, DateTimeInterval
from clean_air.serialisation import MetadataYamlSerialiser


class MetadataYamlSerialiserTest(unittest.TestCase):

    def setUp(self) -> None:
        self.serialiser = MetadataYamlSerialiser()

        test_temporal_extent = TemporalExtent(
            values=[datetime(2022, 4, 6, 5, 23), datetime(2021, 1, 1, 15, 30)],
            intervals=[DateTimeInterval.parse_str("R3/2020-01-01T15:30/P1D")]
        )
        self.test_metadata = Metadata(
            title="Test",
            extent=Extent(box(-1, -1, 1, 1), test_temporal_extent),
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
                "temporal": {
                    "values": [dt.isoformat() for dt in m.extent.temporal.values],
                    "intervals": [str(dti) for dti in m.extent.temporal.intervals]
                }
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

    def test_serialise_empty_temporal_extent(self):
        self.test_metadata.extent.temporal = TemporalExtent()
        expected_yaml = self.get_expected_yaml(self.test_metadata)
        actual = self.serialiser.serialise(self.test_metadata)
        self.assertEqual(expected_yaml, actual)

    def test_deserialise(self):
        test_yaml = self.get_expected_yaml(self.test_metadata)
        actual = self.serialiser.deserialise(test_yaml)

        self.assertEqual(self.test_metadata, actual)

    def test_deserialise_empty_temporal_extent(self):
        self.test_metadata.extent.temporal = TemporalExtent()
        test_yaml = self.get_expected_yaml(self.test_metadata)
        actual = self.serialiser.deserialise(test_yaml)

        self.assertEqual(self.test_metadata, actual)
