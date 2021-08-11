import os
import yaml
import glob
import enum

#Ansi code colours
BLACK = "\033[0;30m"
RED = "\033[0;31m"
GREEN = "\033[0;32m"
END = "\033[0m"


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

        # print("ALL FILES DICTIONARY\n")
        # print(self.yaml_allfiles_dict)
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

        print(f'{GREEN} Setting the filter to on for key: {key}, value: {self.filters_dict[key]}')
        print(END)

    def turn_filter_off(self, key):
        """Turn the filter off for a given <yaml_filename> key
        A boolean value of False represents filter_off"""

        self.filters_dict[key] = False

        print(f'{RED} Setting the filter to off for key: {key}, value: {self.filters_dict[key]}')
        print(END)

    def is_filter_on(self, key)->bool:
        """Checks if filter is turned on for this dataset.
        where the <yaml_filename> is the key"""

        if key in self.filters_dict.keys():
            if self.filters_dict[key]:
                #print("Filter On, ", "value =", self.filters_dict[key])
                print(f"{GREEN} Filter ON, value = {self.filters_dict[key]}  \n")
                return True
            else:
                #print("Filter Off, ", "value =", self.filters_dict[key])
                print(f"{RED} Filter Off, value = {self.filters_dict[key]}  \n")
                return False
        else:
            #print("Filter Off, No Key")
            print(f"{RED} Filter Off, No Key  \n")
            return False
        print(END)

    def get_filtered_data_subsets(self)->set:
        """ returns a set of keys <yaml_filename> for the filters that are switched on"""
        set_out = set()

        for key, value in self.filters_dict.items():
            if self.filters_dict[key]:
                set_out.add(key)

        print(set_out)
        return set_out

    #TODO: if using the turn_filter_on_contains function, will need to rewrite to get to inner lists !!

    # def turn_filter_on_contains(self, filter_key, filter_value):
    #     """Turn the filter on for any keys that contain the <filter_key> , <filter_value>"""
    #
    #     # Loop through yaml_allfiles
    #     for key, value in self.yaml_allfiles_dict.items():
    #         # loop through dict contents for each yaml file
    #         for key1, value1 in value.items():
    #             if key1 == filter_key and str(value1) == filter_value:
    #                 print(f'Filter On: Dataset is {key}, key is {key1}, value is {value1}')
    #                 self.turn_filter_on(key)

    # def turn_filter_off_contains(self, filter_key, filter_value):
    #     """Turn the filter off for any keys that contain the <filter_key> , <filter_value>"""
    #
    #     # Loop through yaml_allfiles
    #     for key, value in self.yaml_allfiles_dict.items():
    #         # loop through dict contents for each yaml file
    #         for key1, value1 in value.items():
    #             if key1 == filter_key and str(value1) == filter_value:
    #                 print(f'Filter Off: Dataset is {key}, key is {key1}, value is {value1}')
    #                 self.turn_filter_off(key)

    def get_filters_dict(self):
        return self.filters_dict

    def get_allfiles_dict(self):
        return self.yaml_allfiles_dict

    # def print_access_inner_dict(self):
    # #THINK THIS CRAZY BIT OF CODE ACTUALLY DOES WHAT I WANT :-)
    # # HAVE TWO VERSIONS SO CAN UPDATE THE FILTERS ( PLAIN & INNER VERSIONS)
    # #KEEP THIS PRINT VERSION TOO SO CAN SEE WHAT HECK IS GOING ON !!
    #     for outer_key in self.get_allfiles_dict():
    #         print('Outer Key = ', outer_key)  #outer key is the yaml filename
    #         for inner_key in self.get_allfiles_dict()[outer_key]: #Now we have a possible key/value pair (this enough for simple ones)
    #             print('   ', 'Inner Key', inner_key, 'Inner Value', self.get_allfiles_dict()[outer_key][inner_key])
    #             #Now check to see if inner key is actually a list of key/value pairs
    #             if type(self.get_allfiles_dict()[outer_key][inner_key]) is list:
    #                 for goal in self.get_allfiles_dict()[outer_key][inner_key]:
    #                     print('      ', 'List' , goal, type(goal))
    #                     #Now get the values in these mini dictionaries
    #                     if type(goal) is dict:
    #                         for key, value in goal.items():
    #                             print(str(key) + " => " + str(value))

    def print_access_inner_dict(self):
    #THINK THIS CRAZY BIT OF CODE ACTUALLY DOES WHAT I WANT :-)
    # PUT THIS IN THE FILTER HANDLER , NOT HERE ..AND HAVE TWO VERSIONS SO CAN UPDATE THE FILTERS ( PLAIN & INNER VERSIONS)
    #KEEP THIS PRINT VERSION TOO SO CAN SEE WHAT HECK IS GOING ON !!
        for outer_key in self.get_allfiles_dict():
            print('Outer Key = ', outer_key)  #outer key is the yaml filename
            for inner_key in self.get_allfiles_dict()[outer_key]: #Now we have a possible key/value pair (this enough for simple ones)
                print('   ',
                      'Inner Key', inner_key,
                      'Inner Value', self.get_allfiles_dict()[outer_key][inner_key] ,
                      'Inner Value Type', type(self.get_allfiles_dict()[outer_key][inner_key]))
                #Now check to see if inner key is actually a list of key/value pairs
                if type(self.get_allfiles_dict()[outer_key][inner_key]) is list:
                   for goal in self.get_allfiles_dict()[outer_key][inner_key]:
                       print('      ', type(self.get_allfiles_dict()[outer_key][inner_key]) , goal, type(goal))
                       #Now get the values in these mini dictionaries
                       if type(goal) is dict:
                          for key, value in goal.items():
                              print('         ', type(goal), str(key) + " => " + str(value))


    def test(self):

        # print yaml all file dict
        print("print yaml all file dict")
        dict_printer(self.yaml_allfiles_dict)
        dict_printer(self.filters_dict)

        print("now check if a filter is on")
        # now check if a filter is on:
        self.is_filter_on('/net/home/h05/clucas/PycharmProjects/CleanAirProject/clean_air/data/music.yaml')
        self.is_filter_on('/net/home/h05/clucas/PycharmProjects/CleanAirProject/clean_air/data/dance.yaml')

        # Turn a filter off
        print("Turn a filter off")
        self.turn_filter_off('/net/home/h05/clucas/PycharmProjects/CleanAirProject/clean_air/data/fruits.yaml')
        self.turn_filter_off('/net/home/h05/clucas/PycharmProjects/CleanAirProject/clean_air/data/veggies.yaml')


        self.is_filter_on('/net/home/h05/clucas/PycharmProjects/CleanAirProject/clean_air/data/fruits.yaml')
        dict_printer(self.filters_dict)

        print("Turn a filter on")
        self.turn_filter_on('/net/home/h05/clucas/PycharmProjects/CleanAirProject/clean_air/data/fruits.yaml')
        self.is_filter_on('/net/home/h05/clucas/PycharmProjects/CleanAirProject/clean_air/data/fruits.yaml')
        dict_printer(self.filters_dict)

        #self.turn_filter_off_contains('filetype','ground')
        #self.turn_filter_on_contains('sweet_potato','2')
        #self.turn_filter_on_contains('chemical_species','no2')

        print("GET FILTERED DATA SUBSETS")
        self.get_filtered_data_subsets()

    # Run main


#d = DataFilterHandler()
#d.test()

