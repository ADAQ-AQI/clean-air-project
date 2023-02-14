"""Unit tests for functions in file_converter.py"""

import os

import pytest
import pandas as pd
import json
import yaml
import csv
import datetime as dt

from clean_air.util import file_converter as fc


@pytest.fixture()
def excel_filepath(sampledir):
    filepath = os.path.join(sampledir, "test_data", "metadata_form_responses.xlsx")
    return filepath


@pytest.fixture()
def netcdf_filepath(sampledir):
    netcdf_filepath = os.path.join(sampledir, "aircraft", "MOCCA_M251_20190903.nc")
    return netcdf_filepath


@pytest.fixture()
def csv_filepath(sampledir):
    csv_filepath = os.path.join(sampledir, "obs", "ABD_2015.csv")
    return csv_filepath


@pytest.fixture()
def yml_filepath(sampledir):
    yml_filepath = os.path.join(sampledir, "yaml_data", "station_metadata.yaml")
    return yml_filepath


@pytest.fixture()
def tmp_output_path(tmp_path):
    tmp_output_path = tmp_path / "tmp_output_path"
    tmp_output_path.mkdir()
    return tmp_output_path


class TestGenerateDataframe:
    """Class to test generation of dataframes within file conversion routines."""
    @pytest.yield_fixture(autouse=True)
    def setup_class(self, excel_filepath, netcdf_filepath, csv_filepath):
        """SETUP dataframe conversion variables for all tests."""
        self.temp_df_xl = fc.generate_dataframe(filepath=excel_filepath)
        self.temp_df_nc = fc.generate_dataframe(filepath=netcdf_filepath)
        self.temp_df_csv = fc.generate_dataframe(filepath=csv_filepath)

    def test_read_excel_data(self):
        """
        GIVEN an excel file containing results from the metadata input form,
        WHEN read by generate_dataframe(),
        THEN the result is a pandas DataFrame.
        """
        assert isinstance(self.temp_df_xl, pd.DataFrame)

    def test_read_netcdf_data(self):
        """
        GIVEN a netCDF file containing aircraft data,
        WHEN read by generate_dataframe(),
        THEN the result is a temporary pandas DataFrame.
        """
        assert isinstance(self.temp_df_nc, pd.DataFrame)

    def test_read_csv_data(self):
        """
        GIVEN a CSV file containing observational data,
        WHEN read by generate_dataframe(),
        THEN the result is a temporary pandas DataFrame.
        """
        assert isinstance(self.temp_df_csv, pd.DataFrame)

    def test_bad_input_data(self, yml_filepath):
        """
        GIVEN an invalid input of a yaml file,
        WHEN read by generate_dataframe(),
        THEN an exception is raised.
        """
        with pytest.raises(Exception):
            fc.generate_dataframe(filepath=yml_filepath)

    def test_slice_data(self):
        """
        GIVEN a set of three temporary dataframes read from an excel matadata input file,
        WHEN slice_data() is used,
        THEN the result is three separate output files.
        """
        # First, read and slice the test file:
        # fc.generate_dataframe(filepath=excel_filepath)
        sliced_data = fc.slice_data(self.temp_df_xl)
        # Now check that three separate files have been generated:
        assert len(sliced_data) == 3


class TestExcelToJson:
    """Class to test conversion of excel metadata input forms to json files."""
    @pytest.yield_fixture(autouse=True)
    def setup_class(self, excel_filepath, tmp_output_path):
        """SETUP excel to json conversion variables for all tests."""
        # Make conversion, dump output to temp location:
        fc.MetadataForm(excel_filepath, tmp_output_path).convert_excel('json')

        # Only name first response form for unit test:
        json_fname = tmp_output_path / "metadata_form_responses0.json"
        self.saved_json = json.load(json_fname.open())

        return self.saved_json

    def test_json_reformat_chemicals(self):
        """
        GIVEN a file saved from the metadata input form and converted to json format,
        WHEN the excel -> json conversion is undergone using convert_excel(),
        THEN the resulting json file will contain the variables 'name', 'shortname' and 'chart' for each pollutant.
        """
        for chem in range(len(self.saved_json["pollutants"])):
            assert self.saved_json["pollutants"][chem]["name"] and \
                   self.saved_json["pollutants"][chem]["shortname"] and \
                   self.saved_json["pollutants"][chem]["chart"]

    def test_json_file_structure(self):
        """
        GIVEN a file saved from the metadata input form and converted to json format,
        WHEN the excel -> json conversion is undergone using convert_excel(),
        THEN the resulting json file will contain the index keys 'pollutants', 'environmentType' and 'dateRange'.
        """
        keys_required = ['pollutants', 'environmentType', 'dateRange']
        for key in keys_required:
            assert key in self.saved_json

    def test_json_date_range(self):
        """
        GIVEN a file saved from the metadata input form and converted to json format,
        WHEN the excel -> json conversion is undergone using convert_excel(),
        THEN the resulting json file will contain the start date and end date.
        """
        assert self.saved_json["dateRange"]["startDate"] and \
            self.saved_json["dateRange"]["endDate"]

    def test_json_date_format(self):
        """
        GIVEN a file saved from the metadata input form and converted to json format,
        WHEN the excel -> json conversion is undergone using convert_excel(),
        THEN the resulting start and end dates will be in isoformat.
        """
        assert dt.datetime.fromisoformat(self.saved_json["dateRange"]["startDate"])
        assert dt.datetime.fromisoformat(self.saved_json["dateRange"]["endDate"])


