"""
Integration tests for test_render_map.py
"""

# NOTE: We currently can't render actual images using the technology we have
# as we need a server to be able to see the images.  As that's the case,
# integration tests for this module will be put on hold until we have a server
# to render images on and test.
import os
import pathlib
import pytest

from clean_air.util import file_converter as fc
from clean_air.visualise import generate_map_based_visulisations as make_maps


@pytest.fixture()
def aircraft_filepath(sampledir):
    aircraft_filepath = os.path.join(sampledir, "obs", "ABD_2015.csv")
    return aircraft_filepath


@pytest.fixture()
def aircraft_track(aircraft_filepath):
    aircraft_track = fc.generate_dataframe(aircraft_filepath)
    return aircraft_track


@pytest.fixture()
def AURN_filepath():
    AURN_filepath = os.path.join("net", "home", "h05", "clucas",
                                 "CAF_Example_Data_Files", "AURN_Observations",
                                 "AURN_Site_Information.csv")
    return AURN_filepath


def test_make_AURN_maps(site_data):
    make_maps.get_aurn__sites_map(site_data)


def test_make_aircraft_track_map(aircraft_track):
    make_maps.get_aircraft_track_map(aircraft_track)


# get_aircraft_track_map(data.get_coords1())

