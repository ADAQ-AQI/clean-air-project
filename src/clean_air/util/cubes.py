"""
Helper functions for Iris Cubes
"""

import itertools

import numpy as np
import iris
import shapely


def get_xy_coords(cube):
    """
    Finds a Cube's X and Y dimension coords.

    Args:
        cube: Cube to get coords of

    Returns:
        xcoord, ycoord: DimCoords in the X and Y directions
    """
    xcoord = cube.coord(axis="x", dim_coords=True)
    ycoord = cube.coord(axis="y", dim_coords=True)
    return xcoord, ycoord


def extract_box(cube, box):
    """
    Extracts a rectangular area from a cube.

    Args:
        cube: Cube to subset
        box (x0, y0, x1, y1): Box defined in terms of its lower-left (x0, y0)
            and upper-right (x1, y1) corners
    """

    def extent_checker(low, high):
        """
        Create a callback function that checks whether a cell is contained
        in a given range.

        For bounded cells, the cell is included if its bounded region
        has non-empty intersection with the requested interval. Otherwise
        falls back to simply checking the point.
        """
        def cb(cell):
            if cell.bound:
                a, b = cell.bound
                # Sufficient to check a <= high and low <= b.
                # Note that this *does* cover the potential edge case where
                # a requested range is entirely contained by a cell, as
                # this is just a < low < high < b
                return a <= high and low <= b
            return low <= cell.point <= high

        return cb

    xcoord, ycoord = get_xy_coords(cube)
    xmin, ymin, xmax, ymax = box

    constraint = iris.Constraint(coord_values={
        ycoord.name(): extent_checker(ymin, ymax)
    })
    if xcoord.units.modulus:
        # ie there is modular arithmetic to worry about.
        # This can be done by extracting with constraints, but it is
        # more convenient to use cube.intersection, which additionally
        # wraps points into the requested range.
        cube = cube.extract(constraint)
        cube = cube.intersection(
            iris.coords.CoordExtent(xcoord, xmin, xmax)
        )
    else:
        constraint &= iris.Constraint(coord_values={
            xcoord.name(): extent_checker(xmin, xmax)
        })
        cube = cube.extract(constraint)

    return cube


<<<<<<< HEAD
=======
def extract_series(cube, dataframe, column_mapping=None):
    """
    Create a new dataframe column by interpolating a Cube.

    Arguments:
        cube (Cube): cube to extract data from
        dataframe (DataFrame): dataframe to match. Must have a column
            corresponding to each data dimension in the cube.
        column_mapping (dict?): mapping from dataframe column names to cube
            coord names, in case there are any differences or ambiguities.

    Returns:
        (Series): interpolated data, as a pandas series with the same length
            and index as the dataframe.
    """
    if column_mapping is None:
        # Try to determine the mapping, with a simple case-insensitive
        # comparison of column/coord names
        column_mapping = {}
        for col_name in dataframe:
            for coord in cube.dim_coords:
                coord_name = coord.name()
                if col_name.lower() == coord_name.lower():
                    column_mapping[col_name] = coord_name

    if len(column_mapping) < cube.ndim:
        missing = [
            coord.name()
            for coord in cube.dim_coords
            if coord.name() not in column_mapping
        ]
        raise ValueError(f"Some columns not matched to cube coords: {missing}")

    sample_points = []
    for col_name, coord_name in column_mapping.items():
        try:
            sample_points.append((coord_name, np.array(dataframe[col_name])))
        except:
            sample_points.append((coord_name, dataframe.index))

    series_cube = iris_traj.interpolate(cube, sample_points, method="linear")
    series = pd.Series(series_cube.data, index=dataframe.index, name=cube.name())

    return series

def _reduce_coord(coord, geom, direction):
    """
    Helper function to reduce a coordinate to the section
    only within a shape's bounding box.

    Args:
        coord (iris dimCoord): 1-D dimensional coordinate being reduced
        geom (shapely polygon): intersecting shape
        direction (str): direction of coord, 'x' or 'y'

    Returns:
        reduced (iris dimCoord): reduced coordinate
        index_ref (int): starting point of the reduced coord, in terms of the original coord's index
    """
    index_ref = None
    reduced = []

    # As geom.bounds returns (minx, miny, maxx, maxy) tuple,
    # need to specify x or y
    if direction == 'y':
        n = 1
    elif direction == 'x':
        n = 0

    for i in range(len(coord.points)):
        if (geom.bounds[0 + n] <= coord[i].bounds[0][-1] and coord[i].bounds[0][0] <= geom.bounds[2 + n]):
            if index_ref is None:
                index_ref = i
            reduced.append(coord[i])

    return reduced, index_ref

>>>>>>> fixed indexing error
def get_intersection_weights(cube, geom, match_cube_dims=False):
    """
    Calculate what proportion of each grid cell intersects a given shape.

    Arguments:
        cube (Cube): cube defining a grid
        geom (BaseGeometry): shape to intersect
        match_cube_dims (bool?):
            Whether to match cube shape or not:

            - If False (the default), the returned array will have shape (x, y)
            - If True, its shape will be compatible with the cube

    Returns:
        (np.array): intersection weights
    """
    # Determine output shape
    xcoord, ycoord = get_xy_coords(cube)
    ndim = 2
    xdim = 0
    ydim = 1
    if match_cube_dims:
        # Make broadcastable to cube shape
        ndim = cube.ndim
        xdim = cube.coord_dims(xcoord)[0]
        ydim = cube.coord_dims(ycoord)[0]

    # The cells must have bounds for shape intersections to have much
    # meaning, especially for shapes that are small compared to the
    # grid size
    if not xcoord.has_bounds():
        xcoord.guess_bounds()
    if not ycoord.has_bounds():
        ycoord.guess_bounds()

    shape = [1] * ndim
    shape[xdim] = len(xcoord.points)
    shape[ydim] = len(ycoord.points)

    # reduce cube coords to only those near shape
    starts = [0] * ndim
    reduced_xcoord, starts[xdim] = _reduce_coord(xcoord, geom, 'x')
    reduced_ycoord, starts[ydim] = _reduce_coord(ycoord, geom, 'y')

    reduced_shape = shape.copy()
    reduced_shape[xdim] = len(reduced_xcoord)
    reduced_shape[ydim] = len(reduced_ycoord)
    # Calculate the weights
    # TODO:
    # - investigate parallelisation. Would reduce the above need for using
    #   bounding boxes, and is likely the only way of achieving any speed
    #   up for large complex shapes at all.
    weights = np.zeros(shape)
    indices = [range(starts[i], starts[i] + reduced_shape[i]) for i in range(len(starts))]
    for i in itertools.product(*indices):
        x0, x1 = xcoord.bounds[i[xdim]]  # aqum x range is -238000 to 856000
        y0, y1 = ycoord.bounds[i[ydim]]  # aqum y range is -184000 to 1222000
        # POLYGON ((-237000 -185000, -237000 -183000, -239000 -183000, -239000 -185000, -237000 -185000))
        cell = shapely.geometry.box(x0, y0, x1, y1)
        # if not cell.intersection(geom).is_empty:
        # print(cell.intersection(geom).area / cell.area) # POLYGON EMPTY
        weight = cell.intersection(geom).area / cell.area  # 0.0 / 4000000.0
        weights[i] = weight

    return weights
