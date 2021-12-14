import os
import pytest

from clean_air.data.metadata_handler import MetadataHandler, dict_printer
from clean_air.data.data_filter_handler import print_yaml_file

#NB: These tests use the test data :
# station_metadata.yaml
# metadata_one.yaml
# antartic_metedata.yaml


#('METADATA TEST', 'Build list of all metadata files and turn filters to on by default \n')
@pytest.fixture()
def mh(sampledir):
    mh = MetadataHandler(os.path.join(sampledir,"test_data"))
    dict_printer(mh.filters_dict)
    return mh

@pytest.fixture()
def metadata_filepath():
    filepath = os.path.join("net","home","h05","clucas","PycharmProjects","CleanAirProject","clean_air","data")
    return filepath


@pytest.fixture()
def station_metadata_filepath(sampledir):
    #filepath = os.path.join('/', 'net', 'home', 'h05', 'clucas', 'PycharmProjects', 'CleanAirProject', 'tests', 'unit','data', 'station_metadata.yaml')
    #filepath = '/net/home/h05/clucas/PycharmProjects/CleanAirProject/tests/unit/data/station_metadata.yaml'
    #return filepath
    filepath = os.path.join(sampledir, "test_data", "station_metadata.yaml")
    return filepath

@pytest.fixture()
def metaone_filepath(sampledir):
    #filepath = os.path.join('/','net','home','h05','clucas','PycharmProjects','CleanAirProject','tests','unit','data', 'metaone.yaml')
    #filepath = '/net/home/h05/clucas/PycharmProjects/CleanAirProject/tests/unit/data/metaone.yaml'
    #return filepath
    filepath = os.path.join(sampledir, "test_data", "metaone.yaml")
    return filepath

@pytest.fixture()
def antartica_filepath(sampledir):
    #filepath = os.path.join('/','net','home','h05','clucas','PycharmProjects','CleanAirProject','tests','unit','data', 'metaone.yaml')
    #filepath = '/net/home/h05/clucas/PycharmProjects/CleanAirProject/tests/unit/data/metaone.yaml'
    #return filepath
    filepath = os.path.join(sampledir, "test_data", "antartica_metadata.yaml")
    return filepath

def checkDictForFilename(dict, filepath):
    found = False
    for key in dict.keys():
        keysplit = key.rsplit('/', 1)[1]

        filepathsplit = filepath.rsplit('/', 1)[1]
        if keysplit == filepathsplit:
            print("Key:", key, " Keysplit:", keysplit, " Filepathsplit:", filepathsplit)
            found = True
    assert found == True # Filename must be in dictionary
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
    assert found == True # Filename must be in dictionary
    return found

def is_filter_on(dict, filepath)->bool:
    ret_type = False
    found = False
    for key in dict.keys():
        keysplit = key.rsplit('/', 1)[1]

        filepathsplit = filepath.rsplit('/', 1)[1]
        if (keysplit == filepathsplit) and (found == False):
            print("Is Filter On :""Key:", key, " Keysplit:", keysplit, " Filepathsplit:", filepathsplit, "Value:",dict.get(key))
            found = True
            ret_type = dict.get(key)

    print ("Returning:", ret_type, "Found in list: ", found)
    return ret_type

#try:
#    checkFiltersDictForFilename(filepath)
#except AssertionError as msg:
#    print(msg)

#TEST 1: 
def test_build_filters(station_metadata_filepath, metaone_filepath, antartica_filepath, mh):
    #Make sure all set to true at start.

    checkDictForFilename(mh.filters_dict, station_metadata_filepath)
    checkDictForFilename(mh.filters_dict, metaone_filepath)
    checkDictForFilename(mh.filters_dict, antartica_filepath)


def test_all_filters_true(station_metadata_filepath, metaone_filepath, mh):

    assert getDictValueOfGivenFilename(mh.filters_dict, station_metadata_filepath) == True
    assert getDictValueOfGivenFilename(mh.filters_dict, metaone_filepath) == True

def test_turn_off_obs_level_ground(station_metadata_filepath, mh):
    #TEST 2: Obs Level:GROUND', ' Turn off all datasets containing Ground')

    mh.set_observation_level_filter(False, 'ground')
    assert getDictValueOfGivenFilename(mh.filters_dict, station_metadata_filepath) == False


def test_turn_on_obs_level_ground(station_metadata_filepath, mh):
    #Test 3 : Obs Level:GROUND', ' Turn on all datasets containing Ground')

    mh.set_observation_level_filter(True, 'ground')
    assert getDictValueOfGivenFilename(mh.filters_dict, station_metadata_filepath) == True


def test_turn_off_source_air_quality(station_metadata_filepath, mh):
    #Test 4 : Data Source:AIR_QUALITY', ' Turn off all datasets containing Air Quality' )
    mh.set_data_source_filter(False, 'air_quality')
    assert getDictValueOfGivenFilename(mh.filters_dict, station_metadata_filepath) == False

def test_turn_on_source_air_quality(station_metadata_filepath, mh):
    #Test 5 : Data Source:AIR_QUALITY', ' Turn on all datasets containing Air Quality')
    mh.set_data_source_filter(True, 'air_quality')
    assert getDictValueOfGivenFilename(mh.filters_dict, station_metadata_filepath) == True

def test_filtered_dataset_list_contents(station_metadata_filepath, metaone_filepath, mh):
    #Test 6: Get back a list of filtered datasets

    checkSetForFilename(mh.get_filtered_data_subsets(), metaone_filepath)
    checkSetForFilename(mh.get_filtered_data_subsets(), station_metadata_filepath)

    #print(mh.filters_dict.keys())

def test_filter_by_point_location(station_metadata_filepath, metaone_filepath, mh):
    #Test 7: Filter files by a given point location

    mh.set_location_filter(0.0984, 51.5138)

    assert is_filter_on(mh.filters_dict, metaone_filepath) == False
    assert is_filter_on(mh.filters_dict, station_metadata_filepath) == True