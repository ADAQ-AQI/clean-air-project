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
    Class to test object initialisation in Renderer.  This process must be able to identify incoming objects, convert
    them to lasy iris cubes and extract the coordinate metadata.
    """

    @pytest.yield_fixture(autouse=True)
    def setup_class(self, sampledir):
        """SET UP all inputs to tests"""
        path = os.path.join(sampledir, "model_full", "aqum_daily_daqi_mean_20200520.nc")
        self.renderer = dr.Renderer(path)

    def test_lazy_iris_data(self):
        """GIVEN a dataset with multiple coordinates,
        WHEN the dataset is loaded into an iris cube to identify coordinates,
        THEN the iris object is lazily loaded (i.e. metadata loaded without data until needed)."""
        assert self.renderer.plot_list[0].has_lazy_data

    def test_found_dim_coords(self):
        """GIVEN a dataset with multiple coordinates,
        WHEN iris guesses the coordinates present,
        THEN those coordinates are as we expected."""
        assert self.renderer.x_coord == 'projection_x_coordinate'
        assert self.renderer.y_coord == 'projection_y_coordinate'
        # height and time are scalar coords so will not be collected:
        assert self.renderer.z_coord is None
        assert self.renderer.t_coord is None


class TestRenderMapCall:
    """
    Class to test 'render' method of Renderer when producing maps.  Specifically, renderer needs to be able to
    identify timeseries datasets and map datasets.  A map will have multiple dimension coordinates.
    """

    @pytest.yield_fixture(autouse=True)
    def setup_class(self, sampledir):
        """SET UP all inputs to tests"""
        self.model_path = os.path.join(sampledir, 'model', 'aqum_daily_daqi_mean.nc')
        self.dframe = dr.Renderer(self.model_path)
        self.dframe.render()

    def test_render_map(self):
        # Check that if the data has an x and a y coordinate, the
        # renderer chooses to create a map rather than a plot.
        assert self.dframe.img_type == 'map'

    def test_map_dataframe_is_geopandas(self):
        # Check that if a map is being plotted, the dataframe generated is a pandas object:
        assert isinstance(self.dframe.rendered_df, pandas.DataFrame)


class TestRenderPlotCall:
    """
    Class to test 'render' method of Renderer when producing plots.  Specifically, renderer needs to be able to
    identify timeseries datasets and map datasets.  A timeseries dataset will have only one dimension coordinate
    (aligned with output from all Timeseries functions in dataset_renderer.py).
    """
    @pytest.yield_fixture(autouse=True)
    def setup_class(self, sampledir):
        """SET UP all inputs to tests."""
        self.timeseries_path = os.path.join(sampledir, "timeseries", "aqum_hourly_no2_timeseries.nc")
        self.dframe = dr.Renderer(self.timeseries_path)
        self.dframe.render()

    def test_render_timeseries(self):
        """GIVEN a dataset with only one dimension coordinate (time),
        WHEN dataset_renderer.Renderer(dataset).render() is called,
        THEN a pandas dataframe ready for plotting a timeseries graph is produced"""
        assert self.dframe.img_type == 'timeseries'

    def test_plot_dataframe_is_pandas(self):
        """GIVEN a single dataset with only one dimension coordinate (time),
        WHEN dataset_renderer.Renderer(dataset).render() is called,
        THEN the resulting dataframe is a pandas Series object."""
        assert isinstance(self.dframe.rendered_df, pandas.Series)

    def test_multipolygon_is_pandas(self, sampledir):
        """GIVEN a dataset with one dimension coordinate (time) and multiple cubes in a cubelist,
        WHEN dataset_renderer.Renderer(dataset).render() is called,
        THEN the resulting dataframe is a pandas object."""
        # Create a cubelist to pass to Renderer:
        cube_zero = iris.load(os.path.join(sampledir, "timeseries", "aqum_hourly_no2_timeseries.nc"))
        # copy cube, add 10 to all values to distinguish copy from original.
        cube_one = cube_zero[0].copy()
        for value in cube_one.data:
            value += 10
        self.cubelist = iris.cube.CubeList([cube_zero, cube_one])

        dframe_list = dr.Renderer(self.cubelist).render()
        assert isinstance(dframe_list, pandas.DataFrame)


def test_render_error():
    """GIVEN a null input (no cubes, no pathstring),
    WHEN the renderer is called to identify coordinates,
    THEN an error is raised as no coordinates can be found."""
    with pytest.raises(ValueError):
        dr.Renderer(None).render()
