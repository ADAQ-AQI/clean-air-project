import pytest
import unittest
from iris.coords import DimCoord
from iris.cube import Cube, CubeList
import iris.coord_systems
import numpy as np
import os
from datetime import datetime
from clean_air import data
from edr_server.core.models.metadata import CollectionMetadata


class TestExtractMetadata:
    @staticmethod
    @pytest.fixture
    def cube_1():
        latitude = DimCoord(
            np.linspace(-90, 90, 4),
            standard_name="latitude",
            units="degrees",
            coord_system=iris.coord_systems.Mercator(),
        )
        longitude = DimCoord(
            np.linspace(45, 360, 8),
            standard_name="longitude",
            units="degrees",
            coord_system=iris.coord_systems.Mercator(),
        )
        time = DimCoord(
            np.linspace(1, 24, 24),
            standard_name="time",
            units="hours since 1970-01-01 00:00:00",
        )
        height = DimCoord(
            3.5, standard_name="height", units="m", attributes={"positive": "up"}
        )
        cube = Cube(
            np.zeros((4, 8, 24), np.float32),
            standard_name="mass_concentration_of_ozone_in_air",
            units="ug/m3",
            dim_coords_and_dims=[(latitude, 0), (longitude, 1), (time, 2)],
        )
        cube.add_aux_coord(height)
        return cube

    @staticmethod
    @pytest.fixture
    def cube_2():
        x = DimCoord(
            np.linspace(1, 100, 200),
            standard_name="projection_x_coordinate",
            units="meters",
        )
        y = DimCoord(
            np.linspace(1, 100, 200),
            standard_name="projection_y_coordinate",
            units="meters",
        )
        time = DimCoord(
            np.linspace(101, 148, 48),
            standard_name="time",
            units="hours since 1970-01-01 00:00:00",
        )
        cube = Cube(
            np.zeros((200, 200, 48), np.float32),
            standard_name="mass_fraction_of_carbon_dioxide_in_air",
            units="l",
            dim_coords_and_dims=[(x, 0), (y, 1), (time, 2)],
        )
        return cube

    @staticmethod
    @pytest.fixture
    def cube_3():
        latitude = DimCoord(
            np.linspace(-150, 150, 4), standard_name="latitude", units="degrees"
        )
        longitude = DimCoord(
            np.linspace(-10, 400, 8), standard_name="longitude", units="degrees"
        )
        time = DimCoord(
            [1, 2, 3, 7, 8, 9],
            standard_name="time",
            units="hours since 1970-01-01 00:00:00",
        )
        cube = Cube(
            np.zeros((4, 8, 6), np.float32),
            standard_name="mass_concentration_of_ozone_in_air",
            units="ug/m3",
            dim_coords_and_dims=[(latitude, 0), (longitude, 1), (time, 2)],
        )
        return cube

    @staticmethod
    @pytest.fixture
    def cube_4():
        latitude = DimCoord(
            np.linspace(125, 175, 4),
            standard_name="latitude",
            units="degrees",
            coord_system=iris.coord_systems.GeogCS(6371229),
        )
        longitude = DimCoord(
            np.linspace(420, 430, 8),
            standard_name="longitude",
            units="degrees",
            coord_system=iris.coord_systems.GeogCS(6371229),
        )
        time = DimCoord(
            np.linspace(1, 24, 24),
            standard_name="time",
            units="hours since 1970-01-01 00:00:00",
        )
        cube = Cube(
            np.zeros((4, 8, 24), np.float32),
            standard_name="mass_concentration_of_ozone_in_air",
            units="ug/m3",
            dim_coords_and_dims=[(latitude, 0), (longitude, 1), (time, 2)],
        )
        return cube


    @staticmethod
    def test_return_type_cube(cube_1):
        """
        GIVEN a single cube
        WHEN metadata is extracted
        THEN the metadata is an instance of CollectionMetadata
        """
        cube_metadata = data.extract_metadata.extract_metadata(
            cube_1, 1, [], ["cube"], ["netCDF"]
        )
        assert isinstance(cube_metadata, CollectionMetadata)

    @staticmethod
    def test_return_type_cubelist(cube_1, cube_2):
        """
        GIVEN a cubelist
        WHEN metadata is extracted
        THEN the metadata is an instance of CollectionMetadata
        """
        cubelist_metadata = data.extract_metadata.extract_metadata(
            CubeList([cube_1, cube_2]), 1, [], ["cube"], ["netCDF"], "title", "desc"
        )
        assert isinstance(cubelist_metadata, CollectionMetadata)

    @staticmethod
    def test_title_cube(cube_1):
        """
        GIVEN a single cube
        WHEN metadata is extracted
        THEN the metadata.title is the cube title
        """
        cube_metadata = data.extract_metadata.extract_metadata(
            cube_1, 1, [], ["cube"], ["netCDF"]
        )
        assert cube_metadata.title == "mass_concentration_of_ozone_in_air"

    @staticmethod
    def test_title_cubelist(cube_1, cube_2):
        """
        GIVEN a cubelist and provided title
        WHEN metadata is extracted
        THEN the metadata.title is the title given
        """
        cubelist_metadata = data.extract_metadata.extract_metadata(
            CubeList([cube_1, cube_2]), 1, [], ["cube"], ["netCDF"], "title", "desc"
        )
        assert cubelist_metadata.title == "title"

    @staticmethod
    def test_unit(cube_1):
        """
        GIVEN a single cube
        WHEN metadata is extracted
        THEN the metadata unit information matches the cube and is in correct format
        """
        cube_metadata = data.extract_metadata.extract_metadata(
            cube_1, 1, [], ["cube"], ["netCDF"]
        )
        assert cube_metadata.parameters[0].unit.labels == "1e-09 meter^-3-kilogram"
        assert cube_metadata.parameters[0].unit.symbol == "1e-09 m-3.kg"

    @staticmethod
    def test_total_time_extent(cube_1):
        """
        GIVEN a single cube
        WHEN metadata is extracted
        THEN the temporal extent is the cube's time range
        """
        cube_metadata = data.extract_metadata.extract_metadata(
            cube_1, 1, [], ["cube"], ["netCDF"]
        )
        assert cube_metadata.extent.temporal.intervals[0].start == datetime(
            1970, 1, 1, 1
        )
        assert cube_metadata.extent.temporal.intervals[0].end == datetime(1970, 1, 2, 0)

    @staticmethod
    def test_total_time_extent_gap(cube_3):
        """
        GIVEN a single cube with a non-continuous time extent
        WHEN metadata is extracted
        THEN the temporal extent is the cube's time range
        """
        cube_metadata = data.extract_metadata.extract_metadata(
            cube_3, 1, [], ["cube"], ["netCDF"]
        )
        assert cube_metadata.extent.temporal.intervals[0].start == datetime(
            1970, 1, 1, 1
        )
        assert cube_metadata.extent.temporal.intervals[0].end == datetime(1970, 1, 1, 9)

    @staticmethod
    def test_total_vertical_extent(cube_1):
        """
        GIVEN a single cube with a height dimension
        WHEN metadata is extracted
        THEN the vertical extent is the same as the cube
        """
        cube_metadata = data.extract_metadata.extract_metadata(
            cube_1, 1, [], ["cube"], ["netCDF"]
        )
        assert cube_metadata.extent.vertical.values == pytest.approx(3.5)

    @staticmethod
    def test_parameters_length_cube(cube_1):
        """
        GIVEN a single cube
        WHEN metadata is extracted
        THEN metadata.parameters has length 1
        """
        cube_metadata = data.extract_metadata.extract_metadata(
            cube_1, 1, [], ["cube"], ["netCDF"]
        )
        assert len(cube_metadata.parameters) == 1

    @staticmethod
    def test_parameters_length_cubelist(cube_1, cube_2):
        """
        GIVEN a cubelist of two cubes
        WHEN metadata is extracted
        THEN metadata.parameters has length 2
        """
        cubelist_metadata = data.extract_metadata.extract_metadata(
            CubeList([cube_1, cube_2]), 1, [], ["cube"], ["netCDF"], "title", "desc"
        )
        assert len(cubelist_metadata.parameters) == 2

    @staticmethod
    def test_containing_polygon_cube(cube_1):
        """
        GIVEN a single cube
        WHEN metadata is extracted
        THEN the bounds of the spatial extent matches the cube
        """
        cube_metadata = data.extract_metadata.extract_metadata(
            cube_1, 1, [], ["cube"], ["netCDF"]
        )
        assert cube_metadata.extent.spatial.bbox.bounds == (45, -90, 360, 90)

    @staticmethod
    def test_containing_polygon_equal(cube_1):
        """
        GIVEN a cubelist of two identical cubes
        WHEN metadata is extracted
        THEN the bounds of the spatial extent matches both cubes
        """
        cubelist_metadata = data.extract_metadata.extract_metadata(
            CubeList([cube_1, cube_1]), 1, [], ["cube"], ["netCDF"], "title", "desc"
        )
        assert cubelist_metadata.extent.spatial.bbox.bounds == (45, -90, 360, 90)

    @staticmethod
    def test_containing_polygon_overlapping(cube_1, cube_2):
        """
        GIVEN a cubelist of two cubes that partially overlap
        WHEN metadata is extracted
        THEN the bounds of the spatial extent matches the group's total extent
        """
        cubelist_metadata = data.extract_metadata.extract_metadata(
            CubeList([cube_1, cube_2]), 1, [], ["cube"], ["netCDF"], "title", "desc"
        )
        assert cubelist_metadata.extent.spatial.bbox.bounds == (1, -90, 360, 100)

    @staticmethod
    def test_containing_polygon_within(cube_1, cube_3):
        """
        GIVEN a cubelist of two cubes, one completely within another
        WHEN metadata is extracted
        THEN the bounds of the spatial extent matches the group's total extent
        """
        cubelist_metadata = data.extract_metadata.extract_metadata(
            CubeList([cube_1, cube_3]), 1, [], ["cube"], ["netCDF"], "title", "desc"
        )
        assert cubelist_metadata.extent.spatial.bbox.bounds == (-10, -150, 400, 150)

    @staticmethod
    def test_containing_polygon_overlapping_and_within(cube_1, cube_2, cube_3):
        """
        GIVEN a cubelist of three cubes; two partially overlapping cubes completely within a third
        WHEN metadata is extracted
        THEN the bounds of the spatial extent matches the group's total extent
        """
        cubelist_metadata = data.extract_metadata.extract_metadata(
            CubeList([cube_1, cube_2, cube_3]),
            1,
            [],
            ["cube"],
            ["netCDF"],
            "title",
            "desc",
        )
        assert cubelist_metadata.extent.spatial.bbox.bounds == (-10, -150, 400, 150)

    @staticmethod
    def test_containing_polygon_separate(cube_1, cube_4):
        """
        GIVEN a cubelist of two spatially separate cubes
        WHEN metadata is extracted
        THEN the bounds of the spatial extent matches the group's total extent
        """
        cubelist_metadata = data.extract_metadata.extract_metadata(
            CubeList([cube_1, cube_4]), 1, [], ["cube"], ["netCDF"], "title", "desc"
        )
        assert cubelist_metadata.extent.spatial.bbox.bounds == (45, -90, 430, 175)

    @staticmethod
    def test_containing_polygon_overlap_within_separate(cube_1, cube_2, cube_3, cube_4):
        """
        GIVEN a cubelist of four cubes;
        two partially overlapping cubes completely within a third, and a completely separate fourth
        WHEN metadata is extracted
        THEN the bounds of the spatial extent matches the group's total extent
        """
        cubelist_metadata = data.extract_metadata.extract_metadata(
            CubeList([cube_1, cube_2, cube_3, cube_4]),
            1,
            [],
            ["cube"],
            ["netCDF"],
            "title",
            "desc",
        )
        assert cubelist_metadata.extent.spatial.bbox.bounds == (-10, -150, 430, 175)


class errorTest(unittest.TestCase):
    def test_dimensionless_cube_error(self):
        """
        GIVEN a single cube with no spatial dimensions
        WHEN metadata is extracted
        THEN the correct error is raised
        """
        time = DimCoord(
            np.linspace(1, 24, 24),
            standard_name="time",
            units="hours since 1970-01-01 00:00:00",
        )
        cube = Cube(
            np.zeros((24), np.float32),
            standard_name="mass_concentration_of_ozone_in_air",
            units="ug/m3",
            dim_coords_and_dims=[(time, 0)],
        )
        with self.assertRaisesRegex(
            ValueError,
            "The dataset must contain at least one variable with x and y axes.",
        ):
            data.extract_metadata.extract_metadata(cube, 1, [], ["cube"], ["netCDF"])
