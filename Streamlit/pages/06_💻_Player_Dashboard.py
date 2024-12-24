import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os
from Home import df_teams, df_games, df_playerstats, df_team_game_logs, df_schedule_and_game_results
import plotly
import plotly.graph_objects as go
from PIL import Image
import sqlite3


# Set up the page
st.title('Player Dashboard')
df_teams = st.session_state['df_teams']
df_games = st.session_state['df_games']
df_playerstats = st.session_state['df_playerstats']
df_team_game_logs = st.session_state['df_all_team_game_logs']
df_schedule_and_game_results = st.session_state['df_schedule_and_game_results']
df_all_passing_rushing_receiving = st.session_state['df_all_passing_rushing_receiving']
st.divider()

# Get the current directory of the script
current_dir = os.path.dirname(os.path.abspath(__file__))

# Set the paths for images and database
image_folder = os.path.join(current_dir, '../images/player-headshots/')
db_path = os.path.join(current_dir, '../data', 'nfl.db')

# Fetch player names and optionally load image in one function
def fetch_player_names_and_image():
    conn = sqlite3.connect(db_path)
    query = """
    SELECT DISTINCT player_display_name
    FROM PlayerStats
    WHERE position IN ('WR', 'TE')
    AND season = 2023
    """
    player_names = pd.read_sql_query(query, conn)['player_display_name'].tolist()
    conn.close()
    # selected_player = st.selectbox("Select Player", options=player_names)
    default_index = player_names.index("Justin Jefferson") if "Justin Jefferson" in player_names else 0
    selected_player = st.selectbox("Select Player", options=player_names, index=default_index)
    first_name, last_name = selected_player.lower().split(' ')
    image_path = None
    for ext in ['png', 'jpg', 'jpeg']:
        potential_path = os.path.join(image_folder, f"{first_name}_{last_name}.{ext}")
        if os.path.exists(potential_path):
            image_path = potential_path
            break
    return selected_player, image_path

# 1. Fetch last 6 games and generate a graph using Plotly
def fetch_last_6_games_and_plot(player_name):
    df = df_playerstats[(df_playerstats['player_display_name'] == player_name) & 
                        (df_playerstats['season'] == 2024)]
    df = df[['week', 'receiving_yards', 'receiving_tds', 'rushing_tds', 'fantasy_points_ppr']].sort_values(by='week', ascending=False).head(6)
    df['total_touchdowns'] = df['receiving_tds'] + df['rushing_tds']

    # Create a line chart with plotly for multiple metrics
    fig = go.Figure()

    fig.add_trace(go.Scatter(x=df['week'], y=df['receiving_yards'], mode='lines+markers', name='Receiving Yards', line=dict(color='blue')))
    fig.add_trace(go.Scatter(x=df['week'], y=df['fantasy_points_ppr'], mode='lines+markers', name='Fantasy Points (PPR)', line=dict(color='red')))
    fig.add_trace(go.Scatter(x=df['week'], y=df['total_touchdowns'], mode='lines+markers', name='Total Touchdowns', line=dict(color='green')))
    fig.update_layout(
        title=f"Last 6 Games for {player_name}",
        xaxis_title='Week',
        yaxis_title='Value',
        template="plotly_dark",  # To match the dark theme
        legend_title="Metrics",
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
        
        # This ensures only exact x-axis values are shown
        xaxis=dict(
            tickmode='array',  # Use an array for exact tick values
            tickvals=df['week'],  # Set the exact week values as ticks
            ticktext=[str(week) for week in df['week']]  # Convert week numbers to strings for display
        )
    )
    return df, fig

# 0. Player Input
col1, col2 = st.columns([0.5, 1])
with col1:
    player_name, image_path = fetch_player_names_and_image() # Fetch the player and image
    if image_path:
        image = Image.open(image_path)
        st.image(image, caption=player_name, use_column_width=True)
    else:
        st.write(f"No image available for {player_name}")
with col2:
    last_6_games, fig_last_6 = fetch_last_6_games_and_plot(player_name)
    st.plotly_chart(fig_last_6)

# 2. Fetch last 6 games function
def fetch_last_6_games(player_name):
    df = df_playerstats[(df_playerstats['player_display_name'] == player_name) & 
                        (df_playerstats['season'] == 2024)]
    # df = df[['week', 'receiving_yards', 'receiving_tds', 'rushing_tds', 'fantasy_points_ppr']].sort_values(by='week', ascending=False).head(6)
    df = df.sort_values(by='week', ascending=False).head(6)
    return df
last_6_games = fetch_last_6_games(player_name)
st.subheader('Last 6 Games:')
st.write(last_6_games)
st.divider()

