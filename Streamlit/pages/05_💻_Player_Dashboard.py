# import streamlit as st
# import pandas as pd
# import matplotlib.pyplot as plt
# import os
# from Home import df_teams, df_games, df_playerstats, df_team_game_logs, df_schedule_and_game_results

# # Set up the page
# st.title('Player Dashboard')
# df_teams = st.session_state['df_teams']
# df_games = st.session_state['df_games']
# df_playerstats = st.session_state['df_playerstats']
# df_team_game_logs = st.session_state['df_team_game_logs']
# df_schedule_and_game_results = st.session_state['df_schedule_and_game_results']
# st.divider()

# # 1. Fetch last 6 games function
# def fetch_last_6_games(player_name):
#     df = df_playerstats[(df_playerstats['player_display_name'] == player_name) & 
#                         (df_playerstats['season'] == 2023)]
#     df = df[['week', 'receiving_yards', 'receiving_tds', 'rushing_tds', 'fantasy_points_ppr']].sort_values(by='week', ascending=False).head(6)
#     return df

# # Running it with Tyreek Hill
# player_name = "Tyreek Hill"
# last_6_games = fetch_last_6_games(player_name)
# st.write(last_6_games)

# # 2. Fetch historical performance function
# def fetch_historical_performance(player_name, opponent_team_abbr):
#     df = df_playerstats[(df_playerstats['player_display_name'] == player_name) & 
#                         ((df_playerstats['home_team'] == opponent_team_abbr) | 
#                          (df_playerstats['away_team'] == opponent_team_abbr))]
#     df = df[['season', 'week', 'receiving_yards', 'receiving_tds', 'fantasy_points_ppr']].sort_values(by=['season', 'week'])
#     return df

# # Running it with Tyreek Hill
# player_name = "Tyreek Hill"
# opponent_team_abbr = "DEN"  # Example opponent abbreviation
# historical_performance = fetch_historical_performance(player_name, opponent_team_abbr)
# st.write(historical_performance)

# # 3. Fetch next opponent function
# def fetch_next_opponent(player_name):
#     df = df_playerstats[(df_playerstats['player_display_name'] == player_name) & 
#                         (df_playerstats['season'] == 2023)]
#     next_opponent = df['player_current_team'].drop_duplicates()
#     return next_opponent

# # Running it with Tyreek Hill
# player_name = "Tyreek Hill"
# next_opponent = fetch_next_opponent(player_name)
# st.write(next_opponent)

# # 4. Get player longest reception stats function
# def get_player_longest_reception_stats(player_name, opponent_team=None):
#     if opponent_team:
#         df = df_playerstats[(df_playerstats['player_display_name'] == player_name) & 
#                             ((df_playerstats['home_team'] == opponent_team) | 
#                              (df_playerstats['away_team'] == opponent_team))]
#     else:
#         df = df_playerstats[df_playerstats['player_display_name'] == player_name]
    
#     df = df[['game_id', 'receiving_yards']].sort_values(by='receiving_yards', ascending=False).head(1)
#     return df

# # Running it with Tyreek Hill
# player_name = "Tyreek Hill"
# opponent_team = "DEN"  # Example opponent team
# longest_reception_stats = get_player_longest_reception_stats(player_name, opponent_team)
# st.write(longest_reception_stats)

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

# 1. Fetch last 6 games and generate a graph
def fetch_last_6_games(player_name):
    df = df_playerstats[(df_playerstats['player_display_name'] == player_name) & 
                        (df_playerstats['season'] == 2023)]
    df = df[['week', 'receiving_yards', 'receiving_tds', 'rushing_tds', 'fantasy_points_ppr']].sort_values(by='week', ascending=False).head(6)
    
    # Create a bar chart for fantasy points in the last 6 games
    fig, ax = plt.subplots()
    ax.bar(df['week'], df['fantasy_points_ppr'])
    ax.set_title(f'Fantasy Points in Last 6 Games for {player_name}')
    ax.set_xlabel('Week')
    ax.set_ylabel('Fantasy Points (PPR)')
    
    return df, fig

# Running it with Tyreek Hill
player_name = "Tyreek Hill"
last_6_games, fig_last_6 = fetch_last_6_games(player_name)
st.write(last_6_games)
st.pyplot(fig_last_6)

# 2. Fetch historical performance and generate a graph
def fetch_historical_performance(player_name, opponent_team_abbr):
    df = df_playerstats[(df_playerstats['player_display_name'] == player_name) & 
                        ((df_playerstats['home_team'] == opponent_team_abbr) | 
                         (df_playerstats['away_team'] == opponent_team_abbr))]
    df = df[['season', 'week', 'receiving_yards', 'receiving_tds', 'fantasy_points_ppr']].sort_values(by=['season', 'week'])

    # Create a line chart for receiving yards and touchdowns over time
    fig, ax = plt.subplots()
    ax.plot(df['week'], df['receiving_yards'], label='Receiving Yards', marker='o')
    ax.plot(df['week'], df['receiving_tds'], label='Receiving TDs', marker='x')
    ax.set_title(f'Historical Performance of {player_name} vs {opponent_team_abbr}')
    ax.set_xlabel('Week')
    ax.set_ylabel('Performance')
    ax.legend()
    
    return df, fig

# Running it with Tyreek Hill and Denver Broncos
player_name = "Tyreek Hill"
opponent_team_abbr = "DEN"  # Example opponent abbreviation
historical_performance, fig_historical = fetch_historical_performance(player_name, opponent_team_abbr)
st.write(historical_performance)
st.pyplot(fig_historical)

# 3. Fetch next opponent (no graph needed for this one)
def fetch_next_opponent(player_name):
    df = df_playerstats[(df_playerstats['player_display_name'] == player_name) & 
                        (df_playerstats['season'] == 2023)]
    next_opponent = df['player_current_team'].drop_duplicates()
    return next_opponent

# Running it with Tyreek Hill
player_name = "Tyreek Hill"
next_opponent = fetch_next_opponent(player_name)
st.write(next_opponent)

# 4. Get player longest reception stats and generate a graph
def get_player_longest_reception_stats(player_name, opponent_team=None):
    if opponent_team:
        df = df_playerstats[(df_playerstats['player_display_name'] == player_name) & 
                            ((df_playerstats['home_team'] == opponent_team) | 
                             (df_playerstats['away_team'] == opponent_team))]
    else:
        df = df_playerstats[df_playerstats['player_display_name'] == player_name]

    df = df[['game_id', 'receiving_yards']].sort_values(by='receiving_yards', ascending=False).head(1)

    # Create a bar chart for the longest reception yards
    fig, ax = plt.subplots()
    ax.bar(df['game_id'], df['receiving_yards'])
    ax.set_title(f'Longest Reception for {player_name}')
    ax.set_xlabel('Game ID')
    ax.set_ylabel('Reception Yards')
    
    return df, fig

# Running it with Tyreek Hill
player_name = "Tyreek Hill"
opponent_team = "DEN"  # Example opponent team
longest_reception_stats, fig_longest_reception = get_player_longest_reception_stats(player_name, opponent_team)
st.write(longest_reception_stats)
st.pyplot(fig_longest_reception)
