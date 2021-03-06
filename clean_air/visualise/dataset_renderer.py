"""
Top-level module for rendering datasets.
"""

import geopandas
import iris
import xarray
from clean_air.visualise import render_map, render_plot


class DatasetRenderer:
    def __init__(self, dataset_path):
        # Use iris to read in dataset as lazy array here:
        self.path = dataset_path
        self.dataset = iris.load_cube(dataset_path)
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
        appropriate renderer in test_render_plot.py or test_render_map.py.
        """
        coords = (self.x_coord, self.y_coord, self.z_coord, self.t_coord)

        # If we have both an x-coord and y-coord then we can draw a map:
        if self.x_coord is not None and self.y_coord is not None:
            self.img_type = 'map'
            self.dataframe = geopandas.read_file(self.path)
            render_map.Map(self.dataframe).render(*coords)
        # If we have just a time coord then we can make a timeseries:
        elif self.x_coord is None and self.y_coord is None:
            self.img_type = 'timeseries'
            self.dataframe = xarray.open_dataset(self.path)
            render_plot.Plot(self.dataframe).render_timeseries()
        # If we don't have any coords then something's gone wrong and we can't
        # plot anything:
        elif all(coord is None for coord in coords):
            raise ValueError('All dimension coordinates are either missing or '
                             'scalar, please choose a dataset with more '
                             'coordinate points.')
