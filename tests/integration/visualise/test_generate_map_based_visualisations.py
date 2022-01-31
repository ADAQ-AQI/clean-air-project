"""Integration tests for generate_map_based_visualisations.py."""

import os
import pytest

from clean_air.visualise import generate_map_based_visualisations as make_maps


@pytest.fixture()
def aircraft_filepath(sampledir):
    aircraft_filepath = os.path.join(sampledir, "aircraft",
                                     "MOCCA_M251_20190903.nc")
    return aircraft_filepath


@pytest.fixture()
def AURN_filepath(sampledir):
    AURN_filepath = os.path.join(sampledir, "AURN", "AURN_Site_Information.csv")
    return AURN_filepath


@pytest.fixture()
def tmp_output_path(tmp_path):
    tmp_output_path = tmp_path / "tmp_output_path"
    tmp_output_path.mkdir()
    return tmp_output_path


def test_make_AURN_map(AURN_filepath, tmp_output_path):
    save_path = os.path.join(tmp_output_path, "AURN.html")
    make_maps.get_aurn_sites_site_map(AURN_filepath, save_path)
    assert os.path.exists(save_path)


def test_make_aircraft_track_map(aircraft_filepath, tmp_output_path):
    save_path = os.path.join(tmp_output_path, "AircraftTrack.html")
    make_maps.get_aircraft_track_map(aircraft_filepath, save_path)
    assert os.path.exists(save_path)
