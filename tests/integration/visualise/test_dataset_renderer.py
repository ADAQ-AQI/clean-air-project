"""
Integration tests for the test_dataset_renderer.py visualisations.
"""

import os
import pytest

import iris
from iris.cube import Cube, CubeList
from iris.time import PartialDateTime
from shapely.geometry import Polygon, MultiPolygon
from clean_air.visualise import dataset_renderer as dr
from clean_air.data import DataSubset


# NOTE: This test now also fails because geopandas cannot load netcdf and iris
# cannot load csv.  We must write a netcdf/csv converter to reinstate all of
# these tests.
# class TestDatasetRenderer:
#     """
#     Class to test integration properties of test_dataset_renderer.py
#     """
#
#     def setup_class(self):
#         self.model_path = os.path.join(MODEL_DATA_PATH,
#                                        'aqum_daily_daqi_mean_20200520.nc')
#         self.obs_path = os.path.join(OBS_DATA_PATH,
#                                      'ABD_2015.csv')
#         self.aircraft_path = os.path.join(AIRCRAFT_DATA_PATH,
#                                           'clean_air_MOCCA_data_'
#                                           '20200121_M265_v0.nc')
#
#     def test_renderer_for_model_data(self):
#         img = dr.Renderer(self.model_path)
#         img.render()
#
#     def test_renderer_for_obs_data(self):
#         # NOTE: This test highlights the fact that iris cannot read csv files
#         # but we need iris to identify coord axes before passing them to the
#         # renderer.  We will therefore need to write a converter as I haven't
#         # managed to find one yet.
#         # TODO: Write csv to nc converter:
#         # https://stackoverflow.com/questions/22933855/convert-csv-to-netcdf
#         # This test will fail until the converter is completed.
#         img = dr.Renderer(self.obs_path)
#         img.render()
#
#     def test_renderer_for_aircraft_data(self):
#         # NOTE: This test fails currently because iris is having trouble
#         # interpreting the CF variables in the aircraft data.  I will be
#         # discussing this with Elle on Thursday but I think it's in the
#         # pipeline to be resolved at some point anyway.
#         # TODO: fix aircraft data
#         img = dr.Renderer(self.aircraft_path)
#         img.render()

@pytest.fixture()
def timeseries_filepath(sampledir):
    timeseries_filepath = os.path.join(sampledir, "model_full",
                                       "aqum_hourly_o3_20200520.nc")
    return timeseries_filepath


@pytest.fixture()
def diurnal_filepath(sampledir):
    diurnal_filepath = os.path.join(sampledir, "model_full",
                                    "aqum_hourly_o3_48_hours.nc")
    return diurnal_filepath


@pytest.fixture()
def aircraft_filepath(sampledir):
    aircraft_filepath = os.path.join(sampledir, "aircraft",
                                     "M285_sample.nc")
    return aircraft_filepath


@pytest.fixture()
def clean_data(timeseries_filepath):
    # Note: This is a DataSubset object which can be used and adapted for later
    # fixtures and tests.  These objects are NOT subscriptable.
    clean_df = DataSubset(timeseries_filepath)
    return clean_df


@pytest.fixture()
def multiday_data(diurnal_filepath):
    # Note: This is a DataSubset object which can be used and adapted for later
    # fixtures and tests.  These objects are NOT subscriptable.
    multiday_df = DataSubset(diurnal_filepath)
    return multiday_df


@pytest.fixture()
def flight_data(aircraft_filepath):
    # Note: This is a DataSubset object which can be used and adapted for later
    # fixtures and tests.  These objects are NOT subscriptable.
    flight_df = DataSubset(iris.load_cube(aircraft_filepath, 'NO2_concentration_ug_m3'))
    return flight_df


@pytest.fixture()
def tmp_output_path(tmp_path):
    tmp_output_path = tmp_path / "tmp_output_path"
    tmp_output_path.mkdir()
    return tmp_output_path


class TestTimeSeries:
    """Class to test generation of time series data with various processing
    methods (i.e. linear interpolation, averaging within shapefile, etc.)."""

    def test_linear_interpolate_3d_data(self, clean_data, tmp_output_path):
        """Test that data passed into this function will be
        returned as an iris cube (of the correct shape for post-interpolation)
        containing a concatenation of interpolated data points."""
        interpolated_data = dr.TimeSeries(clean_data, 150, 150).\
            linear_interpolate()
        assert isinstance(interpolated_data, Cube)
        # Shape of interpolated cube should be (24 time, 1 lat, 1 lon)
        assert interpolated_data.shape == (24, 1, 1)

    def test_box_average_data(self, clean_data, tmp_output_path):
        """Test that when data is passed to this function it will be extracted
         into an iris Cube containing a timeseries dataset."""
        boxed_data = dr.TimeSeries(clean_data).\
            spatial_average(shape='box', coords=[10000, 10000, 15000, 15000])
        assert isinstance(boxed_data, Cube)
        assert boxed_data.shape == (24,)

    def test_shape_averaged_data(self, clean_data, tmp_output_path):
        """Test that when data is passed to this function it is returned as a
        timeseries Cube."""
        shape = Polygon([(0, 0), (100, 100), (100, 0)])
        shape_data = dr.TimeSeries(clean_data).spatial_average(shape=shape)
        assert isinstance(shape_data, Cube)

    def test_shapes_averaged_data(self, clean_data, tmp_output_path):
        """Test that when data is passed to this function it is returned as a
         timeseries Cube."""
        poly_one = Polygon([(0, 0), (100, 100), (100, 0)])
        poly_two = Polygon([(0, 0), (-100, -100), (-100, 0)])
        shapes = MultiPolygon([poly_one, poly_two])
        shape_data = dr.TimeSeries(clean_data).spatial_average(shape=shapes)
        assert isinstance(shape_data, CubeList)

    def test_diurnal_averaged_data(self, multiday_data):
        """Test that when data is passed to this function it is returned as a
        timeseries Cube."""
        diurnal_data = dr.TimeSeries(multiday_data).diurnal_average()
        assert isinstance(diurnal_data, Cube)

    def test_track_data(self, flight_data):
        """
        GIVEN a cube of aircraft data
        WHEN Timeseries.track() is called for valid time bounds
        THEN an iris cube is returned
        """
        track_data = dr.TimeSeries(flight_data).track(PartialDateTime(hour=13), PartialDateTime(hour=14))
        assert isinstance(track_data, Cube)
