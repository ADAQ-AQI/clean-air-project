"""
Top-level module for rendering datasets.  This module will determine from the number and nature of dimensions present
whether to reshape the dataset into a format suitable for hvplot.

If x and y are present no reshaping takes place, so a map can be drawn with hvplot commands.
If only t is present, dataset will be reformed into a pandas dataset, so one or more timeseries can be drawn with
hvplot commands.
"""

import iris
import iris.pandas
from iris.cube import Cube, CubeList
from shapely.geometry import Polygon, MultiPolygon

from clean_air import util
from clean_air.data import DataSubset


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
            # Here we have to collect metadata from just the first Cube in a CubeList:
            self.plot_list = dataset
            # Sometimes we can have a cubelist within a cubelist, so pop a catch in here to convert inner cubelists
            # to cubes:
            for i, cube in enumerate(self.plot_list):
                if isinstance(cube, CubeList):
                    self.plot_list[i] = cube[0]
            self.dims = self.plot_list[0].dim_coords

        elif isinstance(dataset, str):
            # Use iris to read in dataset as lazy array and add to plot list here (iris will always load a CubeList
            # using this function):
            self.plot_list = iris.load(dataset)
            self.dims = self.plot_list[0].dim_coords

        elif isinstance(dataset, Cube):
            # Iris cube is already loaded so no advantage from loading lazily here:
            self.dims = dataset.dim_coords
            self.plot_list.append(dataset)

        # Guess all possible dim coords here using first cube in list before
        # loading dataframe (but scalar coords become None because we
        # can't make plots out of them):
        self.x_coord = self.y_coord = self.z_coord = self.t_coord = None
        for coord in self.dims:
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
        Analyses the dimensionality of the dataset and then converts to appropriate pandas dataframe type.
        """
        coords = (self.x_coord, self.y_coord, self.z_coord, self.t_coord)
        self.rendered_df = None

        # If we have both an x-coord and y-coord then we can draw a map:
        if self.x_coord is not None and self.y_coord is not None:
            self.img_type = 'map'
            # NOTE: Even if multiple cubes are passed in here, only the first cube will be converted to pandas to plot
            # as a map.  Multiple maps cannot be plotted at once as only a single dataframe is returned.
            self.rendered_df = iris.pandas.as_data_frame(self.plot_list[0])

        # If we have just a time coord then we can make a timeseries:
        elif self.x_coord is None and self.y_coord is None and self.t_coord is not None:
            self.img_type = 'timeseries'
            for i, cube in enumerate(self.plot_list):
                if i == 0:
                    self.rendered_df = iris.pandas.as_data_frame(cube)
                    self.rendered_df.columns = [f'{cube.standard_name} \n in {cube.units}']
                    self.rendered_df.index.names = ['Time']
            # For subsequent cubes provided by multipolygon, add them as dataframe columns.
                elif i > 0:
                    self.rendered_df.columns = ['Polygon 1']  # rename to match pattern
                    df = iris.pandas.as_data_frame(cube)
                    col_name = f'Polygon {i + 1}'
                    df.columns = [col_name]
                    extracted_col = df[col_name]
                    self.rendered_df = self.rendered_df.join(extracted_col)

        # If we don't have any coords then something's gone wrong and we can't plot anything:
        elif all(coord is None for coord in coords):
            raise ValueError('All dimension coordinates are either missing or '
                             'scalar, please choose a dataset with more '
                             'coordinate points.')
        return self.rendered_df


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
        # Identify and remove any single-point coordinates:
        scalar_coords = []
        for coord in point_cube.dim_coords:
            if len(coord.points) == 1:
                scalar_coords.append(coord)
        for coord in scalar_coords:
            point_cube = point_cube.collapsed(coord.standard_name, iris.analysis.MEAN)
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

    def track(self, crs=None):
        """Generate time series containing data along a track."""
        track_cube = self.data.extract_track(self.data, crs=crs)

        return track_cube
