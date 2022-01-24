"""
Integration tests for render_plot.py
"""

import os

import iris.cube
import iris.plot
import pytest
import matplotlib as mpl

import pandas as pd
import xarray
import numpy as np

import clean_air.visualise.dataset_renderer
from clean_air.visualise import render_plot, dataset_renderer
from clean_air.data import DataSubset


@pytest.fixture()
def timeseries_filepath(sampledir):
    timeseries_filepath = os.path.join(sampledir, "model_full",
                                       "aqum_hourly_o3_20200520.nc")
    return timeseries_filepath


@pytest.fixture()
def aircraft_filepath(sampledir):
    # aircraft_filepath = os.path.join(sampledir, "aircraft",
    #                                  "MOCCA_M251_20190903.nc")
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


def test_linear_interpolate_3d_data(clean_data, tmp_output_path):
    """Test that data passed into this function will be
    returned as an iris cube (of the correct shape for post-interpolation)
    containing a concatenation of interpolated data points."""
    interpolated_data = dataset_renderer.TimeSeries(clean_data, 150, 150).\
        linear_interpolate()
    assert isinstance(interpolated_data, iris.cube.Cube)
    # Shape of interpolated cube should be (24 time, 1 lat, 1 lon)
    assert interpolated_data.shape == (24, 1, 1)


def test_linear_interpolate_3d_plot(clean_data, tmp_output_path):
    """Test that when data is passed to this function it is processed to
    produce and return a timeseries plot."""
    interped_data = dataset_renderer.TimeSeries(clean_data, 150, 150).\
        linear_interpolate()
    interped_plot = dataset_renderer.Renderer(interped_data).render()
    assert isinstance(interped_plot, mpl.figure.Figure)


def test_box_average_data(clean_data, tmp_output_path):
    """Test that when data is passed to this function it will be extracted
    and averaged successfully into a timeseries dataset."""
    boxed_data = dataset_renderer.TimeSeries(clean_data).\
        spatial_average(shape='box', coords=[10000, 10000, 15000, 15000])
    assert isinstance(boxed_data, iris.cube.Cube)
    assert boxed_data.shape == (24,)


def test_box_average_plot(clean_data, tmp_output_path):
    """Test that when data is passed to this function it is processed to
        produce and return a timeseries plot."""
    boxed_data = dataset_renderer.TimeSeries(clean_data).\
        spatial_average(shape='box', coords=[10000, 10000, 15000, 15000])
    boxed_plot = dataset_renderer.Renderer(boxed_data).render()
    assert isinstance(boxed_plot, mpl.figure.Figure)

# TODO: Add tests for shape_average and shapes_average here


def test_track_data(aircraft_data, tmp_output_path):
    """Test that when data is passed to this function a track cube is
    extracted and returned."""
    track_data = dataset_renderer.TimeSeries(aircraft_data).track()
    assert isinstance(track_data, iris.cube.Cube)
