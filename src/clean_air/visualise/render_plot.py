"""
Module to create fabulous visualisations of various non-map plots.
"""

import iris.plot
import iris.pandas
import hvplot.pandas  # noqa

class Plot:
    def __init__(self, dataset):
        # Note: This should always be a CubeList, even if it only contains
        # one Cube.  This is just for simplification of the code.
        self.dataset = dataset
    def render_timeseries(self):
            # # For a single cube, convert to pandas dataframe and give suitable axis names.
            # if i == 0:
            #     df_main = iris.pandas.as_data_frame(cube)
            #     df_main.columns = [f'{cube.standard_name} \n in {cube.units}']
            #     df_main.index.names = ['Time']
            #
            # # For subsequent cubes provided by multipolygon, add them as dataframe columns.
            # elif i > 0:
            #     df_main.columns = ['Polygon 1'] # rename to match pattern
            #     df = iris.pandas.as_data_frame(cube)
            #     col_name = f'Polygon {i+1}'
            #     df.columns = [col_name]
            #     extracted_col = df[col_name]
            #     df_main = df_main.join(extracted_col)

        return df_main