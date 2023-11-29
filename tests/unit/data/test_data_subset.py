import os

import pytest
import iris
import shapely.geometry
from iris.cube import Cube
from iris.time import PartialDateTime
from shapely.geometry import Polygon, Point
# from shapely import Polygon, Point
import numpy as np
import cartopy.crs as ccrs

from clean_air.data import DataSubset
from clean_air import util


class TestPointSubset:
    @staticmethod
    @pytest.fixture
    def dataset(sampledir):
        return DataSubset(os.path.join(sampledir, "model_full", "aqum_daily*"))

    @staticmethod
    def test_as_cube(dataset):
        cube = dataset.extract_point((100, 200))

        # Check we have the point we asked for
        xcoord, ycoord = util.cubes.get_xy_coords(cube)
        assert iris.util.array_equal(xcoord.points, [100])
        assert iris.util.array_equal(ycoord.points, [200])

    @staticmethod
    def test_as_cube_latlon(dataset):
        cube = dataset.extract_point((-0.1, 51.5), crs=ccrs.Geodetic())

        # Check we have the point we asked for
        xcoord, ycoord = util.cubes.get_xy_coords(cube)
        assert iris.util.array_equal(xcoord.points.round(4), [531866.1304])
        assert iris.util.array_equal(ycoord.points.round(4), [179660.9048])


class TestBoxSubset:
    @staticmethod
    @pytest.fixture
    def dataset(sampledir):
        return DataSubset(os.path.join(sampledir, "model_full", "aqum_daily*"))

    @staticmethod
    def test_as_cube(dataset):
        cube = dataset.extract_box((-1000, -2000, 3000, 4000))

        # Check we have the points we asked for (multiples of 2000m within
        # each range)
        xcoord, ycoord = util.cubes.get_xy_coords(cube)
        assert iris.util.array_equal(xcoord.points, [0, 2000])
        assert iris.util.array_equal(ycoord.points, [-2000, 0, 2000, 4000])

    @staticmethod
    def test_as_cube_latlon(dataset):
        cube = dataset.extract_box((-4, 50.4, -2.8, 51.2), crs=ccrs.Geodetic())

        # Check we have the points we asked for (multiples of 2000m within
        # each range)
        # Strictly speaking, the transformed box would have slightly curved
        # edges, and the "corner-most" gridpoints would be:
        # tl: (262000, 146000)
        # tr: (344000, 144000)
        # br: (342000, 56000)
        # bl: (258000, 58000)
        # We therefore expect a slightly larger box, covering the minimum
        # and maximum in both directions
        xcoord, ycoord = util.cubes.get_xy_coords(cube)
        assert iris.util.array_equal(xcoord.points[[0, -1]], [258000, 344000])
        assert iris.util.array_equal(ycoord.points[[0, -1]], [56000, 146000])


