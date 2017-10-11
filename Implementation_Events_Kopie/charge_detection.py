import pandas as pd
from Event_detection_functions import *
import mmap
import os
import time

# Decleration of dataframes 
Event_df = pd.DataFrame(columns = ['timestamp','Phase','minuten_index',
                                   'Ladevorgang', 'Status', 'Ladeleistung',
                                   'minuten_index_Abschaltung','timestamp_abschalt'])


backtrack_timesteps = 7

path_to_csvs = '../../pqpico3/jsondata'

def countlines(filename):
    f = open(filename, 'r+')
    buf = mmap.mmap(f.fileno(),0)
    lines = 0
    readline = buf.readline
    while readline():
        lines += 1
    return lines


lines = countlines(os.path.join(path_to_csvs, 'power_today_minute_1.csv'))
#print(lines)

phase_1_df = pd.read_csv(os.path.join(path_to_csvs, 'power_today_minute_1.csv'), names = ['timestamp','P'])
phase_1_df['P_delta'] = phase_1_df.P.diff()
no_load_p_1 = phase_1_df.iloc[0]['P']
phase_2_df = pd.read_csv(os.path.join(path_to_csvs, 'power_today_minute_2.csv'), names = ['timestamp','P'])
phase_2_df['P_delta'] = phase_2_df.P.diff()
no_load_p_2 = phase_2_df.iloc[0]['P']
phase_3_df = pd.read_csv(os.path.join(path_to_csvs, 'power_today_minute_3.csv'), names = ['timestamp','P'])
phase_3_df['P_delta'] = phase_3_df.P.diff()
no_load_p_3 = phase_3_df.iloc[0]['P']

for minute_day in range(2,lines):
    time.sleep(0.01)
    #print(minute_day)
    # Insert this in the update routine after the power_today_minute.csv export
    # The following variables have to be set to the corresponding dataframe in the environment (export to power_today_minute_x.csv)
    P_Phase_1 = phase_1_df[max(0,minute_day-backtrack_timesteps):minute_day]
    P_Phase_2 = phase_2_df[max(0,minute_day-backtrack_timesteps):minute_day]
    P_Phase_3 = phase_3_df[max(0,minute_day-backtrack_timesteps):minute_day]

    phase_dict = {1:P_Phase_1, 2:P_Phase_2, 3:P_Phase_3}
    no_load_power_dict = {1:no_load_p_1,2:no_load_p_2,3:no_load_p_3 }
    # Detection of switch-on and switch-off events
    for Phase in [1,2,3]:
        time.sleep(0.01)
        Event_df = detect_switch_event(phase_dict[Phase], Phase, Event_df,no_load_power_dict[Phase])

print(Event_df)
ladevorgang_df = combine_charging_events(Event_df)
print(ladevorgang_df)

#timestamp has to be replaced by variable used in py script
timestamp = phase_1_df.iloc[-1]['timestamp']

charging_df = cars_charging(timestamp,ladevorgang_df)
charging_df.to_csv('charging_df.csv', index=None)

