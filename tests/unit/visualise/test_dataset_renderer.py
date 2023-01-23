"""
Unit tests for test_dataset_renderer.py
"""

import os

import pytest
import geopandas
import xarray

import clean_air.visualise.dataset_renderer as dr


@pytest.fixture
def tmp_output_path(tmp_path):
    tmp_output_path = tmp_path / "tmp_output_path"
    tmp_output_path.mkdir()
    return tmp_output_path


@pytest.fixture
def model_data_path(sampledir):
    model_data_path = os.path.join(sampledir, 'model_full', 'aqum_daily_daqi_mean_20200520.nc')
    return model_data_path


@pytest.fixture
def timeseries_path(sampledir):
    timeseries_path = os.path.join(sampledir, "model_full", "aqum_hourly_o3_20200520.nc")
    return timeseries_path

# @pytest.fixture
# def scalar_path(sampledir):
#     # TODO: This file no longer exists. Replace with file that does exist in cap-sample-data and works for this test.
#     scalar_path = os.path.join(sampledir, "???", "aqum_no2_modified.nc")
#     return scalar_path


class TestDatasetRenderer:
    """
    Class to test object initialisation in Renderer
    """

    @pytest.fixture(scope="class")
    def renderer(self, sampledir):
        path = model_data_path
        return dr.Renderer(path)

    def test_lazy_iris_data(self, renderer):
        # Check that the iris dataset is loaded as lazy data for performance:
        assert renderer.dataset.has_lazy_data

    def test_found_dim_coords(self, renderer):
        # Check that all of the iris-guessed coords are the ones that we
        # expect it to discover:
        assert renderer.x_coord == 'projection_x_coordinate'
        assert renderer.y_coord == 'projection_y_coordinate'
        # height and time are scalar coords so will not be collected:
        assert renderer.z_coord is None
        assert renderer.t_coord is None


# TODO: write netcdf->csv converter to get these tests working
# NOTE: The following two tests fail because geopandas will not load netcdf
# files and iris will not load csv files, so until we have a netcdf/csv
# converter (both ways) these tests cannot be reinstated.
# NOTE 2: They will also need to be rewritten to make use of sampledir
# class TestRenderMapCall:
#     """
#     Class to test 'render' method of Renderer when producing maps.
#     """
#     def setup_class(self):
#         self.dframe = dr.Renderer(model_data_path)
#         self.dframe.render()
#
#     def test_render_map(self):
#         # Check that if the data has an x and a y coordinate, the
#         # renderer chooses to create a map rather than a plot.
#         assert self.dframe.img_type == 'map'
#
#     def test_map_dataframe_is_geopandas(self):
#         # Check that if a map is being plotted, the dataframe generated is a
#         # geopandas object:
#         assert isinstance(self.dframe, geopandas.GeoDataFrame)


# TODO: Find suitable test files for this setup (i.e. fixtures; see top of file).
# class TestRenderPlotCall:
#     """
#     Class to test 'render' method of Renderer when producing plots.
#     """
#
#     def setup_class(self):
#         self.dframe = dr.Renderer(timeseries_path)
#         self.dframe.render()
#
#     def test_render_timeseries(self):
#         # Check that if we have scalar x and y coordinates but a full time
#         # coord, the renderer will choose to make a timeseries:
#         # dframe = dr.Renderer(self.timeseries_path)
#         # dframe.render()
#         assert self.dframe.img_type == 'timeseries'
#
#     def test_plot_dataframe_is_xarray(self):
#         # Check that the dataframe itself is an xarray object:
#         assert isinstance(self.dframe, xarray.Dataset)
#

def test_render_error():
    # Check that if all our coordinates end up set as None, then an
    # error is raised.
    with pytest.raises(ValueError):
        dr.Renderer(None).render()
