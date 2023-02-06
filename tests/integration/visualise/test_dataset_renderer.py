"""
Integration tests for the test_dataset_renderer.py visualisations.
"""

import os
import pytest

from iris.cube import Cube, CubeList
from shapely.geometry import Polygon, MultiPolygon
from pandas import Series, DataFrame
from clean_air.visualise import dataset_renderer as dr
from clean_air.data import DataSubset


@pytest.fixture()
def timeseries_filepath(sampledir):
    timeseries_filepath = os.path.join(sampledir, "model_full", "aqum_hourly_o3_20200520.nc")
    return timeseries_filepath


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
def multiday_data(diurnal_filepath):
    # Note: This is a DataSubset object which can be used and adapted for later fixtures and tests.
    # These objects are NOT subscriptable.
    multiday_df = DataSubset(diurnal_filepath)
    return multiday_df


@pytest.fixture()
def tmp_output_path(tmp_path):
    tmp_output_path = tmp_path / "tmp_output_path"
    tmp_output_path.mkdir()
    return tmp_output_path


def test_linear_interpolate_3d_plot(clean_data, tmp_output_path):
    """
    GIVEN a 3D dataset and two coordinates to specify a point,
    WHEN linearly interpolated through the TimeSeries class and then reshaped through the Renderer class,
    THEN the result is a pandas DataFrame."""
    interpreted_data = dr.TimeSeries(clean_data, 150, 150).linear_interpolate()
    interpreted_plot = dr.Renderer(interpreted_data).render()
    assert isinstance(interpreted_plot, DataFrame)


def test_box_average_plot(clean_data, tmp_output_path):
    """
    GIVEN a 3D dataset and a list to specify min and max x and y coords for the box,
    WHEN spatially averaged over the box through the TimeSeries class and then reshaped through the Renderer class,
    THEN the result is a pandas DataFrame."""
    boxed_data = dr.TimeSeries(clean_data).spatial_average(shape='box', coords=[10000, 10000, 15000, 15000])
    boxed_plot = dr.Renderer(boxed_data).render()
    assert isinstance(boxed_plot, DataFrame)


def test_shape_average_plot(clean_data, tmp_output_path):
    """
    GIVEN a 3D dataset and a shapely Polygon,
    WHEN spatially averaged over the Polygon through the TimeSeries class and then reshaped through the Renderer class,
    THEN the result is a pandas DataFrame."""
    shape = Polygon([(0, 0), (100, 100), (100, 0)])
    shape_data = dr.TimeSeries(clean_data).spatial_average(shape)
    shape_plot = dr.Renderer(shape_data).render()
    assert isinstance(shape_plot, DataFrame)


def test_shapes_average_plots(clean_data, tmp_output_path):
    """
    GIVEN a 3D dataset and a shapely MultiPolygon,
    WHEN spatially averaged over the MultiPolygon through the TimeSeries class and then reshaped through the Renderer 
    class,
    THEN the result is a pandas DataFrame."""
    # NOTE: This test is really slow, presumably due to lots of processing
    # during cell weight evaluation.  Can we speed this up somehow?
    poly_one = Polygon([(0, 0), (10, 10), (10, 0)])
    poly_two = Polygon([(-100, -100), (-90, -90), (-90, 0)])
    shapes = MultiPolygon([poly_one, poly_two])
    shapes_data = dr.TimeSeries(clean_data).spatial_average(shapes)
    # One plot per shape, but side-by-side on same figure
    shapes_plot = dr.Renderer(shapes_data).render()
    assert isinstance(shapes_plot, DataFrame)

