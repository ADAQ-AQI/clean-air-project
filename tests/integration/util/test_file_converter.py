"""Integration tests for file_converter.py"""
import os

import pytest
import pandas as pd
import pathlib

from clean_air.util import file_converter as fc
# TODO: Write tests to check end-to-end processing of file conversions


@pytest.fixture
def xl_input():
    xl_data_path = os.path.join(pathlib.Path.root, "cap-sample-data",
                                "test_data", "metadata_form_responses.xlsx")
    return xl_data_path


@pytest.fixture
def json_output():
    json_data_path = os.path.join(pathlib.Path.root, "cap", "clean_air",
                                  "visualise", "assets", "json_data")
    return json_data_path


# @pytest.fixture
# def json_output_format():
    # json_format = os.path.join(pathlib.Path.root,...)
    # return json format


@pytest.fixture
def yaml_output_format():
    yaml_format = os.path.join(pathlib.Path.root, "cap-sample-data",
                               "test_data", "station_metadata.yaml")
    return yaml_format


def test_convert_excel_to_json(xl_input, json_output):
    """
    Test to check end-to-end processing of excel metadata form responses and
    their conversion to reformatted json files.
    """
    temp_df = fc.read_excel_data(filepath=xl_input)
    fc.save_as_json(data_object=temp_df)
    # TODO: Find out how to check that this has saved


def test_json_output():
    """
    Check that the output of the json file matches the output format required
    for further processing.
    """
    # TODO: Create json input file that matches the exact format required
    # TODO: Add this file to pytest fixtures
    # TODO: Use this to match the output from file_converter to


# def test_convert_excel_to_yaml():

# def test_convert_netcdf_to_csv():

# TODO: Create 'assets' directory (see Catherine's branch) to put saved files
#  in and then change all file outputs to accept a variable defining output
#  location.

