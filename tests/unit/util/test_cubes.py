"""
Unit tests for cubes.py
"""

import os
import pytest
import iris
import xarray as xr
import pandas as pd
from iris.coords import DimCoord
from iris.cube import Cube
import numpy as np
from shapely.geometry import Polygon

from clean_air.util import cubes as cubes_module


@pytest.fixture(scope="class")
def aircraft_cube(sampledir):
	path = os.path.join(sampledir, "aircraft", "M285_sample.nc")
	return iris.load_cube(path, 'NO2_concentration_ug_m3')


@pytest.fixture()
def model_cube(sampledir):
	path = os.path.join(sampledir, "model_full", "aqum_hourly_o3_20200520.nc")
	return iris.load_cube(path)


@pytest.fixture(scope="class")
def track_dataframe(aircraft_cube):
	ds = xr.DataArray.from_iris(aircraft_cube)
	return ds.to_dataframe()


@pytest.fixture(scope="class")
def cube_1():
	x = DimCoord(np.linspace(-1.5, 3.5, 6),
				 standard_name='projection_x_coordinate',
				 units='meters')
	y = DimCoord(np.linspace(-2.5, 2.5, 6),
				 standard_name='projection_y_coordinate',
				 units='meters')
	time = DimCoord(np.linspace(1, 24, 24),
					standard_name='time',
					units="hours since 1970-01-01 00:00:00")
	cube = Cube(np.zeros((6, 6, 24), np.float32),
				standard_name="mass_concentration_of_ozone_in_air",
				units="ug/m3",
				dim_coords_and_dims=[(x, 0),
									 (y, 1),
									 (time, 2)])
	return cube

def test_get_xy_coords(model_cube):
	"""
	GIVEN a cube of model data
	WHEN get_xy_coords is called
	THEN the correct DimCoords are returned
	"""
	x_coord, y_coord = cubes_module.get_xy_coords(model_cube)
	assert x_coord == model_cube.coord('projection_x_coordinate')
	assert y_coord == model_cube.coord('projection_y_coordinate')

def test_get_xy_coords_error(model_cube):
	"""
	GIVEN a cube of model data with the X coord removed
	WHEN get_xy_coords is called
	THEN the appropriate error is raised
	"""
	model_cube.remove_coord('projection_x_coordinate')
	with pytest.raises(iris.exceptions.CoordinateNotFoundError):
		cubes_module.get_xy_coords(model_cube)
	


def test_get_intersection_weights(cube_1):
	shape = Polygon([(1, 3), (3, 1), (1, 0), (0, 2)])
	expected = np.array([[0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0], [0, 0, 0, 0.25, 0.75, 0.5],
						[0, 0, 0, 0.75, 1, 0.5], [0, 0, 0, 0.25, 0.5, 0], [0, 0, 0, 0, 0, 0]])
	np.testing.assert_array_equal(cubes_module.get_intersection_weights(cube_1, shape), expected)
	# test for match_cube_dims=true
	# test for shape partially/totally out of bounds

def test_get_intersection_weights(cube_1):
	shape = Polygon([(1, 3), (3, 1), (1, 0), (0, 2)])

	result = cubes_module.get_intersection_weights(cube_1, shape, True)
	print(cube_1.ndim)
	print(result.ndim)
	assert cube_1.is_compatible(result) == True

class TestExtract:

	#deprecated!!
	# def test_extract_series(self, aircraft_cube, track_dataframe):
	#     series = cubes_module.extract_series(aircraft_cube, track_dataframe, column_mapping={'time': 'time'})
	#     assert isinstance(series, pd.Series)

	def test_extract_box(self, cube_1):
		coords = (-0.25, -0.75, 2.6, 1.4)
		box = cubes_module.extract_box(cube_1, coords)
		assert isinstance(box, iris.cube.Cube)
		assert box.shape == (3, 2, 24)
	# first check subset.extract_box is different
	#test for cell bounds (already done)
	# test for box partially/totally out of bounds 
	# test for 'modular arithmitic`?`

