"""
Module to create fabulous visualisations of various non-map plots.
"""

import hvplot.xarray  # noqa

import iris.cube
import iris.plot
import matplotlib as mpl


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
        fig = mpl.pyplot.figure()
        xcoord = self.dataframe.dim_coords[0]
        ts_plot = fig.add_subplot(1, 1, 1)
        ts_plot.plot(xcoord.points, self.dataframe.data)
        ts_plot.set_title(self.dataframe.var_name)
        ts_plot.set_xticks(xcoord.points)
        ts_plot.set_yticks(self.dataframe.data)
        ts_plot.set_xlabel(xcoord.var_name + ' in ' + xcoord.units.origin)
        ts_plot.set_ylabel(self.dataframe.units)
        # TODO: Format xticks and yticks so they are readable and accurate.

        # This line is for development and testing purposes, I would like to
        # keep it but we can comment it out once we are happy with formatting.
        fig.show()

        return fig

