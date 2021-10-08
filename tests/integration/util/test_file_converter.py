"""Integration tests for file_converter.py"""
import os
import pytest

from clean_air.util import file_converter as fc


@pytest.fixture
def xl_input_path(sampledir):
    xl_data_path = os.path.join(sampledir, "test_data",
                                "metadata_form_responses.xlsx")
    return xl_data_path


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


def test_convert_excel_to_json(xl_input_path, tmp_output_path,
                               json_filename):
    """
    Test to check end-to-end processing of excel metadata form responses and
    their conversion to reformatted json files.
    """
    # Run conversion and check for file in tmp_path:
    fc.convert_excel_to_json(xl_input_path, tmp_output_path)
    try:
        with open(json_filename) as file:
            file.read()
    except FileNotFoundError as fnf_error:
        raise(fnf_error)


def test_convert_excel_to_yaml(xl_input_path, tmp_output_path,
                               yaml_filename):
    """
    Test to check end-to-end processing of excel metadata form responses and
    their conversion to reformatted json files.
    """
    # Run conversion and check for file in tmp_path:
    fc.convert_excel_to_yaml(xl_input_path, tmp_output_path)
    try:
        with open(yaml_filename) as file:
            file.read()
    except FileNotFoundError as fnf_error:
        print(fnf_error)
        print("Unable to locate converted yaml file.")


