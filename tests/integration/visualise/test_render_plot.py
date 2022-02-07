"""
Integration tests for render_plot.py
"""

import os

import iris.cube
import iris.plot
import pytest
import matplotlib as mpl
from shapely.geometry import Polygon, MultiPolygon

from clean_air.data import DataSubset
from clean_air.visualise import dataset_renderer


@pytest.fixture()
def timeseries_filepath(sampledir):
    timeseries_filepath = os.path.join(sampledir, "model_full",
                                       "aqum_hourly_o3_20200520.nc")
    return timeseries_filepath


@pytest.fixture()
def aircraft_filepath(sampledir):
    aircraft_filepath = os.path.join(sampledir, "aircraft",
                                     "MOCCA_M264_20200120.nc")
    return aircraft_filepath


@pytest.fixture()
def clean_data(timeseries_filepath):
    # Note: This is a DataSubset object which can be used and adapted for later
    # fixtures and tests.  These objects are NOT subscriptable.
    clean_df = DataSubset({"files": timeseries_filepath})
    return clean_df


@pytest.fixture()
def aircraft_data(aircraft_filepath):
    aircraft_dataset = DataSubset({"files": aircraft_filepath})
    return aircraft_dataset


@pytest.fixture()
def tmp_output_path(tmp_path):
    tmp_output_path = tmp_path / "tmp_output_path"
    tmp_output_path.mkdir()
    return tmp_output_path


def test_linear_interpolate_3d_plot(clean_data, tmp_output_path):
    """Test that when data is passed to this function it is processed to
    produce and return a timeseries plot."""
    interped_data = dataset_renderer.TimeSeries(clean_data, 150, 150).\
        linear_interpolate()
    interped_plot = dataset_renderer.Renderer(interped_data).render()
    assert isinstance(interped_plot, mpl.figure.Figure)


def test_box_average_plot(clean_data, tmp_output_path):
    """Test that when data is passed to this function it is processed to
        produce and return a timeseries plot."""
    boxed_data = dataset_renderer.TimeSeries(clean_data).\
        spatial_average(shape='box', coords=[10000, 10000, 15000, 15000])
    boxed_plot = dataset_renderer.Renderer(boxed_data).render()
    assert isinstance(boxed_plot, mpl.figure.Figure)


def test_shape_average_plot(clean_data, tmp_output_path):
    """Test that when data is passed to this function it is processed to
    produce and return a timeseries plot."""
    shape = Polygon([(0, 0), (100, 100), (100, 0)])
    shape_data = dataset_renderer.TimeSeries(clean_data).spatial_average(shape)
    shape_plot = dataset_renderer.Renderer(shape_data).render()
    assert isinstance(shape_plot, mpl.figure.Figure)


def test_shapes_average_plots(clean_data, tmp_output_path):
    """Test that when data is passed to this function it is processed to
        produce and return a set of timeseries plots."""
    # NOTE: This test is really slow, presumably due to lots of processing
    # during cell weight evaluation.  Can we speed this up somehow?
    # poly_one = Polygon([(0, 0), (100, 100), (100, 0)])
    # poly_two = Polygon([(0, 0), (-100, -100), (-100, 0)])
    poly_one = Polygon([(0, 0), (10, 10), (10, 0)])
    poly_two = Polygon([(-100, -100), (-90, -90), (-90, 0)])
    shapes = MultiPolygon([poly_one, poly_two])
    shapes_data = dataset_renderer.TimeSeries(clean_data).\
        spatial_average(shapes)
    # One plot per shape, but side-by-side on same figure
    shapes_plot = dataset_renderer.Renderer(shapes_data).render()
    assert isinstance(shapes_plot, mpl.figure.Figure)




