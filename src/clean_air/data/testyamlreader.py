# readand & print contents of yaml files
import os

import yaml
import glob

def yaml_files_loader(yaml_dir_path):

    #Function to load the list of all Yaml Files from the given Directory
    #:return:



    #configs = list(map(lambda x: yaml.safe_load(open(x)), glob.glob("*.yaml")))
    for filename in glob.glob(os.path.join(yaml_dir_path, "*.yaml")):  #List of all filenames that match the *.yaml pattern unix/ windows function
        with open(filename, 'r') as file:
            my_data = yaml.safe_load(file)
            #Store all my data somewhere

            print(os.path.abspath(filename), filename, my_data)


    #print(configs)
    return filename


def print_yaml_file_contents(yaml_filename):

    #with open(r'E:\data\fruits.yaml') as file:
    with open(f'{yaml_filename}', 'r') as file:

        fruits_list = yaml.safe_load(file)
        print(fruits_list)
        print(type(fruits_list))


    #for config in configs:

    #    for item in config:

    #    print
    #    item

#print_yaml_file_contents('fruits.yaml')

#print_yaml_file_contents('music.yaml')

yaml_files_loader('.')
#yaml_files_loader("../")


