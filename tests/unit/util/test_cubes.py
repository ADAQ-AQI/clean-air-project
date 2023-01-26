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

@pytest.fixture(scope="class")
def model_cube(sampledir):
    path = os.path.join(sampledir, "model_full", "aqum_hourly_o3_20200520.nc")
    return iris.load_cube(path)

@pytest.fixture(scope="class")
def track_dataframe(aircraft_cube):
	ds = xr.DataArray.from_iris(aircraft_cube)
	return ds.to_dataframe()

@pytest.fixture(scope="class")
def cube_1():
	x = DimCoord(np.linspace(0.5, 2.5, 3),
					standard_name='projection_x_coordinate',
					units='meters')
	y = DimCoord(np.linspace(0.5, 2.5, 3),
					standard_name='projection_y_coordinate',
					units='meters')
	time = DimCoord(np.linspace(1, 24, 24),
					standard_name='time',
					units="hours since 1970-01-01 00:00:00")
	cube = Cube(np.zeros((3, 3, 24), np.float32),
				standard_name="mass_concentration_of_ozone_in_air",
				units="ug/m3",
				dim_coords_and_dims=[(x, 0),
										(y, 1),
										(time, 2)])
	return cube

def test_get_xy_coords(model_cube):
	x_coord, y_coord = cubes_module.get_xy_coords(model_cube)
	assert x_coord.standard_name == 'projection_x_coordinate'
	assert y_coord.standard_name == 'projection_y_coordinate'

def test_get_intersection_weights(cube_1):
	shape = Polygon([(1, 3), (3, 1), (1, 0), (0, 2)])
	expected = np.array([[0.25, 0.75, 0.5], [0.75, 1, 0.5], [0.25, 0.5, 0]])
	np.testing.assert_array_equal(cubes_module.get_intersection_weights(cube_1, shape), expected)

class TestExtract:

	def test_extract_series(self, aircraft_cube, track_dataframe):
		series = cubes_module.extract_series(aircraft_cube, track_dataframe, column_mapping={'time':'time'})
		assert isinstance(series, pd.Series)
