import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os
from Home import df_teams, df_games, df_playerstats, df_team_game_logs, df_schedule_and_game_results
import plotly.graph_objects as go


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

# 1. Fetch last 6 games and generate a graph using Plotly
def fetch_last_6_games_and_plot(player_name):
    df = df_playerstats[(df_playerstats['player_display_name'] == player_name) & 
                        (df_playerstats['season'] == 2023)]
    df = df[['week', 'receiving_yards', 'receiving_tds', 'rushing_tds', 'fantasy_points_ppr']].sort_values(by='week', ascending=False).head(6)
    df['total_touchdowns'] = df['receiving_tds'] + df['rushing_tds']

    # Create a line chart with plotly for multiple metrics
    fig = go.Figure()

    fig.add_trace(go.Scatter(x=df['week'], y=df['receiving_yards'], mode='lines+markers', name='Receiving Yards', line=dict(color='blue')))
    fig.add_trace(go.Scatter(x=df['week'], y=df['fantasy_points_ppr'], mode='lines+markers', name='Fantasy Points (PPR)', line=dict(color='red')))
    fig.add_trace(go.Scatter(x=df['week'], y=df['total_touchdowns'], mode='lines+markers', name='Total Touchdowns', line=dict(color='green')))

    # Update layout for the chart
    fig.update_layout(
        title=f"Last 6 Games for {player_name}",
        xaxis_title='Week',
        yaxis_title='Value',
        template="plotly_dark",  # To match the dark theme
        legend_title="Metrics",
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01)
    )

    return df, fig

# Running it with Tyreek Hill
player_name = "Tyreek Hill"
last_6_games, fig_last_6 = fetch_last_6_games_and_plot(player_name)
st.write(last_6_games)
st.plotly_chart(fig_last_6)

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
    
    df = df[['game_id', 'receiving_yards']].sort_values(by='receiving_yards', ascending=False).head(1)
    return df

# Running it with Tyreek Hill
player_name = "Tyreek Hill"
opponent_team = "DEN"  # Example opponent team
longest_reception_stats = get_player_longest_reception_stats(player_name, opponent_team)
st.write(longest_reception_stats)
