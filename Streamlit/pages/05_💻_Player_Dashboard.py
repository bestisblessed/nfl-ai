import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os
import streamlit as st
from Home import df_teams, df_games, df_playerstats, df_team_game_logs, df_schedule_and_game_results
import sqlite3


st.title('Player Dashboard')
df_teams = st.session_state['df_teams']
df_games = st.session_state['df_games']
df_playerstats = st.session_state['df_playerstats']
df_team_game_logs = st.session_state['df_team_game_logs']
df_schedule_and_game_results = st.session_state['df_schedule_and_game_results']
st.divider()


def fetch_last_6_games(player_name):
    conn = sqlite3.connect('data/nfl.db')
    query = f"""
    SELECT week, receiving_yards, receiving_tds, rushing_tds, fantasy_points_ppr
    FROM PlayerStats
    WHERE player_display_name = '{player_name}'
    AND season = 2023
    ORDER BY week DESC
    LIMIT 6;
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

# Running it with Tyreek Hill
player_name = "Tyreek Hill"
last_6_games = fetch_last_6_games(player_name)
st.write(last_6_games)

def fetch_historical_performance(player_name, opponent_team_abbr):
    conn = sqlite3.connect('data/nfl.db')
    query = f"""
    SELECT season, week, receiving_yards, receiving_tds, fantasy_points_ppr
    FROM PlayerStats
    WHERE player_display_name = '{player_name}'
    AND (home_team = '{opponent_team_abbr}' OR away_team = '{opponent_team_abbr}')
    ORDER BY season, week;
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

# Running it with Tyreek Hill and an opponent abbreviation
player_name = "Tyreek Hill"
opponent_team_abbr = "DEN"  # Example opponent abbreviation for Denver Broncos
historical_performance = fetch_historical_performance(player_name, opponent_team_abbr)
st.write(historical_performance)


def fetch_next_opponent(player_name):
    conn = sqlite3.connect('data/nfl.db')
    team_query = f"""
    SELECT DISTINCT player_current_team
    FROM PlayerStats
    WHERE player_display_name = '{player_name}'
    AND season = 2023;
    """
    team_df = pd.read_sql_query(team_query, conn)
    conn.close()
    return team_df

# Running it with Tyreek Hill
player_name = "Tyreek Hill"
next_opponent = fetch_next_opponent(player_name)
st.write(next_opponent)


def get_player_longest_reception_stats(player_name, opponent_team=None):
    conn = sqlite3.connect('data/nfl.db')
    query = f"""
    SELECT game_id, rec_yds
    FROM PlayerStats
    WHERE player_display_name = '{player_name}'
    AND (home_team = '{opponent_team}' OR away_team = '{opponent_team}')
    ORDER BY rec_yds DESC
    LIMIT 1;
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

# Running it with Tyreek Hill
player_name = "Tyreek Hill"
opponent_team = "DEN"  # Example opponent team
longest_reception_stats = get_player_longest_reception_stats(player_name, opponent_team)
st.write(longest_reception_stats)

