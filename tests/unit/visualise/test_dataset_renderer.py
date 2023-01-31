"""
Unit tests for test_dataset_renderer.py
"""

import os
import pytest
import pandas
import iris
import iris.cube

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



class TestRenderMapCall:
    """
    Class to test 'render' method of Renderer when producing maps.
    """
    def setup_class(self, sampledir):
        self.model_path = os.path.join(sampledir, 'model', 'aqum_daily_daqi_mean_20200520.nc')
        self.dframe = dr.Renderer(self.model_path)
        self.dframe.render()

    def test_render_map(self):
        # Check that if the data has an x and a y coordinate, the
        # renderer chooses to create a map rather than a plot.
        assert self.dframe.img_type == 'map'

    def test_map_dataframe_is_geopandas(self):
        # Check that if a map is being plotted, the dataframe generated is a
        # geopandas object:
        assert isinstance(self.dframe, pandas.GeoDataFrame)


class TestRenderPlotCall:
    """
    Class to test 'render' method of Renderer when producing plots.  Specifically, renderer needs to be able to
    identify timeseries datasets and map datasets.  A timeseries dataset will have only one dimension coordinate
    (aligned with output from all Timeseries functions in dataset_renderer.py) whereas a map will have multiple
    dimension coordinates.
    """
    @pytest.yield_fixture(autouse=True)
    def setup_class(self, sampledir):
        """SET UP all inputs to tests."""
        self.timeseries_path = os.path.join(sampledir, "timeseries", "aqum_hourly_no2_timeseries.nc")
        self.dframe = dr.Renderer(self.timeseries_path)
        self.dframe.render()

        cube_zero = iris.load(os.path.join(sampledir, "timeseries", "aqum_hourly_no2_timeseries.nc"))
        # copy cube, add 10 to all values to distinguish copy from original.
        cube_one = cube_zero[0].copy()
        for value in cube_one.data:
            value += 10
        self.cubelist = iris.cube.CubeList([cube_zero, cube_one])

    def test_render_timeseries(self):
        """GIVEN a dataset with only one dimension coordinate (time),
        WHEN dataset_renderer.Renderer(dataset).render() is called,
        THEN a pandas dataframe ready for plotting a timeseries graph is produced"""
        assert self.dframe.img_type == 'timeseries'

    def test_plot_dataframe_is_pandas(self):
        """GIVEN a dataset with only one dimension coordinate (time),
        WHEN dataset_renderer.Renderer(dataset).render() is called,
        THEN the resulting dataframe is a pandas object."""
        assert isinstance(self.dframe, pandas.Dataset)

    def test_multipolygon_is_pandas(self):
        """GIVEN a dataset with one dimension coordinate (time) and multiple cubes in a cubelist,
        WHEN dataset_renderer.Renderer(dataset).render() is called,
        THEN the resulting dataframe is a pandas object."""
        dframe_list = dr.Renderer(self.cubelist).render()
        assert isinstance(dframe_list, pandas.Dataset)


def test_render_error():
    """GIVEN a null input (no cubes, no pathstring),
    WHEN the renderer is called to identify coordinates,
    THEN an error is raised as no coordinates can be found."""
    with pytest.raises(ValueError):
        dr.Renderer(None).render()
