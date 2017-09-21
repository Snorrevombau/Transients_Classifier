import pandas as pd
import numpy as np

def add_p_delta(df):
    df_length = len(df)
    index_last_row = df_length - 1
    if(df_length > 1):
        p_new = df.iloc[index_last_row]['P']
        p_old = df.iloc[index_last_row-1]['P']
        p_delta = p_new - p_old
        return p_delta
    else:
        return 0

def detect_switch_event(rows, phase, Event_df):
    minuten_index = rows.index[-1]
    timestamp = rows.iloc[-1]['timestamp']
    ### Einschaltvorgang dedektieren ###
    # ist delta P relevant
    if(rows.iloc[-1]['P_delta'] > 400):
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
                if ((deviation > 0.15) | (Ladeleistung < 1500)):
                    Event_df = Event_df.drop(row_event)
                    Event_df = Event_df.reset_index(drop=True)
                else:
                    Event_df.loc[row_event, ['Status', 'Ladeleistung']] = ['checked', Ladeleistung]
            event_df_length = len(Event_df)
            row_event += 1
         
    ### Ausschaltvorgang dedektieren ###
    #Checken ob aktuelle Leistung das Ende eines Einschaltvorgangs impliziert        
    if (('ein' in Event_df['Ladevorgang'].unique()) &
        ('checked' in Event_df['Status'].unique())):
        # create df with charging status on
        only_load_event_df = Event_df[(Event_df['Ladevorgang'] == 'ein') &
                                      (Event_df['minuten_index'] < minuten_index)]
        # Soll Leistung = Leistung die auf der Phase anliegen sollte,
        # wenn alle zuvor ladenden Autos noch an der Phase hängen würden
        Soll_Leistung = Leerlaufleistung_Phase + Event_df[(Event_df['Ladevorgang']=='ein') & 
                                                          (Event_df['minuten_index'] <= minuten_index) & 
                                                          (Event_df['minuten_index_Abschaltung'] == 0) & 
                                                          (Event_df['Phase'] == phase)]['Ladeleistung'].sum()
        #Aktuelle Leistung (neuer Messwert)
        Ist_Leistung = rows.iloc[-1]['P']
        #Residuale Leistung 
        P_residual = Soll_Leistung - Ist_Leistung
        #Überprüfen ob fehlende Leistung (P_residual) zu einem zuvor ladenden Auto passt
        only_load_event_df['deviation_P'] = only_load_event_df['Ladeleistung']. \
                                    apply(lambda ladeleistung_auto: abs(ladeleistung_auto-P_residual)/ladeleistung_auto)
        if ((only_load_event_df['deviation_P'] < 0.03).any()):
            # sort load events by size
            # und nehme das erste Event, was der aktuellen leistung am nächsten ist
            charg_off_ev_index = only_load_event_df['deviation_P'].sort_values().index[0]
            Event_df.loc[charg_off_ev_index,['minuten_index_Abschaltung']] = minuten_index
            Event_df.loc[charg_off_ev_index,['timestamp_abschalt']] = timestamp
            Event_df.loc[charg_off_ev_index, ['Ladevorgang']] = 'aus'
            
    return Event_df

def combine_charging_events(Event_df):
    # Zusammenfassen von mehrphasigen Ladevorängen
    for events in range(0,len(Event_df)):
        timestamp = Event_df.iloc[events]['timestamp']
        timestamp_abschaltung = Event_df.iloc[events]['timestamp_abschalt']
        Phase = []
        Ladeleistung = []
        same_events = Event_df.loc[Event_df['timestamp'] == Event_df.iloc[events]['timestamp']]
        event_count = len(same_events)
        for a in range (0,event_count):
            Phase.append(same_events.iloc[a]['Phase'])
            Ladeleistung.append(str(same_events.iloc[a]['Phase'])+': '+str(same_events.iloc[a]['Ladeleistung']))
        if (len(ladevorgang_df.loc[ladevorgang_df['timestamp_start'] == timestamp]) !=1):
            ladevorgang_df.loc[len(ladevorgang_df)]= [timestamp, Phase, Ladeleistung, timestamp_abschaltung]
            
    return ladevorgang_df