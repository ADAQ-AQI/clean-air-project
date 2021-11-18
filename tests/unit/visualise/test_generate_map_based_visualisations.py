import os
import pytest

from clean_air.visualise import generate_map_based_visualisations as make_maps


@pytest.fixture()
def tmp_output_path(tmp_path):
    tmp_output_path = tmp_path / "tmp_output_path"
    tmp_output_path.mkdir()
    return tmp_output_path


@pytest.fixture()
def AURN_filepath(sampledir):
    AURN_filepath = os.path.join(sampledir, "AURN",
                                 "AURN_Site_Information.csv")
    return AURN_filepath


@pytest.fixture()
def aircraft_filepath(sampledir):
    aircraft_filepath = os.path.join(sampledir, "aircraft",
                                     "MOCCA_M251_20190903.nc")
    return aircraft_filepath


@pytest.fixture()
def AURN_site_map(AURN_filepath, tmp_output_path):
    save_path = os.path.join(tmp_output_path, "AURN.html")
    site_map = make_maps.get_aurn__sites_site_map(AURN_filepath, save_path)
    return site_map


@pytest.fixture()
def aircraft_track(aircraft_filepath, tmp_output_path):
    save_path = os.path.join(tmp_output_path, "AircraftTrack.html")
    aircraft_track = make_maps.get_aircraft_track_map(aircraft_filepath,
                                                      save_path)
    return aircraft_track


# Tests for get_AURN__sites_site_map:
def test_AURN_site_map_is_Map(AURN_site_map):
    """Test that AURN site data has been successfully converted to a folium
    Map object."""
    assert AURN_site_map._name == 'Map'


def test_AURN_site_map_has_children(AURN_site_map):
    """Test that children (markers) added during map processing are present in
    site_map object."""
    # This is always the same input file, so the number of markers generated
    # should always be the same.
    assert len(AURN_site_map._children) == 275


# Tests for get_aircraft_track_map:
def test_input_filetype_error(AURN_filepath, tmp_output_path):
    """Test that an error is thrown when a non-netCDF filetype is used as
    input data."""
    save_path = os.path.join(tmp_output_path, "InvalidAircraftTrack.html")
    with pytest.raises(ValueError):
        make_maps.get_aircraft_track_map(AURN_filepath, save_path)


def test_aircraft_track_map_is_Map(aircraft_track):
    """Test that aircraft track data has been successfully converted to a
    folium Map object."""
    assert aircraft_track._name == 'Map'


def test_aircraft_track_map_has_children(aircraft_track):
    """Test that children (lines) added during map processing are present in
    site_map object."""
    # Again, this input file is fixed and static so the output should always
    # produce three children.
    assert len(aircraft_track._children) == 3
