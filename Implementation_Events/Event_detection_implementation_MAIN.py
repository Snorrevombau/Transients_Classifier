
# coding: utf-8

# In[1]:

import pandas as pd
import numpy as np
import itertools
import os
from IPython.display import display, HTML


from Event_detection_functions import *


# In[3]:

# Decleration of dataframes 
Event_df = pd.DataFrame(columns = ['timestamp','Phase','minuten_index',
                                   'Ladevorgang', 'Status', 'Ladeleistung',
                                   'minuten_index_Abschaltung','timestamp_abschalt'])
pseudocode_df = pd.DataFrame([])


# In[5]:

#test loop, delete later
for minute_day in range (2,690):

    # Insert this in the update routine after the power_today_minute.csv export
    # The following variables have to be set to the corresponding dataframe in the environment (export to power_today_minute_x.csv)
    P_Phase_1 = pd.read_csv('power_today_minute_1.csv', names = ['timestamp','P'])
    P_Phase_1 = P_Phase_1[:minute_day]
    P_Phase_2 = pd.read_csv('power_today_minute_2.csv', names = ['timestamp','P'])
    P_Phase_2 = P_Phase_2[:minute_day]
    P_Phase_3 = pd.read_csv('power_today_minute_3.csv', names = ['timestamp','P'])
    P_Phase_3 = P_Phase_3[:minute_day]

    dict = {1:P_Phase_1,2:P_Phase_2,3:P_Phase_3}

    #Detection of switch-on and switch-off events
    for Phase in range (1,4):
        
        pseudocode_df = dict[Phase]
        pseudocode_df['P_delta'] = dict[Phase].P.diff()
        Event_df = detect_switch_event(pseudocode_df, Phase, Event_df)

        


# In[6]:

Event_df


# In[7]:

ladevorgang_df = combine_charging_events(Event_df)
ladevorgang_df


# In[9]:

#timestamp has to be replaced by variable used in py script
timestamp = (pd.read_csv('power_today_minute_1.csv', names = ['timestamp','P'])).iloc[700]['timestamp']

charging_df=cars_charging(timestamp,ladevorgang_df)
charging_df


# In[10]:

#export
charging_df.to_csv('charging_df.csv', )

