"""
Module to create fabulous visualisations of maps.
"""

import hvplot.xarray  # noqa


class Map:
    """
    Class to process data and create a lovely map from it.
    """
    def __init__(self, dataframe):
        self.df = dataframe.load()

    def render(self, x_coord, y_coord, z_coord=None, t_coord=None):
        # NOTE: Must have a a deployed Bokeh Server app or a deployed Panel
        # app to be able to view these plots.
        # NOTE: At this stage this is only displaying data points, without an
        # actual map behind it yet (although geo=True might add a map, I need
        # to see the image to find out...)

        # TODO: work out what to do when we have x and t coords as well
        # I assume this will involve Panel so that we can make sliders and
        # dashboards and widgets and stuff:
        # https://holoviz.org/tutorial/Building_Panels.html
        self.df.hvplot.points(x=x_coord, y=y_coord, datashade=True, geo=True)
