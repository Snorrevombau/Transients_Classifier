# -*- coding: utf-8 -*-
"""
Created on Sun May 28 18:22:41 2017

@author: Admin

Note: This function imports the hdf5 files and assigns a timeseries of choseable parameters (P, S, f,  u_rms, i_rms, cos_phi) to the transient dataframe
The length of the timeseries is defined by the timestamp of the transient +- a variable T[s]
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from glob import glob



# Input variables for the import function
# transient_dataframe is the dataframe filled with the data from the transient jsons
# directory_hdf5 is the path to the hdf5 files
# T is the time in seconds and defines the length of imported time intervals
# measurements_to_map are the columns of the hdf5 file which will be imported 
transients_dataframe=data
directory_hdf5 ='HDF5'
T = 5
measurements_to_map = ['P', 'S']

def map_transients_to_PQ_data(transients_dataframe, directory_hdf5, T, measurements_to_map):
    
    # Definition of blank variables for new columns of df 
    for m in range(0,len(measurements_to_map)):
        transients_dataframe[measurements_to_map[m]]=np.nan
    
    #looping over all rows of transient file
    for row in range(0, len(transients_dataframe)):
        # Concatenate the right file name for the current transient
        transient_date  = transients_dataframe.iloc[row]["begin_timestamp_string"][6:10] + '-' + transients_dataframe.iloc[row]["begin_timestamp_string"][3:5]+ '-'+ transients_dataframe.iloc[row]["begin_timestamp_string"][:2]
        transient_phase = transients_dataframe.iloc[row]["phase_num"]
        hdf_filename = directory_hdf5+'/'+'phase_'+transient_phase+'_'+transient_date+ '.h5'
        
        #Import hdf as pd
        PQ_data_total = pd.read_hdf(hdf_filename)
        #Filtering relevant PQ_data for transient (timestamp +-T[s])
        transient_timestamp = transients_dataframe.iloc[row]["begin_timestamp_float"]
        PQ_data_relevant = (PQ_data_total[(PQ_data_total['timestamp'] >= float(transient_timestamp)-T) & (PQ_data_total['timestamp'] <=(float(transient_timestamp)+T))])
        
         #Adding the chosen measurements to a column
        for m in range(0,len(measurements_to_map)):
            PQ_data_list = PQ_data_relevant[measurements_to_map[m]].tolist()
            transients_dataframe[measurements_to_map[m]] = transients_dataframe.astype(object)
            transients_dataframe.set_value(row,measurements_to_map[m],PQ_data_list)
            
    
    return transients_dataframe


transients_dataframe_PQ = map_transients_to_PQ_data(transients_dataframe, directory_hdf5, T, measurements_to_map)