# 3. Get player longest reception stats for the last 10 games across all opponents
st.subheader(f"Longest Reception Stats for {player_name}:")
def plot_last_20_games_reception_trend(player_name):
    player_data = df_all_passing_rushing_receiving[df_all_passing_rushing_receiving['player'] == player_name].dropna(subset=['rec_long'])
    player_data = player_data.drop_duplicates(subset=['game_id']).sort_values(by='game_id', ascending=True)
    if len(player_data) > 15:
        player_data = player_data[-15:]
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=player_data['game_id'],
        y=player_data['rec_long'],
        mode='lines+markers',
        marker=dict(color='blue'),
        name=player_name
    ))
    fig.update_layout(
        title=f'Longest Reception in Last 15 Games for {player_name}',
        xaxis_title='Game ID',
        yaxis_title='Longest Reception (yards)',
        xaxis_tickangle=-90,
        template='plotly_white',
        height=500,
        # width=800
    )
    st.plotly_chart(fig)
plot_last_20_games_reception_trend(player_name)

def plot_reception_distribution(player_name):
    player_data = df_all_passing_rushing_receiving[df_all_passing_rushing_receiving['player'] == player_name].dropna(subset=['rec_long'])
    fig = go.Figure(data=[go.Histogram(
        x=player_data['rec_long'],
        nbinsx=10,
        marker_color='blue',
        opacity=0.75
    )])
    fig.update_layout(
        title=f'Longest Reception Distribution for {player_name}',
        xaxis_title='Longest Reception (yards)',
        yaxis_title='Frequency',
        template='plotly_white'
    )
    st.plotly_chart(fig)
plot_reception_distribution(player_name)

def plot_reception_distribution(player_name):
    player_data = df_all_passing_rushing_receiving[df_all_passing_rushing_receiving['player'] == player_name].dropna(subset=['rec'])
    fig = go.Figure(data=[go.Histogram(
        x=player_data['rec'],
        nbinsx=10,
        marker_color='blue',
        opacity=0.75
    )])
    
    fig.update_layout(
        title=f'Reception Distribution for {player_name}',
        xaxis_title='Number of Receptions',
        yaxis_title='Frequency',
        template='plotly_white'
    )
    st.plotly_chart(fig)
plot_reception_distribution(player_name)

def get_player_reception_stats(player_name):
    player_data = df_all_passing_rushing_receiving[df_all_passing_rushing_receiving['player'] == player_name]
    player_data = player_data[['game_id', 'rec_long']].dropna(subset=['rec_long'])
    player_data = player_data.groupby('game_id').agg({'rec_long': 'max'}).reset_index()
    player_data = player_data.sort_values(by='game_id', ascending=False)
    col1, col2 = st.columns([1, 2.5])
    with col1:
        st.write(player_data)
    with col2:
        total_games = len(player_data)
        avg_rec_long = player_data['rec_long'].mean()
        max_rec_long = player_data['rec_long'].max()
        st.write("\n--- Overall Stats ---")
        st.write(f"Total games: {total_games}")
        st.write(f"Average longest reception: {avg_rec_long:.2f}")
        st.write(f"Maximum longest reception: {max_rec_long}")
get_player_reception_stats(player_name)
st.divider()

# 4. Fetch historical performance function
def fetch_historical_performance(player_name, opponent_team_abbr):
    df = df_playerstats[(df_playerstats['player_display_name'] == player_name) & 
                        ((df_playerstats['home_team'] == opponent_team_abbr) | 
                         (df_playerstats['away_team'] == opponent_team_abbr))]
    df = df[['season', 'week', 'receiving_yards', 'receiving_tds', 'fantasy_points_ppr']].sort_values(by=['season', 'week'])
    return df
st.subheader(f'Historical Performance')
team_abbr_list = df_teams['TeamID'].tolist()
opponent_team_abbr = st.selectbox("Select Opponent Team Abbreviation:", options=team_abbr_list)
historical_performance = fetch_historical_performance(player_name, opponent_team_abbr)
st.write(historical_performance)
st.divider()

# 5. Get player longest reception stats function
def get_player_longest_reception_stats(player_name, opponent_team=None):
    if opponent_team:
        df = df_playerstats[(df_playerstats['player_display_name'] == player_name) & 
                            ((df_playerstats['home_team'] == opponent_team) | 
                             (df_playerstats['away_team'] == opponent_team))]
    else:
        df = df_playerstats[df_playerstats['player_display_name'] == player_name]
    
    df = df[['game_id', 'receiving_yards']].sort_values(by='receiving_yards', ascending=False).head(1)
    return df
st.subheader(f'Longest Receptions Against {opponent_team_abbr}: ')
longest_reception_stats = get_player_longest_reception_stats(player_name, opponent_team_abbr)
st.write(longest_reception_stats)
st.divider()
