"""This converts xcel data files to JSON file types for processing."""
import pandas as pd
import openpyxl
import json
import datetime
from json import JSONEncoder
from collections import OrderedDict


def read_excel_data(filepath):
    """
    Reads in data from excel spreadsheets and holds as temporary
    pandas.DataFrame object.
    """
    temp_dataframe = pd.read_excel(filepath, engine='openpyxl')
    print("reading today's data file and committing to memory...")
    return pd.DataFrame(temp_dataframe)


def save_as_json(self):
    """
    Uses data held in pandas DataFrame to enter into form template and
    save as JSON string.
    """
    # iterate through each row to split into separate dataframes and save in
    # clean_air/data/json_data/:
    for r, row in enumerate(temp_df.iterrows()):
        print('extracting data from row ', r, ' right now...')

        # obtain data from excel file:
        self.title = row[1].values[16]  # title of the model, not the user.
        self.description = row[1].values[17]  # again, description of model.
        # self.cs = ?
        self.firstname1 = row[1].values[6]
        self.surname1 = row[1].Surname
        self.firstname2 = row[1].values[11]
        self.surname2 = row[1].values[12]
        self.north = row[1].values[42]
        self.south = row[1].values[41]
        self.east = row[1].values[43]
        self.west = row[1].values[44]
        self.chemicals = row[1].values[46]
        self.obs_level = row[1].values[19]
        self.data_source = row[1].values[20]
        self.time_range_start = row[1].values[37]
        self.time_range_end = row[1].values[38]
        self.lineage = row[1].values[50]
        self.quality = row[1].values[51]
        self.docs = row[1].values[22]

        # turn this into an OrderedDict first, then save to json:
        new_file = OrderedDict({"title": self.title,
                                "description": self.description,
                                "authors":
                                    ["firstname", self.firstname1,
                                     "surname", self.surname1,
                                     "firstname2", self.firstname2,
                                     "surname2", self.surname2],
                                "bbox":
                                    ["north", self.north,
                                     "south", self.south,
                                     "east", self.east,
                                     "west", self.west],
                                "chemical species": self.chemicals,
                                "observation level/model": self.obs_level,
                                "data source": self.data_source,
                                "time range":
                                    ["start", self.time_range_start,
                                     "end", self.time_range_end],
                                "lineage": self.lineage,
                                "quality": self.quality,
                                "docs": self.docs})

        # subclass JSONEncoder
        class DateTimeEncoder(JSONEncoder):
            # Override default method so we can extract and encode datetimes:
            def default(self, obj):
                if isinstance(obj, (datetime.date, datetime.datetime)):
                    return obj.isoformat()

        with open('../data/json_data/dailydata' + str(r) + '.json', 'w') as fp:
            json.dump(new_file, fp, indent=0, cls=DateTimeEncoder)


path = "../../../cap-sample-data/test_data/metadata_form_responses.xlsx"
temp_df = read_excel_data(path)
save_as_json(temp_df)
print("all data should be saved in separate files now...")
