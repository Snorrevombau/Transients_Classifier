import pandas as pd
import progressbar
import os
from glob import glob


def convert_to_datetime(timestamp_as_str):
    """Convert a timestring as str to pandas timestring dtype

    Args:
        timestamp_as_str: Timestamp in string format

    Returns:
        A readable timestamp for pandas
    """
    date, time, time_ns = timestamp_as_str.split('_')
    return pd.to_datetime(date + ' ' + time + '.' + time_ns)


def transient_from_file(url_of_folder):
    """Get jsons from a folder and put them into a DataFrame

    Args:
        url_of_folder: The url where we can find all jsons

    Returns:
        A DataFrame with all transients and all
        relevant information
    """
    append_data = []

    # find out how many files in the folder
    list = os.listdir(url_of_folder)
    number_files = len(list)
    bar = progressbar.ProgressBar()
    with progressbar.ProgressBar(max_value=number_files) as bar:
        for i, file_name in enumerate(glob(url_of_folder + '*.json')):
            data = pd.read_json(file_name)
            append_data.append(data)
            bar.update(i)
        all_data = pd.concat(append_data, axis=1).transpose()
    only_trasients = all_data[all_data["transient_flag"] == "true"] \
        .reset_index() \
        .drop(['index', 'transient_flag'], 1)
    # convert object types to float, timestamp, int
    only_trasients['begin_timestamp_string'] = \
        only_trasients['begin_timestamp_string'].apply(convert_to_datetime)

    numric_colums = ['begin_index',
                     'begin_timestamp_float',
                     'phase_num',
                     'transient_rise_gradient']
    only_trasients[numric_colums] = only_trasients[numric_colums] \
        .apply(pd.to_numeric)
    # set column 'begin_timestamp_float' as index
    only_trasients = only_trasients.set_index('begin_timestamp_float')
    return only_trasients
