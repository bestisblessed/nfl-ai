import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os
import streamlit as st
from Home import df_teams, df_games, df_playerstats, df_team_game_logs, df_schedule_and_game_results


st.title('Player Dashboard')
df_teams = st.session_state['df_teams']
df_games = st.session_state['df_games']
df_playerstats = st.session_state['df_playerstats']
df_team_game_logs = st.session_state['df_team_game_logs']
df_schedule_and_game_results = st.session_state['df_schedule_and_game_results']
st.divider()
