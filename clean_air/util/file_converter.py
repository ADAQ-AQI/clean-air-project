"""This converts xcel data files to JSON file types for processing."""
import os
import pandas as pd
import json
import yaml
import datetime
from json import JSONEncoder


# subclass JSONEncoder
class DateTimeEncoder(JSONEncoder):
    # Override default method so we can extract and encode datetimes:
    def default(self, obj):
        if isinstance(obj, (datetime.date, datetime.datetime)):
            return obj.isoformat()


def read_excel_data(filepath):
    """
    Reads in data from excel spreadsheets and holds as temporary
    pandas.DataFrame object.
    """
    temp_dataframe = pd.read_excel(filepath, engine='openpyxl')
    print("reading today's excel data file and committing to memory...")
    return pd.DataFrame(temp_dataframe)


def slice_data(dataframe):
    """
    This function iterates through rows of a multiple-response dataframe and 
    creates a more organised dataframe for each response.  This is a necessary 
    step in the conversion between xlsx and json/yaml as it allows access to
    some variables which are otherwise inaccessible due to the structure of the
    original multi-level dataframe.
    """
    # This dataframe will collect more information than is necessary for the
    # json output, but may still be necessary for the yaml output or even for
    # use as a dataframe.
    form_responses = list()
    for r, row in enumerate(dataframe.iterrows()):
        # iterate through each row to split into separate dataframes and save
        # all to appropriate location:
        print('extracting data from row ', r, ' now...')
        form_name = pd.DataFrame
        # TODO: FIX THIS!! Name these dataframes independently so that they
        #  don't overwrite each other
        form_name.title = row[1].values[16]  # title of model, not user.
        form_name.description = row[1].values[17]  # model description.
        form_name.firstname1 = row[1].values[6]
        form_name.surname1 = row[1].Surname
        form_name.firstname2 = row[1].values[11]
        form_name.surname2 = row[1].values[12]
        form_name.north = row[1].values[42]
        form_name.south = row[1].values[41]
        form_name.east = row[1].values[43]
        form_name.west = row[1].values[44]
        form_name.chemicals = row[1].values[46].split(';')
        form_name.obs_level = row[1].values[19]
        form_name.data_source = row[1].values[20]
        form_name.time_range_start = row[1].values[37]
        form_name.time_range_end = row[1].values[38]
        form_name.lineage = row[1].values[50]
        form_name.quality = row[1].values[51]
        form_name.docs = row[1].values[22]

        # form_responses.append([data_object, r])

        form_responses.append([form_name, r])

    return form_responses


def save_as_json(data_object, r, output_location):
    """
    Uses data held in pandas DataFrame to enter into form template and
    save as JSON string.
    """
    # Pollutants(chemicals) must be organised into a useable structure before
    # being entered into the new file:
    chemicals = []
    for chem in data_object.chemicals:
        if chem != "":
            chems = {'name': chem,
                     'shortname': chem[chem.find("(") + 1:chem.find(")")],
                     'chart': "url/to/chart/image.(png|jpg|svg|etc)"}
            chemicals.append(chems)

    new_file = {"pollutants": chemicals,
                "environmentType": data_object.obs_level,
                "dateRange": {"startDate": data_object.time_range_start,
                              "endDate": data_object.time_range_end}}

    # write the dictionary above (new_file) to a json in the cap-sample-data
    # directory with the addition of a unit to indicate the number of the
    # metadata form response.
    with open(output_location + str(r) + '.json', 'w') as fp:
        json.dump(new_file, fp, indent=2, cls=DateTimeEncoder)


def save_as_yaml(data_object, r, output_location):
    """
    Uses data held in pandas DataFrame to enter into form template and
    save as yaml.
    """
    new_file = {"title": data_object.title,
                "description": data_object.description,
                "authors":
                    {"firstname": data_object.firstname1,
                     "surname": data_object.surname1,
                     "firstname2": data_object.firstname2,
                     "surname2": data_object.surname2},
                "bbox":
                    {"north": data_object.north,
                     "south": data_object.south,
                     "east": data_object.east,
                     "west": data_object.west},
                "chemical species": data_object.chemicals,
                "observation level/model": data_object.obs_level,
                "data source": data_object.data_source,
                "time range":
                    {"start": data_object.time_range_start,
                     "end": data_object.time_range_end},
                "lineage": data_object.lineage,
                "quality": data_object.quality,
                "docs": data_object.docs}

    # now remove names from dictionary if response is nan and convert
    # datetimes to isoformat:
    for key, value in new_file.items():
        if isinstance(value, dict):
            for k, v in value.copy().items():
                # Check sub-dicts for nans and remove nan elements
                if pd.isna(v):
                    value.pop(k, None)
                # Check sub-dicts for datetimes and convert to str(isoformat)
                if isinstance(v, (datetime.date, datetime.datetime)):
                    value[k] = v.isoformat()

    # write the dictionary above (new_file) to a yaml in the cap-sample-data
    # directory with the addition of a unit to indicate the number of the
    # metadata form response.
    with open(output_location + str(r) + '.yaml', 'w') as fp:
        yaml.dump(new_file, fp,
                  indent=2, default_flow_style=False, sort_keys=False)


def convert_excel_to_json(filepath, output_location):
    """
    Convert excel metadata files to required json output format.
    """
    temp_dataframe = read_excel_data(filepath)
    sliced_dataframes = slice_data(temp_dataframe)
    for df in sliced_dataframes:
        save_as_json(data_object=df[0], r=df[1],
                     output_location=output_location)


def convert_excel_to_yaml(filepath, output_location):
    """
    Convert excel metadata files to required yaml output format.
    """
    temp_dataframe = read_excel_data(filepath)
    sliced_dataframes = slice_data(temp_dataframe)
    for df in sliced_dataframes:
        save_as_yaml(data_object=df[0], r=df[1],
                     output_location=output_location)


# NOTE: The lines below are only for quick testing and can be removed as soon
# as I have all the data I need to complete the proper tests (and have
# completed them).
xl_path = "../../../cap-sample-data/test_data/metadata_form_responses.xlsx"
json_path = "../visualise/assets/json_data/dailymetadata"
yaml_path = "../visualise/assets/yaml_data/dailymetadata"
convert_excel_to_json(filepath=xl_path, output_location=json_path)
convert_excel_to_yaml(filepath=xl_path, output_location=yaml_path)
