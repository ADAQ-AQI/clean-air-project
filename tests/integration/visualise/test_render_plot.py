"""
Integration tests for render_plot.py
"""

import os

import iris.cube
import iris.plot
import pytest

import pandas as pd
import xarray
import numpy as np

from clean_air.visualise import render_plot, dataset_renderer
from clean_air.data import DataSubset


@pytest.fixture()
def timeseries_filepath(sampledir):
    timeseries_filepath = os.path.join(sampledir, "model_full",
                                       "aqum_hourly_o3_20200520.nc")
    return timeseries_filepath


@pytest.fixture()
def clean_data(timeseries_filepath):
    # Note: This is a DataSubset object which can be used and adapted for later
    # fixtures and tests.  These objects are NOT subscriptable.
    clean_df = DataSubset({"files": timeseries_filepath})
    return clean_df


@pytest.fixture()
def tmp_output_path(tmp_path):
    tmp_output_path = tmp_path / "tmp_output_path"
    tmp_output_path.mkdir()
    return tmp_output_path


def test_linear_interpolate_3d_data(clean_data, tmp_output_path):
    """Test that data passed into this function will be
    returned as an iris cube (of the correct shape for post-interpolation)
    containing a concatenation of interpolated data points."""
    interpolated_data = render_plot.TimeSeries(clean_data, 150, 150).\
        linear_interpolate()
    assert isinstance(interpolated_data, iris.cube.Cube)
    # Shape of interpolated cube should be (24 time, 1 lat, 1 lon)
    assert interpolated_data.shape == (24, 1, 1)


def test_linear_interpolate_3d_plot(clean_data, tmp_output_path):
    """Test that when data is passed to this function it is processed to
    produce and return a timeseries plot."""
    interpolated_data = render_plot.TimeSeries(clean_data, 150, 150).\
        linear_interpolate()
    interpolated_plot = dataset_renderer.DatasetRenderer(interpolated_data).\
        render()
    # TODO: Figure out how to make this plot into an actual type to test for...
    assert isinstance(interpolated_plot, iris.plot)


def test_box_average_data(clean_data, tmp_output_path):
    """Test that when data is passed to this function it will be extracted
    and averaged successfully into a timeseries dataset."""
    boxed_data = render_plot.TimeSeries(clean_data).\
        spatial_average(shape='box', coords=[10000, 10000, 15000, 15000])
    assert isinstance(boxed_data, iris.cube.Cube)
    assert boxed_data.shape == (24,)


def test_box_average_plot(clean_data, tmp_output_path):
    """Test that when data is passed to this function it is processed to
        produce and return a timeseries plot."""
    boxed_data = render_plot.TimeSeries(clean_data, 150, 150). \
        spatial_average(shape='box', coords=[10000, 10000, 15000, 15000])
    boxed_plot = dataset_renderer.DatasetRenderer(boxed_data).render()
    # TODO: Figure out how to make this plot into an actual type to test for...
    assert isinstance(boxed_plot, iris.plot)

