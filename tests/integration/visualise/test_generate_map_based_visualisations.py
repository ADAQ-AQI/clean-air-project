"""Integration tests for generate_map_based_visualisations.py."""

import os
import pathlib
import pytest

from clean_air.util import file_converter as fc
from clean_air.visualise import generate_map_based_visualisations as make_maps


@pytest.fixture()
def aircraft_filepath(sampledir):
    aircraft_filepath = os.path.join(sampledir, "aircraft",
                                     "MOCCA_M251_20190903.nc")
    return aircraft_filepath


# @pytest.fixture()
# def aircraft_track(aircraft_filepath):
#     aircraft_track = fc.generate_dataframe(aircraft_filepath)
#     return aircraft_track


@pytest.fixture()
def AURN_filepath():
    AURN_filepath = os.path.join("net", "home", "h05", "clucas",
                                 "CAF_Example_Data_Files", "AURN_Observations",
                                 "AURN_Site_Information.csv")
    return AURN_filepath


def test_make_AURN_maps(site_data):
    make_maps.get_aurn__sites_map(site_data)


def test_make_aircraft_track_map(aircraft_filepath):
    make_maps.get_aircraft_track_map(aircraft_filepath)


# get_aircraft_track_map(data.get_coords1())

