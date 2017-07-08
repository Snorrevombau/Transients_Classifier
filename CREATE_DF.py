import numpy as np
import pandas as pd


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
                    'peak_3']] = sep_input_data['three_first_peaks'].apply(pd.Series)
    # seperate peak index
    sep_input_data[['p_index_1',
                    'p_index_2',
                    'p_index_3']] = sep_input_data['three_first_peaks_index'].apply(pd.Series)
    # cleanup dataframe
    sep_input_data = sep_input_data.drop(['three_first_peaks',
                                          'three_first_peaks_index'], 1)
    index = sep_input_data.index.unique()
    columns = ['peak_1_1', 'peak_2_1', 'peak_3_1',
               'peak_1_2', 'peak_2_2', 'peak_3_2',
               'peak_1_3', 'peak_2_3', 'peak_3_3',
               'index_1_1', 'index_2_1', 'index_3_1',
               'index_1_2', 'index_2_2', 'index_3_2',
               'index_1_3', 'index_2_3', 'index_3_3',
               'transient_rise_gradient_1', 'transient_rise_gradient_2',
               'transient_rise_gradient_3', 'P_delta']
    feature_df = pd.DataFrame(np.nan, index=index, columns=columns)
    for index, row in sep_input_data.iterrows():
        phase_num = row['phase_num']
        # put to phase 1
        if(phase_num == 1):
            feature_df.set_value(
                index,
                ['peak_1_1', 'peak_2_1', 'peak_3_1',
                 'index_1_1', 'index_2_1', 'index_3_1',
                 'transient_rise_gradient_1', 'P_delta'],
                [row['peak_1'], row['peak_2'], row['peak_3'],
                 row['p_index_1'], row['p_index_2'], row['p_index_3'],
                 row['transient_rise_gradient'], row['P_delta']])
        # put to phase 2
        elif(phase_num == 2):
            feature_df.set_value(
                index,
                ['peak_1_2', 'peak_2_2', 'peak_3_2',
                 'index_1_2', 'index_2_2', 'index_3_2',
                 'transient_rise_gradient_2', 'P_delta'],
                [row['peak_1'], row['peak_2'], row['peak_3'],
                 row['p_index_1'], row['p_index_2'], row['p_index_3'],
                 row['transient_rise_gradient'], row['P_delta']])
        # put to phase 3
        elif(phase_num == 3):
            feature_df.set_value(
                index,
                ['peak_1_3', 'peak_2_3', 'peak_3_3',
                 'index_1_3', 'index_2_3', 'index_3_3',
                 'transient_rise_gradient_3', 'P_delta'],
                [row['peak_1'], row['peak_2'], row['peak_3'],
                 row['p_index_1'], row['p_index_2'], row['p_index_3'],
                 row['transient_rise_gradient'], row['P_delta']])
        # Case 4: All undefine Cases
        else:
            print('Error: create_feature_dataframe')
    return(feature_df)
