# Class to handle the filtering of datasets.
# Takes a list of datasets and uses the parameters provided  (in variety of combinations) to filter down the datasets.
# Then return a list of filtered results


"""
Development notes for this class:
constructor
reads all files into a memory object . Have flag to include/ exclude
takes one arg : path to metadata yaml files

yaml files have path to data

filter needs to know where folder is

have method apply filter : sets flag to in
method unapply filter: set flags to out

expect will need a method to follow path to yaml file directory and load up a list of all yaml files in the directory

Yaml file. ( text/ or handle as Json files)
The yaml file represents in txt basic data structures such as strings, lists, key/value pairs.
Read the yaml file and create state.

There are python functions to load yaml files as dictionaries. Can then have method to look through dictionary and check if it matches filter.

*probably going to be using the data_subset.py file

"""

# readand & print contents of yaml files
import os
import yaml
import glob


def yaml_files_loader(yaml_dir_path):
    """Function to load the list of all Yaml Files from the given Directory
    :return: dictionary of key <absolute file path> , value <contents of yaml file>"""

    yaml_allfiles_dict = {}

    # configs = list(map(lambda x: yaml.safe_load(open(x)), glob.glob("*.yaml")))

    for filename in glob.glob(os.path.join(yaml_dir_path,
                                           "*.yaml")):  # List of all filenames that match the *.yaml pattern unix/ windows function
        with open(filename, 'r') as file:
            my_data = yaml.safe_load(file)
            # print(os.path.abspath(filename), filename, my_data)
            yaml_allfiles_dict[str(os.path.abspath(filename))] = my_data  # make a dictionary of all my files & contents

    return yaml_allfiles_dict


def print_yaml_file(yaml_filename):
    with open(f'{yaml_filename}', 'r') as file:
        fruits_list = yaml.safe_load(file)
        print(fruits_list)
        print(type(fruits_list))


def dict_printer(d):
    """This function prints out the contents of a dictionary"""
    for key, value in d.items():
        print(str(key) + " => " + str(value))


def yaml_extractor(yaml_filename, yaml_allfiles_dict):
    """This function extracts one element from the yaml dictionary, using the given yaml_filename as a key"""
    dict1 = yaml_allfiles_dict[str(yaml_filename)]
    return dict1


def initialise_filter_builder(yaml_allfiles_dict):
    """This function builds an 'in' filter list using the keys from the given yaml_allfiles dictionary
    It initialises all filters to 'in' so all datasets initially included"""
    initial_filter_dict = {}

    for key, value in yaml_allfiles_dict.items():
        ...
        # print(key, '->', value)
        # print(yaml_extractor(key, d_allfiles))

        # Want to have initial_filter_dict = ( current Key: True) as the dict in here.
        # d = {'key': 'value'}
        # print(d)
        # {'key': 'value'}
        # d['mynewkey'] = 'mynewvalue'
        # print(d)
        # {'key': 'value', 'mynewkey': 'mynewvalue'}

        initial_filter_dict[key] = True
        print(initial_filter_dict)
    return initial_filter_dict


def main_func():
    ##test run my functions##

    # print_yaml_file('fruits.yaml')
    # print_yaml_file('music.yaml')

    # Load all yaml files for given directory
    d_allfiles = yaml_files_loader('.')
    # yaml_files_loader("../")

    # print yaml all file dict
    dict_printer(d_allfiles)

    # Extract contents of yaml file into dict
    # loop through dictionary
    # extract a line and print it ( eventually this will filter it instead)

    for key, value in d_allfiles.items():
        ...
        # print(key, '->', value)
        print(yaml_extractor(key, d_allfiles))

    # create a second dictionary that has the filename as a key and the yes/no flag as a value
    filter_dict = initialise_filter_builder(d_allfiles)
    print(filter_dict)


# Run main
main_func()

