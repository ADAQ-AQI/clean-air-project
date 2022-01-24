"""
Unit tests for test_dataset_renderer.py
"""

import os

import pytest
# import geopandas
# import xarray

import clean_air.visualise.dataset_renderer as dr


class TestDatasetRenderer:
    """
    Class to test object initialisation in Renderer
    """

    @pytest.fixture(scope="class")
    def renderer(self, sampledir):
        path = os.path.join(
            sampledir,
            "model_full",
            "aqum_daily_daqi_mean_20200520.nc"
        )
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

# NOTE: The following two tests fail because geopandas will not load netcdf
# files and iris will not load csv files, so until we have a netcdf/csv
# converter (both ways) these tests cannot be reinstated.
# NOTE 2: They will also need to be rewritten to make use of sampledir
# class TestRenderMapCall:
#     """
#     Class to test 'render' method of Renderer when producing maps.
#     """
#     def setup_class(self):
#         self.model_path = os.path.join(MODEL_DATA_PATH,
#                                        'aqum_daily_daqi_mean_20200520.nc')
#         self.timeseries_path = os.path.join(TIMESERIES_PATH,
#                                             'aqum_hourly_no2_modified.nc')
#         self.scalar_path = os.path.join(SCALAR_PATH,
#                                         'aqum_no2_modified.nc')
#         self.dframe = dr.Renderer(self.model_path)
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


# class TestRenderPlotCall:
#     """
#     Class to test 'render' method of Renderer when producing plots.
#     """
#
#     def setup_class(self):
#         self.model_path = os.path.join(MODEL_DATA_PATH,
#                                        'aqum_daily_daqi_mean_20200520.nc')
#         self.timeseries_path = os.path.join(TIMESERIES_PATH,
#                                             'aqum_hourly_no2_modified.nc')
#         self.scalar_path = os.path.join(SCALAR_PATH,
#                                         'aqum_no2_modified.nc')
#         self.dframe = dr.Renderer(self.timeseries_path)
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


class TestErrors:
    """
    Class to check that errors are caught and handled correctly.
    """

    @staticmethod
    @pytest.fixture(scope="class")
    def renderer(sampledir):
        path = os.path.join(
            sampledir,
            "timeseries",
            "aircraft_o3_timeseries.nc"
        )
        return dr.Renderer(path)

    def test_render_error(self, renderer):
        # Check that if all our coordinates end up set as None, then an
        # error is raised.
        with pytest.raises(ValueError):
            renderer.render()
