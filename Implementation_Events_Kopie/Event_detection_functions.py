import pandas as pd
import numpy as np
import itertools

def detect_switch_event(rows, phase, Event_df):
    minuten_index = rows.index[-1]
    timestamp = rows.iloc[-1]['timestamp']
    Leerlaufleistung_Phase = rows.iloc[0]['P']  

    ### Detect plug-in events ###
    # Relevent P_delta?
    if(rows.iloc[-1]['P_delta'] > 500):
        # Creating a plug-in event to later check if it was a "real" plug-in
        Event_df.loc[len(Event_df)]= [timestamp, phase, minuten_index, 'ein', 'not checked', 0,0,0]
    
    event_df_length = len(Event_df)
    row_event = 0
    # Iterate through event dataframe to verify if previously added events are "real" plug-ins 
    while row_event < event_df_length:
            minuten_index_event = Event_df.iloc[row_event]['minuten_index']
            #Checking previously added events if 3 minutes passed
            if ((minuten_index_event+3 == minuten_index) & 
                (Event_df.iloc[row_event]['Ladevorgang'] == 'ein') &
                (Event_df.iloc[row_event]['Phase'] == phase)):

                #Condition 1: P_L = P(t+3)-P(t-3) > 2000
                Ladeleistung = rows.loc[minuten_index_event+3]['P'] - rows.loc[minuten_index_event-3]['P']  
                #Condition 2: sum(P_delta)(t:t+3) ≈ P_L        
                sum_delta_P = rows.loc[minuten_index_event:minuten_index_event+3]['P_delta'].sum()
                deviation = abs(Ladeleistung-sum_delta_P)/Ladeleistung 
                
                #Verifying conditions 1 & 2 for 3 Cases
                # Case 1: No plug-in
                if ((deviation > 0.12) | (Ladeleistung < 2000)):
                    Event_df = Event_df.drop(row_event)
                    Event_df = Event_df.reset_index(drop=True)
                #Case 2: More then 1 ev plug-in to the same time
                else:
                    num_cars = Ladeleistung//3000
                    if (num_cars>=2):
                        Event_df.loc[row_event, ['Status', 'Ladeleistung']] = ['checked', (Ladeleistung/num_cars)]
                        for num_cars in range (2,int(num_cars)+1):
                            Event_df.loc[row_event+1]= [timestamp, phase, minuten_index_event, 'ein', 'not checked', 0,0,0]
                            Event_df.loc[row_event+1, ['Status', 'Ladeleistung']] = ['checked', (Ladeleistung/num_cars)]
                            row_event += 1
                    #Case 3: 1 ev plug-in
                    else:
                        Event_df.loc[row_event, ['Status', 'Ladeleistung']] = ['checked', Ladeleistung]
            event_df_length = len(Event_df)
            row_event += 1
            #security break for endless loop (shouldn't happen, butjust in case :D )
            if row_event>=100:
                break

         
    ### Detecting Unplug Eventes ###
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

        # Check if current power implies an unplug event of a previously plugged in car
        # Soll_Leistung: Power consumption theoretically implied by currently charging cars
        Soll_Leistung = Leerlaufleistung_Phase + Event_df[(Event_df['Ladevorgang']=='ein') & 
                                                          (Event_df['minuten_index'] <= minuten_index) & 
                                                          (Event_df['minuten_index_Abschaltung'] == 0) & 
                                                          (Event_df['Phase'] == phase)]['Ladeleistung'].sum()
        #Ist_Leistung: Current powr consumption
        Ist_Leistung = rows.iloc[-1]['P']
        #P_residual: Power which is 'missing'
        P_residual = Soll_Leistung - Ist_Leistung
        #Calculating the deviation of the rated power of all charging cars with the residual power
        only_load_event_df['deviation_P'] = only_load_event_df['Ladeleistung'].apply(lambda ladeleistung_auto: abs(ladeleistung_auto-P_residual)/ladeleistung_auto)
        
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
        
        #Check for unplug vevent of 1 car
        if (((only_load_event_df['deviation_P'] < 0.2).any()) & ((abs_gradient_P < 5) | (gradient_P > 100))):
            # sort load events by size
            # Sorting all currently charging cars by the lowest deviation to the residual power and chosing the closest one as an unplug event
            charg_off_ev_index = only_load_event_df['deviation_P'].sort_values().index[0]
            Event_df.loc[charg_off_ev_index,['minuten_index_Abschaltung']] = minuten_index_off
            Event_df.loc[charg_off_ev_index,['timestamp_abschalt']] = timestamp_off
            Event_df.loc[charg_off_ev_index, ['Ladevorgang']] = 'aus'
            
        #Check for unplug events of n_cars
        n_cars = int(P_residual//3000)           
        if (n_cars >= 2):
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




def combine_charging_events(Event_df):
    # Combine charging events starting at the same timestamp to multiple phase charging events
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











