
#%% 
import streamlit as st
import numpy as np
import pandas as pd
import glob
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle, Arc
import matplotlib as mpl
import seaborn as sns
from scipy import stats

# Streamlit layout settings
"""
players = pd.read_csv("players.csv", dtype={'ID': str})
players['select'] = players['Name'] + ' | ' + players['ID']
player = st.sidebar.selectbox("Select Player", players['select'], key='player')
player = player.split(' | ')[1]
"""

teams_schema = {
    'ID': str,
    'City': str,
    'Nickname': str,
    'Abbreviation': str
}

season = 2024
file_path = glob.glob('totals/SEASON=' + str(season) + '/*' )
percentiles_data = pd.read_parquet(file_path)
print(percentiles_data)
#%%