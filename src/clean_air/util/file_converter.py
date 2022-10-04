"""
This converts input metadata and data files to selected file types for
processing.  For example, for converting metadata files from excel to either
'json' or 'yaml':
>> metadata_file = clean_air.util.file_converter.MetadataForm(input_filepath,
output_directory_path)
>> metadata_file.convert_excel(output_filetype)

To convert data files there are two methods; if you want to convert a netCDF
to a CSV:
>> data_file = clean_air.util.file_converter.DataFile(input_filepath,
output_directory_path)
>> data_file.convert_netcdf()

Or to convert a CSV to a netCDF:
>> data_file = clean_air.util.file_converter.DataFile(input_filepath,
output_directory_path)
>> data_file.convert_csv()

You can also use this module to access a pandas.DataFrame extracted from
either an excel, netcdf or csv input file, for example:
>> dataframe = clean_air.util.file_converter.generate_dataframe(filepath)
"""

import os
from typing import List

import pandas as pd
import json
import yaml
import datetime
import xarray as xr
from json import JSONEncoder

from clean_air.util import conversion_lists

# subclass JSONEncoder
from pandas.errors import ParserError


class DateTimeEncoder(JSONEncoder):
    # Override default method so that we can extract and encode datetimes:
    def default(self, obj):
        if isinstance(obj, (datetime.date, datetime.datetime)):
            return obj.isoformat()


def csv_reformatter(filepath) -> pd.DataFrame:
    """This function uses a template to reformat AURN-style CSV metadata
    files into a fixed format that we can then very easily read into a
    pandas dataframe (ready for conversion to netcdf files)."""
    # rules for csv format:
    # - header line (column names) must be on row 4 of file (top row is 0)
    # - column names must be standard python strings.

    # This is a dictionary containing names to look for and what to convert
    # them into.
    field_names = conversion_lists.csv_convert()
    # Now that we have some things to look for we can read the header row of
    # the file to pull out the applicable column names:
    data_names = pd.read_csv(filepath, nrows=1, skiprows=4, delimiter=',')

    # We need to narrow down our own list of column names by matching them
    # to those we are looking for:
    good_names = []
    bad_names = []   # This contains any extra fields (not in list above)
    for name in data_names.columns:
        if name in (field_names.keys() or field_names.values()):
            good_names.append(name)
        else:
            bad_names.append(name)

    # And then we need to produce a shorter conversion list containing only
    # the conversions required in this file.  This part also ensures that
    # only readable (user-friendly) names are presented in the converted
    # file:
    conversion_list = {}
    for k, v in field_names.items():
        if (k or v) in good_names:
            conversion_list[k] = v

    # Now that we have all these relevant lists, we can use them to read the
    # file into a dataframe, remove the columns we don't need and convert
    # the column names we do need into an appropriate format for netCDF4:
    temp_dataframe = pd.read_csv(filepath, header=4, engine='python')
    temp_dataframe.drop(columns=bad_names, inplace=True)
    temp_dataframe.rename(columns=conversion_list, inplace=True)
    # This can now be passed back to our more general converter functions.

    return temp_dataframe


def generate_dataframe(filepath) -> pd.DataFrame:
    """
    Reads in data from specified input type and holds as temporary
    pandas.DataFrame object.
    """
    if filepath.endswith(".xlsx"):
        temp_dataframe = pd.read_excel(filepath, engine='openpyxl')
    elif filepath.endswith(".nc"):
        # NOTE: We need to use xarray to open the netcdf dataset, then turn
        # that into a pandas dataframe.
        temp_dataset = xr.open_dataset(filepath)
        temp_dataframe = temp_dataset.to_dataframe()
    elif filepath.endswith(".csv"):
        # Not only do we need to read this format into a dataframe, but we
        # also need to reformat it into acceptable standards before passing
        # it on to saving functions.
        temp_dataframe = csv_reformatter(filepath)
    else:
        raise ValueError("No reader configured yet for this input format.")
    return pd.DataFrame(temp_dataframe)


def slice_data(dataframe) -> List:
    """
    This function iterates through rows of a multiple-response dataframe
    and creates a more organised dataframe for each response.  This is a
    necessary step in the conversion between xlsx and json/yaml as it
    allows access to some variables which are otherwise inaccessible due
    to the structure of the original multi-level dataframe.
    """
    # This dataframe will collect more information than is necessary for
    # the json output, but may still be necessary for the yaml output or
    # even for use as a dataframe.
    form_responses = conversion_lists.excel_slice(dataframe)

    return form_responses


