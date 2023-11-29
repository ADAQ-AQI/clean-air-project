from typing import Union, List

import iris
import iris.cube
import iris.exceptions
from shapely.geometry import Polygon, MultiPolygon
from cftime import num2pydate
import numpy as np

from edr_server.core.models.extents import Extents, SpatialExtent, TemporalExtent, VerticalExtent
from edr_server.core.models.links import DataQueryLink
from edr_server.core.models.metadata import CollectionMetadata
from edr_server.core.models.parameters import Parameter, ObservedProperty, Unit
from edr_server.core.models.crs import CrsObject
from edr_server.core.models.time import DateTimeInterval


def _cube_to_polygon(cube: iris.Cube) -> tuple(Polygon, Union[CrsObject, None]):
    """
    Given an iris cube, this function returns a shapely geometry polygon of the spatial extent.
    Adapted from iris.analysis.geometry._extract_relevant_cube_slice.

    Arguments:
        cube (iris.Cube): Data cube with x and y axes.

    Returns:
        Polygon: Representation of data's spatial extent.
        CrsObject (optional): Coordinate reference system of data, if it exists.
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
        x_bounds_lower = np.ma.min(x_coord.points)
        x_bounds_upper = np.ma.max(x_coord.points)
        y_bounds_lower = np.ma.min(y_coord.points)
        y_bounds_upper = np.ma.max(y_coord.points)

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


def _find_cube_spatial_extent(cube: iris.Cube) -> Union[SpatialExtent, None]:
    """
    Returns a SpatialExtent object representing the data's x-y bounding box,
    if x and y coordinates exist, else returns None.

    Args:
        cube (iris.Cube): Data cube.

    Returns:
        SpatialExtent, None: X-y spatial extent of the cube's data, if found.
    """

    spatial_extent = None

    if len(cube.coords(axis="x")) == 1 and len(cube.coords(axis="y")) == 1:
        bounding_polygon, bounding_polygon_crs = _cube_to_polygon(cube)
        if bounding_polygon_crs:
            spatial_extent = SpatialExtent(bounding_polygon, bounding_polygon_crs)
        else:
            spatial_extent = SpatialExtent(bounding_polygon)
    
    return spatial_extent
    

def _find_cube_temporal_extent(cube: iris.Cube) -> Union[TemporalExtent, None]:
    """
    Returns a TemporalExtent object representing the data's time extent,
    if a time coordinate exist, else returns None.
    Given sequential time bounds, the function attempts to convert a list of
    time values to a single DateTimeInterval object.

    Args:
        cube (iris.Cube): Data cube.

    Returns:
        TemporalExtent, None: Temporal extent of the cube's data, if found.
    """

    temporal_extent = None

    if len(cube.coords('time')) == 1:
        time_list = num2pydate(times=cube.coord('time').points,
                                units=cube.coord('time').units.name,
                                calendar=cube.coord('time').units.calendar).tolist()
        if min(time_list) < max(time_list):
            time_interval = []
            time_interval.append(DateTimeInterval(start=min(time_list), end=max(time_list)))
            temporal_extent = TemporalExtent(intervals=time_interval)
        else:
            temporal_extent = TemporalExtent(values=time_list)

    return temporal_extent


def _find_cube_vertical_extent(cube: iris.Cube) -> Union[VerticalExtent, None]:
    """
    Returns a VerticalExtent object representing the data's vertical levels,
    if a vertical coordinate exists, else returns None.
    The function will attempt to extract an 'altitude' coordinate first, and 
    then fall back on any z axis coordinate.

    Args:
        cube (iris.Cube): Data cube.

    Returns:
        VerticalExtent, None: Z vertical extent of the cube's data, if found.
    """

    z_coord = None
    vertical_extent = None

    # list of coords that may represent z axis, in ascending order of preference
    z_options = [cube.coords('altitude'), cube.coords(axis='z')]
    for item in z_options:
        if len(item) == 1:
            z_coord = item[0].points
    if z_coord is not None:
        if np.ma.isMaskedArray(z_coord):
            z_coord = z_coord.compressed()
        vertical_extent = VerticalExtent(z_coord)

    return vertical_extent


def _find_total_extent(
        total_polygons: List[Polygon], total_temporal_values: set, total_vertical_values: set
        ) -> Extents:
    """
    Find the total extent that contains a collection of data cubes.

    Args:
        total_polygons (List[Polygon]): Polygons representing the xy spatial extent of multiple data cubes.
        total_temporal_values (set): Values representing the time coordinate points of multiple data cubes.
        total_vertical_values (set): Values representing the z coordinate points of multiple data cubes.

    Raises:
        ValueError: If total_polygons is empty, as at least one data cube with xy coordinates is required.

    Returns:
        Extents: Total extent of multiple data cubes.
    """

    total_spatial_extent = None
    total_temporal_extent = None
    total_vertical_extent = None

    if total_temporal_values:
        if min(total_temporal_values) < max(total_temporal_values):
            total_interval = []
            total_interval.append(
                DateTimeInterval(
                    start=min(total_temporal_values), end=max(total_temporal_values)
                    )
                )
            total_temporal_extent = TemporalExtent(intervals=total_interval)
        else:
            total_temporal_extent = TemporalExtent(values=list(total_temporal_values))

    if total_vertical_values:
        total_vertical_extent = VerticalExtent(total_vertical_values)

    if total_polygons:
        # TODO placeholder for spatial extent until we do this https://github.com/MetOffice/edr_server/issues/31
        containing_polygon = MultiPolygon(total_polygons).convex_hull
        total_spatial_extent = SpatialExtent(containing_polygon)
    else:
        raise ValueError('The dataset must contain at least one variable with x and y axes.')

    return Extents(total_spatial_extent, total_temporal_extent, total_vertical_extent)


def extract_metadata(
        cubes: Union[iris.cube.Cube, iris.cube.CubeList], metadata_id: str, keywords: List[str],
        data_queries: List[DataQueryLink], output_formats: List[str], title: str = None, description: str = None
    ) -> CollectionMetadata:
    """
    Given gridded data and required metadata arguments, return a CollectionMetadata instance representing
    the data.

    Args:
        cubes (Union[iris.cube.Cube, iris.cube.CubeList]): Input data.
        metadata_id (str): Id of the collection.
        keywords (List[str]): Keywords to help describe the collection.
        data_queries (List[DataQueryLink]): Individual query types, i.e. 'cube', 'trajectory'.
        output_formats (List[str]): Formats the results can be presented in, i.e. 'GeoJSON'.
        title (str, optional): Title of the collection. Defaults to None.
        description (str, optional): Description of the collection. Defaults to None.

    Raises:
        TypeError: If 'cubes' arguments is not of type 'Cube' or 'CubeList'.

    Returns:
        CollectionMetadata: EDR compliant object representing the metadata.
    """
    
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
    total_polygons = []
    total_temporal_values = set()
    total_vertical_values = set()
    cube_extent = None

    for cube in cubes:
        cube_extent = Extents(
            _find_cube_spatial_extent(cube),
            _find_cube_temporal_extent(cube),
            _find_cube_vertical_extent(cube)
        )
        unit = Unit(labels=cube.units.name, symbol=cube.units.symbol)
        obs = ObservedProperty(cube.name())
        parameters.append(
            Parameter(id=cube.name(), unit=unit, observed_property=obs, extent=cube_extent)
        )

        total_polygons.append(cube_extent.spatial.bbox)
        total_temporal_values.update(cube_extent.temporal.values)
        total_vertical_values.update(cube_extent.vertical.values)

    if len(cubes) == 1:
        total_extent = cube_extent
    else:
        total_extent = _find_total_extent(
            total_polygons, total_temporal_values, total_vertical_values
        )

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