class TestExcelToYaml:
    """Class to test conversion of excel metadata input forms to yaml files."""
    @pytest.yield_fixture(autouse=True)
    def setup_class(self, excel_filepath, tmp_output_path):
        """SETUP excel to yaml conversion variables for all tests."""
        # Make conversion, dump output to temp location:
        fc.MetadataForm(excel_filepath, tmp_output_path).convert_excel('yaml')

        # Only name first response form for unit test:
        yaml_fname = tmp_output_path / "metadata_form_responses0.yaml"
        self.saved_yaml = yaml.safe_load(yaml_fname.open())

        return self.saved_yaml

    def test_yaml_reformat_chemicals(self):
        """
        GIVEN a file saved from the metadata input form and converted to yaml format,
        WHEN the excel -> yaml conversion is undergone using convert_excel(),
        THEN each entry of 'chemical species' will consist of its shortened name (see util/conversion_lists.py).
        """
        for entry in self.saved_yaml['chemical species']:
            assert len(entry) <= 7

    def test_yaml_file_structure(self):
        """
        GIVEN a file saved from the metadata input form and converted to yaml format,
        WHEN the excel -> yaml conversion is undergone using convert_excel(),
        THEN expected keys are all present in resulting yaml file.
        """
        keys_required = ['title', 'description', 'authors', 'bbox',
                         'chemical species', 'observation level/model',
                         'data source', 'time range', 'lineage', 'quality', 'docs']
        for key in keys_required:
            assert key in self.saved_yaml

    def test_yaml_authors_subset(self):
        """
        GIVEN a file saved from the metadata input form and converted to yaml format,
        WHEN the excel -> yaml conversion is undergone using convert_excel(),
        THEN expected keys are all present in 'authors' subset of resulting yaml file.
        """
        keys_required = ['firstname', 'surname']
        for key in keys_required:
            assert key in self.saved_yaml['authors'][0]

    def test_yaml_bbox_subset(self):
        """
        GIVEN a file saved from the metadata input form and converted to yaml format,
        WHEN the excel -> yaml conversion is undergone using convert_excel(),
        THEN expected keys are all present in 'bbox' subset of resulting yaml file.
        """
        keys_required = ['north', 'south', 'east', 'west']
        for key in keys_required:
            assert key in self.saved_yaml['bbox']

    def test_yaml_timerange_subset(self):
        """
        GIVEN a file saved from the metadata input form and converted to yaml format,
        WHEN the excel -> yaml conversion is undergone using convert_excel(),
        THEN expected keys are all present in 'time range' subset of resulting yaml file.
        """
        keys_required = ['start', 'end']
        for key in keys_required:
            assert key in self.saved_yaml['time range']

    def test_yaml_remove_nan_names(self):
        """
        GIVEN a file saved from the metadata input form (containing only one author) and converted to yaml format,
        WHEN the excel -> yaml conversion is undergone using convert_excel(),
        THEN only one author is present in resulting yaml file.
        """
        # Note: This test works specifically with this test file as the second
        # set of names in the file are nans.
        assert len(self.saved_yaml['authors']) == 1

    def test_yaml_datetime_format(self):
        """
        GIVEN a file saved from the metadata input form and converted to yaml format,
        WHEN the excel -> yaml conversion is undergone using convert_excel(),
        THEN 'start' and 'end' values from 'time range' subset are in isoformat.
        """
        assert dt.datetime.fromisoformat(self.saved_yaml["time range"]["start"])
        assert dt.datetime.fromisoformat(self.saved_yaml["time range"]["end"])

    def test_bad_output_type(self, excel_filepath, tmp_output_path):
        """
        GIVEN a file saved from the metadata input form,
        WHEN converting from excel -> yaml using convert_excel() AND an invalid filetype as an argument,
        THEN a ValueError is raised.
        """
        with pytest.raises(ValueError):
            fc.MetadataForm(excel_filepath, tmp_output_path).convert_excel('yiml')


# TODO: Add test class here for MetaDataForm conversions.
class TestDataFile:
    """Class to test conversion of input CSV and netCDF files to netCDF and CSV files (respectively)."""

    def test_csv_no_index(self, tmp_output_path, netcdf_filepath):
        """
        GIVEN a filepath to a netCDF file,
        WHEN the file is converted to CSV format using DataFile.convert_netcdf(),
        THEN the first element of each row (except the header row) will be a datetime object in isoformat.
        """
        # NOTE: Due to the behaviour of the csv reader, this file can only be
        # examined within the condition 'with open...', so more set-up tasks must
        # be performed here as opposed to inside a fixture.
        csv_fname = tmp_output_path / "flightpath.csv"
        fc.DataFile(netcdf_filepath, csv_fname).convert_netcdf()
        with open(csv_fname, newline='') as csvfile:
            saved_csv = csv.reader(csvfile)
            for n, row in enumerate(saved_csv):
                if n == 0:
                    # First line of csv is headers, no check required here.
                    pass
                else:
                    assert dt.datetime.fromisoformat(row[0])

        # TODO: Check for more tests to add here for DataFile class.


class TestCSVReformatter:
    """Class to test reformatting of CSV files during conversion process."""

    @pytest.yield_fixture(autouse=True)
    def setup_class(self, csv_filepath):
        """SET UP all inputs to tests."""
        self.tmp_df = fc.csv_reformatter(csv_filepath)

    def test_csv_reformat_bad_names_removed(self):
        """
        GIVEN a CSV filepath as input,
        WHEN the file is reformatted using csv_reformatter(),
        THEN unrequired (unspecified) fields will be removed.
        """
        assert "status" not in self.tmp_df.columns

    def test_csv_reformat_syntax_corrected(self):
        """
        GIVEN a CSV filepath as input,
        WHEN the file is reformatted using csv_reformatter(),
        THEN fields with invalid syntax headers will be removed.
        """
        assert "PM<sub>10</sub> particulate matter (Hourly measured)" \
               not in self.tmp_df.columns
