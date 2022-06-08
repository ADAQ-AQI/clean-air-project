"""Integration tests for generate_map_based_visualisations.py."""
from datetime import date
from decimal import Decimal
import os
import pytest

from clean_air.visualise import generate_map_based_visualisations as make_maps
from clean_air.data.storage import AURNSite


@pytest.fixture()
def aircraft_filepath(sampledir):
    aircraft_filepath = os.path.join(sampledir, "aircraft",
                                     "MOCCA_M251_20190903.nc")
    return aircraft_filepath


@pytest.fixture()
def aurn_data():
    test_sites = [AURNSite(
        "Aberdeen", "ABD", "URBAN_BACKGROUND", Decimal("57.15736000"), Decimal("-2.094278000"),
        date(1999, 9, 18), None,
        ["CO", "NO", "NO2", "NOx", "O3", "PM10", "PM2p5", "SO2", "nvPM10", "nvPM2p5", "vPM10", "vPM2p5"]),
        AURNSite(
        "Aberdeen_Union_St_Roadside", "ABD7", "URBAN_TRAFFIC", Decimal("57.14455500"), Decimal("-2.106472000"),
        date(2008, 1, 1), None, ["NO", "NO2", "NOx"]),
        AURNSite(
        "Aberdeen_Wellington_Road", "ABD8", "URBAN_TRAFFIC", Decimal("57.13388800"), Decimal("-2.094198000"),
        date(2016, 2, 9), None, ["NO", "NO2", "NOx"])]
    return test_sites


@pytest.fixture()
def tmp_output_path(tmp_path):
    tmp_output_path = tmp_path / "tmp_output_path"
    tmp_output_path.mkdir()
    return tmp_output_path


def test_make_aurn_map(aurn_data, tmp_output_path):
    save_path = os.path.join(tmp_output_path, "AURN.html")
    make_maps.get_aurn_sites_site_map(aurn_data, save_path)
    assert os.path.exists(save_path)


def test_make_aircraft_track_map(aircraft_filepath, tmp_output_path):
    save_path = os.path.join(tmp_output_path, "AircraftTrack.html")
    make_maps.get_aircraft_track_map(aircraft_filepath, save_path)
    assert os.path.exists(save_path)
