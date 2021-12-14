#WIP . Need to add Chemical Species filters

import os
import yaml
import glob
import enum


def print_yaml_file(yaml_filename):
    """This function loads a yaml file and prints out the contents"""
    with open(f'{yaml_filename}', 'r') as file:
        contents_list = yaml.safe_load(file)
        print(contents_list)
        print(type(contents_list))


def dict_printer(dict_in):
    """This function prints out the contents of a dictionary"""
    for key, value in dict_in.items():
        print(str(key) + " => " + str(value))


class DataFilterHandler:
    """Class to handle the filtering of datasets.
    Takes a list of datasets as metadata yaml files and provides methods to filter down the datasets.
    Can return a list of filtered results on request"""

    def __init__(
            self,
            filepath='.',

    ):
        self.filepath = filepath
        self.yaml_allfiles_dict = {}
        self.filters_dict = {}

        self.__yaml_files_loader(self.filepath)
        self.__initialise_filter_builder()


    def __yaml_files_loader(self, yaml_dir_path):
        """Function to load the list of all Yaml Files from the given Directory
        returns a dictionary of key <absolute file path> , value <contents of yaml file>"""

        for filename in glob.glob(os.path.join(yaml_dir_path, "*.yaml")):
            with open(filename, 'r') as file:
                self.yaml_allfiles_dict[str(os.path.abspath(filename))] = yaml.safe_load(file)

        return self.yaml_allfiles_dict

    def yaml_extractor(self, yaml_filename):
        """This function extracts one element from the yaml dictionary, using the given yaml_filename as a key
        returns the element as a dictionary"""

        return self.yaml_allfiles_dict[str(yaml_filename)]

    def __initialise_filter_builder(self):
        """This function builds an 'in' filter list using the keys from the given yaml_allfiles dictionary
        It initialises all filters to 'in' so all datasets initially included"""

        self.filters_dict = {}

        for key, value in self.yaml_allfiles_dict.items():
            self.filters_dict[key] = True

        return self.filters_dict

    def turn_filter_on(self, key):
        """Turn the filter off for a given <yaml_filename> key
        A boolean value of True represents filter_on"""

        self.filters_dict[key] = True


    def turn_filter_off(self, key):
        """Turn the filter off for a given <yaml_filename> key
        A boolean value of False represents filter_off"""

        self.filters_dict[key] = False


    def is_match(self, key)->bool:
        """Checks if there is a match for this dataset in the filtered list of datasets.
        where the <yaml_filename> is the key"""

        return bool(self.filters_dict.get(key))

    def get_filtered_data_subsets(self)->set:
        """ returns a set of keys <yaml_filename> for the filters that are switched on"""
        set_out = set()

        return {key for key, value in self.filters_dict.items() if value}

    def get_filters_dict(self):
        return self.filters_dict

    def get_allfiles_dict(self):
        return self.yaml_allfiles_dict

