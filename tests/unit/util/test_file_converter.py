"""Unit tests for functions in file_converter.py"""

import os

import pytest
import pandas as pd
import pathlib

from clean_air.util import file_converter as fc


@pytest.fixture()
def excel_filepath(sampledir):
    filepath = os.path.join(sampledir, "test_data",
                            "metadata_form_responses.xlsx")
    return filepath


@pytest.fixture()
def test_output_path(sampledir):
    # Note: This path includes the first part of the filename (only omitting
    # unit number).
    test_output_path = os.path.join(sampledir, "test_data", "test_output")
    return test_output_path


@pytest.fixture()
def saved_json(test_output_path):
    saved_json = open(test_output_path + str(0) + '.json')
    return saved_json


def test_read_excel_data(excel_filepath):
    """Test that excel files are read and converted successfully to
    temporary dataframe objects"""
    temp_df = fc.read_excel_data(filepath=excel_filepath)
    assert isinstance(temp_df, pd.DataFrame)


def test_slice_data(excel_filepath):
    """Test that data from temporary dataframes (read from excel files) are
    split into single dataframes for each row of data.  Test excel file has
    three rows, so should be split into three separate files here."""
    # First, read and slice the test file:
    temp_df = fc.read_excel_data(filepath=excel_filepath)
    sliced_data = fc.slice_data(temp_df)
    # Now check that three separate files have been generated:
    assert len(sliced_data) is 3


def test_json_reformat_chemicals(saved_json):
    """Test that the single excel entry for each chemical is reformatted
    into three seperate lines representing 'name', 'shortname' and
    'chart' information."""
    for entry in saved_json:
        if entry == 'pollutants':
            assert len(entry) is 3


def test_json_file_structure(saved_json):
    """Test that new_file has index names; 'pollutants', environmentType'
    and 'dateRange'."""
    keys_required = ['pollutants', 'environmentType', 'dateRange']
    json_file = saved_json.read()
    for key in keys_required:
        assert key in json_file


def test_json_date_range(saved_json):
    """Test that item 'dateRange' in new_file is a list containing two
    entries."""
    for entry in saved_json:
        if entry == 'dateRange':
            assert len(entry) is 2


def test_json_date_format(saved_json):
    """Test that saved json file contains dates in isoformat."""
    for entry in saved_json:
        if entry == 'dateRange':
            for date in entry:
                assert date.format is 'isoformat'

# TODO: set up all yaml tests required, then fill in test details.