class TestTrackSubset:
    """Tests for data_subset.extract_track method"""

    @staticmethod
    @pytest.fixture
    def dataset(sampledir):
        path = os.path.join(sampledir, "aircraft", "M285_sample.nc")
        sample_cube = iris.load_cube(path, 'NO2_concentration_ug_m3')
        return DataSubset(sample_cube)

    @staticmethod
    @pytest.fixture
    def model_dataset(sampledir):
        path = os.path.join(sampledir, "model_full", "aqum_hourly_o3_20200521.nc")
        return DataSubset(path)

    @staticmethod
    def test_as_cube(dataset):
        """
        GIVEN a cube of aircraft data
        WHEN the track is extracted
        THEN the track is an instance of an iris cube
        """
        cube = dataset.extract_track()
        assert isinstance(cube, Cube)

    @staticmethod
    def test_dimensions(dataset):
        """
        GIVEN a cube of aircraft data
        WHEN the track is extracted
        THEN the track has no auxillary coordinates and a single dimensional coordinate
        """
        cube = dataset.extract_track()
        assert len(cube.aux_coords) == 0
        assert len(cube.dim_coords) == 1

    @staticmethod
    def test_time_bound(dataset):
        """
        GIVEN a cube of aircraft data
        WHEN the track is extracted for a specified time period
        THEN the track's time coordinate matches this period
        """
        cube = dataset.extract_track(start=PartialDateTime(hour=13), end=PartialDateTime(hour=14))
        # integer values are in seconds since 2021-03-30 00:00:00
        assert cube.coord('time').points[0] == int(46800)
        assert cube.coord('time').points[-1] == int(50399)

    @staticmethod
    def test_time_bound_start_only(dataset):
        """
        GIVEN a cube of aircraft data
        WHEN the track is extracted after a specified start time
        THEN the track's time coordinate matches this period
        """
        cube = dataset.extract_track(start=PartialDateTime(hour=13))
        # integer values are in seconds since 2021-03-30 00:00:00
        assert cube.coord('time').points[0] == int(46800)
        assert cube.coord('time').points[-1] == int(54300)

    @staticmethod
    def test_time_bound_end_only(dataset):
        """
        GIVEN a cube of aircraft data
        WHEN the track is extracted before a specified end time
        THEN the track's time coordinate matches this period
        """
        cube = dataset.extract_track(end=PartialDateTime(hour=14))
        # integer values are in seconds since 2021-03-30 00:00:00
        assert cube.coord('time').points[0] == int(43260)
        assert cube.coord('time').points[-1] == int(50399)

    @staticmethod
    def test_time_bound_error(dataset):
        """
        GIVEN a cube of aircraft data
        WHEN the track is extracted for a specified time period out of data range
        THEN the appropriate error is raised
        """
        with pytest.raises(ValueError, match='Empty cube, likely due to time bounds being out of range'):
            dataset.extract_track(start=PartialDateTime(hour=20), end=PartialDateTime(hour=21))

    @staticmethod
    def test_multidim_data(model_dataset, capsys):
        """
        GIVEN a cube of multidimensional model data
        WHEN the track is extracted
        THEN the appropriate statement is printed and the coordinates are reduced, 
        even if the resulting data doesn't make sense
        """
        cube = model_dataset.extract_track()
        captured = capsys.readouterr()
        assert captured.out.strip() == "Found extra dimensions, attempting to remove..."
        assert len(cube.aux_coords) == 0
        assert len(cube.dim_coords) == 1


class TestAverageTime:
    @staticmethod
    @pytest.fixture
    def dataset(sampledir):
        return DataSubset(os.path.join(sampledir, "model_full", "aqum_hourly_o3_48_hours.nc"))

    @staticmethod
    def test_as_cube(dataset):
        cube = dataset.average_time(iris.analysis.MEAN)

        # check that the resulting cube has 24 hours
        assert cube.coord('time').points.shape == (24,)


class TestPolygonSubset:
    """Tests for DataSubset using a Polygon"""

    @staticmethod
    @pytest.fixture
    def polygon_subset(sampledir):
        """Set up inputs for all tests"""
        path = os.path.join(sampledir, "model_full", "aqum_hourly_o3_48_hours.nc")
        dataset = DataSubset(path)
        points = [(289271.9, 93197.0),
                  (289351.3, 95110.1),
                  (293405.1, 96855.0),
                  (296721.1, 94960.3),
                  (297165.1, 86966.9),
                  (294181.6, 89357.2),
                  (291388.0, 89272.6)]

        # Extract the test polygon
        shape = Polygon(points)
        cube = dataset.extract_shape(shape)
        return cube

    @staticmethod
    def test_is_cube(polygon_subset):
        """
        GIVEN a dataset of gridded model points, an OSGB CRS and a set of points roughly representing Exeter,
        WHEN these points are extracted into a subcube using DataSubset.extract_shape,
        THEN the result is an iris cube.
        """
        assert isinstance(polygon_subset, Cube)

    @staticmethod
    def test_data_masking(polygon_subset):
        """
        GIVEN a dataset of gridded model points, an OSGB CRS and a set of points roughly representing Exeter,
        WHEN these points are extracted into a subcube using DataSubset.extract_shape and points outside the shape
        are masked,
        THEN the masked points appear where we expect.
        """
        # Create mask array (these are the indices of points inside the Polygon, so these points will NOT be masked):
        x_points = [135, 136, 136, 136, 137, 137, 137, 137, 137, 138, 138, 138, 138, 139, 139, 139, 139, 140, 140, 140,
                    140]
        y_points = [268, 266, 267, 268, 264, 265, 266, 267, 268, 264, 265, 266, 267, 264, 265, 266, 267, 264, 265, 266,
                    267]

        subcube = polygon_subset[0]  # Polygon is geographical, so one time slice will cover all unmasked points.
        for x, y in zip(x_points, y_points):
            assert subcube.data.mask[x, y] == False
