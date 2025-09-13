import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os
# from Home import df_teams, df_games, df_playerstats, df_team_game_logs, df_schedule_and_game_results
import plotly
import plotly.graph_objects as go
from PIL import Image
import sqlite3

# Page configuration
st.set_page_config(
    page_title="🥇 Player Dashboard",
    page_icon="🥇",
    # layout="wide"
    layout="centered"
)

# Set up the page
st.title('Player Dashboard')

# Always use 2025 data
selected_season = 2025

df_teams = st.session_state['df_teams']
df_games = st.session_state['df_games']
df_playerstats = st.session_state['df_playerstats']
df_team_game_logs = st.session_state['df_all_team_game_logs']
df_schedule_and_game_results = st.session_state['df_schedule_and_game_results']
df_all_passing_rushing_receiving = st.session_state['df_all_passing_rushing_receiving']

# Load the comprehensive player data
current_dir = os.path.dirname(os.path.abspath(__file__))
csv_path = os.path.join(current_dir, '../data', 'all_passing_rushing_receiving.csv')
df_player_data = pd.read_csv(csv_path)

# Set the database path for headshots
db_path = os.path.join(current_dir, '../data', 'nfl.db')

# Extract year and week from game_id (format: YYYY_WW_TEAM1_TEAM2)
df_player_data['year'] = df_player_data['game_id'].str.split('_').str[0].astype(int)
df_player_data['week'] = df_player_data['game_id'].str.split('_').str[1].astype(int)

# Filter to selected season and WR/TE positions
df_player_data_filtered = df_player_data[
    (df_player_data['year'] == selected_season) & 
    (df_player_data['position'].isin(['WR', 'TE']))
]

# Helper function to get recent games data (current season + previous season if needed)
def get_recent_games_data(player_name, num_games=6):
    """
    Get the most recent games for a player, using previous season data if current season has insufficient games.
    """
    if player_name is None:
        return None
    
    # Get all data for this player across all years
    player_data = df_player_data[df_player_data['player'] == player_name].copy()
    
    if player_data.empty:
        return None
    
    # Sort by year and week ascending to get oldest games first (for proper timeline)
    player_data = player_data.sort_values(['year', 'week'], ascending=[True, True])
    
    # Take the most recent games up to the requested number
    recent_games = player_data.tail(num_games)
    
    # Create evenly spaced positions for the x-axis
    recent_games = recent_games.copy()
    recent_games['x_position'] = range(len(recent_games))
    
    return recent_games

st.divider()

# Fetch player names from CSV data and headshots from database
def fetch_player_names_and_image():
    # Check if we have any player data for the selected season
    if df_player_data_filtered.empty:
        st.warning(f"No player data available for {selected_season} season yet. Please select 2024 to view player statistics.")
        return None, None
    
    # Get unique player names from CSV
    player_names = df_player_data_filtered['player'].unique().tolist()
    player_names.sort()  # Sort alphabetically
    
    # Try to set default to Justin Jefferson, otherwise use first player
    default_index = 0
    if "Justin Jefferson" in player_names:
        default_index = player_names.index("Justin Jefferson")
    
    selected_player = st.selectbox("Select Player", options=player_names, index=default_index)
    
    # Get headshot URL from database
    headshot_url = None
    try:
        conn = sqlite3.connect(db_path)
        query = """
        SELECT DISTINCT headshot_url
        FROM PlayerStats
        WHERE player_display_name = ?
        AND headshot_url IS NOT NULL 
        AND headshot_url != ''
        LIMIT 1
        """
        headshot_data = pd.read_sql_query(query, conn, params=[selected_player])
        conn.close()
        
        if not headshot_data.empty:
            headshot_url = headshot_data['headshot_url'].iloc[0]
    except Exception as e:
        st.write(f"Could not fetch headshot: {e}")
    
    return selected_player, headshot_url

