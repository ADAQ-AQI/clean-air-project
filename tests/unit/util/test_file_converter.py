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


@pytest.fixture()
def saved_yaml(test_output_path):
    saved_yaml = open(test_output_path + str(0) + '.yaml')
    return saved_yaml


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


def test_yaml_reformat_chemicals(saved_yaml):
    """Test that all chemical entries are reformatted to contain their
    shortname only (i.e. '(PM10)' as opposed to
    'Course Particulate Matter (PM10)')."""
    for entry in saved_yaml:
        if entry == 'chemical species':
            for chemical in entry:
                assert chemical.startswith('(') and chemical.endswith(')')


def test_yaml_file_structure(saved_yaml):
    """Test that yaml file structure contains all keys required for yaml
    output."""
    # NOTE: See test_json_file_structure for help with this one
    keys_required = ['title', 'description', 'authors', 'bbox',
                     'chemical species', 'observation level/model',
                     'data source', 'time range', 'lineage', 'quality', 'docs']
    yaml_file = saved_yaml.read()
    for key in keys_required:
        assert key in yaml_file


def test_yaml_authors_subset(saved_yaml):
    """Test that all required keys are present in authors subset."""
    keys_required = ['firstname', 'surname', 'firstname2', 'surname2']
    for entry in saved_yaml:
        if entry == 'authors':
            for key in keys_required:
                assert key in entry


def test_yaml_bbox_subset(saved_yaml):
    """Test that all required keys are present in bbox subset."""
    keys_required = ['north', 'south', 'east', 'west']
    for entry in saved_yaml:
        if entry == 'bbox':
            for key in keys_required:
                assert key in entry


def test_yaml_timerange_subset(saved_yaml):
    """Test that all required keys are present in time range subset."""
    keys_required = ['start', 'end']
    for entry in saved_yaml:
        if entry == 'time range':
            for key in keys_required:
                assert key in entry


def test_yaml_remove_nan_names(saved_yaml):
    """Test that all names (of users), if NAN values, are removed from yaml
    output (including keys)."""
    keys_not_required = ['firstname2', 'surname2']
    for entry in saved_yaml:
        if entry == 'authors':
            for key in keys_not_required:
                assert key not in entry


def test_yaml_datetime_format(saved_yaml):
    """Test that saved yaml file contains dates in isoformat."""
    for entry in saved_yaml:
        if entry == 'time range':
            for date in entry:
                assert date.format is 'isoformat'


