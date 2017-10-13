
# coding: utf-8

# In[2]:

#Import bibs
import pandas as pd
import numpy as np
from pylab import *
import progressbar
import matplotlib.pyplot as plt
get_ipython().magic('matplotlib notebook')
import itertools
import os
import sys
from IPython.display import display, HTML


# In[24]:




# In[106]:

def plot_transients (transients_df, number_plots, column_to_plot, columns_of_figure):
    values_to_plot = column_to_plot
    number_of_subplots=number_plots
    number_of_columns=columns_of_figure
    transients=transients_df
    fig = plt.figure(figsize=(5*number_of_columns,number_of_subplots) )
    fig.subplots_adjust(hspace=.5)
    b=0
    for v in range(0,(number_of_subplots)):
        v = v+1
        #print(v)
        #preprocessing before printing
        transient_rise_gradient = transients.iloc[v]['transient_rise_gradient']
        if transient_rise_gradient<0:
            z=-1
        else:
            z=1
            
        phase = transients.iloc[v]['phase_num']
        num_cars_on_phase = str(int(transients.iloc[v]['cars_phase_'+str(phase)]))
        voltage_peak = transients.iloc[v]['three_first_peaks'][0]
        #print((transients.iloc[v]['begin_index']+1000)-10000)
        
       #if ((transients.iloc[v]['begin_index']+1000)-10000>500):
        #   continue
        ax1 = subplot(number_of_subplots,number_of_columns,v-b)
        ax1.plot(np.asarray(transients.iloc[v][values_to_plot])*z)
        plt.suptitle(values_to_plot)
        plt.title('cars/phase: '+num_cars_on_phase +'  V_peak: '+ str(voltage_peak)+'  Plugin='+str(transients.iloc[v]['plugin'])+' minute:'+ str(transients.iloc[v]['minute_index']),fontsize=10)
        plt.xlim([transients.iloc[v]['begin_index']-100,transients.iloc[v]['begin_index']+1000])
        plt.setp(ax1.get_xticklabels(), visible=False)
    
    return


# In[107]:

#plot_transients(transients,10,'filtered_signal',2)


# In[ ]:



