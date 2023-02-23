"""
Integration tests for the test_dataset_renderer.py visualisations.
"""

import os
import pytest

import iris
from iris.time import PartialDateTime
from shapely.geometry import Polygon, MultiPolygon
from pandas import Series, DataFrame
from clean_air.visualise import dataset_renderer as dr
from clean_air.data import DataSubset


@pytest.fixture()
def timeseries_filepath(sampledir):
    timeseries_filepath = os.path.join(sampledir, "model_full", "aqum_hourly_o3_20200520.nc")
    return timeseries_filepath


@pytest.fixture()
def aircraft_filepath(sampledir):
    aircraft_filepath = os.path.join(sampledir, "aircraft", "M285_sample.nc")
    return aircraft_filepath


@pytest.fixture()
def diurnal_filepath(sampledir):
    diurnal_filepath = os.path.join(sampledir, "model_full", "aqum_hourly_o3_48_hours.nc")
    return diurnal_filepath


@pytest.fixture()
def clean_data(timeseries_filepath):
    # Note: This is a DataSubset object which can be used and adapted for later fixtures and tests.
    # These objects are NOT subscriptable.
    clean_df = DataSubset(timeseries_filepath)
    return clean_df


@pytest.fixture()
def flight_data(aircraft_filepath):
    # Note: This is a DataSubset object which can be used and adapted for later fixtures and tests.
    # These objects are NOT subscriptable.
    flight_df = DataSubset(iris.load_cube(aircraft_filepath, 'NO2_concentration_ug_m3'))
    return flight_df


@pytest.fixture()
def multiday_data(diurnal_filepath):
    # Note: This is a DataSubset object which can be used and adapted for later fixtures and tests.
    # These objects are NOT subscriptable.
    multiday_df = DataSubset(diurnal_filepath)
    return multiday_df


def test_linear_interpolate_3d_render(clean_data):
    """
    GIVEN a 3D dataset and two coordinates to specify a point,
    WHEN linearly interpolated through the TimeSeries class and then reshaped through the Renderer class,
    THEN the result is a pandas Series.
    """
    interpolated_data = dr.TimeSeries(clean_data, 150, 150).linear_interpolate()
    rendered_data = dr.Renderer(interpolated_data).render()
    assert isinstance(rendered_data, Series)


def test_box_average_render(clean_data):
    """
    GIVEN a 3D dataset and a list to specify min and max x and y coords for the box,
    WHEN spatially averaged over the box through the TimeSeries class and then reshaped through the Renderer class,
    THEN the result is a pandas Series."""
    boxed_data = dr.TimeSeries(clean_data).spatial_average(shape='box', coords=[10000, 10000, 15000, 15000])
    rendered_data = dr.Renderer(boxed_data).render()
    assert isinstance(rendered_data, Series)


def test_shape_average_render(clean_data):
    """
    GIVEN a 3D dataset and a shapely Polygon,
    WHEN spatially averaged over the Polygon through the TimeSeries class and then reshaped through the Renderer class,
    THEN the result is a pandas Series.
    """
    shape = Polygon([(0, 0), (100, 100), (100, 0)])
    shape_data = dr.TimeSeries(clean_data).spatial_average(shape)
    rendered_data = dr.Renderer(shape_data).render()
    assert isinstance(rendered_data, Series)


def test_shapes_average_renders(clean_data):
    """
    GIVEN a 3D dataset and a shapely MultiPolygon,
    WHEN spatially averaged over the MultiPolygon through the TimeSeries class and then reshaped through the Renderer 
    class,
    THEN the result is a pandas DataFrame.
    """
    # NOTE: This test is really slow, presumably due to lots of processing
    # during cell weight evaluation.  Can we speed this up somehow?
    poly_one = Polygon([(0, 0), (10, 10), (10, 0)])
    poly_two = Polygon([(-100, -100), (-90, -90), (-90, 0)])
    shapes = MultiPolygon([poly_one, poly_two])
    shapes_data = dr.TimeSeries(clean_data).spatial_average(shapes)
    # One plot per shape, but side-by-side on same figure
    rendered_data = dr.Renderer(shapes_data).render()
    assert isinstance(rendered_data, DataFrame)


def test_track_render(flight_data):
    """
    GIVEN a trajectory dataset and two timestamps,
    WHEN a track is generated through the TimeSeries class and then reshaped through the Renderer class,
    THEN the result is a pandas Series.
    """
    track_data = dr.TimeSeries(flight_data).track(PartialDateTime(hour=13, minute=30),
                                                       PartialDateTime(hour=14, minute=30))
    rendered_data = dr.Renderer(track_data).render()
    assert isinstance(rendered_data, Series)


def test_diurnal_average_render(multiday_data):
    """
    GIVEN a multiday 3D dataset and two coordinates to specify a point,
    WHEN linearly interpolated through the TimeSeries class, averaged diurnally 
    and then reshaped through the Renderer class,
    THEN the result is a pandas Series.
    """
    interpolated_data = dr.TimeSeries(multiday_data, 19200, 97200).linear_interpolate()
    averaged_data = dr.TimeSeries(interpolated_data).diurnal_average()
    rendered_data = dr.Renderer(averaged_data).render()
    assert isinstance(rendered_data, Series)
