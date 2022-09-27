"""
Configuration for pytest - this file is automatically executed on startup.
"""

from pathlib import Path
import cap_sample_data
import pytest


# Hooks

def pytest_addoption(parser):
    """
    Register custom command-line arguments that can be passed to `pytest`
    """
    # NOTE: The root path as defined in the cap_sample_data/__init__.py is
    # cap_sample_data/sample_data
    root = cap_sample_data.path
    default = root
    parser.addoption(
        "--sampledir",
        default=default,
        type=Path,
        help="cap-sample-data package "
             "(https://github.com/ADAQ-AQI/cap-sample-data).\n"
        "Default: `cap-sample-data` as a sibling of this repository."
    )


def pytest_report_header(config):
    """
    Add extra information to the report header
    """
    sampledir = config.getoption("sampledir")
    return f"--sampledir: {sampledir.absolute()}"


# Fixtures

@pytest.fixture(scope="session")
def sampledir(pytestconfig):
    """
    Fixture to conveniently access the sample data directory
    """
    return pytestconfig.getoption("sampledir")
