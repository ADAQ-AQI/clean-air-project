"""
Load a dictionary
"""

def my_dict_loader():
     with open('data/fruits.yaml', 'r') as file:
    #with open(f'{yaml_filename}', 'r') as file:
        fruits_list = yaml.safe_load(file)
        print(fruits_list)
        print(type(fruits_list))

my_dict_loader