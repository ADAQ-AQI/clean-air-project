"""
Top-level module for rendering datasets.
"""

import geopandas
import iris
import xarray
from shapely.geometry import Polygon, MultiPolygon

from clean_air import util as util
from clean_air.data import DataSubset
from clean_air.visualise import render_map, render_plot


class Renderer:
    """This class is for preparing datasets for the plotting process.

    Args:
        * dataset: this can be either an iris cube or a dataset path.
        """
    def __init__(self, dataset):
        if isinstance(dataset, str):
            # Use iris to read in dataset as lazy array here:
            self.path = dataset
            self.dataset = iris.load_cube(dataset)
        elif isinstance(dataset, iris.cube.Cube):
            # Iris cube is already loaded so no advantage from loading lazily
            # here:
            self.dataset = dataset
        self.dims = self.dataset.dim_coords

        # Guess all possible dim coords here using iris object before loading
        # dataframe as xarray object (but scalar coords become None because we
        # can't make plots out of them):
        self.x_coord = self.y_coord = self.z_coord = self.t_coord = None
        for coord in self.dataset.coords():
            if len(coord.points) > 1:
                axis = iris.util.guess_coord_axis(coord)
                if axis == 'X' and self.x_coord is None:
                    self.x_coord = coord.name()
                elif axis == 'Y' and self.y_coord is None:
                    self.y_coord = coord.name()
                elif axis == 'Z' and self.z_coord is None:
                    self.z_coord = coord.name()
                elif axis == 'T' and self.t_coord is None:
                    self.t_coord = coord.name()

    def render(self):
        """
        Analyses the dimensionality of the dataset and then sends to
        appropriate renderer in render_plot.py or render_map.py.
        """
        coords = (self.x_coord, self.y_coord, self.z_coord, self.t_coord)

        # If we have both an x-coord and y-coord then we can draw a map:
        if self.x_coord is not None and self.y_coord is not None:
            self.img_type = 'map'
            # self.dataframe = geopandas.read_file(self.path)
            fig = render_map.Map(self.dataset).render(*coords)
        # If we have just a time coord then we can make a timeseries:
        elif self.x_coord is None and self.y_coord is None:
            self.img_type = 'timeseries'
            # self.dataframe = xarray.open_dataset(self.path)
            fig = render_plot.Plot(self.dataset).render_timeseries()
        # If we don't have any coords then something's gone wrong and we can't
        # plot anything:
        elif all(coord is None for coord in coords):
            raise ValueError('All dimension coordinates are either missing or '
                             'scalar, please choose a dataset with more '
                             'coordinate points.')

        return fig


class TimeSeries:
    """This class should handle inputs and outputs, hopefully.

        Args:
        * lat: latitude coordinate for point of interest (if required)
        * lon: longitude coordinate for point of interest (if required)
        * data: full path of data file selected by user or DataSubset object
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

    def track(self, crs=None):
        """Generate time series containing data along a track."""
        track_cube = self.data.extract_track(self.data, crs=crs)

        return track_cube

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
        elif isinstance(shape, Polygon):
            shape_cube = self.data.extract_shape(shape, crs=crs)
        elif isinstance(shape, MultiPolygon):
            shape_cube = self.data.extract_shapes(shape, crs=crs)
        else:
            raise TypeError

        # Now we must average data points over extracted cube to become a
        # timeseries.
        if isinstance(shape_cube, iris.cube.Cube):
            xcoord, ycoord = util.cubes.get_xy_coords(shape_cube)
            partial_cube = shape_cube.collapsed(xcoord, iris.analysis.MEAN)
            collapsed_cube = partial_cube.collapsed(ycoord, iris.analysis.MEAN)
            return collapsed_cube

        elif isinstance(shape_cube, iris.cube.CubeList):
            shapes_data = iris.cube.CubeList()
            for i, cube in enumerate(shape_cube):
                xcoord, ycoord = util.cubes.get_xy_coords(cube)
                partial = cube.collapsed(xcoord, iris.analysis.MEAN)
                collapsed = partial.collapsed(ycoord, iris.analysis.MEAN)
                shapes_data.append(collapsed)
                return shapes_data




