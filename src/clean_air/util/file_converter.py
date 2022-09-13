"""
This converts input metadata files to selected file types for processing,
for example:
convert_excel(filepath, output_location)
convert_netcdf(filepath, output_location)
convert_csv(filepath, output_location)

You can also use this module to access a pandas.DataFrame extracted from
either an excel, netcdf or csv input file, for example:
clean_air.util.file_converter.generate_dataframe(filepath)
"""

import os
from typing import List

import pandas as pd
import json
import yaml
import datetime
import xarray as xr
from json import JSONEncoder

# subclass JSONEncoder
from pandas.errors import ParserError


class DateTimeEncoder(JSONEncoder):
    # Override default method so that we can extract and encode datetimes:
    def default(self, obj):
        if isinstance(obj, (datetime.date, datetime.datetime)):
            return obj.isoformat()


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


def csv_reformatter(filepath) -> pd.DataFrame:
    """This function uses a template to reformat AURN-style CSV files into a
    fixed format that we can then very easily read into a pandas dataframe
    (ready for conversion to netcdf files)."""
    # rules for csv format:
    # - header line (column names) must be on row 4 of file (top row is 0)
    # - column names must be standard python strings.

    # This is a dictionary containing names to look for and what to convert
    # them into.
    cap_converters = dict(
        {'PM<sub>10</sub> particulate matter (Hourly measured)': 'PM10',
         'Non-volatile PM<sub>10</sub> (Hourly measured)': 'Non-volatilePM10',
         'Non-volatile PM<sub>2.5</sub> (Hourly measured)': 'Non-volatilePM2p5',
         'PM<sub>2.5</sub> particulate matter (Hourly measured)': 'PM2p5',
         'Volatile PM<sub>10</sub> (Hourly measured)': 'Volatile PM10',
         'Volatile PM<sub>2.5</sub> (Hourly measured)': 'Volatile PM2p5',
         'Ozone': 'O3',
         'Nitric Oxide': 'NO',
         'Nitrogen Dioxide': 'NO2',
         'Sulphur Dioxide': 'SO2',
         'Carbon Monoxide': 'CO',
         'Date': 'Date',
         'time': 'time'})

    # Now that we have some things to look for we can read the header row of
    # the file to pull out the applicable column names:
    data_names = pd.read_csv(filepath, nrows=1, skiprows=4, delimiter=',')

    # We need to narrow down our own list of column names by matching them
    # to those we are looking for:
    good_names = []
    bad_names = []
    for name in data_names.columns:
        if name in (cap_converters.keys() or cap_converters.values()):
            good_names.append(name)
        else:
            bad_names.append(name)

    # And then we need to produce a shorter conversion list containing only
    # the conversions required in this file.  This part also ensures that only
    # readable (user-friendly) names are presented in the converted file:
    conversion_list = {}
    for k, v in cap_converters.items():
        if (k or v) in good_names:
            conversion_list[k] = v

    # Now that we have all these relevant lists, we can use them to read the
    # file into a dataframe, remove the columns we don't need and convert the
    # column names we do need into an appropriate format for netCDF4:
    temp_dataframe = pd.read_csv(filepath, header=4, engine='python')
    temp_dataframe.drop(columns=bad_names, inplace=True)
    temp_dataframe.rename(columns=conversion_list, inplace=True)
    # This can now be passed back to our more general converter functions.

    return temp_dataframe


def slice_data(dataframe) -> List:
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
        form_data = {'title': row[1].values[16],
                     'description': row[1].values[17],
                     'firstname1': row[1].values[6],
                     'surname1': row[1].values[7],
                     'firstname2': row[1].values[11],
                     'surname2': row[1].values[12],
                     'north': row[1].values[42],
                     'south': row[1].values[41],
                     'east': row[1].values[43],
                     'west': row[1].values[44],
                     'chemicals': row[1].values[46].split(';'),
                     'obs_level': row[1].values[19],
                     'data_source': row[1].values[20],
                     'time_range_start': row[1].values[37],
                     'time_range_end': row[1].values[38],
                     'lineage': row[1].values[50],
                     'quality': row[1].values[51],
                     'docs': row[1].values[22]}

        form = pd.Series(data=form_data)
        form_responses.append([form, r])

    return form_responses


