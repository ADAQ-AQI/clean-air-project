"""
Top-level module for rendering datasets.
"""

import iris
import hvplot.pandas  # noqa
import iris.pandas
from iris.cube import Cube, CubeList
from shapely.geometry import Polygon, MultiPolygon

from clean_air import util
from clean_air.data import DataSubset
from clean_air.visualise import render_map


class Plot:
    def __init__(self, dataset):
        # Note: This should always be a CubeList, even if it only contains
        # one Cube.  This is just for simplification of the code.
        self.dataset = dataset

    def render_timeseries(self):
        for i, cube in enumerate(self.dataset):
            # First check that cube is 1-dimensional, otherwise reduce
            # dimensions:
            if cube.ndim > 1:
                for coord in cube.dim_coords:
                    if coord.points.size == 1:
                        cube = cube.collapsed(coord, iris.analysis.MEAN)

            # Now create a pandas dataframe to populate:
            df_main = iris.pandas.as_data_frame(cube)

            # Now check again to make sure cube is 1D, otherwise raise error:
            if cube.ndim != 1:
                raise ValueError('There are too many coordinates to plot this '
                                 'cube as a timeseries.  Please pass in a cube '
                                 'containing only one dimension (i.e. time).')
            # For a single cube, convert to pandas dataframe and give suitable axis names.
            if i == 0:
                df_main.columns = [f'{cube.standard_name} \n in {cube.units}']
                df_main.index.names = ['Time']

            # For subsequent cubes provided by multipolygon, add them as dataframe columns.
            elif i > 0:
                df_main.columns = ['Polygon 1']  # TODO: rename to match pattern?
                df = iris.pandas.as_data_frame(cube)
                col_name = f'Polygon {i+1}'
                df.columns = [col_name]
                extracted_col = df[col_name]
                df_main = df_main.join(extracted_col)

        return df_main


class TimeSeries:
    """This class should handle inputs and outputs, hopefully.

        Args:
        * x: x coordinate for point of interest (if required)
        * y: y coordinate for point of interest (if required)
        * data: full path of data file selected by user or DataSubset object
    """
    def __init__(self, data, x=None, y=None):
        if isinstance(data, (str, iris.cube.Cube)):
            self.dpath = data
            self.data = DataSubset(data)
        elif isinstance(data, DataSubset):
            self.dpath = data.metadata
            self.data = data
        else:
            raise TypeError

        self.x = x
        self.y = y

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
        point_cube = self.data.extract_point((self.x, self.y))

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
            * An iris cube containing single-point timeseries data spatially
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
            for cube in shape_cube:
                xcoord, ycoord = util.cubes.get_xy_coords(cube)
                partial = cube.collapsed(xcoord, iris.analysis.MEAN)
                collapsed = partial.collapsed(ycoord, iris.analysis.MEAN)
                shapes_data.append(collapsed)
            return shapes_data

    def diurnal_average(self, aggregator=iris.analysis.MEAN) -> iris.cube.Cube:
        """Generate a mean 24hr profile for data spanning multiple days."""

        return self.data.average_time(aggregator)


class Renderer:
    """This class is for preparing datasets for the plotting process.

    Args:
        * dataset: this can be either an iris cube, a cubelist or a dataset
        path.
        """
    def __init__(self, dataset):
        # First we put all datasets in a cubelist so that we can plot them
        # together if necessary without too much extra coding:
        self.plot_list = CubeList()

        if isinstance(dataset, CubeList):
            # Here we have to collect metadata from just the first Cube in a
            # CubeList (assuming that multiple datasets such as shapes files
            # will contain the same coordinate data), then render to produce
            # multiple plots on single figure:
            self.dataset = dataset
            self.plot_list = self.dataset
            for i, cube in enumerate(self.plot_list):
                if i == 0:
                    self.dims = cube.dim_coords
                else:
                    pass
        elif isinstance(dataset, str):
            # Use iris to read in dataset as lazy array and add to CubeList
            # here:
            self.path = dataset
            self.dataset = iris.load_cube(dataset)
            self.dims = self.dataset.dim_coords
            self.plot_list.append(self.dataset)
        elif isinstance(dataset, Cube):
            # Iris cube is already loaded so no advantage from loading lazily
            # here:
            self.dataset = dataset
            self.dims = self.dataset.dim_coords
            self.plot_list.append(self.dataset)

        # Guess all possible dim coords here using first cube in list before
        # loading dataframe (but scalar coords become None because we
        # can't make plots out of them):
        self.x_coord = self.y_coord = self.z_coord = self.t_coord = None
        for i, cube in enumerate(self.plot_list):
            if i == 0:
                for coord in cube.coords():
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
            else:
                pass

    def render(self):
        """
        Analyses the dimensionality of the dataset and then sends to
        appropriate renderer.
        """
        coords = (self.x_coord, self.y_coord, self.z_coord, self.t_coord)

        # If we have both an x-coord and y-coord then we can draw a map:
        if self.x_coord is not None and self.y_coord is not None:
            self.img_type = 'map'
            fig = render_map.Map(self.dataset).render(*coords)
        # If we have just a time coord then we can make a timeseries:
        elif self.x_coord is None and self.y_coord is None and \
                self.t_coord is not None:
            self.img_type = 'timeseries'
            fig = Plot(self.plot_list).render_timeseries()
        # If we don't have any coords then something's gone wrong, and we can't
        # plot anything:
        elif all(coord is None for coord in coords):
            fig = None
            raise ValueError('All dimension coordinates are either missing or '
                             'scalar, please choose a dataset with more '
                             'coordinate points.')
        return fig
