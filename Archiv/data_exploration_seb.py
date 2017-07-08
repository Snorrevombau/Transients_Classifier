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
    only_trasients['begin_timestamp_string'] = \
        only_trasients['begin_timestamp_string'].apply(convert_to_datetime)

    numric_colums = ['begin_index',
                     'begin_timestamp_float',
                     'phase_num',
                     'transient_rise_gradient']
    only_trasients[numric_colums] = only_trasients[numric_colums] \
        .apply(pd.to_numeric)
    return only_trasients


data = import_trasient_from_file("jsons/")
print(data.head())
'''transientlist = pd.read_csv("Test_Data/transientlist.csv")


###Adding the maximum Voltage as a column and possbile feature for clustering
max_voltage_deviation_column=[]
transient_index=[]
number_phases_column=[]
begin_timestep=[]
for row in range(0, len(data)):
    max_voltage_deviation=max(map(float,(data.iloc[row]["three_first_peaks"])))
    max_voltage_deviation_column.append(max_voltage_deviation)
    
    
    transient_index.append(int(row))
    
    begin_timestep = data.iloc[row]["begin_timestamp_string"][0:19]
    transient_list_row = transientlist[(transientlist["begin_timestamp_string"].str.contains(begin_timestep)) ]
    phases_str = transient_list_row.iloc[0]['phase']
    if len(phases_str) == 3:
        number_phases=1
    elif len(phases_str) == 5:
        number_phases=2
    else:
        number_phases=3
    number_phases_column.append(number_phases)
    
data['max_voltage_deviation']=max_voltage_deviation_column
data['transient_index']=transient_index
data['num_phases']=number_phases_column

data = data.set_index('transient_index')

plt.figure(1)
for i in range(1,65):
    plt.subplot(8,8,int(str(i)))
    plot_transient = data.iloc[i]["raw_signal_voltage"]
    plot_start = (data.iloc[i]["three_first_peaks_index"])[0]
    plot_end = (data.iloc[i]["three_first_peaks_index"])[2]
    plt.plot(plot_transient[(int(plot_start)-500):(int(plot_end)+500)])
    plt.title(str(i))
#    r®
#plt.show()

#print(data.head())

#y = data.iloc["max_voltage_deviation"]
#x = data.iloc["num_phases "]
#
#plt.scatter(x, y, s=area, c=colors, alpha=0.5)
#plt.title('Scatter plot pythonspot.com')
#plt.xlabel('x')
#plt.ylabel('y')
#plt.show()'''