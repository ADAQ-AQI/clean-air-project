"""Unit tests for functions in file_converter.py"""

import os

import pytest
import pandas as pd
import pathlib

from clean_air.util import file_converter as fc


@pytest.fixture
def excel_filepath(sampledir):
    filepath = os.path.join(sampledir, "test_data",
                            "metadata_form_responses.xlsx")
    return filepath


@pytest.fixture
def pandas_dataframe():
    dataframe = pd.DataFrame
    dataframe.title = "UK Air Quality Reanalysis"
    dataframe.description = "This reanalysis has been produced  by the " \
                           "Atmospheric Dispersion and Air Quality Group " \
                           "at the Met Office using Air Quality in the " \
                           "Unified Model (AQUM). " \
                           "The reanalysis begins in January 2003 and will " \
                           "be maintained as a rolling 20 year archive. " \
                           "The data covers the UK at a horizontal " \
                           "resolution of 0.11 degree (~12 km), a vertical " \
                           "resolution of 63 model levels (model top ~40 km) " \
                           "and an hourly temporal resolution. " \
                           "The reanalysis dataset also contains bias " \
                           "corrected surface concentrations of some " \
                           "pollutants. " \
                           "Observations from the Automatic Urban and Rural " \
                           "Network (AURN), London Air Quality Network " \
                           "(LAQN) and additional UK local authority " \
                           "monitoring stations are used to produce the bias " \
                           "corrected surface concentrations.\n\nFurther " \
                           "information can be found at " \
                           "https://www.ukcleanair.org/storage/" \
                           "met-office-research/",
    dataframe.firstname1 = "Eleanor"
    dataframe.surname1 = "Smith"
    dataframe.north = 11.55
    dataframe.south = -8.465
    dataframe.east = -7.105
    dataframe.west = 8.995
    dataframe.chemicals = "Coarse Particulate Matter (PM10);" \
                         "Fine Particulate Matter (PM2.5);" \
                         "Isoprene (C5H8);" \
                         "Carbon Monoxide (CO);" \
                         "Sulphur Dioxide (SO2);" \
                         "Ozone (O3);" \
                         "Nitrogen Oxides (NOx);" \
                         "Nitrogen Dioxide (NO2);" \
                         "Nitrogen Monoxide (NO);",
    dataframe.obs_level = "Model Data"
    dataframe.data_source = "Air Quality in the Unified Model (AQUM)"    
    return dataframe


@pytest.fixture
def data_path():
    root = pathlib.Path(__file__).parent
    path = root.parent / "data/json_data"
    return path


def test_read_excel_data(excel_filepath):
    """Test that excel files are read and converted successfully to
    temporary dataframe objects"""
    temp_df = fc.read_excel_data(filepath=excel_filepath)
    assert isinstance(temp_df, pd.DataFrame)


def test_save_to_json(pandas_dataframe, data_path):
    """Test that a simple pandas DataFrame can be converted successfully
    to a JSON file"""
    fc.save_as_json(data_object=pandas_dataframe)
    json = os.path.join(data_path, "dailydata0.json")
    # TODO: How do I test this?

