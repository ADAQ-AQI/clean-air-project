import pytest
import os
import iris
from clean_air import data
from edr_server.core.models.metadata import CollectionMetadata
from shapely.geometry import Polygon
from datetime import datetime


class TestAircraftMetadata:
    """Integration tests for metadata extraction of 
        'Corrected_(Virkkula_et_al,_2010)_blue_(wavelength_=_467nm)_absorption_coefficient,_measured_by_TAP.' 
        data cube from flight M285"""

    @staticmethod
    @pytest.fixture
    def aircraft_cube(sampledir):
        path = os.path.join(sampledir, "aircraft", "M285_sample.nc")
        return iris.load(path)

    @staticmethod
    @pytest.fixture
    def metadata(aircraft_cube):
        cubelist_metadata = data.extract_metadata.extract_metadata(
            aircraft_cube, 'M285', ['clean_air:type=aircraft',
                                    'clean_air:aircraft_platform=MOASA',
                                    'clean_air:location=UK'], [], [], 'example aircraft')
        return cubelist_metadata

    @staticmethod
    def test_metadata_type(metadata):
        """
        GIVEN some metadata
        THEN it is an instance of CollectionMetadata
        """
        assert isinstance(metadata, CollectionMetadata)

    @staticmethod
    def test_id(metadata):
        """
        GIVEN some metadata
        THEN it has the correct id
        """
        assert metadata.id == 'M285'

    @staticmethod
    def test_title(metadata):
        """
        GIVEN some metadata
        THEN it has the correct title
        """
        assert metadata.title == 'example aircraft'

    @staticmethod
    def test_spatial_extent(metadata):
        """
        GIVEN some metadata
        THEN it has the expected spatial extent
        """
        bounds = Polygon(((-1.918275, 50.628853), (-1.918275, 51.313744), (1.943674,
                         51.313744), (1.943674, 50.628853), (-1.918275, 50.628853)))
        assert metadata.extent.spatial.bbox == bounds

    @staticmethod
    def test_temporal_extent(metadata):
        """
        GIVEN some metadata
        THEN it has the expected time bounds
        """
        assert metadata.extent.temporal.intervals[0].start == pytest.approx(datetime(2021, 3, 30, 12, 1))
        assert metadata.extent.temporal.intervals[0].end == pytest.approx(datetime(2021, 3, 30, 15, 5))

    @staticmethod
    def test_vertical_extent(metadata):
        """
        GIVEN some metadata
        THEN it has the expected vertical extent value
        """
        assert min(metadata.extent.vertical.values) == pytest.approx(53.0)
        assert max(metadata.extent.vertical.values) == pytest.approx(521.0)

    @staticmethod
    def test_keywords_length(metadata):
        """
        GIVEN some metadata
        THEN it has the correct number of keywords
        """
        assert len(metadata.keywords) == 3

    @staticmethod
    def test_outputs_length(metadata):
        """
        GIVEN some metadata
        THEN it has the correct number of output formats
        """
        assert len(metadata.output_formats) == 0

    @staticmethod
    def test_parameters_length(metadata):
        """
        GIVEN some metadata
        THEN it has the correct number of parameters
        """
        assert len(metadata.parameters) == 3

    @staticmethod
    def test_parameters_details(metadata):
        """
        GIVEN some metadata
        THEN it's parameter properties has the correct id and unit properties
        """
        assert metadata.parameters[0].id == 'Corrected_(Virkkula_et_al,_2010)_blue_(wavelength_=_467nm)_absorption_coefficient,_measured_by_TAP.'
        assert metadata.parameters[0].unit.labels == '1e-06 meter^-1'
        assert metadata.parameters[0].unit.symbol == '1e-06 m-1'

        assert metadata.parameters[1].id == 'mass_concentration_of_nitrogen_dioxide_in_air'
        assert metadata.parameters[1].unit.labels == '1e-09 meter^-3-kilogram'
        assert metadata.parameters[1].unit.symbol == '1e-09 m-3.kg'

        assert metadata.parameters[2].id == 'mass_concentration_of_sulfur_dioxide_in_air'
        assert metadata.parameters[2].unit.labels == '1e-09 meter^-3-kilogram'
        assert metadata.parameters[2].unit.symbol == '1e-09 m-3.kg'


class TestModelMetadata:
    "Integration tests for metadata extraction of a day's worth of hourly AQUM O3 data"

    @staticmethod
    @pytest.fixture
    def model_cube(sampledir):
        path = os.path.join(sampledir, "model_full", "aqum_hourly_o3_20200520.nc")
        return iris.load(path)

    @staticmethod
    @pytest.fixture
    def metadata(model_cube):
        cubelist_metadata = data.extract_metadata.extract_metadata(
            model_cube, 'O3', ['clean_air:type=gridded',
                               'clean_air:horizontal_coverage=UK',
                               'clean_air:horizontal_resolution=0.11 degree',
                               'clean_air:vertical_resolution=63 Levels'], [], ['PP'], 'AQUM Forecast')
        return cubelist_metadata

    @staticmethod
    def test_metadata_type(metadata):
        """
        GIVEN some metadata
        THEN it is an instance of CollectionMetadata
        """
        assert isinstance(metadata, CollectionMetadata)

    @staticmethod
    def test_id(metadata):
        """
        GIVEN some metadata
        THEN it has the correct id
        """
        assert metadata.id == 'O3'

    @staticmethod
    def test_title(metadata):
        """
        GIVEN some metadata
        THEN it has the correct title
        """
        assert metadata.title == 'AQUM Forecast'

    @staticmethod
    def test_spatial_extent(metadata):
        """
        GIVEN some metadata
        THEN it has the expected spatial extent
        """
        bounds = Polygon(((-238000, -184000), (856000, -184000), (856000, 1222000),
                          (-238000, 1222000)))
        assert metadata.extent.spatial.bbox == bounds

    @staticmethod
    def test_temporal_extent(metadata):
        """
        GIVEN some metadata
        THEN it has the expected time bounds
        """
        assert metadata.extent.temporal.intervals[0].start == pytest.approx(datetime(2020, 5, 20, 0, 59, 59, 999987))
        assert metadata.extent.temporal.intervals[0].end == pytest.approx(datetime(2020, 5, 21, 0, 0, 0, 0))

    @staticmethod
    def test_vertical_extent(metadata):
        """
        GIVEN some metadata
        THEN it has the expected vertical extent value
        """
        assert metadata.extent.vertical.values[0] == pytest.approx(1.65)

    @staticmethod
    def test_keywords_length(metadata):
        """
        GIVEN some metadata
        THEN it has the correct number of keywords
        """
        assert len(metadata.keywords) == 4

    @staticmethod
    def test_outputs_length(metadata):
        """
        GIVEN some metadata
        THEN it has the correct number of output formats
        """
        assert len(metadata.output_formats) == 1

    @staticmethod
    def test_parameters_length(metadata):
        """
        GIVEN some metadata
        THEN it has the correct number of parameters
        """
        assert len(metadata.parameters) == 1

    @staticmethod
    def test_parameters_details(metadata):
        """
        GIVEN some metadata
        THEN it's parameter properties has the correct id and unit properties
        """
        assert metadata.parameters[0].id == 'mass_concentration_of_ozone_in_air'
        assert metadata.parameters[0].unit.labels == '1e-09 meter^-3-kilogram'
        assert metadata.parameters[0].unit.symbol == '1e-09 m-3.kg'
