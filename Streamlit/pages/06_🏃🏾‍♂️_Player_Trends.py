import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

### --- Title and Data --- ###
st.title('Player Trends')
df_teams = pd.read_csv('./data/Teams.csv')
df_games = pd.read_csv('./data/Games.csv')
df_playerstats = pd.read_csv('./data/PlayerStats.csv')

### ---  --- ###
st.divider()
st.header("")
st.write("##")