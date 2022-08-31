import pytest
from iris.coords import DimCoord
from iris.cube import Cube, CubeList
import numpy as np
from clean_air import data

class TestExtractMetadata:
	@staticmethod
	@pytest.fixture
	def cube_1():
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
	@pytest.fixture
	def cube_2():
		latitude = DimCoord(np.linspace(0, 100, 100),
                    standard_name='projection_x_coordinate',
                    units='meters')
		longitude = DimCoord(np.linspace(0, 100, 100),
					standard_name='projection_y_coordinate',
					units='meters')
		time = DimCoord(np.linspace(100, 148, 48),
					standard_name='time',
					units="hours since 1970-01-01 00:00:00")
		cube = Cube(np.zeros((100, 100, 48), np.float32),
					standard_name="mass_fraction_of_carbon_dioxide_in_air",
					units="l",
					dim_coords_and_dims=[(latitude, 0),
										(longitude, 1),
										(time, 2)])
		return cube

	@staticmethod
	@pytest.fixture
	def cube_list(cube_1, cube_2):
		return CubeList([cube_1, cube_2])

	@staticmethod
	def test_extract_cube(cube_1):
		metadata = data.extract_metadata.extract_cubelist_metadata(cube_1, 1, [], ['cube'], ['netCDF'])
		assert(metadata.title=="mass_concentration_of_ozone_in_air")

	@staticmethod
	def test_extract_cubelist(cube_list):
		metadata = data.extract_metadata.extract_cubelist_metadata(cube_list, 1, [], ['cube'], ['netCDF'], 'title', 'desc')
		assert(metadata.title=="titlee")
