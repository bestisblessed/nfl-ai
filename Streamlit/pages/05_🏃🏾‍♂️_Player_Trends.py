import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os

# Define the base directory
base_dir = os.path.abspath('./data')

# Use absolute paths
df_teams = pd.read_csv(os.path.join(base_dir, 'Teams.csv'))
df_games = pd.read_csv(os.path.join(base_dir, 'Games.csv'))
df_playerstats = pd.read_csv(os.path.join(base_dir, 'PlayerStats.csv'))

### --- Title and Data --- ###
st.title('Player Trends')
# df_teams = pd.read_csv('./data/Teams.csv')
# df_games = pd.read_csv('./data/Games.csv')
# df_playerstats = pd.read_csv('./data/PlayerStats.csv')
st.divider()

tab1, tab2, tab3, tab4 = st.tabs(["QBs", "RBs", "WRs", "TEs"])

with tab1:
### SACKS ###
    st.header('Quarterback Sack Rankings')
    player_stats_df = pd.read_csv('./data/PlayerStats.csv')
    qb_2023_stats = player_stats_df[(player_stats_df['position'] == 'QB') & (player_stats_df['season'] == 2023)]
    qb_sacked_2023 = qb_2023_stats.groupby('player_display_name')['sacks'].sum().reset_index()
    qb_sacked_ranked_2023 = qb_sacked_2023.sort_values(by='sacks')
    plt.figure(figsize=(12, len(qb_sacked_ranked_2023) / 2))
    bars = plt.barh(qb_sacked_ranked_2023['player_display_name'], qb_sacked_ranked_2023['sacks'], color='skyblue')
    plt.xlabel('Number of Sacks', fontsize=32)
    plt.ylabel('Quarterbacks', fontsize=32)
    plt.title('Number of Sacks for NFL Quarterbacks in 2023', fontsize=16)
    plt.xticks(fontsize=8)
    plt.yticks(fontsize=8)
    plt.bar_label(bars)
    st.pyplot(plt)

    ### INTERCEPTIONS ###
    st.header('Quarterback Interception Rankings')
    qb_interceptions_stats = player_stats_df[(player_stats_df['position'] == 'QB') & (player_stats_df['season'] == 2023)]
    qb_interceptions_2023 = qb_interceptions_stats.groupby('player_display_name')['interceptions'].sum().reset_index()
    qb_interceptions_ranked_2023 = qb_interceptions_2023.sort_values(by='interceptions')
    plt.figure(figsize=(12, len(qb_interceptions_ranked_2023) / 2))
    bars = plt.barh(qb_interceptions_ranked_2023['player_display_name'], qb_interceptions_ranked_2023['interceptions'], color='salmon')
    plt.xlabel('Number of Interceptions', fontsize=32)
    plt.ylabel('Quarterbacks', fontsize=32)
    plt.title('Number of Interceptions for NFL Quarterbacks in 2023', fontsize=16)
    plt.xticks(fontsize=8)
    plt.yticks(fontsize=8)
    plt.bar_label(bars)
    st.pyplot(plt)
