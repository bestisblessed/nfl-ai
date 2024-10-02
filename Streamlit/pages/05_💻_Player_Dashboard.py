import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os
from Home import df_teams, df_games, df_playerstats, df_team_game_logs, df_schedule_and_game_results

# Set up the page
st.title('Player Dashboard')
df_teams = st.session_state['df_teams']
df_games = st.session_state['df_games']
df_playerstats = st.session_state['df_playerstats']
df_team_game_logs = st.session_state['df_team_game_logs']
df_schedule_and_game_results = st.session_state['df_schedule_and_game_results']
st.divider()

# 1. Fetch last 6 games function
def fetch_last_6_games(player_name):
    df = df_playerstats[(df_playerstats['player_display_name'] == player_name) & 
                        (df_playerstats['season'] == 2023)]
    df = df[['week', 'receiving_yards', 'receiving_tds', 'rushing_tds', 'fantasy_points_ppr']].sort_values(by='week', ascending=False).head(6)
    return df

# Running it with Tyreek Hill
player_name = "Tyreek Hill"
last_6_games = fetch_last_6_games(player_name)
st.write(last_6_games)

# 2. Fetch historical performance function
def fetch_historical_performance(player_name, opponent_team_abbr):
    df = df_playerstats[(df_playerstats['player_display_name'] == player_name) & 
                        ((df_playerstats['home_team'] == opponent_team_abbr) | 
                         (df_playerstats['away_team'] == opponent_team_abbr))]
    df = df[['season', 'week', 'receiving_yards', 'receiving_tds', 'fantasy_points_ppr']].sort_values(by=['season', 'week'])
    return df

# Running it with Tyreek Hill
player_name = "Tyreek Hill"
opponent_team_abbr = "DEN"  # Example opponent abbreviation
historical_performance = fetch_historical_performance(player_name, opponent_team_abbr)
st.write(historical_performance)

# 3. Fetch next opponent function
def fetch_next_opponent(player_name):
    df = df_playerstats[(df_playerstats['player_display_name'] == player_name) & 
                        (df_playerstats['season'] == 2023)]
    next_opponent = df['player_current_team'].drop_duplicates()
    return next_opponent

# Running it with Tyreek Hill
player_name = "Tyreek Hill"
next_opponent = fetch_next_opponent(player_name)
st.write(next_opponent)

# 4. Get player longest reception stats function
def get_player_longest_reception_stats(player_name, opponent_team=None):
    if opponent_team:
        df = df_playerstats[(df_playerstats['player_display_name'] == player_name) & 
                            ((df_playerstats['home_team'] == opponent_team) | 
                             (df_playerstats['away_team'] == opponent_team))]
    else:
        df = df_playerstats[df_playerstats['player_display_name'] == player_name]
    
    df = df[['game_id', 'rec_yds']].sort_values(by='rec_yds', ascending=False).head(1)
    return df

# Running it with Tyreek Hill
player_name = "Tyreek Hill"
opponent_team = "DEN"  # Example opponent team
longest_reception_stats = get_player_longest_reception_stats(player_name, opponent_team)
st.write(longest_reception_stats)
