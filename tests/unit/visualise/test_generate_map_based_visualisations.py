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
    path = os.path.join(sampledir, "aircraft", "MOCCA_M251_20190903.nc")
    return path


@pytest.fixture()
def aircraft_savepath(tmp_output_path):
    path = os.path.join(tmp_output_path, "AircraftTrack.html")
    return path


@pytest.fixture()
def boundaries_filepath(sampledir):
    path = os.path.join(sampledir, "shapefiles",  "NUTS_Level_1_boundries500mgjsn.geojson")
    return path


@pytest.fixture()
def boundaries_savepath(tmp_output_path):
    path = os.path.join(tmp_output_path, "boundaries.html")
    return path


class TestAURNSites:
    """Test for AURN site map functionality."""
    @pytest.yield_fixture(autouse=True)
    def setup_class(self, aurn_data, aurn_savepath):
        """SET UP all inputs to tests."""
        self.site_map = make_maps.get_aurn_sites_site_map(aurn_data, aurn_savepath)

    def test_aurn_site_map_is_Map(self):
        """
        GIVEN a set of AURN site data,
        WHEN the function make_maps.get_aurn_sites_site_map() is used with the data,
        THEN the result will be a folium Map object.
        """
        assert isinstance(self.site_map, folium.Map)

    def test_aurn_site_map_has_children(self):
        """
        GIVEN a set of AURN site data,
        WHEN the function make_maps.get_aurn_sites_site_map() is used with the data,
        THEN the resulting site map will have five markers, known as children, added during the mapping process.
        """
        assert len(self.site_map._children) == 5


class TestAircraftTrackMap:
    """Tests for get_aircraft_track_map()"""
    @pytest.yield_fixture(autouse=True)
    def setup_class(self, aircraft_filepath, aircraft_savepath):
        """SET UP all inputs to tests."""
        self.aircraft_track = make_maps.get_aircraft_track_map(aircraft_filepath, aircraft_savepath)

    def test_aircraft_track_map_is_Map(self):
        """
        GIVEN an aircraft track dataset,
        WHEN function make_maps.get_aircraft_track_map() is used with the data,
        THEN the result is a folium Map object.
        """
        assert isinstance(self.aircraft_track, folium.Map)

    def test_aircraft_track_map_has_children(self):
        """
        GIVEN an aircraft track dataset,
        WHEN function make_maps.get_aircraft_track_map() is used with the data,
        THEN the resulting site map will have three lines, known as children, added during the mapping process.
        """
        # Again, this input file is fixed and static so the output should always produce three children.
        assert len(self.aircraft_track._children) == 3

    def test_input_filetype_error(self, boundaries_filepath, tmp_output_path):
        """
        GIVEN an invalid input filetype (.html in this case),
        WHEN function make_maps.get_aircraft_track_map() is used with the data,
        THEN a ValueError is raised.
        """
        save_path = os.path.join(tmp_output_path, "InvalidAircraftTrack.html")
        with pytest.raises(ValueError):
            make_maps.get_aircraft_track_map(boundaries_filepath, save_path)


class TestGetBoundaries:
    """Tests for get_boundaries()"""
    @pytest.yield_fixture(autouse=True)
    def setup_class(self, boundaries_filepath, boundaries_savepath):
        """SET UP all inputs to tests."""
        self.boundaries = make_maps.get_boundaries(boundaries_filepath, boundaries_savepath)

    def test_boundaries_map_is_Map(self):
        """
        GIVEN a shapefile representing the boundaries of a dataset,
        WHEN function make_maps.get_boundaries() is used with the dataset,
        THEN the result will be a folium Map object.
        """
        assert isinstance(self.boundaries, folium.Map)

    def test_boundaries_map_has_children(self):
        """
        GIVEN a shapefile representing the boundaries of a dataset,
        WHEN function make_maps.get_boundaries() is used with the dataset,
        THEN the resulting site map will have two lines, known as children, added during the mapping process.
        """
        # This is always the same input file, so the number of children should always be the same.
        assert len(self.boundaries._children) == 2

