"""Integration tests for file_converter.py"""
import os
import pytest
import netCDF4

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
def json_filename(tmp_output_path):
    json_fname = os.path.join(tmp_output_path, "form_response0.json")
    return json_fname


@pytest.fixture
def yaml_filename(tmp_output_path):
    yaml_fname = os.path.join(tmp_output_path, "form_response0.yaml")
    return yaml_fname
# TODO: For json and yaml filenames, extend to check for all three responses.

@pytest.fixture
def csv_filename(tmp_output_path):
    csv_fname = os.path.join(tmp_output_path, "flightpath.csv")
    return csv_fname


@pytest.fixture
def netcdf_filename(tmp_output_path):
    netcdf_fname = os.path.join(tmp_output_path, "ACTH_2016.nc")
    return netcdf_fname


def test_convert_excel_to_json(xl_input_path, json_filename):
    """
    Test to check end-to-end processing of excel metadata form responses and
    their conversion to reformatted json files.
    """
    # Run conversion and check for file in tmp_path:
    fc.convert_excel(xl_input_path, json_filename)

    def test_conversion():
        """Check that the file has been converted to a new json file."""
        try:
            with open(json_filename) as file:
                file.read()
        except FileNotFoundError as exc:
            pytest.fail(f"Unexpected exception: {exc}")

    def test_content():
        """Check that the contents of the converted file are as expected."""
        required_items = ["pollutants", "environmentType", "dateRange"]
        with open(json_filename) as file:
            json_file = file.read()  # This object is a string
            for item in required_items:
                assert item in json_file, f"{item} not found in json file."

    test_conversion()
    test_content()


def test_convert_excel_to_yaml(xl_input_path, yaml_filename):
    """
    Test to check end-to-end processing of excel metadata form responses and
    their conversion to reformatted json files.
    """
    # Run conversion and check for file in tmp_path:
    fc.convert_excel(xl_input_path, yaml_filename)

    def test_conversion():
        """Check that the file has been converted to a new yaml file."""
        try:
            with open(yaml_filename) as file:
                file.read()
        except FileNotFoundError as exc:
            pytest.fail(f"Unexpected exception: {exc}")

    def test_content():
        """Check that the contents of the converted file are as expected."""
        required_items = ["title", "description", "authors", "bbox",
                          "chemical species", "observation level/model",
                          "data source", "time range", "lineage", "quality",
                          "docs"]
        with open(yaml_filename) as file:
            yaml_file = file.read()
            for item in required_items:
                assert item in yaml_file, f"{item} not found in yaml file."

    test_conversion()
    test_content()


def test_convert_netcdf_to_csv(netcdf_input_path, csv_filename):
    """Test to check end-to-end processing of netcdf files and their
    conversion into csv files."""
    fc.convert_netcdf(netcdf_input_path, csv_filename)

    def test_conversion():
        """Check that the file has been converted to a new csv file."""
        try:
            with open(csv_filename) as file:
                file.read()
        except FileNotFoundError as exc:
            pytest.fail(f"Unexpected exception: {exc}")

    def test_content():
        """Check that the contents of the converted file are as expected."""
        # read netcdf file, produce object
        # check object for ? (what is needed in csv files?)
        pass  # (until I have more info on required output)

    test_conversion()
    test_content()


def test_convert_csv_to_netcdf(csv_input_path, netcdf_filename):
    """Test to check end-to-end processing of csv files and their
     conversion into netcdf files."""
    fc.convert_csv(csv_input_path, netcdf_filename)

    def test_conversion():
        """Check that the file has been converted to a new netcdf file."""
        try:
            netCDF4.Dataset(netcdf_filename)
        except FileNotFoundError as exc:
            pytest.fail(f"Unexpected exception: {exc}")

    def test_content():
        """Check that the contents of the converted file are as expected."""
        # read csv file, produce object
        # check object for ? (what is needed in netcdf files?)
        pass  # (until I have more info on required output)

    test_conversion()
    test_content()

