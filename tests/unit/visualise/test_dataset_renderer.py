"""
Unit tests for test_dataset_renderer.py
"""

import os
import pytest
import pandas
import iris
from iris.cube import Cube, CubeList
from iris.time import PartialDateTime
from shapely.geometry import Polygon, MultiPolygon

import clean_air.visualise.dataset_renderer as dr
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
def aircraft_data(sampledir):
    aircraft_file = os.path.join(sampledir, "aircraft", "M285_sample.nc")
    aircraft_data = iris.load_cube(aircraft_file, "mass_concentration_of_nitrogen_dioxide_in_air")
    return aircraft_data


@pytest.fixture()
def tmp_output_path(tmp_path):
    tmp_output_path = tmp_path / "tmp_output_path"
    tmp_output_path.mkdir()
    return tmp_output_path


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
        """
        GIVEN a dataset with multiple coordinates,
        WHEN the dataset is loaded into an iris cube to identify coordinates,
        THEN the iris object is lazily loaded (i.e. metadata loaded without data until needed)."""
        assert self.renderer.plot_list[0].has_lazy_data

    def test_found_dim_coords(self):
        """
        GIVEN a dataset with multiple coordinates,
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
        """
        GIVEN a dataset with only one dimension coordinate (time),
        WHEN dataset_renderer.Renderer(dataset).render() is called,
        THEN a pandas dataframe ready for plotting a timeseries graph is produced"""
        assert self.dframe.img_type == 'timeseries'

    def test_plot_dataframe_is_pandas(self):
        """
        GIVEN a single dataset with only one dimension coordinate (time),
        WHEN dataset_renderer.Renderer(dataset).render() is called,
        THEN the resulting dataframe is a pandas Series object."""
        assert isinstance(self.dframe.rendered_df, pandas.Series)

    def test_multipolygon_is_pandas(self, sampledir):
        """
        GIVEN a dataset with one dimension coordinate (time) and multiple cubes in a cubelist,
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
    """
    GIVEN a null input (no cubes, no pathstring),
    WHEN the renderer is called to identify coordinates,
    THEN an error is raised as no coordinates can be found."""
    with pytest.raises(AttributeError):
        dr.Renderer(None).render()


class TestTimeSeries:
    """Class to test generation of time series data with various processing methods (i.e. linear interpolation and
    box, shape and diurnal averaging)."""

    def test_linear_interpolate_3d_data(self, clean_data, tmp_output_path):
        """
        GIVEN a full dataset with multiple dimension coordinates,
        WHEN linearly interpolated through the TimeSeries class,
        THEN the result is an iris Cube of the expected shape."""
        interpolated_data = dr.TimeSeries(clean_data, 150, 150).linear_interpolate()
        assert isinstance(interpolated_data, Cube)
        # Shape of interpolated cube should be (24 time, 1 lat, 1 lon), however scalar coords will be collapsed to
        # assist plot rendering process, so final shape should be (24,).
        assert interpolated_data.shape == (24,)

    def test_box_average_data(self, clean_data, tmp_output_path):
        """
        GIVEN a full dataset with multiple dimension coordinates,
        WHEN spatially averaged as a box through the TimeSeries class,
        THEN the result is an iris Cube of the expected shape."""
        boxed_data = dr.TimeSeries(clean_data).spatial_average(shape='box', coords=[10000, 10000, 15000, 15000])
        assert isinstance(boxed_data, Cube)
        assert boxed_data.shape == (24,)

    def test_shape_averaged_data(self, clean_data, tmp_output_path):
        """
        GIVEN a shapely Polygon,
        WHEN spatially averaged as that Polygon through the TimeSeries class,
        THEN the result is an iris Cube of the expected shape."""
        shape = Polygon([(0, 0), (100, 100), (100, 0)])
        shape_data = dr.TimeSeries(clean_data).spatial_average(shape=shape)
        assert isinstance(shape_data, Cube)

    def test_shapes_averaged_data(self, clean_data, tmp_output_path):
        """
        GIVEN a shapely MultiPolygon,
        WHEN spatially averaged as those respective Polygons through the TimeSeries class,
        THEN the result is an iris CubeList."""
        poly_one = Polygon([(0, 0), (100, 100), (100, 0)])
        poly_two = Polygon([(0, 0), (-100, -100), (-100, 0)])
        shapes = MultiPolygon([poly_one, poly_two])
        shape_data = dr.TimeSeries(clean_data).spatial_average(shape=shapes)
        assert isinstance(shape_data, CubeList)

    def test_diurnal_averaged_data(self, multiday_data):
        """
        GIVEN a DataSubset object containing data from multiple days,
        WHEN diurnally averaged through the TimeSeries class,
        THEN the result is a single iris Cube"""
        diurnal_data = dr.TimeSeries(multiday_data).diurnal_average()
        assert isinstance(diurnal_data, Cube)

    def test_track_data(self, aircraft_data):
        """
        GIVEN a cube of aircraft data
        WHEN Timeseries.track() is called for valid time bounds
        THEN an iris cube is returned
        """
        track_data = dr.TimeSeries(aircraft_data).track(PartialDateTime(hour=13), PartialDateTime(hour=14))
        assert isinstance(track_data, Cube)
