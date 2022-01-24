"""
Integration tests for the test_dataset_renderer.py visualisations.
"""

# import os
#
# import clean_air.visualise.dataset_renderer as dr


# NOTE: This test now also fails because geopandas cannot load netcdf and iris
# cannot load csv.  We must write a netcdf/csv converter to reinstate all of
# these tests.
# class TestDatasetRenderer:
#     """
#     Class to test integration properties of test_dataset_renderer.py
#     """
#
#     def setup_class(self):
#         self.model_path = os.path.join(MODEL_DATA_PATH,
#                                        'aqum_daily_daqi_mean_20200520.nc')
#         self.obs_path = os.path.join(OBS_DATA_PATH,
#                                      'ABD_2015.csv')
#         self.aircraft_path = os.path.join(AIRCRAFT_DATA_PATH,
#                                           'clean_air_MOCCA_data_'
#                                           '20200121_M265_v0.nc')
#
#     def test_renderer_for_model_data(self):
#         img = dr.Renderer(self.model_path)
#         img.render()
#
#     def test_renderer_for_obs_data(self):
#         # NOTE: This test highlights the fact that iris cannot read csv files
#         # but we need iris to identify coord axes before passing them to the
#         # renderer.  We will therefore need to write a converter as I haven't
#         # managed to find one yet.
#         # TODO: Write csv to nc converter:
#         # https://stackoverflow.com/questions/22933855/convert-csv-to-netcdf
#         # This test will fail until the converter is completed.
#         img = dr.Renderer(self.obs_path)
#         img.render()
#
#     def test_renderer_for_aircraft_data(self):
#         # NOTE: This test fails currently because iris is having trouble
#         # interpreting the CF variables in the aircraft data.  I will be
#         # discussing this with Elle on Thursday but I think it's in the
#         # pipeline to be resolved at some point anyway.
#         # TODO: fix aircraft data
#         img = dr.Renderer(self.aircraft_path)
#         img.render()
