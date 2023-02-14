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
    path = os.path.join(sampledir, "aircraft_tracks_multidim", "aircraft_o3_timeseries.nc")
    return iris.load_cube(path)


class TestConvertToGeoDF:
    """
    Unit tests for conversion of cubes to GeoDataFrames.  This class will test the structural direction of objects
    through the function depending on the number of dimensions they possess.
    """

    def test_3d_cube(self, multidim_cube):
        """
        GIVEN a cube with multiple dimensions,
        WHEN converted to a dataframe using convert_to_geodf(),
        THEN the result is a geopandas GeoDataFrame.
        """
        gdf = dc.convert_to_geodf(multidim_cube, restitch=True)
        assert isinstance(gdf, geopd.GeoDataFrame)

    def test_2d_cube(self, doubledim_cube):
        """
        GIVEN a cube with two dimensions,
        WHEN converted to a dataframe using convert_to_geodf(),
        THEN the result is a geopandas GeoDataFrame.
        """
        gdf = dc.convert_to_geodf(doubledim_cube, restitch=False)
        assert isinstance(gdf[0], geopd.GeoDataFrame)

    def test_2d_cube_restitch(self, doubledim_cube):
        """
        GIVEN a cube with two dimensions,
        WHEN converted to a dataframe using convert_to_geodf() AND the 'restitch=True' argument,
        THEN the result is a geodpandas GeoDataFrame.
        """
        gdf = dc.convert_to_geodf(doubledim_cube, restitch=True)
        assert isinstance(gdf, geopd.GeoDataFrame)

    def test_1d_cube_series(self, onedim_cube):
        """
        GIVEN a cube with one dimension,
        WHEN converted to a dataframe using convert_to_geodf(),
        THEN the result is a pandas Series.
        """
        gs = dc.convert_to_geodf(onedim_cube)
        assert isinstance(gs, pd.Series)


class TestMakeGeo:
    """
    Unit tests for helper function to convert cubes to GeoDataFrames.  This class will test the breakdown of cubes
    into x-y subcubes and their subsequent conversion to GeoDataFrames.
    """

    def test_3d_cube_conversion(self, multidim_cube):
        """
        GIVEN a cube with multiple dimensions including x and y coordinates,
        WHEN helper function _make_geo() is used,
        THEN each resulting x-y subcube is a geopandas GeoDataFrame.
        """
        x_coord, y_coord = get_xy_coords(multidim_cube)
        gdfs = dc._make_geo(multidim_cube, x_coord, y_coord)
        for gdf in gdfs:
            assert isinstance(gdf, geopd.GeoDataFrame)

    def test_2d_cube_conversion(self, doubledim_cube):
        """
        GIVEN a cube with just x and y coordinates,
        WHEN helper function _make_geo() is used,
        THEN the result is a dataset containing one geopandas GeoDataFrame.
        """
        x_coord, y_coord = get_xy_coords(doubledim_cube)
        gdf = dc._make_geo(doubledim_cube, x_coord, y_coord)
        assert isinstance(gdf[0], geopd.GeoDataFrame)

    def test_data_order_3d(self, multidim_cube):
        """
        GIVEN a cube with multiple dimensions including x and y coordinates,
        WHEN helper function _make_geo() is used,
        THEN the resulting data is as we expected.
        """
        x_coord, y_coord = get_xy_coords(multidim_cube)
        expected_data = [3.60000, 3.5, 3.5, 3.5, 3.60000, 3.60000,
                         3.60000, 3.5, 3.70000, 3.70000, 3.60000, 3.60000]
        gdfs = dc._make_geo(multidim_cube, x_coord, y_coord)
        rounded_data = np.round(gdfs[0].data.array, decimals=5)
        assert np.all(rounded_data == np.float32(expected_data))
