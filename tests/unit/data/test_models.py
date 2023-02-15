import unittest
from clean_air.data.models import Metadata, DataSet
from edr_server.core.models.extents import Extents, SpatialExtent
from shapely.geometry import box
from pathlib import Path



class TestDataSet(unittest.TestCase):
	"Basic testing of DataSet properties"
	def setUp(self) -> None:
		self.metadata = Metadata(
			f"an ID", f"test dataset", "A Test", [], Extents(SpatialExtent(box(-1, -1, 1, 1))), [])
		self.files = [Path("test-file.csv")]

	def test_name_populated(self):
		"""
		GIVEN a Metadata object and list of datafile paths
		WHEN a DataSet object is created
		THEN the DataSet name is equal to the metadata title
		"""
		dataset = DataSet(self.files, self.metadata)
		assert dataset.name == "test dataset"

	def test_id_populated(self):
		"""
		GIVEN a Metadata object and list of datafile paths
		WHEN a DataSet object is created
		THEN the DataSet id is equal to the metadata id
		"""
		dataset = DataSet(self.files, self.metadata)
		assert dataset.id == "an ID"

	def test_name_empty(self):
		"""
		WHEN an empty DataSet object is created
		THEN the DataSet name is an empty string
		"""
		dataset = DataSet()
		assert dataset.name == ""

	def test_id_empty(self):
		"""
		WHEN an empty DataSet object is created
		THEN the DataSet id is None
		"""
		dataset = DataSet()
		self.assertIsNone(dataset.id)