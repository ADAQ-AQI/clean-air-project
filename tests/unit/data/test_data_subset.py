import os

import pytest
import numpy as np
import iris
import shapely.geometry
import cartopy.crs as ccrs

from clean_air.data import DataSubset
from clean_air import util


# Define some sample points (an extremely simple representation of Exeter)
POINTS_OSGB = [
    (289271.9, 93197.0),
    (289351.3, 95110.1),
    (293405.1, 96855.0),
    (296721.1, 94960.3),
    (297165.1, 86966.9),
    (294181.6, 89357.2),
    (291388.0, 89272.6),
]
POINTS_LATLON = [
    (-3.5690, 50.7273),
    (-3.5685, 50.7445),
    (-3.5115, 50.7609),
    (-3.4640, 50.7445),
    (-3.4555, 50.6727),
    (-3.4984, 50.6936),
    (-3.5379, 50.6924),
]


class TestPointSubset:
    @staticmethod
    def test_as_cube(sampledir):
        # Create example dataset
        ds = DataSubset(
            os.path.join(sampledir, "model_full", "aqum_daily*"),
            point=(100, 200),
        )
        cube = ds.as_cube()

        # Check we have the point we asked for
        xcoord, ycoord = util.cubes.get_xy_coords(cube)
        assert iris.util.array_equal(xcoord.points, [100])
        assert iris.util.array_equal(ycoord.points, [200])

    @staticmethod
    def test_as_cube_latlon(sampledir):
        # Create example dataset
        ds = DataSubset(
            os.path.join(sampledir, "model_full", "aqum_daily*"),
            point=(-0.1, 51.5),
            crs=ccrs.Geodetic(),
        )
        cube = ds.as_cube()

        # Check we have the point we asked for
        xcoord, ycoord = util.cubes.get_xy_coords(cube)
        assert iris.util.array_equal(xcoord.points.round(4), [531866.1304])
        assert iris.util.array_equal(ycoord.points.round(4), [179660.9048])


class TestBoxSubset:
    @staticmethod
    def test_as_cube(sampledir):
        # Create example dataset
        ds = DataSubset(
            os.path.join(sampledir, "model_full", "aqum_daily*"),
            box=(-1000, -2000, 3000, 4000),
        )
        cube = ds.as_cube()

        # Check we have the points we asked for (multiples of 2000m within
        # each range)
        xcoord, ycoord = util.cubes.get_xy_coords(cube)
        assert iris.util.array_equal(xcoord.points, [0, 2000])
        assert iris.util.array_equal(ycoord.points, [-2000, 0, 2000, 4000])

    @staticmethod
    def test_as_cube_latlon(sampledir):
        # Create example dataset
        ds = DataSubset(
            os.path.join(sampledir, "model_full", "aqum_daily*"),
            box=(-4, 50.4, -2.8, 51.2),
            crs=ccrs.Geodetic(),
        )
        cube = ds.as_cube()

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


class TestPolygonSubset:
    @staticmethod
    @pytest.mark.parametrize(
        "crs, points",
        [(None, POINTS_OSGB), (ccrs.Geodetic(), POINTS_LATLON)],
    )
    def test_as_cube(sampledir, crs, points):
        # Define a test polygon
        shape = shapely.geometry.Polygon(points)

        # Create example dataset
        ds = DataSubset(
            os.path.join(
                sampledir,
                "model_full",
                "aqum_hourly_o3_20200520.nc"
            ),
            shape=shape,
            crs=crs,
        )
        cube = ds.as_cube()

        # Check we have the right mask (on a 2d slice of this 3d cube)
        # Note: this "looks" upside down compared to how it would be plotted
        expected_mask = np.array(
            [[1, 1, 1, 1, 0],
             [1, 1, 0, 0, 0],
             [0, 0, 0, 0, 0],
             [0, 0, 0, 0, 1],
             [0, 0, 0, 0, 1],
             [0, 0, 0, 0, 1]]
        )
        subcube = next(cube.slices_over("time"))
        assert iris.util.array_equal(subcube.data.mask, expected_mask)

        # Simple data check, which, as the mask is taken into account, should
        # be a pretty reliable test
        assert round(cube.data.mean(), 8) == 57.66388811
