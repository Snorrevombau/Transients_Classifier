import pandas as pd
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
    events_from_outside = events_from_outside.astype(dtype=dtypes)
    one_phase_df = one_phase_df.astype(dtype=dtypes)
    two_phase_df = two_phase_df.astype(dtype=dtypes)
    three_phase_df = three_phase_df.astype(dtype=dtypes)
    return [events_from_outside, one_phase_df, two_phase_df, three_phase_df]
