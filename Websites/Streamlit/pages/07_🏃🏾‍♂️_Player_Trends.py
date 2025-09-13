import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os
import streamlit as st
# from Home import df_teams, df_games, df_playerstats, df_team_game_logs, df_schedule_and_game_results

# # Define the base directory
# base_dir = os.path.abspath('../data')

# # Use absolute paths
# df_teams = pd.read_csv(os.path.join(base_dir, 'Teams.csv'))
# df_games = pd.read_csv(os.path.join(base_dir, 'Games.csv'))
# df_playerstats = pd.read_csv(os.path.join(base_dir, 'PlayerStats.csv'))

### --- Title and Data --- ###
st.title('Player Trends')

# Season selector
selected_season = st.selectbox("Select Season:", [2025, 2024], index=0)

# df_teams = pd.read_csv('./data/Teams.csv')
# df_games = pd.read_csv('./data/Games.csv')
# df_playerstats = pd.read_csv('./data/PlayerStats.csv')

# Store DataFrames in session state
# st.session_state['df_teams'] = df_teams
# st.session_state['df_games'] = df_games
# st.session_state['df_playerstats'] = df_playerstats
# st.session_state['df_team_game_logs'] = df_team_game_logs
# st.session_state['df_schedule_and_game_results'] = df_schedule_and_game_results
df_teams = st.session_state['df_teams']
df_games = st.session_state['df_games']
df_playerstats = st.session_state['df_playerstats']
df_team_game_logs = st.session_state['df_all_team_game_logs']
df_schedule_and_game_results = st.session_state['df_schedule_and_game_results']

st.divider()

tab1, tab2, tab3, tab4 = st.tabs(["QBs", "RBs", "WRs", "TEs"])

with tab1:
### SACKS ###
    st.header('Quarterback Sack Rankings')
    # df_playerstats = pd.read_csv('./data/PlayerStats.csv')
    qb_selected_stats = df_playerstats[(df_playerstats['position'] == 'QB') & (df_playerstats['season'] == selected_season)]
    qb_sacked_selected = qb_selected_stats.groupby('player_display_name')['sacks'].sum().reset_index()
    qb_sacked_ranked_selected = qb_sacked_selected.sort_values(by='sacks')
    plt.figure(figsize=(12, len(qb_sacked_ranked_selected) / 2))
    bars = plt.barh(qb_sacked_ranked_selected['player_display_name'], qb_sacked_ranked_selected['sacks'], color='skyblue')
    plt.xlabel('Number of Sacks', fontsize=32)
    plt.ylabel('Quarterbacks', fontsize=32)
    plt.title(f'Number of Sacks for NFL Quarterbacks in {selected_season}', fontsize=16)
    plt.xticks(fontsize=8)
    plt.yticks(fontsize=8)
    plt.bar_label(bars)
    st.pyplot(plt)

    ### INTERCEPTIONS ###
    st.header('Quarterback Interception Rankings')
    qb_interceptions_stats = df_playerstats[(df_playerstats['position'] == 'QB') & (df_playerstats['season'] == selected_season)]
    qb_interceptions_selected = qb_interceptions_stats.groupby('player_display_name')['interceptions'].sum().reset_index()
    qb_interceptions_ranked_selected = qb_interceptions_selected.sort_values(by='interceptions')
    plt.figure(figsize=(12, len(qb_interceptions_ranked_selected) / 2))
    bars = plt.barh(qb_interceptions_ranked_selected['player_display_name'], qb_interceptions_ranked_selected['interceptions'], color='salmon')
    plt.xlabel('Number of Interceptions', fontsize=32)
    plt.ylabel('Quarterbacks', fontsize=32)
    plt.title(f'Number of Interceptions for NFL Quarterbacks in {selected_season}', fontsize=16)
    plt.xticks(fontsize=8)
    plt.yticks(fontsize=8)
    plt.bar_label(bars)
    st.pyplot(plt)
