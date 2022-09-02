import iris
from edr_server.core.models.metadata import CollectionMetadata
from edr_server.core.models.parameters import Parameter
from edr_server.core.models.extents import Extents, SpatialExtent, TemporalExtent, VerticalExtent
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

    if x_coord.coord_system == y_coord.coord_system:
        return Polygon(coords), x_coord.coord_system

    else:
        return Polygon(coords)

def extract_metadata(cubes, id, keywords, supported_data_queries, output_formats, title=None, description=None):

    if isinstance(cubes, iris.cube.Cube):
        name = cubes.standard_name
        summary = cubes.summary()
        cubes = iris.cube.CubeList([cubes])

    elif isinstance(cubes, iris.cube.CubeList):
        name = title
        summary = description

    parameters = []
    total_temporal_extent_list = [] # list of numpy ndarrays
    total_vertical_extent_list = [] 

    for cube in cubes:
        spatial_extent = SpatialExtent(_cube_to_polygon(cube))
        temporal_extent = TemporalExtent(cube.coord('time').points)
        if len(cube.coords(axis='z')) == 1:
            vertical_extent = VerticalExtent(cube.coord(axis='z').points)
            total_vertical_extent_list.append(cube.coord(axis='z').points)
        else:
            vertical_extent = None
        total_temporal_extent_list.append(cube.coord('time').points)
        cube_extent = Extents(spatial_extent, temporal_extent, vertical_extent)

        parameters.append(Parameter(id=cube.name, unit=cube.units, observed_property=cube.name, extent=cube_extent))

    if len(cubes) == 1:
        total_extent = cube_extent
    else:
        total_temporal_extent = TemporalExtent(total_temporal_extent_list)
        total_vertical_extent = VerticalExtent(total_vertical_extent_list)

        # Placeholder for spatial extent until we do this https://github.com/MetOffice/edr_server/issues/31. 
        # Also remember MultiPolygon class!
        total_spatial_extent = Polygon([(0, 0), (1, 1), (1, 0)])
        total_extent = Extents(total_spatial_extent, total_temporal_extent, total_vertical_extent)

    kwargs = {
        "id": id,
        "title": name,
        "description": summary,
        "keywords": keywords,
        "extent": total_extent,
        "supported_data_queries": supported_data_queries,
        "output_formats": output_formats,
        "parameters": parameters
    }
    return CollectionMetadata(**kwargs)