"""
Objects representing data subsets
"""
import os.path

import numpy as np
import iris
import shapely.geometry
import shapely.ops

from .. import util


class DataSubset:
    """
    Represents a subset of a dataset, for example according to variable
    or time. Areas can be extracted with dedicated methods.
    """

    def __init__(
        self,
        metadata,
        category=None,
        parameter=None,
        start_time=None,
        end_time=None,
    ):
        self.metadata = metadata
        self.category = category
        self.parameter = parameter
        self.start_time = start_time
        self.end_time = end_time

        self._cube = None

    def _load_cube(self, force=False):
        if not force and self._cube is not None:
            return self._cube

        constraints = None
        if self.parameter:
            constraints = constraints & iris.Constraint(self.parameter)
        if self.start_time:
            constraints = constraints & iris.Constraint(
                time=lambda cell: self.start_time <= cell.point
            )
        if self.end_time:
            constraints = constraints & iris.Constraint(
                time=lambda cell: cell.point < self.end_time
            )

        try:
            cube = iris.load_cube(self.metadata, constraints)
        except AttributeError:
            cube = iris.load_cube(self.metadata['files'], constraints)

        self._cube = cube
        return self._cube

    def extract_point(self, point, crs=None):
        """
        Extract a rectangular area of gridded data.

        Arguments:
            point: point in the form (x, y)
            crs: coordinate reference system for the point. Same as the
                dataset by default.
        """
        point = shapely.geometry.Point(point)

        cube = self._load_cube()

        # Ensure coordinate systems match
        if crs is not None:
            data_crs = cube.coord_system().as_cartopy_crs()
            point = util.crs.transform_shape(point, crs, data_crs)

        # Interpolate data to the requested point
        try:
            xcoord, ycoord = util.cubes.get_xy_coords(cube)
            x, y = point.xy
            cube = cube.interpolate(
                [(xcoord.name(), x), (ycoord.name(), y)],
                iris.analysis.Linear()
            )
        except iris.exceptions.CoordinateNotFoundError:
            # This implies that the cube is missing an X or Y coord, which
            # we will assume means that it already represents a single point,
            # stored as attributes instead of coords
            pass

        return cube

    def extract_box(self, box, crs=None):
        """
        Extract a rectangular area of gridded data.

        Arguments:
            box: extent in the form (xmin, ymin, xmax, ymax)
            crs: coordinate reference system of the box. Same as the
                dataset by default.
        """
        box = shapely.geometry.box(*box)
        cube = self._load_cube()

        # Ensure coordinate systems match
        if crs is not None:
            data_crs = cube.coord_system().as_cartopy_crs()
            box = util.crs.transform_shape(box, crs, data_crs)

        cube = util.cubes.extract_box(cube, box.bounds)

        return cube

    def extract_track(self, track, crs=None):
        """
        Extract a track

        Arguments:
            track: timeseries of the track, as a dataframe
        """
        cube = self._load_cube()

        return util.cubes.extract_series(cube, track)

    def extract_shape(self, shape, crs=None):
        """
        Extract an arbitrary area

        Arguments:
            shape: shape to extract, as a shapely polygon
            crs: coordinate reference system used by the polygon. Same as
                the dataset by default.
        """
        cube = self._load_cube()

        # Ensure coordinate systems match
        if crs is not None:
            data_crs = cube.coord_system().as_cartopy_crs()
            shape = util.crs.transform_shape(shape, crs, data_crs)

        # The cells must have bounds for shape intersections to have much
        # meaning, especially for shapes that are small compared to the
        # grid size
        xcoord, ycoord = util.cubes.get_xy_coords(cube)
        if not xcoord.has_bounds():
            xcoord.guess_bounds()
        if not ycoord.has_bounds():
            ycoord.guess_bounds()

        # Mask points outside the actual shape
        # Note we need to do the broadcasting manually: numpy is strangely
        # reluctant to do it, no matter which of the many ways of creating
        # a masked array we try
        weights = util.cubes.get_intersection_weights(cube, shape, True)
        mask = np.broadcast_to(weights == 0, cube.shape)
        data = np.ma.array(cube.data, mask=mask)
        cube = cube.copy(data=data)

        return cube

    def extract_shapes(self, shapes, crs=None):
        """
        Arguments:
            shapes: iterable of shapely geometries. For example the
                ``geometry`` column of a ``GeoDataFrame``.
            crs: coordinate reference system of the shapes. Same as the
                dataset by default.
        """
        crs = crs or getattr(shapes, "crs", None)
        cubes = iris.cube.CubeList()
        for geom in shapes:
            cubes.append(self.extract_shape(geom, crs=crs))

        return cubes
