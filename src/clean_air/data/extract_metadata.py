import iris
from edr_server.core.models.metadata import CollectionMetadata
from edr_server.core.models.extents import Extents, SpatialExtent, TemporalExtent
from shapely.geometry import Polygon

def _cube_to_polygon(cube):
    """
    Given a iris cube, this function returns a shapely geometry polygon of the spatial extent. 
    Adapted from iris.analysis.geometry._extract_relevant_cube_slice.
    """

    # Validate the input parameters
    if not cube.coords(axis="x") or not cube.coords(axis="y"):
        raise ValueError("The cube must contain x and y axes.")

    x_coords = cube.coords(axis="x")
    y_coords = cube.coords(axis="y")
    if len(x_coords) != 1 or len(y_coords) != 1:
        raise ValueError(
            "The cube must contain one, and only one, coordinate "
            "for each of the x and y axes."
        )

    x_coord = x_coords[0]
    y_coord = y_coords[0]
    if (x_coord.has_bounds() and y_coord.has_bounds()):
        # bounds of cube dimensions
        x_bounds = x_coord.bounds
        y_bounds = y_coord.bounds

        # identify ascending/descending coordinate dimensions
        x_ascending = x_coord.points[1] - x_coord.points[0] > 0.0
        y_ascending = y_coord.points[1] - y_coord.points[0] > 0.0

        # identify upper/lower bounds of coordinate dimensions
        x_bounds_lower = x_bounds[:, 0] if x_ascending else x_bounds[:, 1]
        y_bounds_lower = y_bounds[:, 0] if y_ascending else y_bounds[:, 1]
        x_bounds_upper = x_bounds[:, 1] if x_ascending else x_bounds[:, 0]
        y_bounds_upper = y_bounds[:, 1] if y_ascending else y_bounds[:, 0]
    else:
        x_bounds_lower = x_coord.points[0]
        x_bounds_upper = x_coord.points[-1]
        y_bounds_lower = y_coord.points[0]
        y_bounds_upper = y_coord.points[-1]

    if x_coord.ndim != 1:
        raise iris.exceptions.CoordinateMultiDimError(x_coord)
    if y_coord.ndim != 1:
        raise iris.exceptions.CoordinateMultiDimError(y_coord)

    coords = [(x_bounds_lower, y_bounds_lower), 
                (x_bounds_upper, y_bounds_lower), 
                (x_bounds_lower, y_bounds_upper), 
                (x_bounds_upper, y_bounds_upper)]

    return Polygon(coords)

def extract_cube_metadata(cubes):
    name = cubes.standard_name

    #convert iris geometry to polygon
    spatial_extent = SpatialExtent(_cube_to_polygon(cubes)) #include crs? each Coord has coord_system
    temporal_extent = TemporalExtent(cubes.coord('time').points)
    total_extents = Extents(spatial_extent, temporal_extent)
    kwargs = {
        "id": 1,
        "title": name,
        "extent": total_extents
    }
    return CollectionMetadata(**kwargs)