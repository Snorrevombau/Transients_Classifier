
# coding: utf-8

# In[2]:

import pandas as pd
import numpy as np
import progressbar
import matplotlib.pyplot as plt
from IMPORT_DATAFRAME_JSON_HDF5 import *
get_ipython().magic('matplotlib notebook')
import itertools
import os
from IPython.display import display, HTML


# In[3]:

def detect_switch_event(rows, phase, Event_df):
    minuten_index = rows.index[-1]
    timestamp = rows.iloc[-1]['timestamp']
    Leerlaufleistung_Phase = rows.iloc[0]['P']  
    ### Einschaltvorgang dedektieren ###
    # ist delta P relevant
    if(rows.iloc[-1]['P_delta'] > 500):
        # Prüfen ob Ladenvorgang beginnt/beendet
        # Wenn delta P positiv ---> event kreieren um später zu checken ob es ein Einschaltvorgang war
        Event_df.loc[len(Event_df)]= [timestamp, phase, minuten_index, 'ein', 'not checked', 0,0,0]
    
    #Check events: Überprüfen ob vorher eingetragenes event wirklich ein Einschaltvorgang ist
    event_df_length = len(Event_df)
    row_event = 0

    while row_event < event_df_length:
            #condition to check event
            minuten_index_event = Event_df.iloc[row_event]['minuten_index']
            #Check auf Einschaltvorgang
            if ((minuten_index_event+3 == minuten_index) & 
                (Event_df.iloc[row_event]['Ladevorgang'] == 'ein') &
                (Event_df.iloc[row_event]['Phase'] == phase)):
                Ladeleistung = rows.loc[minuten_index_event+3]['P'] - rows.loc[minuten_index_event-3]['P']            
                sum_delta_P = rows.loc[minuten_index_event:minuten_index_event+3]['P_delta'].sum()
                deviation = abs(Ladeleistung-sum_delta_P)/Ladeleistung 
                
                #Kein Einschaltvorgang:
                if ((deviation > 0.12) | (Ladeleistung < 2000)):
                    Event_df = Event_df.drop(row_event)
                    Event_df = Event_df.reset_index(drop=True)
                #Einschaltvorgang
                else:
                    #Mehrere Einschaltungen gleichzeitig
                    num_cars = Ladeleistung//3000
                    if (num_cars>=2):
                        Event_df.loc[row_event, ['Status', 'Ladeleistung']] = ['checked', (Ladeleistung/num_cars)]
                        for num_cars in range (2,int(num_cars)+1):
                            Event_df.loc[row_event+1]= [timestamp, phase, minuten_index_event, 'ein', 'not checked', 0,0,0]
                            Event_df.loc[row_event+1, ['Status', 'Ladeleistung']] = ['checked', (Ladeleistung/num_cars)]
                            row_event += 1
                    #Ein Einschaltvorgang
                    else:
                        Event_df.loc[row_event, ['Status', 'Ladeleistung']] = ['checked', Ladeleistung]
            event_df_length = len(Event_df)
            row_event += 1
            #security break for endless loop (just in case :D )
            if row_event>=100:
                break

         
    ### Ausschaltvorgang dedektieren ###
    #Checken ob aktuelle Leistung das Ende eines Einschaltvorgangs impliziert 
    
    
    
    if (('ein' in Event_df['Ladevorgang'].unique()) &
        ('checked' in Event_df['Status'].unique())):
        # create df with charging status on
        only_load_event_df = Event_df[(Event_df['Ladevorgang'] == 'ein') &
                                      (Event_df['minuten_index'] < minuten_index)&
                                      (Event_df['Phase'] == phase)&
                                      (Event_df['Status'] == 'checked')]
        # Soll Leistung = Leistung die auf der Phase anliegen sollte,
        # wenn alle zuvor ladenden Autos noch an der Phase hängen würden
        
        minuten_index_off = rows.index[-5]
        timestamp_off = rows.iloc[-5]['timestamp']
        
        Soll_Leistung = Leerlaufleistung_Phase + Event_df[(Event_df['Ladevorgang']=='ein') & 
                                                          (Event_df['minuten_index'] <= minuten_index) & 
                                                          (Event_df['minuten_index_Abschaltung'] == 0) & 
                                                          (Event_df['Phase'] == phase)]['Ladeleistung'].sum()
        #Aktuelle Leistung (neuer Messwert)
        Ist_Leistung = rows.iloc[-1]['P']
        #Residuale Leistung 
        P_residual = Soll_Leistung - Ist_Leistung
        #Überprüfen ob fehlende Leistung (P_residual) zu einem zuvor ladenden Auto passt
        only_load_event_df['deviation_P'] = only_load_event_df['Ladeleistung'].                                     apply(lambda ladeleistung_auto: abs(ladeleistung_auto-P_residual)/ladeleistung_auto)
        
        
        # create a np array from the last four P
        last_four_P = rows[-4:]['P'].values
        # calculate the gradient
        gradients_P = np.gradient(last_four_P)
        # calculate absolute gradients values
        abs_gradients_P = np.absolute(gradients_P)
        # calculate the absolute mean of the gradients
        abs_gradient_P = np.mean(abs_gradients_P)
        # calculate zhe mean of the gradients
        gradient_P = np.mean(gradients_P)
        
        #Check auf einphasige Abschaltung
        if (((only_load_event_df['deviation_P'] < 0.2).any()) & ((abs_gradient_P < 5) | (gradient_P > 100))):
            # sort load events by size
            # und nehme das erste Event, was der aktuellen leistung am nächsten ist
            charg_off_ev_index = only_load_event_df['deviation_P'].sort_values().index[0]
            Event_df.loc[charg_off_ev_index,['minuten_index_Abschaltung']] = minuten_index_off
            Event_df.loc[charg_off_ev_index,['timestamp_abschalt']] = timestamp_off
            Event_df.loc[charg_off_ev_index, ['Ladevorgang']] = 'aus'
            
        #Check auf Abschaltung von X (n_cars) Autos gleichzeitig
        n_cars = int(P_residual//3000)           
        if (P_residual >=2):
            only_load_event_df_multiple = only_load_event_df.set_index('minuten_index')
            combinations = list(itertools.combinations(only_load_event_df_multiple.index.tolist(),n_cars))
            combination_df = pd.DataFrame([only_load_event_df_multiple.loc[c,:]['Ladeleistung'].sum() for c in combinations ],columns=['Ladeleistung'], index=combinations )
            combination_df['deviation_P'] = combination_df['Ladeleistung'].                                     apply(lambda ladeleistung_auto: abs(ladeleistung_auto-P_residual)/ladeleistung_auto)
            
            if (combination_df['deviation_P'] < 0.1).any():
                charg_off_ev_index = combination_df['deviation_P'].sort_values().index[0]
                Event_df.loc[((Event_df['minuten_index'].isin(charg_off_ev_index)) & (Event_df['Phase']==phase)),['timestamp_abschalt']]=timestamp
                Event_df.loc[((Event_df['minuten_index'].isin(charg_off_ev_index)) & (Event_df['Phase']==phase)),['minuten_index_Abschaltung']]=minuten_index
                Event_df.loc[((Event_df['minuten_index'].isin(charg_off_ev_index)) & (Event_df['Phase']==phase)),['Ladevorgang']]='aus'            
    return Event_df


# In[4]:

def combine_charging_events(Event_df):
    # Zusammenfassen von mehrphasigen Ladevorängen
    ladevorgang_df = pd.DataFrame(columns = ['timestamp_start','Phasen', 'Durchschnittliche Ladeleistung','Ladevorgang_ende'])
    for events in range(0,len(Event_df)):
        timestamp = Event_df.iloc[events]['timestamp']
        timestamp_abschaltung = Event_df.iloc[events]['timestamp_abschalt']
        Phase = []
        Ladeleistung = []
        same_events = Event_df.loc[Event_df['timestamp'] == Event_df.iloc[events]['timestamp']]
        same_events['deviation_average'] = same_events['Ladeleistung'].                                     apply(lambda ladeleistung_auto: ladeleistung_auto/(same_events['Ladeleistung'].mean()))                     
        same_events = same_events.loc[(same_events['deviation_average']>0.95) & (same_events['deviation_average']<1.05)] 
        event_count = len(same_events)
        for a in range (0,event_count):
            Phase.append(same_events.iloc[a]['Phase'])
            Ladeleistung.append(str(same_events.iloc[a]['Phase'])+': '+str(same_events.iloc[a]['Ladeleistung']))
        if (len(ladevorgang_df.loc[ladevorgang_df['timestamp_start'] == timestamp]) !=1):
            ladevorgang_df.loc[len(ladevorgang_df)]= [timestamp, Phase, Ladeleistung, timestamp_abschaltung]
            
    return ladevorgang_df


# In[5]:

def cars_charging(timestamp,ladevorgang_df):
    
    #Filter out all events that are in the timeframe of the input timestamp
    current_cars = ladevorgang_df[((timestamp >= ladevorgang_df['timestamp_start']) & ((timestamp <  ladevorgang_df['Ladevorgang_ende']) | (ladevorgang_df['Ladevorgang_ende'] == 0)))]
    
    #Helper columns for the calculation
    current_cars['length_phase'] = current_cars['Phasen'].apply(lambda x: len(x))
    current_cars['Phase_1'] = current_cars['Phasen'].apply(lambda x: 1 in x)
    current_cars['Phase_2'] = current_cars['Phasen'].apply(lambda x: 2 in x)
    current_cars['Phase_3'] = current_cars['Phasen'].apply(lambda x: 3 in x)

    one_phase = int(current_cars[current_cars['length_phase']==1].count()['Phasen'])
    two_phases = int(current_cars[current_cars['length_phase']==2].count()['Phasen'])
    three_phases = int(current_cars[current_cars['length_phase']==3].count()['Phasen'])

    cars_phase_1 = int(current_cars[current_cars['Phase_1'] == True].count()['Phase_1'])
    cars_phase_2 = int(current_cars[current_cars['Phase_2'] == True].count()['Phase_2'])
    cars_phase_3 = int(current_cars[current_cars['Phase_3'] == True].count()['Phase_3'])
    
    cars_total = one_phase+two_phases+three_phases

    one_phase, two_phases, three_phases, cars_total, cars_phase_1, cars_phase_2, cars_phase_3

    charging_df = pd.DataFrame(columns = ['timestamp','cars_total','one_phase' ,'two_phases', 'three_phases', 'cars_phase_1','cars_phase_2','cars_phase_3'])
    charging_df.loc[0] = [timestamp,cars_total,one_phase, two_phases, three_phases,cars_phase_1, cars_phase_2, cars_phase_3 ]

    return charging_df


# In[ ]:




# In[ ]:



