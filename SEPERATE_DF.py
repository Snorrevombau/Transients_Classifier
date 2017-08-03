import pandas as pd
from collections import Counter


def seperate_transients(input_df):
    # get a df with all car events plugin or unplug
    data_ev_charge_event = input_df[(input_df['P_Plugin'] == 1) |
                                    (input_df['P_Unplug'] == 1)]
    # convert the data_ev_charge_events indexes to a list
    ev_charge_indexes = data_ev_charge_event.index.tolist()
    # seperate the hole raw data, into events from outside and ev events
    events_from_outside = input_df[~(input_df.index.isin(ev_charge_indexes))]
    ev_events = input_df[(input_df.index.isin(ev_charge_indexes))]
    # put all timestamps to a list
    # and create a dict with Counter() to get a timestamp as key and a
    # value how often we can find this timestamp
    timestamps = ev_events.index.tolist()
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
    one_phase_df = pd.DataFrame(columns=header)
    two_phase_df = pd.DataFrame(columns=header)
    three_phase_df = pd.DataFrame(columns=header)
    for index, row in ev_events.iterrows():
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
