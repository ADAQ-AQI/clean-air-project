"""
Module to create fabulous visualisations of various non-map plots.
"""

import hvplot.xarray  # noqa

from iris.cube import Cube, CubeList
import iris.plot
import matplotlib as mpl
from matplotlib import pyplot as plt


class Plot:
    def __init__(self, dataframe):
        # Note: This should always be a CubeList, even if it only contains
        # one Cube.  This is just for simplification of the code.
        self.dataframe = dataframe

    def render_timeseries(self):
        # First make a figure, then add all datasets as subplots:
        fig = plt.figure(figsize=(11, 5))

        # We want 3 plots per row unless there are less than 3 plots to
        # render, then we want the figsize to match the number of plots:
        n_plots = len(self.dataframe)
        n_rows = int((n_plots-1)/3) + 1
        if len(self.dataframe) <= 3:
            n_cols = len(self.dataframe)
        else:
            n_cols = 3

        for i, cube in enumerate(self.dataframe):
            # First check that cube is 1-dimensional, otherwise reduce
            # dimensions:
            if cube.ndim > 1:
                for coord in cube.dim_coords:
                    if coord.points.size == 1:
                        cube = cube.collapsed(coord, iris.analysis.MEAN)

            # Now check again to make sure cube is 1D, otherwise raise error:
            if cube.ndim != 1:
                raise ValueError('There are too many coordinates to plot this '
                                 'cube as a timeseries.  Please pass in a cube '
                                 'containing only one dimension (i.e. time).')

            xcoord = cube.dim_coords[0]
            ts_plot = fig.add_subplot(n_rows, n_cols, i+1)
            ts_plot.plot(xcoord.points, cube.data)
            ts_plot.set_title(cube.var_name)
            ts_plot.set_xticks(xcoord.points)
            ts_plot.set_yticks(cube.data)
            ts_plot.set_xlabel(xcoord.var_name + ' in ' + xcoord.units.origin)
            ts_plot.set_ylabel(cube.units)

            # Format tick labels/marks for readability:
            ts_plot.yaxis.set_major_locator(plt.MaxNLocator(10))
            ts_plot.xaxis.set_major_locator(plt.MaxNLocator(15))
            # TODO: Set readable tick labelling for x axis

        # This line is for development and testing purposes, I would like to
        # keep it but we can comment it out once we are happy with formatting.
        # fig.show()

        return fig

