"""This converts xcel data files to JSON file types for processing."""
import pandas as pd
import json
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


def save_as_json(data_object):
    """
    Uses data held in pandas DataFrame to enter into form template and
    save as JSON string.
    """
    # iterate through each row to split into separate dataframes and save in
    # clean_air/data/json_data/:
    for r, row in enumerate(temp_df.iterrows()):
        print('extracting data from row ', r, ' right now...')

        # create new temporary dataframe for each row of pandas dataframe and
        # obtain data to save as json:
        # Note: if this step is not taken then it is almost impossible to
        # extract values correctly from each row directly into a dictionary.
        df_slice = pd.DataFrame
        df_slice.title = row[1].values[16]  # title of the model, not the user.
        df_slice.description = row[1].values[17]  # again, description of model.
        df_slice.firstname1 = row[1].values[6]
        df_slice.surname1 = row[1].Surname
        df_slice.firstname2 = row[1].values[11]
        df_slice.surname2 = row[1].values[12]
        df_slice.north = row[1].values[42]
        df_slice.south = row[1].values[41]
        df_slice.east = row[1].values[43]
        df_slice.west = row[1].values[44]
        df_slice.chemicals = row[1].values[46]
        df_slice.obs_level = row[1].values[19]
        df_slice.data_source = row[1].values[20]
        df_slice.time_range_start = row[1].values[37]
        df_slice.time_range_end = row[1].values[38]
        df_slice.lineage = row[1].values[50]
        df_slice.quality = row[1].values[51]
        df_slice.docs = row[1].values[22]

        # turn this into a dictionary first for formatting purposes, then
        # save to json:
        new_file = {"title": df_slice.title,
                    "description": df_slice.description,
                    "authors":
                        {"firstname": df_slice.firstname1,
                         "surname": df_slice.surname1,
                         "firstname2": df_slice.firstname2,
                         "surname2": df_slice.surname2},
                    "bbox":
                        {"north": df_slice.north,
                         "south": df_slice.south,
                         "east": df_slice.east,
                         "west": df_slice.west},
                    "chemical species": df_slice.chemicals,
                    "observation level/model": df_slice.obs_level,
                    "data source": df_slice.data_source,
                    "time range":
                        {"start": df_slice.time_range_start,
                         "end": df_slice.time_range_end},
                    "lineage": df_slice.lineage,
                    "quality": df_slice.quality,
                    "docs": df_slice.docs}

        # now remove items from dictionary if response is nan:
        for key, value in new_file.items():
            if isinstance(value, dict):
                for k, v in value.copy().items():
                    if pd.isna(v):
                        print('removing ' + k)
                        value.pop(k, None)

        # write the dictionary above (new_file) to a json in the location
        # indicated here with the addition of a unit to indicate the number
        # of the metadata form response.
        with open('../data/json_data/dailydata' + str(r) + '.json', 'w') as fp:
            json.dump(new_file, fp, indent=2, cls=DateTimeEncoder)


xl_path = "../../../cap-sample-data/test_data/metadata_form_responses.xlsx"
temp_df = read_excel_data(filepath=xl_path)
save_as_json(data_object=temp_df)
print("all excel data should be saved in separate json files now...")