# 1. Fetch last 6 games and generate a graph using Plotly
def fetch_last_6_games_and_plot(player_name):
    if player_name is None:
        return None, None
    
    # Get recent games data (current season + previous season if needed)
    recent_games = get_recent_games_data(player_name, 6)
    
    if recent_games is None or recent_games.empty:
        return None, None
    
    # Create a line chart with plotly for multiple metrics
    fig = go.Figure()

    fig.add_trace(go.Scatter(x=recent_games['x_position'], y=recent_games['rec_yds'], mode='lines+markers', name='Receiving Yards', line=dict(color='#FF4444')))
    fig.add_trace(go.Scatter(x=recent_games['x_position'], y=recent_games['rec_td'], mode='lines+markers', name='Receiving TDs', line=dict(color='#FFFFFF')))
    fig.add_trace(go.Scatter(x=recent_games['x_position'], y=recent_games['rec'], mode='lines+markers', name='Receptions', line=dict(color='#888888')))
    
    # Create custom x-axis labels showing year and week
    x_labels = [f"{int(year)}-W{int(week):02d}" for year, week in zip(recent_games['year'], recent_games['week'])]
    
    fig.update_layout(
        title=f"Last 6 Games for {player_name}",
        xaxis_title='Game (Year-Week)',
        yaxis_title='Value',
        template="plotly_dark",  # To match the dark theme
        legend_title="Metrics",
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
        height=400,  # Fixed height for better tiling
        # Use evenly spaced positions for the x-axis
        xaxis=dict(
            tickmode='array',  # Use an array for exact tick values
            tickvals=recent_games['x_position'],  # Use evenly spaced positions
            ticktext=x_labels  # Custom labels showing year-week
        )
    )
    return recent_games, fig

# 0. Player Input - Better organized layout
col1, col2 = st.columns([1, 2])
with col1:
    player_name, headshot_url = fetch_player_names_and_image()
    if player_name is not None and pd.notna(headshot_url):  # Check if player_name and URL exist
        try:
            st.image(headshot_url, caption=player_name, use_container_width=True)
        except Exception as e:
            st.write(f"Could not load image for {player_name}")
    elif player_name is not None:
        st.write(f"No image available for {player_name}")
with col2:
    if player_name is not None:
        last_6_games, fig_last_6 = fetch_last_6_games_and_plot(player_name)
        if fig_last_6 is not None:
            st.plotly_chart(fig_last_6, use_container_width=True)

st.divider()

# 2. Fetch last 6 games function
def fetch_last_6_games(player_name):
    if player_name is None:
        return None
    
    # Get recent games data (current season + previous season if needed)
    recent_games = get_recent_games_data(player_name, 6)
    
    if recent_games is None or recent_games.empty:
        return None
    
    # Select relevant columns for display
    display_columns = ['year', 'week', 'team', 'opponent_team', 'rec', 'rec_yds', 'rec_td', 'rec_long', 'targets']
    available_columns = [col for col in display_columns if col in recent_games.columns]
    
    return recent_games[available_columns]

last_6_games = fetch_last_6_games(player_name)
if last_6_games is not None:
    st.subheader('Last 6 Games:')
    st.write(last_6_games)

st.divider()

# 3. Get player longest reception stats for the last 10 games across all opponents
if player_name is not None:
    st.subheader(f"Longest Reception Stats for {player_name}:")
else:
    st.subheader("Longest Reception Stats:")

def plot_last_20_games_reception_trend(player_name):
    if player_name is None:
        return None
    
    # Get recent games data (current season + previous season if needed)
    recent_games = get_recent_games_data(player_name, 15)
    
    if recent_games is None or recent_games.empty:
        return None
    
    # Filter to games with reception data
    recent_games = recent_games.dropna(subset=['rec_long'])
    recent_games = recent_games.drop_duplicates(subset=['game_id']).sort_values(by='game_id', ascending=True)
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=recent_games['game_id'],
        y=recent_games['rec_long'],
        mode='lines+markers',
        marker=dict(color='#FF4444'),
        name=player_name
    ))
    fig.update_layout(
        title=f'Longest Reception in Last 15 Games for {player_name}',
        xaxis_title='Game ID',
        yaxis_title='Longest Reception (yards)',
        xaxis_tickangle=-90,
        template='plotly_dark',
        height=400,  # Fixed height for better tiling
    )
    st.plotly_chart(fig, use_container_width=True)

if player_name is not None:
    plot_last_20_games_reception_trend(player_name)

