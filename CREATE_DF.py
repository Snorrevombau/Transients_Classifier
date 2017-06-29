import pandas as pd
import numpy as np
from collections import Counter
# documentation : https://docs.python.org/2/library/collections.html


def seperate_transients(input_df):
    # put all timestamps to a list
    # and create a dict with Counter() to get a timestamp as key and a
    # value how often we can find this timestamp
    timestamps = input_df.index.tolist()
    # create a counter object
    counter_timestamps = Counter()
    # count how often one Timestamp is in the list
    for timestamp in timestamps:
        counter_timestamps[timestamp] += 1
    # create a series from the counter object, that we can handle better
    # the information
    counter_timestamps_series = pd.Series(counter_timestamps)
    # create three new df
    # take the header from the input data
    header = input_df.dtypes.index
    events_from_outside = pd.DataFrame(columns=header)
    one_phase_df = pd.DataFrame(columns=header)
    two_phase_df = pd.DataFrame(columns=header)
    three_phase_df = pd.DataFrame(columns=header)
    for index, row in input_df.iterrows():
        # ev_start 1 mean that ev start charging
        ev_start = row['P_Plugin']
        # ev_stop 1 mean that ev stop charging
        ev_stop = row['P_Unplug']
        # seperate events from outside and charging events
        if(ev_start == 0 & ev_stop == 0):
            # events from outside
            events_from_outside = events_from_outside.append(row)
        else:
            # charging events
            num_phase = counter_timestamps_series[index]
            # Events with one phase
            if(num_phase == 1):
                one_phase_df = one_phase_df.append(row)
            # Events with two phases
            elif(num_phase == 2):
                two_phase_df = two_phase_df.append(row)
            # Events with three phases
            elif(num_phase == 3):
                three_phase_df = three_phase_df.append(row)
    # take the dtypes from the input header
    dtypes = dict(input_df.dtypes)
    one_phase_df = one_phase_df.astype(dtype=dtypes)
    two_phase_df = two_phase_df.astype(dtype=dtypes)
    three_phase_df = three_phase_df.astype(dtype=dtypes)
    return [events_from_outside, one_phase_df, two_phase_df, three_phase_df]


def squeeze_nan(x):
    # get original column names
    original_columns = x.index.tolist()
    # drop all nan values
    squeezed = x.dropna()
    # create new index
    squeezed.index = [original_columns[n] for n in range(squeezed.count())]
    # return new Series with all nan values at the last column
    return squeezed.reindex(original_columns, fill_value=np.nan)


def create_feature_df(sep_input_data):
    # sep_input_data = seperate df by different event types
    # drop all unnecessary columns
    sep_input_data = sep_input_data.drop(['begin_index',
                                          'begin_timestamp_string',
                                          'filtered_signal',
                                          'raw_signal_current',
                                          'raw_signal_voltage'], 1)
    # seperate peaks
    sep_input_data[['peak_1',
                    'peak_2',
                    'peak_3']] = sep_input_data['three_first_ \
                                                 peaks'].apply(pd.Series)
    # seperate peak index
    sep_input_data[['p_index_1',
                    'p_index_2',
                    'p_index_3']] = sep_input_data['three_first_peaks_ \
                                                    index'].apply(pd.Series)
    # cleanup dataframe
    sep_input_data = sep_input_data.drop(['three_first_peaks',
                                          'three_first_peaks_index'], 1)
    index = sep_input_data.index.unique()
    columns = ['peak_1_1', 'peak_2_1', 'peak_3_1',
               'peak_1_2', 'peak_2_2', 'peak_3_2',
               'peak_1_3', 'peak_2_3', 'peak_3_3']
    feature_df = pd.DataFrame(np.nan, index=index, columns=columns)
    for index, row in sep_input_data.iterrows():
        phase_num = row['phase_num']
        # put to phase 1
        if(phase_num == 1):
            feature_df.set_value(
                index,
                ['peak_1_1', 'peak_2_1', 'peak_3_1'],
                [row['peak_1'], row['peak_2'], row['peak_3']])
        # put to phase 2
        elif(phase_num == 2):
            feature_df.set_value(
                index,
                ['peak_1_2', 'peak_2_2', 'peak_3_2'],
                [row['peak_1'], row['peak_2'], row['peak_3']])
        # put to phase 3
        elif(phase_num == 3):
            feature_df.set_value(
                index,
                ['peak_1_3', 'peak_2_3', 'peak_3_3'],
                [row['peak_1'], row['peak_2'], row['peak_3']])
        # Case 4: All undefine Cases
        else:
            print('Error: create_feature_dataframe')
    return(feature_df)