def save_as_json(data_object: pd.DataFrame, r, output_location):
    """
    Uses data held in pandas DataFrame to enter into form template and
    save as JSON string.

    The variable 'r' represents the specific row of the temporary dataframe
    being restructured in this instance.
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

    # write the dictionary above (new_file) to a json with the addition of
    # a unit to indicate the number of the metadata form response (input
    # metadata files can have multiple sets of data and will therefore output
    # multiple files).
    filename = "form_response" + str(r) + ".json"
    with open(os.path.join(output_location, filename), 'w') as fp:
        json.dump(new_file, fp, indent=2, cls=DateTimeEncoder)


def save_as_yaml(data_object: pd.DataFrame, r, output_location):
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
    new_file = {"title": data_object.title,
                "description": data_object.description,
                "authors": authors,
                "bbox": bbox,
                "chemical species": chem_species,
                "observation level/model": data_object.obs_level,
                "data source": data_object.data_source,
                "time range": time_range,
                "lineage": data_object.lineage,
                "quality": data_object.quality,
                "docs": data_object.docs}

    # write the dictionary above (new_file) to a yaml in the cap-sample-data
    # directory with the addition of a unit to indicate the number of the
    # metadata form response (input metadata files can have multiple sets of
    # data and will therefore output multiple files).
    filename = "form_response" + str(r) + ".yaml"
    with open(os.path.join(output_location, filename), 'w') as fp:
        yaml.dump(new_file, fp, indent=2, default_flow_style=False,
                  sort_keys=False)


def save_as_csv(data_object: pd.DataFrame, output_location):
    """
    Convert pandas.DataFrame object to csv file and save in specified
    location.  Filename must be included as part of output_location.
    """
    data_object.to_csv(output_location, index=False)


def save_as_netcdf(data_object: pd.DataFrame, output_location):
    """
    Convert pandas.DataFrame object to netcdf file and save in specified
    location.  Filename must be included as part of output_location.
    """
    # pandas can't convert to netcdf, so we will have to first convert
    # to xarray (which can):
    xr_object = data_object.to_xarray()
    xr_object.to_netcdf(output_location)


def convert_excel(filepath, output_location):
    """
    Convert excel metadata files to required output format.  Filename must be
    included in the output_location parameter with a valid file extension of
    either 'json', 'yml' or 'yaml'.
    """
    temp_dataframe = generate_dataframe(filepath)
    sliced_dataframes = slice_data(temp_dataframe)
    output_dir = os.path.split(output_location)[0]
    filetype = os.path.splitext(output_location)[1]
    for df in sliced_dataframes:
        if filetype == '.json':
            save_as_json(data_object=df[0], r=df[1],
                         output_location=output_dir)
        elif filetype == '.yaml' or filetype == '.yml':
            save_as_yaml(data_object=df[0], r=df[1],
                         output_location=output_dir)
        else:
            raise ValueError("Filetype not recognized.  Please specify output "
                             "type as either 'json', 'yml' or 'yaml'.")


def convert_netcdf(filepath, output_location):
    """
    Convert netcdf files to required csv output format.  Output filename must
    be included in output location.
    """
    temp_dataframe = generate_dataframe(filepath)
    save_as_csv(temp_dataframe, output_location)


def convert_csv(filepath, output_location):
    """Convert csv files to required netcdf output format.  Output filename
    must be included in output location with a valid extension of either '.txt'
    or '.nc'."""
    temp_dataframe = generate_dataframe(filepath)
    filetype = os.path.splitext(output_location)[1]
    if filetype == ".nc":
        save_as_netcdf(temp_dataframe, output_location)
    elif filetype == ".txt":
        pass