def plot_reception_distribution(player_name):
    if player_name is None:
        return None
    
    # Get recent games data (current season + previous season if needed)
    recent_games = get_recent_games_data(player_name, 20)  # Get more games for better distribution
    
    if recent_games is None or recent_games.empty:
        return None
    
    # Filter to games with reception data
    recent_games = recent_games.dropna(subset=['rec'])
    
    fig = go.Figure(data=[go.Histogram(
        x=recent_games['rec'],
        nbinsx=10,
        marker_color='#FF4444',
        opacity=0.75
    )])
    
    fig.update_layout(
        title=f'Reception Distribution for {player_name}',
        xaxis_title='Number of Receptions',
        yaxis_title='Frequency',
        template='plotly_dark',
        height=400,  # Fixed height for better tiling
    )
    st.plotly_chart(fig, use_container_width=True)

if player_name is not None:
    plot_reception_distribution(player_name)

def get_player_reception_stats(player_name):
    if player_name is None:
        return None
    
    # Get recent games data (current season + previous season if needed)
    recent_games = get_recent_games_data(player_name, 20)  # Get more games for better stats
    
    if recent_games is None or recent_games.empty:
        return None
    
    # Filter to games with reception data
    recent_games = recent_games[['game_id', 'rec_long']].dropna(subset=['rec_long'])
    recent_games = recent_games.groupby('game_id').agg({'rec_long': 'max'}).reset_index()
    recent_games = recent_games.sort_values(by='game_id', ascending=False)
    
    col1, col2 = st.columns([1, 2])
    with col1:
        st.write(recent_games)
    with col2:
        total_games = len(recent_games)
        avg_rec_long = recent_games['rec_long'].mean()
        max_rec_long = recent_games['rec_long'].max()
        st.write("\n--- Overall Stats ---")
        st.write(f"Total games: {total_games}")
        st.write(f"Average longest reception: {avg_rec_long:.2f}")
        st.write(f"Maximum longest reception: {max_rec_long}")

if player_name is not None:
    get_player_reception_stats(player_name)

st.divider()

# 4. Fetch historical performance function
def fetch_historical_performance(player_name, opponent_team_abbr):
    if player_name is None:
        return None
    
    # Get player data from CSV for all years, not just selected season
    player_data = df_player_data[df_player_data['player'] == player_name].copy()
    
    if player_data.empty:
        return None
    
    # Filter by opponent team
    player_data = player_data[player_data['opponent_team'] == opponent_team_abbr]
    
    if player_data.empty:
        return None
    
    # Select relevant columns
    display_columns = ['year', 'week', 'rec_yds', 'rec_td', 'rec', 'rec_long']
    available_columns = [col for col in display_columns if col in player_data.columns]
    
    return player_data[available_columns].sort_values(by=['year', 'week'])

if player_name is not None:
    st.subheader(f'Historical Performance')
    team_abbr_list = df_teams['TeamID'].tolist()
    opponent_team_abbr = st.selectbox("Select Opponent Team Abbreviation:", options=team_abbr_list)
    historical_performance = fetch_historical_performance(player_name, opponent_team_abbr)
    if historical_performance is not None:
        st.write(historical_performance)
    else:
        st.write("No historical data found for this player against the selected team.")

st.divider()

# 5. Get player longest reception stats function
def get_player_longest_reception_stats(player_name, opponent_team=None):
    if player_name is None:
        return None
    
    # Get player data from CSV
    player_data = df_player_data[df_player_data['player'] == player_name].copy()
    
    if player_data.empty:
        return None
    
    # Filter by opponent team if specified
    if opponent_team:
        player_data = player_data[player_data['opponent_team'] == opponent_team]
    
    if player_data.empty:
        return None
    
    # Get longest reception stats
    longest_stats = player_data[['game_id', 'rec_yds', 'rec_long']].dropna(subset=['rec_yds'])
    longest_stats = longest_stats.sort_values(by='rec_yds', ascending=False).head(1)
    
    return longest_stats

if player_name is not None:
    st.subheader(f'Longest Receptions Against {opponent_team_abbr}: ')
    longest_reception_stats = get_player_longest_reception_stats(player_name, opponent_team_abbr)
    if longest_reception_stats is not None:
        st.write(longest_reception_stats)
    else:
        st.write("No reception data found for this player against the selected team.")

st.divider()
