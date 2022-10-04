"""Integration tests for file_converter.py"""
import os
import pytest
import netCDF4
import csv

from clean_air.util import file_converter as fc


@pytest.fixture
def xl_input_path(sampledir):
    xl_data_path = os.path.join(sampledir, "test_data",
                                "metadata_form_responses.xlsx")
    return xl_data_path


@pytest.fixture
def netcdf_input_path(sampledir):
    netcdf_data_path = os.path.join(sampledir, "aircraft",
                                    "MOCCA_M251_20190903.nc")
    return netcdf_data_path


@pytest.fixture
def csv_input_path(sampledir):
    csv_data_path = os.path.join(sampledir, "obs", "ACTH_2016.csv")
    return csv_data_path


@pytest.fixture
def tmp_output_path(tmp_path):
    tmp_output_path = tmp_path / "test_data"
    tmp_output_path.mkdir()
    return tmp_output_path


@pytest.fixture
def csv_filename(tmp_output_path):
    csv_fname = os.path.join(tmp_output_path, "flightpath.csv")
    return csv_fname


@pytest.fixture
def netcdf_filename(tmp_output_path):
    netcdf_fname = os.path.join(tmp_output_path, "ACTH_2016.nc")
    return netcdf_fname


def test_convert_excel_to_json(xl_input_path, tmp_output_path):
    """
    Test to check end-to-end processing of Excel metadata form responses and
    their conversion to reformatted json files.
    """
    input_filename = os.path.split(xl_input_path)[-1]
    output_filename = os.path.splitext(input_filename)[0]
    input_file = fc.MetadataForm(xl_input_path, tmp_output_path)
    input_file.convert_excel('json')

    def test_conversion():
        """Check that the file has been converted to a new json file."""
        # input files for this conversion test have 3 rows, so return set of 3
        # filenames to check for:
        for i in range(3):
            fname = output_filename + str(i) + ".json"
            fpath = os.path.join(tmp_output_path, fname)
            try:
                with open(fpath) as file:
                    file.read()
            except FileNotFoundError as exc:
                pytest.fail(f"Unexpected exception: {exc}")

    def test_content():
        """Check that the contents of the converted file are as expected."""
        required_items = ["pollutants", "environmentType", "dateRange"]
        # Only test the first file here, can change later if deemed necessary:
        fpath = os.path.join(tmp_output_path,
                             output_filename + str(0) + ".json")
        with open(fpath) as file:
            json_file = file.read()  # This object is a string
            for item in required_items:
                assert item in json_file, f"{item} not found in json file."

    test_conversion()
    test_content()


def test_convert_excel_to_yaml(xl_input_path, tmp_output_path):
    """
    Test to check end-to-end processing of Excel metadata form responses and
    their conversion to reformatted json files.
    """
    input_filename = os.path.split(xl_input_path)[-1]
    output_filename = os.path.splitext(input_filename)[0]
    input_file = fc.MetadataForm(xl_input_path, tmp_output_path)
    input_file.convert_excel('yaml')

    def test_conversion():
        """Check that the file has been converted to a new yaml file."""
        for i in range(3):
            fname = output_filename + str(i) + ".yaml"
            fpath = os.path.join(tmp_output_path, fname)
            try:
                with open(fpath) as file:
                    file.read()
            except FileNotFoundError as exc:
                pytest.fail(f"Unexpected exception: {exc}")

    def test_content():
        """Check that the contents of the converted file are as expected."""
        required_items = ["title", "description", "authors", "bbox",
                          "chemical species", "observation level/model",
                          "data source", "time range", "lineage", "quality",
                          "docs"]
        # Only test the first file here, can change later if deemed necessary:
        fpath = os.path.join(tmp_output_path,
                             output_filename + str(0) + ".yaml")
        with open(fpath) as file:
            yaml_file = file.read()
            for item in required_items:
                assert item in yaml_file, f"{item} not found in yaml file."

    test_conversion()
    test_content()


def test_convert_netcdf_to_csv(netcdf_input_path, csv_filename):
    """Test to check end-to-end processing of netcdf files and their
    conversion into csv files."""
    input_file = fc.DataFile(netcdf_input_path, csv_filename)
    input_file.convert_netcdf()

    def test_conversion():
        """Check that the file has been converted to a new csv file."""
        try:
            with open(csv_filename) as file:
                file.read()
        except FileNotFoundError as exc:
            pytest.fail(f"Unexpected exception: {exc}")

    def test_content():
        """Check that the contents of the converted file are as expected."""
        field_names = {'Time', 'Latitude', 'Longitude', 'Altitude',
                       'Pressure', 'Temperature', 'Relative_Humidity',
                       'Wind_Speed', 'Wind_Direction', 'NO2', 'O3', 'SO2'}
        with open(csv_filename, newline='') as new_file:
            reader = csv.reader(new_file)
            for row in reader:
                # Only check first row for header names:
                if row == row[0]:
                    assert all(field_names) in row
                # Check all other rows for data length:
                else:
                    assert len(row) == 12

    test_conversion()
    test_content()


def test_convert_csv_to_netcdf(csv_input_path, netcdf_filename):
    """Test to check end-to-end processing of csv files and their
     conversion into netcdf files."""
    input_file = fc.DataFile(csv_input_path, netcdf_filename)
    input_file.convert_csv()

    def test_conversion():
        """Check that the file has been converted to a new netcdf file."""
        try:
            netCDF4.Dataset(netcdf_filename)
        except FileNotFoundError as exc:
            pytest.fail(f"Unexpected exception: {exc}")

    def test_content():
        """Check that the contents of the converted file are as expected."""
        # NOTE: The CSV file being used for this test only contains 9 of the
        # accepted 13 variables, so we will only check for those:
        field_names = {'PM10', 'Non-volatilePM10', 'Non-volatilePM2p5',
                       'PM2p5', 'Volatile PM10', 'Volatile PM2p5', 'O3',
                       'Date', 'time'}
        new_file = netCDF4.Dataset(netcdf_filename)
        with new_file:
            # Check all fields are present in output file:
            for name in field_names:
                assert name in new_file.variables
            # Also check that length of data fields is correct:
            for variable in new_file.variables:
                if variable in field_names:
                    assert new_file[variable].size == 8784

    test_conversion()
    test_content()

