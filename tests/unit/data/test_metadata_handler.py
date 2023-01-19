import os
import pytest

from clean_air.data.metadata_handler import MetadataHandler


@pytest.fixture()
def mh(sampledir):
    return MetadataHandler(os.path.join(sampledir, "test_data"))


@pytest.fixture()
def station_metadata_filepath(sampledir):
    return os.path.join(sampledir, "test_data", "station_metadata.yaml")


@pytest.fixture()
def metaone_filepath(sampledir):
    return os.path.join(sampledir, "test_data", "metaone.yaml")


@pytest.fixture()
def antartica_filepath(sampledir):
    return os.path.join(sampledir, "test_data", "antartica_metadata.yaml")


def checkDictForFilename(dict, filepath):
    found = False
    for key in dict.keys():
        keysplit = key.rsplit('/', 1)[1]
        filepathsplit = filepath.rsplit('/', 1)[1]
        if keysplit == filepathsplit:
            print("Key:", key, " Keysplit:", keysplit, " Filepathsplit:", filepathsplit)
            found = True
    return found


def getDictValueOfGivenFilename(dict, filepath):

    for key in dict.keys():
        keysplit = key.rsplit('/', 1)[1]

        filepathsplit = filepath.rsplit('/', 1)[1]
        if keysplit == filepathsplit:
            print("Key:", key, " Keysplit:", keysplit, " Filepathsplit:", filepathsplit)
            value = dict.get(key)
    return value


def checkSetForFilename(this_set, filepath):
    found = False
    for key in this_set:
        keysplit = key.rsplit('/', 1)[1]

        filepathsplit = filepath.rsplit('/', 1)[1]
        if keysplit == filepathsplit:
            print("Key:", key, " Keysplit:", keysplit, " Filepathsplit:", filepathsplit)
            found = True
    return found


def is_filter_on(dict, filepath) -> bool:
    ret_type = False
    found = False
    for key in dict.keys():
        keysplit = key.rsplit('/', 1)[1]

        filepathsplit = filepath.rsplit('/', 1)[1]
        if (keysplit == filepathsplit) and (found == False):
            found = True
            ret_type = dict.get(key)

    return ret_type


def test_build_filters(station_metadata_filepath, metaone_filepath, antartica_filepath, mh):
    # Make sure all filepaths are in metadata handler dictionary

    assert checkDictForFilename(mh.filters_dict, station_metadata_filepath) == True
    assert checkDictForFilename(mh.filters_dict, metaone_filepath) == True
    assert checkDictForFilename(mh.filters_dict, antartica_filepath) == True


def test_all_filters_true(station_metadata_filepath, metaone_filepath, mh):
    # Make sure all filters are set to true at start

    assert getDictValueOfGivenFilename(mh.filters_dict, station_metadata_filepath) == True
    assert getDictValueOfGivenFilename(mh.filters_dict, metaone_filepath) == True


def test_turn_off_obs_level_ground(station_metadata_filepath, mh):
    # Obs Level:GROUND
    # Turn off all datasets containing Ground

    mh.set_observation_level_filter(False, 'ground')
    assert getDictValueOfGivenFilename(mh.filters_dict, station_metadata_filepath) == False


def test_turn_on_obs_level_ground(station_metadata_filepath, mh):
    # Obs Level:GROUND
    # Turn on all datasets containing Ground

    mh.set_observation_level_filter(True, 'ground')
    assert getDictValueOfGivenFilename(mh.filters_dict, station_metadata_filepath) == True


def test_turn_off_source_air_quality(station_metadata_filepath, mh):
    # Data Source:AIR_QUALITY
    # Turn off all datasets containing Air Quality

    mh.set_data_source_filter(False, 'air_quality')
    assert getDictValueOfGivenFilename(mh.filters_dict, station_metadata_filepath) == False


def test_turn_on_source_air_quality(station_metadata_filepath, mh):
    # Data Source:AIR_QUALITY
    # Turn on all datasets containing Air Quality

    mh.set_data_source_filter(True, 'air_quality')
    assert getDictValueOfGivenFilename(mh.filters_dict, station_metadata_filepath) == True


def test_filtered_dataset_list_contents(station_metadata_filepath, metaone_filepath, mh):
    # Get back a list of filtered datasets

    assert checkSetForFilename(mh.get_filtered_data_subsets(), metaone_filepath) == True
    assert checkSetForFilename(mh.get_filtered_data_subsets(), station_metadata_filepath) == True
    assert checkSetForFilename(mh.get_filtered_data_subsets(), station_metadata_filepath) == True


def test_filter_by_point_location(station_metadata_filepath, metaone_filepath, mh):
    # Filter files by a given point location

    mh.set_location_filter(0.0984, 51.5138)
    assert is_filter_on(mh.filters_dict, metaone_filepath) == False
    assert is_filter_on(mh.filters_dict, station_metadata_filepath) == True