class MetadataForm:
    """This class will handle conversions of metadata files from excel (as per
    the 17-page input form created by our lovely scientists) into either json
    files (for chemical metadata) or yaml files (for all other metadata)."""

    def __init__(self, input_filepath, output_directory):
        self.filepath = input_filepath
        self.output_dir = output_directory

    def save_as_json(self, data_object: pd.DataFrame, r, fname):
        """
        Uses data held in pandas DataFrame to enter into form template and
        save as JSON string.

        The variable 'r' represents the specific row of the temporary dataframe
        being restructured in this instance.

        The variable 'fname' represents the name associated with the input
        file before it has been enumerated into output files.
        """
        # Pollutants(chemicals) must be organised into a useable structure
        # before being entered into the new file:
        chemicals = []
        for chem in data_object.chemicals:
            if chem != "":
                chems = {'name': chem,
                         'shortname': chem[chem.find("(") + 1:chem.find(")")],
                         'chart': "url/to/chart/image.(png|jpg|svg|etc)"}
                chemicals.append(chems)

        new_file = conversion_lists.to_json(data_object, chemicals)

        # write the dictionary above (new_file) to a json with the addition of
        # a unit to indicate the number of the metadata form response (input
        # metadata files can have multiple sets of data and will therefore
        # output multiple files).
        filename = fname + str(r) + ".json"
        with open(os.path.join(self.output_dir, filename), 'w') as fp:
            json.dump(new_file, fp, indent=2, cls=DateTimeEncoder)

    def save_as_yaml(self, data_object: pd.DataFrame, r, fname):
        """
        Uses data held in pandas DataFrame to enter into form template and
        save as yaml.  Each data object entered here should be a single
        response from the previous form input section.

        The variable 'r' represents the specific row of the temporary dataframe
        being restructured in this instance.
        """
        # First extract the shortname only for chemical species:
        chem_species = []
        for chem in data_object.chemicals:
            if chem != "":
                chem_shortname = chem[chem.find("(") + 1:chem.find(")")]
                chem_species.append(chem_shortname)

        authors = []
        for i in range(1, 3):
            firstname = data_object.get(f"firstname{i}")
            surname = data_object.get(f"surname{i}")
            if firstname and surname:
                if not isinstance((firstname and surname), str):
                    pass
                else:
                    authors.append({"firstname": firstname,
                                    "surname": surname})

        bbox = {}
        for way in ["north", "south", "east", "west"]:
            direction = data_object.get(f"{way}")
            bbox.update({f"{way}": direction})

        time_range = {"start": data_object.get("time_range_start").isoformat(),
                      "end": data_object.get("time_range_end").isoformat()}

        # Now add all relevant data to a dictionary to save as yaml:
        new_file = conversion_lists.to_yaml(data_object, chem_species,
                                            authors, bbox, time_range)

        # write the dictionary above (new_file) to a yaml in the specified
        # directory with the addition of a unit to indicate the number of the
        # metadata form response (input metadata files can have multiple sets of
        # data and will therefore output multiple files).
        filename = fname + str(r) + ".yaml"
        with open(os.path.join(self.output_dir, filename), 'w') as fp:
            yaml.dump(new_file, fp, indent=2, default_flow_style=False,
                      sort_keys=False)

    def convert_excel(self, output_type):
        """
        Convert excel metadata files to required output format.  Output
        directory must be included in the output_location parameter with a
        valid file type of either 'json', 'yml' or 'yaml'.
        """
        temp_dataframe = generate_dataframe(self.filepath)
        sliced_dataframes = slice_data(temp_dataframe)
        fname = os.path.split(self.filepath)[-1]
        output_name = os.path.splitext(fname)[0]
        filetype = output_type
        for df in sliced_dataframes:
            if filetype == 'json':
                self.save_as_json(data_object=df[0], r=df[1], fname=output_name)
            elif filetype == 'yaml' or filetype == 'yml':
                self.save_as_yaml(data_object=df[0], r=df[1], fname=output_name)
            else:
                raise ValueError("Filetype not recognized.  Please specify "
                                 "output " "type as either 'json', 'yml' or "
                                 "'yaml'.")


class DataFile:
    """This class handles conversion of data files, which will either be in
    the format of a netCDF or a csv.

    To convert netCDF --> CSV, use:
    >> convert_netcdf(input_path, output_path)

    To convert CSV --> netCDF, use:
    >> convert_csv(input_path, output_path)"""
    def __init__(self, input_file, output_path):
        self.filepath = input_file
        self.output_location = output_path

    def convert_netcdf(self):
        """
        Convert netcdf files to required csv output format.  Output filename
        must be included in output location.
        """
        temp_dataframe = generate_dataframe(self.filepath)
        temp_dataframe.to_csv(self.output_location, index=False)

    def convert_csv(self):
        """Convert csv files to required netcdf output format.  Output filename
        must be included in output location with a valid extension of either
        '.txt' or '.nc'."""
        temp_dataframe = generate_dataframe(self.filepath)
        # pandas can't convert to netcdf, so we will have to first convert
        # to xarray (which can):
        xr_object = temp_dataframe.to_xarray()
        xr_object.to_netcdf(self.output_location)

