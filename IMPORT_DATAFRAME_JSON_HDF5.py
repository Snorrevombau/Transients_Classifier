# -*- coding: utf-8 -*-
"""
Created on Sun Jun 11 22:56:00 2017

Notes to this file:
This script imports all transients located in /jsons and puts them inta a pandas df (function: import_trasient_from_file)
The unique index to identify the transients is the timestamp (float)

As a second step the function map_transients_to_PQ_data  imports the hdf5 files and assigns a timeseries of choseable
parameters (P, S, f,  u_rms, i_rms, cos_phi) to the transient dataframe
The length of the timeseries is defined by the timestamp of the transient +- a variable T[s]

If called, the output of this script is a pandas df (data) including both the columns of the json as well as the columns of the hdf5 file
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
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


def import_trasient_from_file(url_of_folder):
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
#    only_trasients['begin_timestamp_string'] = \
#        only_trasients['begin_timestamp_string'].apply(convert_to_datetime)

    numric_colums = ['begin_index',
                     'begin_timestamp_float',
                     'phase_num',
                     'transient_rise_gradient']
    only_trasients[numric_colums] = only_trasients[numric_colums] \
        .apply(pd.to_numeric)
        
    # set column 'begin_timestamp_float' as index
    only_trasients = only_trasients.set_index('begin_timestamp_float')
    return only_trasients





def map_transients_to_PQ_data(transients_dataframe, directory_hdf5, T, measurements_to_map):
    transients_dataframe = transients_dataframe.reset_index()
    # Definition of blank variables for new columns of df 
    for m in range(0,len(measurements_to_map)):
        transients_dataframe[measurements_to_map[m]]=np.nan
        transients_dataframe[measurements_to_map[m]] = transients_dataframe.astype(object)
    #looping over all rows of transient file
    for row in range(0, len(transients_dataframe)):
        # Concatenate the right file name for the current transient
        transient_date  = transients_dataframe.iloc[row]["begin_timestamp_string"][6:10] + '-' + transients_dataframe.iloc[row]["begin_timestamp_string"][3:5]+ '-'+ transients_dataframe.iloc[row]["begin_timestamp_string"][:2]
        transient_phase = str(transients_dataframe.iloc[row]["phase_num"])
        hdf_filename = directory_hdf5+'/'+'phase_'+transient_phase+'_'+transient_date+ '.h5'
        
        #Import hdf as pd
        PQ_data_total = pd.read_hdf(hdf_filename)
#        #Filtering relevant PQ_data for transient (timestamp +-T[s])
        transient_timestamp = transients_dataframe.iloc[row]['begin_timestamp_float']
        PQ_data_relevant = (PQ_data_total[(PQ_data_total['timestamp'] >= float(transient_timestamp)-T) & (PQ_data_total['timestamp'] <=(float(transient_timestamp)+T))])
        
#         #Adding the chosen measurements to a column
        for m in range(0,len(measurements_to_map)):
            PQ_data_list = PQ_data_relevant[measurements_to_map[m]].tolist()
            
            transients_dataframe.set_value(row,measurements_to_map[m],PQ_data_list)
            
    transients_dataframe= transients_dataframe.set_index('begin_timestamp_float')
    return transients_dataframe


#data = import_trasient_from_file("jsons/")
#data = map_transients_to_PQ_data(data, "HDF5", 5, ['P'])
