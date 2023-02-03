"""
Unit tests for cubes.py
"""

import pytest
import iris
from iris.coords import DimCoord
from iris.cube import Cube
import numpy as np
from shapely.geometry import Polygon

from clean_air.util import cubes as cubes_module


@pytest.fixture(scope="class")
def sample_cube():
    x = DimCoord(np.linspace(-1.5, 3.5, 6),
                 standard_name='projection_x_coordinate',
                 units='meters')
    y = DimCoord(np.linspace(-2.5, 2.5, 6),
                 standard_name='projection_y_coordinate',
                 units='meters')
    time = DimCoord(np.linspace(1, 24, 24),
                    standard_name='time',
                    units="hours since 1970-01-01 00:00:00")
    cube = Cube(np.zeros((6, 6, 24), np.float32),
                standard_name="mass_concentration_of_ozone_in_air",
                units="ug/m3",
                dim_coords_and_dims=[(x, 0),
                                     (y, 1),
                                     (time, 2)])
    return cube


class TestGetXYCoords:
    "Tests for cubes.get_xy_coords method"

    def test_get_xy_coords(self, sample_cube):
        """
        GIVEN a cube of data
        WHEN get_xy_coords is called
        THEN the correct DimCoords are returned
        """
        x_coord, y_coord = cubes_module.get_xy_coords(sample_cube)
        assert x_coord == sample_cube.coord('projection_x_coordinate')
        assert y_coord == sample_cube.coord('projection_y_coordinate')

    def test_get_xy_coords_error(self, sample_cube):
        """
        GIVEN a cube of data with the X coord removed
        WHEN get_xy_coords is called
        THEN the appropriate error is raised
        """
        sample_cube.remove_coord('projection_x_coordinate')
        with pytest.raises(iris.exceptions.CoordinateNotFoundError):
            cubes_module.get_xy_coords(sample_cube)


class TestGetIntersectionWeights:
    "Tests for cubes.get_intersection_weights method"

    def test_get_intersection_weights(self, sample_cube):
        """
        GIVEN a cube of data and quadrilateral polygon that intersect entirely
        WHEN get_intersection_weights is called
        THEN the correct weights array is returned
        """
        shape = Polygon([(1, 3), (3, 1), (1, 0), (0, 2)])
        expected = np.array([[0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0], [0, 0, 0, 0.25, 0.75, 0.5],
                             [0, 0, 0, 0.75, 1, 0.5], [0, 0, 0, 0.25, 0.5, 0], [0, 0, 0, 0, 0, 0]])
        np.testing.assert_array_equal(cubes_module.get_intersection_weights(sample_cube, shape), expected)

    def test_get_intersection_weights_partial(self, sample_cube):
        """
        GIVEN a cube of data and quadrilateral polygon that intersect partially
        WHEN get_intersection_weights is called
        THEN the correct weights array is returned
        """
        shape = Polygon([(-2, 3), (0, 1), (-2, 0), (-3, 2)])
        expected = np.array([[0, 0, 0, 0.75, 1, 0.5], [0, 0, 0, 0.25, 0.5, 0], [0, 0, 0, 0, 0, 0],
                             [0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0]])
        np.testing.assert_array_equal(cubes_module.get_intersection_weights(sample_cube, shape), expected)

    def test_get_intersection_weights_total(self, sample_cube):
        """
        GIVEN a cube of data and quadrilateral polygon that don't intersect
        WHEN get_intersection_weights is called
        THEN a zero array of the correct shape is
        """
        shape = Polygon([(6, 3), (8, 1), (6, 0), (5, 2)])
        expected = np.zeros([6, 6])
        np.testing.assert_array_equal(cubes_module.get_intersection_weights(sample_cube, shape), expected)

    def test_get_intersection_weights_match_cube_dims(self, sample_cube):
        """
        GIVEN a cube of data and quadrilateral polygon that intersect entirely
        WHEN get_intersection_weights is called with match_cube_dims=True
        THEN the resulting array has the same number of dimensions as the original data
        """
        shape = Polygon([(1, 3), (3, 1), (1, 0), (0, 2)])
        result = cubes_module.get_intersection_weights(sample_cube, shape, True)
        assert sample_cube.ndim == result.ndim


class TestExtractBox:
    "Tests for cubes.extract_box method"

    def test_extract_box(self, sample_cube):
        """
        GIVEN a cube of data and rectangular polygon that intersect entirely
        WHEN extract_box is called
        THEN the result is an iris cube with the correct shape
        """
        coords = (-0.25, -0.75, 2.6, 1.4)
        box = cubes_module.extract_box(sample_cube, coords)
        assert isinstance(box, iris.cube.Cube)
        assert box.shape == (3, 2, 24)

    def test_extract_box_partial(self, sample_cube):
        """
        GIVEN a cube of data and rectangular polygon that intersect partially
        WHEN extract_box is called
        THEN the result is an iris cube with the correct shape
        """
        coords = (-6, -0.75, 2.6, 1.4)
        box = cubes_module.extract_box(sample_cube, coords)
        assert isinstance(box, iris.cube.Cube)
        assert box.shape == (5, 2, 24)

    def test_extract_box_partial(self, sample_cube):
        """
        GIVEN a cube of data and rectangular polygon that don't intersect
        WHEN extract_box is called
        THEN None is returned
        """
        coords = (-6, -3, -3, 1.4)
        box = cubes_module.extract_box(sample_cube, coords)
        assert isinstance(box, type(None))
