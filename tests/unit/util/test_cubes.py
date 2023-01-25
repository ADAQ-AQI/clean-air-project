"""
Unit tests for cubes.py
"""

import os
import pytest
import iris
import xarray as xr
import pandas as pd

from clean_air.util import cubes as cubes_module

@pytest.fixture(scope="class")
def aircraft_cube(sampledir):
    path = os.path.join(sampledir, "aircraft", "M285_sample.nc")
    return iris.load_cube(path, 'NO2_concentration_ug_m3')

@pytest.fixture(scope="class")
def track_dataframe(aircraft_cube):
	ds = xr.DataArray.from_iris(aircraft_cube)
	return ds.to_dataframe()

class TestExtract:

	def test_extract_series(self, aircraft_cube, track_dataframe):
		series = cubes_module.extract_series(aircraft_cube, track_dataframe, column_mapping={'time':'time'})
		assert isinstance(series, pd.Series)
