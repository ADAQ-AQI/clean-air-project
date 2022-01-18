"""
Module to create fabulous visualisations of various non-map plots.
"""

import hvplot.xarray  # noqa

import iris.cube
import iris.plot
import matplotlib as mpl


class Plot:
    def __init__(self, dataframe, xcoord_name=None, ycoord_name=None):
        self.dataframe = dataframe
        self.xname = xcoord_name
        self.yname = ycoord_name

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
        fig = mpl.pyplot.figure()
        ts_plot = fig.add_subplot(1, 1, 1)
        ts_plot.plot(self.dataframe.data)
        ts_plot.set_title(self.dataframe.var_name)
        # TODO: Find latest point that x and y coords are available, and pass
        #  names of coords into dataset_renderer.DatasetRenderer and then on
        #  into render_plot.Plot so we can use them for plot labels here.
        ts_plot.set_xlabel(self.xname)
        ts_plot.set_ylabel(self.yname)

        # This line is for development and testing purposes, I would like to
        # keep it but we can comment it out once we are happy with formatting.
        fig.show()

        return fig

