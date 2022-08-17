import pytest
from iris.coords import DimCoord
from iris.cube import Cube
import numpy as np
from clean_air import data

class TestExtractMetadata:
	@staticmethod
	@pytest.fixture
	def cube():
		latitude = DimCoord(np.linspace(-90, 90, 4),
                    standard_name='latitude',
                    units='degrees')
		longitude = DimCoord(np.linspace(45, 360, 8),
					standard_name='longitude',
					units='degrees')
		time = DimCoord(np.linspace(0, 24, 24),
					standard_name='time',
					units="hours since 1970-01-01 00:00:00")
		cube = Cube(np.zeros((4, 8, 24), np.float32),
					standard_name="mass_concentration_of_ozone_in_air",
					units="ug/m3",
					dim_coords_and_dims=[(latitude, 0),
										(longitude, 1),
										(time, 2)])
		return cube

	@staticmethod
	def test_extract(cube):
		a = data.extract_metadata.extract_cube_metadata(cube)
		print(a)
		assert(a.title=="mass_concentration_of_ozone_in_air")
