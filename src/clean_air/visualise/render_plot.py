"""
Module to create fabulous visualisations of various non-map plots.
"""

import hvplot.xarray  # noqa
import xarray
from datetime import datetime

import numpy as np
import pandas as pd
import iris.cube
import iris.plot
import matplotlib as mpl
import shapely.geometry as sgeom


import clean_air.util as util
from clean_air.data import DataSubset
from clean_air.visualise import dataset_renderer


# TODO: Figure out where this class lives and put it there.
class TimeSeries:
    """This class should handle inputs and outputs, hopefully.

        Args:
        * lat: latitude coordinate for point of interest
        * lon: longitude coordinate for point of interest
        * data: full path of data file selected by user
    """
    def __init__(self, data, lat=None, lon=None):
        if isinstance(data, str):
            self.dpath = data
            self.data = DataSubset(data)
        elif isinstance(data, DataSubset):
            self.dpath = data.metadata['files']
            self.data = data
        else:
            raise TypeError

        self.lat = lat
        self.lon = lon

    def linear_interpolate(self):
        """Generate dataframe containing linearly interpolated data.  This will
        provide a time series of data values at a single point in space,
        defaulting to ground level for altitude.  We may expand this feature
        to create a dataset for each level of altitude at some point in the
        future.

        Returns:
            * point_cube: an iris cube containing linearly
            interpolated data.
            """
        point_cube = self.data.extract_point((self.lat, self.lon))

        return point_cube

    def spatial_average(self, shape, coords=None, crs=None):
        """Generate time series containing spatially averaged data.

        Args:
            * shape: (this will be selected by user from a drop-down menu).
            * coords: required for positioning of shape for averaging in the
            form (xmin, ymin, xmax, ymax) or as a shapely polygon or
            multipolygon. Not required if shape = 'Track' (coords implied
            within data in this case).
            * crs: Coordinate reference system. If None, this will default to
            the CRS of the dataset.

        Returns:
            * An iris cube containing single-point timeseries data spacially
            averaged over shape passed in by user.
            """
        # This bit determines the shape required by the user and sends all the
        # bits through some checking operations and then through iris for
        # extraction of sub-cube.  IT DOES NOT AVERAGE THE DATA.
        if shape == 'box':
            shape_cube = self.data.extract_box(coords, crs=crs)
        elif shape == 'track':
            shape_cube = self.data.extract_track(crs=crs)
        elif shape == 'shape':
            shape_cube = self.data.extract_shape(coords, crs=crs)
        elif shape == 'shapes':
            shape_cube = self.data.extract_shapes(coords, crs=crs)

        # Now we must average data points over extracted cube to become a
        # timeseries.
        try:
            xcoord, ycoord = util.cubes.get_xy_coords(shape_cube)
        except iris.exceptions.CoordinateNotFoundError:
            # This implies that the cube is missing an X or Y coord, which
            # will be a problem for collapsing the data.
            print("Please supply a cube containing both an x and a y coord.")

        partial_cube = shape_cube.collapsed(xcoord, iris.analysis.MEAN)
        collapsed_cube = partial_cube.collapsed(ycoord, iris.analysis.MEAN)

        return collapsed_cube

    def obs_data(self, site):
        """Generate time series plot containing observational data from a
        single-site observational dataset."""
        # TODO: Use ABD_2015.csv or similar to test this function.


class Plot:
    def __init__(self, dataframe):
        self.dataframe = dataframe

    def render_timeseries(self):
        # First check that cube is 1-dimensional, otherwise reduce dimensions:
        if self.dataframe.ndim > 1:
            for coord in self.dataframe.dim_coords:
                if coord.points.size == 1:
                    self.dataframe = self.dataframe.collapsed(
                            coord, iris.analysis.MEAN)
                else:
                    pass

        # Now check again to make sure cube is 1D, otherwise raise error:
        if self.dataframe.ndim != 1:
            raise ValueError('There are too many coordinates to plot this '
                             'cube as a timeseries.  Please pass in a cube '
                             'containing only one dimension (i.e. time).')

        # This is where we make an actual plot...
        fig = mpl.figure.Figure()
        timeseries_plot = fig.add_subplots(self.dataframe)
        # TODO: Get iris to return an object which I can do things with
        # TODO: Make it pretty (maybe use mpl.pyplot instead of iris.plot)

        return timeseries_plot

