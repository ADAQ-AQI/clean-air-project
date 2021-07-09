"""
Unit tests for dataframe_converter.py
"""

import os

import pytest
import iris
import geopandas as geopd
import pandas as pd
import numpy as np

from clean_air.util import dataframe_converter as dc
from clean_air.util.cubes import get_xy_coords


# Fixtures for loading cubes

@pytest.fixture(scope="class")
def multidim_cube(sampledir):
    path = os.path.join(sampledir, "model", "aqum_hourly_so2.nc")
    return iris.load_cube(path)


@pytest.fixture(scope="class")
def doubledim_cube(sampledir):
    path = os.path.join(sampledir, "model", "aqum_daily_daqi_mean.nc")
    return iris.load_cube(path)


@pytest.fixture(scope="class")
def onedim_cube(sampledir):
    path = os.path.join(sampledir, "timeseries", "aircraft_o3_timeseries.nc")
    return iris.load_cube(path)


class TestConvertToGeoDF:
    """
    Unit tests for conversion of cubes to GeoDataFrames.  This class will test
    the structural direction of objects through the function depending on the
    number of dimensions they possess.
    """

    def test_3d_cube(self, multidim_cube):
        gdf = dc.convert_to_geodf(multidim_cube, restitch=True)
        assert isinstance(gdf, geopd.GeoDataFrame)

    def test_2d_cube(self, doubledim_cube):
        gdf = dc.convert_to_geodf(doubledim_cube, restitch=False)
        assert isinstance(gdf[0], geopd.GeoDataFrame)

    def test_2d_cube_restitch(self, doubledim_cube):
        gdf = dc.convert_to_geodf(doubledim_cube, restitch=True)
        assert isinstance(gdf, geopd.GeoDataFrame)

    def test_1d_cube_series(self, onedim_cube):
        gs = dc.convert_to_geodf(onedim_cube)
        assert isinstance(gs, pd.Series)


class TestMakeGeo:
    """
    Unit tests for helper function to convert cubes to GeoDataFrames.  This
    class will test the breakdown of cubes into x-y sub-cubes and their
    subsequent conversion to GeoDataFrames.
    """

    def test_3d_cube_conversion(self, multidim_cube):
        x_coord, y_coord = get_xy_coords(multidim_cube)
        gdfs = dc._make_geo(multidim_cube, x_coord, y_coord)
        for gdf in gdfs:
            assert isinstance(gdf, geopd.GeoDataFrame)

    def test_2d_cube_conversion(self, doubledim_cube):
        x_coord, y_coord = get_xy_coords(doubledim_cube)
        gdf = dc._make_geo(doubledim_cube, x_coord, y_coord)
        assert isinstance(gdf[0], geopd.GeoDataFrame)

    def test_data_order_3d(self, multidim_cube):
        x_coord, y_coord = get_xy_coords(multidim_cube)
        expected_data = [3.6, 3.5, 3.5, 3.5, 3.6, 3.6,
                         3.6, 3.5, 3.7, 3.7, 3.6, 3.6]
        gdfs = dc._make_geo(multidim_cube, x_coord, y_coord)
        result = gdfs[0].data.array
        assert np.allclose(result, expected_data)
