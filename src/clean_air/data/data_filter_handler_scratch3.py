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

QUESTION: DO WE NEED TO KNOW WHICH FILTERS ARE ON ie: pollutant, temperature etc
OR Do we just need to know if a dataset in or out regardless of why??

"""

# read and & print contents of yaml files
import os
import yaml
import glob
import enum


#class Filters(enum.Enum):
 #   'FilterOn' = True
  #  'FilterOff' = False


class DataFilterHandler:

    def __init__(
            self,
            filepath='.',
            # yaml_allfiles_dict={},
            # filters_dict={}

    ):
        self.filepath = filepath

        self.yaml_allfiles_dict = {}
        self.filters_dict = {}

        self.yaml_files_loader(self.filepath)
        self.initialise_filter_builder()


    def yaml_files_loader(self, yaml_dir_path):
        """Function to load the list of all Yaml Files from the given Directory
        returns a dictionary of key <absolute file path> , value <contents of yaml file>"""

        # self.yaml_allfiles_dict = {}

        for filename in glob.glob(os.path.join(yaml_dir_path, "*.yaml")):
            with open(filename, 'r') as file:
                self.yaml_allfiles_dict[str(os.path.abspath(filename))] = yaml.safe_load(file)

        #print("ALL FILES DICTIONARY\n")
        #print(self.yaml_allfiles_dict)
        return self.yaml_allfiles_dict

    def print_yaml_file(self, yaml_filename):

        with open(f'{yaml_filename}', 'r') as file:
            contents_list = yaml.safe_load(file)
            print(contents_list)
            print(type(contents_list))

    def dict_printer(self, dict_in):
        """This function prints out the contents of a dictionary"""
        for key, value in dict_in.items():
            print(str(key) + " => " + str(value))

    def yaml_extractor(self, yaml_filename):
        """This function extracts one element from the yaml dictionary, using the given yaml_filename as a key
        returns the element as a dictionary"""
        return self.yaml_allfiles_dict[str(yaml_filename)]

    def initialise_filter_builder(self):
        """This function builds an 'in' filter list using the keys from the given yaml_allfiles dictionary
        It initialises all filters to 'in' so all datasets initially included"""
        self.filters_dict = {}

        for key, value in self.yaml_allfiles_dict.items():
            self.filters_dict[key] = True

        #print(self.filters_dict)
        return self.filters_dict

    def turn_filter_on(self, key):
        ## Turn the filter off for a given key ( using <yaml_filename> as the key)
        ## A boolean value of True represents filter_on

        self.filters_dict[key] = True

        print(f'Setting the filter to on for key: {key}, value: {self.filters_dict[key]}')

    def turn_filter_off(self, key):
        ## Turn the filter off for a given key ( using <yaml_filename> as the key)
        ## A boolean value of False represents filter_off


        #value = self.filters_dict.get(yaml_filename)

        self.filters_dict[key] = False

        print(f'Setting the filter to off for key: {key}, value: {self.filters_dict[key]}')

    def is_filter_on(self, key):
        """Checks if filter is turned on for this dataset.
        where the <yaml_filename> is the key"""

        if key in self.filters_dict.keys():
            if self.filters_dict[key]:
                print("Filter On, ", "value =", self.filters_dict[key])
                return True
            else:
                print("Filter Off, ", "value =", self.filters_dict[key])
                return False
        else:
            print("Filter Off, No Key")
            return False

    def get_filtered_data_subsets(self):
        """ returns a list of data subsets for the filters that are switched on"""

    def test(self):

        # Load all yaml files for given directory
        # d_allfiles = self.yaml_files_loader('.')
        # print(type(self.yaml_allfiles_dict))

        # print yaml all file dict
        self.dict_printer(self.yaml_allfiles_dict)
        self.dict_printer(self.filters_dict)

        # Extract contents of yaml file into dict
        # loop through dictionary
        # extract a line and print it ( eventually this will filter it instead)
        #for key, value in self.yaml_allfiles_dict.items():
        #    ...
         #   # print(key, '->', value)
         #   print(self.yaml_extractor(key))

        # create a second dictionary that has the filename as a key and the yes/no flag as a value
        #filter_status = self.initialise_filter_builder()
        #print(filter_status)

        ##now check if a filter is on:
        self.is_filter_on('/net/home/h05/clucas/PycharmProjects/CleanAirProject/clean_air/data/music.yaml')
        self.is_filter_on('/net/home/h05/clucas/PycharmProjects/CleanAirProject/clean_air/data/dance.yaml')

        ##Turn a filter off
        self.turn_filter_off('/net/home/h05/clucas/PycharmProjects/CleanAirProject/clean_air/data/fruits.yaml')
        self.turn_filter_off('/net/home/h05/clucas/PycharmProjects/CleanAirProject/clean_air/data/veggies.yaml')

        self.is_filter_on('/net/home/h05/clucas/PycharmProjects/CleanAirProject/clean_air/data/fruits.yaml')

        self.dict_printer(self.filters_dict)


    # Run main


d = DataFilterHandler()
d.test()