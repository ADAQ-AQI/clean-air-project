from typing import Union, List

import iris
import iris.cube
import iris.exceptions
from shapely.geometry import Polygon, MultiPolygon
from cftime import num2pydate

from edr_server.core.models.extents import Extents, SpatialExtent, TemporalExtent, VerticalExtent
from edr_server.core.models.links import DataQueryLink
from edr_server.core.models.metadata import CollectionMetadata
from edr_server.core.models.parameters import Parameter
from edr_server.core.models.crs import CrsObject


def _cube_to_polygon(cube):
    """
    Given an iris cube, this function returns a shapely geometry polygon of the spatial extent.
    Adapted from iris.analysis.geometry._extract_relevant_cube_slice.
    """

    x_coord = cube.coords(axis="x")[0]
    y_coord = cube.coords(axis="y")[0]

    if x_coord.has_bounds() and y_coord.has_bounds():
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
              (x_bounds_upper, y_bounds_upper),
              (x_bounds_lower, y_bounds_upper)]

    if x_coord.coord_system and x_coord.coord_system == y_coord.coord_system:
        crs = CrsObject(x_coord.coord_system.as_cartopy_crs())
        return Polygon(coords), crs
    else:
        return Polygon(coords), None

def extract_metadata(
        cubes: Union[iris.cube.Cube, iris.cube.CubeList], metadata_id: str, keywords: List[str],
        data_queries: List[DataQueryLink], output_formats: List[str], title: str = None, description: str = None
):
    if isinstance(cubes, iris.cube.Cube):
        name = cubes.standard_name
        summary = cubes.summary()
        cubes = iris.cube.CubeList([cubes])

    elif isinstance(cubes, iris.cube.CubeList):
        name = title
        summary = description
    else:
        raise TypeError(
            f"cubes argument was a {type(cubes)!r}, but was expected to be an iris.cube.Cube or iris.cube.CubeList"
        )

    parameters = []
    total_temporal_extent_list = set()
    total_vertical_extent_list = []
    total_polygon_list = []
    cube_extent = None

    for cube in cubes:
        spatial_extent = None
        temporal_extent = None
        vertical_extent = None
        if len(cube.coords(axis="x")) == 1 and len(cube.coords(axis="y")) == 1:
            bounding_polygon, bounding_polygon_crs = _cube_to_polygon(cube)
            total_polygon_list.append(bounding_polygon)
            if bounding_polygon_crs:
                spatial_extent = SpatialExtent(bounding_polygon, bounding_polygon_crs)
            else:
                spatial_extent = SpatialExtent(bounding_polygon)
        if len(cube.coords('time')) == 1:

            time_list = num2pydate(times=cube.coord('time').points, units=cube.coord('time').units.cftime_unit, calendar=cube.coord('time').units.calendar).tolist()
            temporal_extent = TemporalExtent(time_list)
            total_temporal_extent_list.update(time_list)
        if len(cube.coords(axis='z')) == 1:
            vertical_extent = VerticalExtent(cube.coord(axis='z').points)
            total_vertical_extent_list.append(cube.coord(axis='z').points)
        cube_extent = Extents(spatial_extent, temporal_extent, vertical_extent)

        parameters.append(
            Parameter(id=cube.name, unit=cube.units, observed_property=cube.name, extent=cube_extent)
        )
    if len(total_polygon_list) == 0:
        raise ValueError('The dataset must contain at least one variable with x and y axes.')
    if len(cubes) == 1:
        total_extent = cube_extent
    else:
        total_temporal_extent = TemporalExtent(list(total_temporal_extent_list))
        total_vertical_extent = VerticalExtent(total_vertical_extent_list)

        # Placeholder for spatial extent until we do this https://github.com/MetOffice/edr_server/issues/31.
        total_polygon_list = MultiPolygon(total_polygon_list)
        containing_polygon = total_polygon_list.convex_hull
        total_spatial_extent = SpatialExtent(containing_polygon)
        total_extent = Extents(total_spatial_extent, total_temporal_extent, total_vertical_extent)

    kwargs = {
        "id": metadata_id,
        "title": name,
        "description": summary,
        "keywords": keywords,
        "extent": total_extent,
        "data_queries": data_queries,
        "output_formats": output_formats,
        "parameters": parameters
    }
    return CollectionMetadata(**kwargs)
