"""
This module contains functions to convert between dataframe types.
"""

from .cubes import get_xy_coords
from iris.pandas import _assert_shared, _as_pandas_coord
import numpy as np
import pandas as pd
from geopandas import GeoDataFrame
from shapely.geometry import Point
import warnings


def as_pandas_data(data, copy=True):
    """
    Sort iris cube style data into pandas style data.

    Args:
        data: Data array to be converted.
        copy: Boolean value representing whether the data should be copied.
              or not (this will return an error if the array is masked).

    Returns:
        Data array in pandas format.
    """
    if isinstance(data, np.ma.MaskedArray):
        if not copy:
            raise ValueError("Masked arrays must always be copied.")
        data = data.astype('f').filled(np.nan)
    elif copy:
        data = data.copy()

    return data


def as_series(cube, index=None, copy=True):
    """
    Static function to convert an iris cube into a pandas series.

    Args:
        cube: iris cube (1-dimensional) for conversion.
        index: 1-dimensional array representing the order of data for input
               (if not supplied, the input order will be the same as the cube
               data).
        copy: boolean value representing whether to keep a copy of the
              data upon conversion.

    Returns:
        pandas Series containing information converted from iris cube.
    """
    # NOTE: This is as yet untested and unfinished; pulled from iris but in
    # need of simplification and modification.
    data = as_pandas_data(cube.data)
    if index is None:
        if cube.dim_coords:
            index = _as_pandas_coord(cube.dim_coords[0])
    else:
        index = _as_pandas_coord(index)

    series = pd.Series(data, index)
    if not copy:
        _assert_shared(data, series)

    return series


def _make_geo(cube, x_coord, y_coord):
    """
    Helper function for conversion to geodataframe(s).

    Args:
        cube: cube for conversion
        x_coord: iris dim coord representing x direction
        y_coord: iris dim coord representing y direction

    Returns:
        list of geodataframes
    """
    dataframes = []
    for sub_cube in cube.slices([x_coord, y_coord], ordered=True):
        # Get the coordinates, data and geometry in the right
        # order here:
        x_coords_pd = []
        y_coords_pd = []
        data_pd = []
        geom = []
        for i, x in enumerate(x_coord.points):
            for j, y in enumerate(y_coord.points):
                x_coords_pd.append(x)
                y_coords_pd.append(y)
                data_pd.append(sub_cube.data[i, j])
                geom.append(Point(x, y))

        # Now construct pandas geodataframe object for this sub_cube:
        geo_df = GeoDataFrame({'x_coord': x_coords_pd,
                               'y_coord': y_coords_pd,
                               'data': data_pd,
                               'geometry': geom})

        dataframes.append(geo_df)

    return dataframes


def convert_to_geodf(cube, restitch=False):
    """
    Callable for converting iris-style cubes into geopandas dataframes.

    Note: This conversion is only possible for 2-dimensional cubes, so input
    cubes with two or more dimensions will be sliced up before conversion
    and then restitched if necessary.  Cubes with less than two dimensions
    will be converted to a series instead.

    Args:
        cube: input cube.
        restitch: Boolean representing whether to concatenate the
                  dataframes after conversion to pandas arrays.
                  If restitch=True then the dataframes will be returned alone,
                  but if restitch=False then the dataframes will be returned
                  in a list.

    Returns:
        pandas-style dataframe(s) or series, depending on input (see note).
    """
    geodataframes = series = geodataframe = None

    # For cubes with two or more dim coords:
    if len(cube.dim_coords) >= 2:
        # If there are two or more coords, we need to look for standard
        # xy dimension coords and use them to slice the cube up:
        x_coord, y_coord = get_xy_coords(cube)
        geodataframes = _make_geo(cube, x_coord, y_coord)

        # Now we have a set of 2D geopandas dataframes which must be
        # stitched back together if required
        if restitch is True:
            geodataframe = pd.concat(geodataframes)
            return geodataframe
        else:
            return geodataframes

    # For cubes with less than 2 dim coords (warn then convert to series):
    elif len(cube.dim_coords) < 2:
        warnings.warn("Converting to non-geographical series instead of "
                      "geodataframe as there is only one coordinate.")
        series = as_series(cube)
        return series
