"""This file contains the lists of conversion requirements for yaml, CSV and
json file conversions (used by file_converter.py)."""

import pandas as pd


def csv_convert():
    """List of data components extracted and converted in reformatting of CSV
    input files."""
    conversion_list = dict(
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

    return conversion_list


def excel_slice(dataframe):
    """List of data components extracted when converting multiple-response
    excel files into single-response json or yaml files."""
    # NOTE: This list requires more functionality than just the list itself
    # because it has to pull data from specific rows and columns in a flat
    # Excel file. This means that the entire dataframe must be passed in and
    # looped over to obtain values.
    output_set = list()
    for r, row in enumerate(dataframe.iterrows()):
        # iterate through each row to split into separate dataframes and
        # save all to appropriate location:
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
        output_set.append([form, r])

    return output_set


def to_json(dataframe, chems):
    """List of data components required in writing Excel metadata form to
    json files."""
    # NOTE: Modification of chemical fields in this data object are performed
    # in the function file_converter.MetdataForm.save_as_json().
    data_fields = {"pollutants": chems,
                   "environmentType": dataframe.obs_level,
                   "dateRange": {"startDate": dataframe.time_range_start,
                                 "endDate": dataframe.time_range_end}}

    return data_fields


def to_yaml(dataframe, chems, authors, bbox, time_range):
    """List of data components required in writing Excel metadata form to
    yaml files."""
    data_fields = {"title": dataframe.title,
                   "description": dataframe.description,
                   "authors": authors,
                   "bbox": bbox,
                   "chemical species": chems,
                   "observation level/model": dataframe.obs_level,
                   "data source": dataframe.data_source,
                   "time range": time_range,
                   "lineage": dataframe.lineage,
                   "quality": dataframe.quality,
                   "docs": dataframe.docs}

    return data_fields
