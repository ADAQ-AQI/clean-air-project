import pytest
import unittest
from iris.coords import DimCoord
from iris.cube import Cube, CubeList
import iris.coord_systems
import numpy as np
from datetime import datetime, timedelta
from clean_air import data
from edr_server.core.models.metadata import CollectionMetadata


class TestExtractMetadata:
    @staticmethod
    @pytest.fixture
    def cube_1():
        latitude = DimCoord(np.linspace(-90, 90, 4),
                            standard_name='latitude',
                            units='degrees',
                            coord_system=iris.coord_systems.Mercator())
        longitude = DimCoord(np.linspace(45, 360, 8),
                             standard_name='longitude',
                             units='degrees',
                             coord_system=iris.coord_systems.Mercator())
        time = DimCoord(np.linspace(1, 24, 24),
                        standard_name='time',
                        units="hours since 1970-01-01 00:00:00")
        height = DimCoord(3.5,
                          standard_name="height",
                          units="m",
                          attributes={'positive': 'up'})
        cube = Cube(np.zeros((4, 8, 24), np.float32),
                    standard_name="mass_concentration_of_ozone_in_air",
                    units="ug/m3",
                    dim_coords_and_dims=[(latitude, 0),
                                         (longitude, 1),
                                         (time, 2)])
        cube.add_aux_coord(height)
        return cube

    @staticmethod
    @pytest.fixture
    def cube_2():
        x = DimCoord(np.linspace(1, 100, 200),
                     standard_name='projection_x_coordinate',
                     units='meters')
        y = DimCoord(np.linspace(1, 100, 200),
                     standard_name='projection_y_coordinate',
                     units='meters')
        time = DimCoord(np.linspace(101, 148, 48),
                        standard_name='time',
                        units="hours since 1970-01-01 00:00:00")
        cube = Cube(np.zeros((200, 200, 48), np.float32),
                    standard_name="mass_fraction_of_carbon_dioxide_in_air",
                    units="l",
                    dim_coords_and_dims=[(x, 0),
                                         (y, 1),
                                         (time, 2)])
        return cube

    @staticmethod
    @pytest.fixture
    def cube_3():
        latitude = DimCoord(np.linspace(-150, 150, 4),
                            standard_name='latitude',
                            units='degrees')
        longitude = DimCoord(np.linspace(-10, 400, 8),
                             standard_name='longitude',
                             units='degrees')
        time = DimCoord([1, 2, 3, 7, 8, 9],
                        standard_name='time',
                        units="hours since 1970-01-01 00:00:00")
        cube = Cube(np.zeros((4, 8, 6), np.float32),
                    standard_name="mass_concentration_of_ozone_in_air",
                    units="ug/m3",
                    dim_coords_and_dims=[(latitude, 0),
                                         (longitude, 1),
                                         (time, 2)])
        return cube

    @staticmethod
    @pytest.fixture
    def cube_4():
        latitude = DimCoord(np.linspace(125, 175, 4),
                            standard_name='latitude',
                            units='degrees',
                            coord_system=iris.coord_systems.GeogCS(6371229))
        longitude = DimCoord(np.linspace(420, 430, 8),
                             standard_name='longitude',
                             units='degrees',
                             coord_system=iris.coord_systems.GeogCS(6371229))
        time = DimCoord(np.linspace(1, 24, 24),
                        standard_name='time',
                        units="hours since 1970-01-01 00:00:00")
        cube = Cube(np.zeros((4, 8, 24), np.float32),
                    standard_name="mass_concentration_of_ozone_in_air",
                    units="ug/m3",
                    dim_coords_and_dims=[(latitude, 0),
                                         (longitude, 1),
                                         (time, 2)])
        return cube

    @staticmethod
    def test_return_type_cube(cube_1):
        cube_metadata = data.extract_metadata.extract_metadata(
            cube_1, 1, [], ['cube'], ['netCDF'])
        assert isinstance(cube_metadata, CollectionMetadata)

    @staticmethod
    def test_return_type_cubelist(cube_1, cube_2):
        cubelist_metadata = data.extract_metadata.extract_metadata(
            CubeList([cube_1, cube_2]), 1, [], ['cube'], ['netCDF'], 'title', 'desc')
        assert isinstance(cubelist_metadata, CollectionMetadata)

    @staticmethod
    def test_title_cube(cube_1):
        cube_metadata = data.extract_metadata.extract_metadata(
            cube_1, 1, [], ['cube'], ['netCDF'])
        assert cube_metadata.title == "mass_concentration_of_ozone_in_air"

    @staticmethod
    def test_title_cubelist(cube_1, cube_2):
        cubelist_metadata = data.extract_metadata.extract_metadata(
            CubeList([cube_1, cube_2]), 1, [], ['cube'], ['netCDF'], 'title', 'desc')
        assert cubelist_metadata.title == "title"

    @staticmethod
    def test_total_time_extent(cube_1):
        cube_metadata = data.extract_metadata.extract_metadata(
            cube_1, 1, [], ['cube'], ['netCDF'])
        test_array = np.arange(datetime(1970,1,1,1), datetime(1970,1,2,1), timedelta(hours=1)).astype(datetime)
        assert cube_metadata.extent.temporal.values == test_array.tolist()

    @staticmethod
    def test_total_time_extent_gap(cube_3):
        cube_metadata = data.extract_metadata.extract_metadata(
            cube_3, 1, [], ['cube'], ['netCDF'])
        lower = np.arange(datetime(1970,1,1,1), datetime(1970,1,1,4), timedelta(hours=1)).astype(datetime)
        upper = np.arange(datetime(1970,1,1,7), datetime(1970,1,1,10), timedelta(hours=1)).astype(datetime)
        test_array = np.concatenate((lower, upper))
        assert cube_metadata.extent.temporal.values == test_array.tolist()

    @staticmethod
    def test_total_vertical_extent(cube_1):
        cube_metadata = data.extract_metadata.extract_metadata(
            cube_1, 1, [], ['cube'], ['netCDF'])
        assert cube_metadata.extent.vertical.values == pytest.approx(3.5)

    @staticmethod
    def test_parameters_length_cube(cube_1):
        cube_metadata = data.extract_metadata.extract_metadata(
            cube_1, 1, [], ['cube'], ['netCDF'])
        assert len(cube_metadata.parameters) == 1

    @staticmethod
    def test_parameters_length_cubelist(cube_1, cube_2):
        cubelist_metadata = data.extract_metadata.extract_metadata(
            CubeList([cube_1, cube_2]), 1, [], ['cube'], ['netCDF'], 'title', 'desc')
        assert len(cubelist_metadata.parameters) == 2

    @staticmethod
    def test_containing_polygon_cube(cube_1):
        cube_metadata = data.extract_metadata.extract_metadata(
            cube_1, 1, [], ['cube'], ['netCDF'])
        assert cube_metadata.extent.spatial.bbox.bounds == (45, -90, 360, 90)

    @staticmethod
    def test_containing_polygon_equal(cube_1):
        # two equal polygons
        cubelist_metadata = data.extract_metadata.extract_metadata(
            CubeList([cube_1, cube_1]), 1, [], ['cube'], ['netCDF'], 'title', 'desc')
        assert cubelist_metadata.extent.spatial.bbox.bounds == (45, -90, 360, 90)

    @staticmethod
    def test_containing_polygon_overlapping(cube_1, cube_2):
        # two partially overlapping polygons
        cubelist_metadata = data.extract_metadata.extract_metadata(
            CubeList([cube_1, cube_2]), 1, [], ['cube'], ['netCDF'], 'title', 'desc')
        assert cubelist_metadata.extent.spatial.bbox.bounds == (1, -90, 360, 100)

    @staticmethod
    def test_containing_polygon_within(cube_1, cube_3):
        # one polygon completely within another polygon
        cubelist_metadata = data.extract_metadata.extract_metadata(
            CubeList([cube_1, cube_3]), 1, [], ['cube'], ['netCDF'], 'title', 'desc')
        assert cubelist_metadata.extent.spatial.bbox.bounds == (-10, -150, 400, 150)

    @staticmethod
    def test_containing_polygon_overlapping_and_within(cube_1, cube_2, cube_3):
        # two partially overlapping polygons completely within a third polygon
        cubelist_metadata = data.extract_metadata.extract_metadata(
            CubeList([cube_1, cube_2, cube_3]), 1, [], ['cube'], ['netCDF'], 'title', 'desc')
        assert cubelist_metadata.extent.spatial.bbox.bounds == (-10, -150, 400, 150)

    @staticmethod
    def test_containing_polygon_separate(cube_1, cube_4):
        # two completely separate polygons
        cubelist_metadata = data.extract_metadata.extract_metadata(
            CubeList([cube_1, cube_4]), 1, [], ['cube'], ['netCDF'], 'title', 'desc')
        assert cubelist_metadata.extent.spatial.bbox.bounds == (45, -90, 430, 175)

    @staticmethod
    def test_containing_polygon_overlap_within_separate(cube_1, cube_2, cube_3, cube_4):
        # two partially overlapping polygons completely within a third polygon, and a completely separate fourth polygon
        cubelist_metadata = data.extract_metadata.extract_metadata(
            CubeList([cube_1, cube_2, cube_3, cube_4]), 1, [], ['cube'], ['netCDF'], 'title', 'desc')
        assert cubelist_metadata.extent.spatial.bbox.bounds == (-10, -150, 430, 175)


class errorTest(unittest.TestCase):
    def test_dimensionless_cube_error(self):
        time = DimCoord(np.linspace(1, 24, 24),
                        standard_name='time',
                        units="hours since 1970-01-01 00:00:00")
        cube = Cube(np.zeros((24), np.float32),
                    standard_name="mass_concentration_of_ozone_in_air",
                    units="ug/m3",
                    dim_coords_and_dims=[(time, 0)])
        with self.assertRaisesRegex(ValueError, 'The dataset must contain at least one variable with x and y axes.'):
            data.extract_metadata.extract_metadata(
                cube, 1, [], ['cube'], ['netCDF'])
