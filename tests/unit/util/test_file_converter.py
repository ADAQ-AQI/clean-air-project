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
def test_output_path(sampledir):
    # Note: This path includes the first part of the filename (only omitting
    # unit number).
    test_output_path = os.path.join(sampledir, "test_data", "test_output")
    return test_output_path


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


# TODO: Fill in details of tests below:
class SaveAsJSONTest(test_output_path):
    def setUp(self):
        # read and slice the test file then send to save_as_json():
        self.temp_df = fc.read_excel_data(filepath=excel_filepath)
        self.sliced_data = fc.slice_data(self.temp_df)
        self.json_conversion = fc.save_as_json(data_object=self.sliced_data,
                                               r=0,
                                               output_location=
                                               self.test_output_path)

    def test_reformat_chemicals(self):
        """Test that the single excel entry for each chemical is reformatted
        into three seperate lines representing 'name', 'shortname' and
        'chart' information."""

    def test_new_file_structure(self):
        """Test that new_file has index names; 'pollutants', environmentType'
        and 'dateRange'."""

    def test_date_range(self):
        """Test that item 'dateRange' in new_file is a list containing two
        entries."""

    def test_date_format(self):
        """Test that saved json file contains dates in isoformat."""

# class SaveAsYAMLTest(test_output_path):
#
#     def setUp(self):
#
#     def test_...
