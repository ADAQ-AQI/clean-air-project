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
    default = Path(cap_sample_data.path)
    parser.addoption(
        "--sampledir",
        default=default,
        type=Path,
        help="cap-sample-data package (https://github.com/ADAQ-AQI/cap-sample-data).\n"
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
