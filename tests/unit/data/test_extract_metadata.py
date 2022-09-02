import array
import pytest
from iris.coords import DimCoord
from iris.cube import Cube, CubeList
import numpy as np
from clean_air import data
from edr_server.core.models.metadata import CollectionMetadata

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
		time = DimCoord(np.linspace(1, 24, 24),
					standard_name='time',
					units="hours since 1970-01-01 00:00:00")
		height = DimCoord(3.5, 
					standard_name="height",
					units="m",
					attributes={'positive': 'up'})
		cube = Cube(np.zeros((4, 8, 24), np.float32),
					standard_name="mass_concentration_of_ozone_in_air",
					units="ug/m3",
					dim_coords_and_dims=[(latitude, 0),
										(longitude, 1),
										(time, 2)])
		cube.add_aux_coord(height)
		return cube

	@staticmethod
	@pytest.fixture
	def cube_2():
		latitude = DimCoord(np.linspace(1, 100, 100),
                    standard_name='projection_x_coordinate',
                    units='meters')
		longitude = DimCoord(np.linspace(1, 100, 100),
					standard_name='projection_y_coordinate',
					units='meters')
		time = DimCoord(np.linspace(101, 148, 48),
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
	def cube_metadata(cube_1):
		return data.extract_metadata.extract_metadata(cube_1, 1, [], ['cube'], ['netCDF'])

	@staticmethod
	@pytest.fixture
	def cubelist_metadata(cube_1, cube_2):
		return data.extract_metadata.extract_metadata(CubeList([cube_1, cube_2]), 1, [], ['cube'], ['netCDF'], 'title', 'desc')

	@staticmethod
	def test_cube_return_type(cube_metadata):
		assert isinstance(cube_metadata, CollectionMetadata)

	@staticmethod
	def test_cubelist_return_type(cubelist_metadata):
		assert isinstance(cubelist_metadata, CollectionMetadata)

	@staticmethod
	def test_cube_title(cube_metadata):
		assert(cube_metadata.title=="mass_concentration_of_ozone_in_air")

	@staticmethod
	def test_cubelist_title(cubelist_metadata):
		assert(cubelist_metadata.title=="title")

	@staticmethod
	def test_total_time_extent(cube_metadata):
		assert(np.allclose(cube_metadata.extent.temporal.values, np.linspace(1, 24, 24)))

	@staticmethod
	def test_total_vertical_extent(cube_metadata):
		assert(cube_metadata.extent.vertical.values==pytest.approx(3.5))

	@staticmethod
	def test_cube_parameters_length(cube_metadata):
		assert(len(cube_metadata.parameters)==1)

	@staticmethod
	def test_cubelist_parameters_length(cubelist_metadata):
		assert(len(cubelist_metadata.parameters)==2)