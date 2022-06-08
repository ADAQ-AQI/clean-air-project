from datetime import date
from decimal import Decimal
import os
import folium
import pytest

from clean_air.visualise import generate_map_based_visualisations as make_maps
from clean_air.data.storage import AURNSite


@pytest.fixture()
def tmp_output_path(tmp_path):
    path = tmp_path / "tmp_output_path"
    path.mkdir()
    return path


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
def aurn_savepath(tmp_output_path):
    path = os.path.join(tmp_output_path, "AURN.html")
    return path


@pytest.fixture()
def aircraft_filepath(sampledir):
    path = os.path.join(sampledir, "aircraft",
                                     "MOCCA_M251_20190903.nc")
    return path


@pytest.fixture()
def aircraft_savepath(tmp_output_path):
    path = os.path.join(tmp_output_path, "AircraftTrack.html")
    return path


@pytest.fixture()
def boundaries_filepath(sampledir):
    path = os.path.join(sampledir, "shapefiles",
                                     "NUTS_Level_1_boundries500mgjsn.geojson")
    return path


@pytest.fixture()
def boundaries_savepath(tmp_output_path):
    path = os.path.join(tmp_output_path, "boundaries.html")
    return path


# Tests for get_AURN__sites_site_map:
def test_aurn_site_map_is_Map(aurn_data, aurn_savepath):
    """Test that AURN site data has been successfully converted to a folium
    Map object."""
    site_map = make_maps.get_aurn_sites_site_map(aurn_data, aurn_savepath)
    assert isinstance(site_map, folium.Map)


def test_aurn_site_map_has_children(aurn_data, aurn_savepath):
    """Test that children (markers) added during map processing are present in
    site_map object."""
    site_map = make_maps.get_aurn_sites_site_map(aurn_data, aurn_savepath)
    assert len(site_map._children) == 5


# Tests for get_aircraft_track_map:
def test_input_filetype_error(boundaries_filepath, tmp_output_path):
    """Test that an error is thrown when a non-netCDF filetype is used as
    input data."""
    save_path = os.path.join(tmp_output_path, "InvalidAircraftTrack.html")
    with pytest.raises(ValueError):
        make_maps.get_aircraft_track_map(boundaries_filepath, save_path)


def test_aircraft_track_map_is_Map(aircraft_filepath, aircraft_savepath):
    """Test that aircraft track data has been successfully converted to a
    folium Map object."""
    aircraft_track = make_maps.get_aircraft_track_map(aircraft_filepath, aircraft_savepath)
    assert isinstance(aircraft_track, folium.Map)


def test_aircraft_track_map_has_children(aircraft_filepath, aircraft_savepath):
    """Test that children (lines) added during map processing are present in
    site_map object."""
    # Again, this input file is fixed and static so the output should always
    # produce three children.
    aircraft_track = make_maps.get_aircraft_track_map(aircraft_filepath, aircraft_savepath)
    assert len(aircraft_track._children) == 3


# Tests for get_boundaries:
def test_boundaries_map_is_Map(boundaries_filepath, boundaries_savepath):
    """Test that boundary data has been successfully converted to a folium
    Map object."""
    boundaries = make_maps.get_boundaries(boundaries_filepath, boundaries_savepath)
    assert isinstance(boundaries, folium.Map)


def test_boundaries_map_has_children(boundaries_filepath, boundaries_savepath):
    """Test that children (lines) added during map processing are present in
    site_map object."""
    # This is always the same input file, so the number of children
    # should always be the same.
    boundaries = make_maps.get_boundaries(boundaries_filepath, boundaries_savepath)
    assert len(boundaries._children) == 2