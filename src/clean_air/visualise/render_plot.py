"""
Module to create fabulous visualisations of various non-map plots.
"""

import hvplot.xarray  # noqa


class Plot:
    """
    Class to process data and create a lovely map from it.
    """
    def __init__(self, dataframe):
        self.df = dataframe.load()

    def render_timeseries(self):
        # NOTE: Must have a a deployed Bokeh Server app or a deployed Panel
        # app to be able to view these plots.
        self.df.hvplot.line(datashade=True)
