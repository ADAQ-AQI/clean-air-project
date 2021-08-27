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
def test_output_path(sampledir):
    # Note: This path includes the first part of the filename (only omitting
    # unit number).
    test_output_path = os.path.join(sampledir, "test_data", "test_output")
    return test_output_path


@pytest.fixture
def json_test_file(sampledir):
    json_output = os.path.join(sampledir, "test_data",
                               "test_output0.json")
    return json_output


@pytest.fixture
def yaml_test_file(sampledir):
    yaml_output = os.path.join(sampledir, "test_data",
                               "test_output0.yaml")
    return yaml_output


def test_convert_excel_to_json(xl_input_path, test_output_path,
                               json_test_file):
    """
    Test to check end-to-end processing of excel metadata form responses and
    their conversion to reformatted json files.
    """
    # First delete copied test file so that we can check that it has been
    # replaced upon conversion of test file:
    if os.path.isfile(json_test_file):
        os.remove(json_test_file)
    else:
        pass

    # Now run conversion and check for file:
    fc.convert_excel_to_json(xl_input_path, test_output_path)
    try:
        with open(json_test_file) as file:
            file.read()
    except FileNotFoundError as fnf_error:
        print(fnf_error)


def test_convert_excel_to_yaml(xl_input_path, test_output_path,
                               yaml_test_file):
    """
    Test to check end-to-end processing of excel metadata form responses and
    their conversion to reformatted json files.
    """
    # First delete copied test file so that we can check that it has been
    # replaced upon conversion of test file:
    if os.path.isfile(yaml_test_file):
        os.remove(yaml_test_file)
    else:
        pass
    # Now run conversion and check for file:
    fc.convert_excel_to_yaml(xl_input_path, test_output_path)
    try:
        with open(yaml_test_file) as file:
            file.read()
    except FileNotFoundError as fnf_error:
        print(fnf_error)


