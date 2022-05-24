import os
import folium
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
def AURN_savepath(tmp_output_path):
    AURN_savepath = os.path.join(tmp_output_path, "AURN.html")
    return AURN_savepath


@pytest.fixture()
def aircraft_filepath(sampledir):
    aircraft_filepath = os.path.join(sampledir, "aircraft",
                                     "MOCCA_M251_20190903.nc")
    return aircraft_filepath


@pytest.fixture()
def aircraft_savepath(tmp_output_path):
    aircraft_savepath = os.path.join(tmp_output_path, "AircraftTrack.html")
    return aircraft_savepath


@pytest.fixture()
def boundaries_filepath(sampledir):
    boundaries_filepath = os.path.join(sampledir, "shapefiles",
                                     "NUTS_Level_1_boundries500mgjsn.geojson")
    return boundaries_filepath


@pytest.fixture()
def boundaries_savepath(tmp_output_path):
    boundaries_savepath = os.path.join(tmp_output_path, "boundaries.html")
    return boundaries_savepath


# Tests for get_AURN__sites_site_map:
def test_AURN_site_map_is_Map(AURN_filepath, AURN_savepath):
    """Test that AURN site data has been successfully converted to a folium
    Map object."""
    site_map = make_maps.get_aurn_sites_site_map(AURN_filepath, AURN_savepath)
    assert isinstance(site_map, folium.Map)


def test_AURN_site_map_has_children(AURN_filepath, AURN_savepath):
    """Test that children (markers) added during map processing are present in
    site_map object."""
    # This is always the same input file, so the number of markers generated
    # should always be the same.
    site_map = make_maps.get_aurn_sites_site_map(AURN_filepath, AURN_savepath)
    assert len(site_map._children) == 275


# Tests for get_aircraft_track_map:
def test_input_filetype_error(AURN_filepath, tmp_output_path):
    """Test that an error is thrown when a non-netCDF filetype is used as
    input data."""
    save_path = os.path.join(tmp_output_path, "InvalidAircraftTrack.html")
    with pytest.raises(ValueError):
        make_maps.get_aircraft_track_map(AURN_filepath, save_path)


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