"""
Data Visuliser Class to handle rendering of maps and plots
"""


class DataVisuliser():
    def __init__(self, *datasets):
        self.datasets = datasets  # declare variable to hold a list of datasets

    def render_obs(self):
        # do Something
        pass

    def render_gridded(self, subsetter=None):
        # do Something
        pass

    def _render_gridded_point(self, latlon):
        # doSomething
        pass

    def _render_gridded_poly(self, shapefile):
        # doSomething
        pass

    def _render_gridded_box(self, gridbox):
        # doSomething
        pass

    def _render_gridded_track(self, track):
        # doSomething
        pass
