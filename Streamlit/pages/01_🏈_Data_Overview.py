import streamlit as st
import pandas as pd
import numpy as np

st.title('Data Overview')

df_teams = st.session_state['df_teams']
df_games = st.session_state['df_games'] 
df_playerstats = st.session_state['df_playerstats']
dataframes = [df_teams, df_games, df_playerstats]

# Dropdown button for datasets 
option = st.selectbox('Choose a DataFrame to display:', ('None', 'Teams', 'Games', 'Player Stats'))

if option == 'Teams':
    st.header('Teams DataFrame')
    st.write('Statistics:')
    st.write(df_teams.describe())
    st.write('First few rows:')
    st.write(df_teams.head())

elif option == 'Games':
    st.header('Games DataFrame')
    st.write('Statistics:')
    st.write(df_games.describe())
    st.write('First few rows:')
    st.write(df_games.head())

elif option == 'Player Stats':
    st.header('Player Stats DataFrame')
    st.write('Statistics:')
    st.write(df_playerstats.describe())
    st.write('First few rows:')
    st.write(df_playerstats.head())

# # v1
# # Displaying dataframes statistics
# table_count = 1
# for df in dataframes:
#     st.header(f'Table: {table_count} Statistics')
#     st.write(df.describe())
#     st.header(f'Table: {table_count} Headers')
#     st.write(df.head())
#     table_count = table_count + 1


# # v2
# # Button for displaying Teams Dataframe
# if st.button('Show Teams Dataframe'):
#     st.header('Teams Dataframe Statistics')
#     st.write(df_teams.describe())
#     st.header('Teams Dataframe Headers')
#     st.write(df_teams.head())

# # Button for displaying Games Dataframe
# if st.button('Show Games Dataframe'):
#     st.header('Games Dataframe Statistics')
#     st.write(df_games.describe())
#     st.header('Games Dataframe Headers')
#     st.write(df_games.head())

# # Button for displaying Player Stats Dataframe
# if st.button('Show Player Stats Dataframe'):
#     st.header('Player Stats Dataframe Statistics')
#     st.write(df_playerstats.describe())
#     st.header('Player Stats Dataframe Headers')
#     st.write(df_playerstats.head())