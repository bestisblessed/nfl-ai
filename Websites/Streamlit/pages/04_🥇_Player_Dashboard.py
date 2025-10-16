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
    layout="wide"
    # layout="centered"
)

st.markdown(f"""
    <div style='text-align: center;'>
        <div style='font-size: 3.1rem; font-weight: 800; padding-bottom: 0.5rem;'>
            Player Dashboard
        </div>
        <div style='color: #7f8c8d; font-size: 1rem; margin-top: 0; line-height: 1.2;'>
            Comprehensive player performance analytics and historical trends
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

# Always use 2025 data
selected_season = 2025

# Load data using cached function
@st.cache_data(show_spinner=False)
def load_data():
    """Load all required CSV files for the Player Dashboard"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    try:
        df_teams = pd.read_csv(os.path.join(current_dir, '../data', 'Teams.csv'))
        df_games = pd.read_csv(os.path.join(current_dir, '../data', 'Games.csv'))
        df_playerstats = pd.read_csv(os.path.join(current_dir, '../data', 'PlayerStats.csv'))
        df_team_game_logs = pd.read_csv(os.path.join(current_dir, '../data', 'all_team_game_logs.csv'))
        df_schedule_and_game_results = pd.read_csv(os.path.join(current_dir, '../data', 'all_teams_schedule_and_game_results_merged.csv'))
        df_all_passing_rushing_receiving = pd.read_csv(os.path.join(current_dir, '../data', 'all_passing_rushing_receiving.csv'))
        
        return (df_teams, df_games, df_playerstats, df_team_game_logs, 
                df_schedule_and_game_results, df_all_passing_rushing_receiving)
    except FileNotFoundError as e:
        st.error(f"Error loading data files: {e}")
        st.stop()

# Load all data
df_teams, df_games, df_playerstats, df_team_game_logs, df_schedule_and_game_results, df_all_passing_rushing_receiving = load_data()

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
def get_recent_games_data(player_name, num_games=10):
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
    # Get all players from the full dataset
    all_players_data = df_player_data[df_player_data['year'] == selected_season]
    
    if all_players_data.empty:
        st.warning(f"No player data available for {selected_season} season yet. Please select 2024 to view player statistics.")
        return None, None
    
    # Get unique player names from CSV
    player_names = all_players_data['player'].unique().tolist()
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

# 1. Fetch last 10 games and generate a graph using Plotly
def fetch_last_10_games_and_plot(player_name):
    if player_name is None:
        return None, None
    
    # Get recent games data (current season + previous season if needed)
    recent_games = get_recent_games_data(player_name, 10)
    
    if recent_games is None or recent_games.empty:
        return None, None
    
    # Create a line chart with plotly for continuous metrics
    fig = go.Figure()

    # Receiving yards and receptions (continuous metrics that work well as lines)
    fig.add_trace(go.Scatter(
        x=recent_games['x_position'], 
        y=recent_games['rec_yds'], 
        mode='lines+markers+text', 
        name='Receiving Yards', 
        line=dict(color='#FF4444'),
        text=recent_games['rec_yds'].astype(int),
        textposition='top center',
        textfont=dict(color='#FF4444', size=10)
    ))
    fig.add_trace(go.Scatter(
        x=recent_games['x_position'], 
        y=recent_games['rec'], 
        mode='lines+markers+text', 
        name='Receptions', 
        line=dict(color='#888888'),
        text=recent_games['rec'].astype(int),
        textposition='top center',
        textfont=dict(color='#888888', size=10)
    ))
    
    # Create custom x-axis labels showing year and week
    x_labels = [f"{int(year)}-W{int(week):02d}" for year, week in zip(recent_games['year'], recent_games['week'])]
    
    fig.update_layout(
        title=f"Last 10 Games for {player_name}",
        # xaxis_title='Game (Year-Week)',
        yaxis_title='Value',
        template="plotly_dark",  # To match the dark theme
        legend_title="Metrics",
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
        height=400,  # Fixed height for better tiling
        title_font_size=16,  # Consistent title size
        # Use evenly spaced positions for the x-axis
        xaxis=dict(
            tickmode='array',  # Use an array for exact tick values
            tickvals=recent_games['x_position'],  # Use evenly spaced positions
            ticktext=x_labels  # Custom labels showing year-week
        )
    )
    return recent_games, fig

# 0. Player Input - Better organized layout
col1, spacer_col, col2 = st.columns([1, 0.1, 2])
with col1:
    player_name, headshot_url = fetch_player_names_and_image()
    if player_name is not None and pd.notna(headshot_url):  # Check if player_name and URL exist
        try:
            st.image(headshot_url, caption=player_name, use_container_width=True)
        except Exception as e:
            st.write(f"Could not load image for {player_name}")
    elif player_name is not None:
        st.write(f"No image available for {player_name}")

with spacer_col:
    st.write("")  # Empty spacer column

with col2:
    if player_name is not None:
        # Add overall stats metrics above the chart (2025 season only)
        season_2025_data = df_player_data[(df_player_data['player'] == player_name) & (df_player_data['year'] == selected_season)]
        
        if not season_2025_data.empty:
            st.markdown("")
            st.markdown("#### 2025 Season Stats")
            st.markdown("")
            
            # Get player position
            player_position = season_2025_data['position'].iloc[0] if 'position' in season_2025_data.columns else 'Unknown'
            
            # Create metrics columns for better visual display
            metric_col1, metric_col2, metric_col3 = st.columns(3)
            
            with metric_col1:
                total_rec_yds = season_2025_data['rec_yds'].sum() if 'rec_yds' in season_2025_data.columns else 0
                st.metric(
                    label="Total Rec Yards",
                    value=f"{total_rec_yds:.0f}",
                    help="Total receiving yards (2025)"
                )
            
            with metric_col2:
                avg_rec_per_game = season_2025_data['rec'].mean() if 'rec' in season_2025_data.columns else 0
                st.metric(
                    label="Avg Rec/Game",
                    value=f"{avg_rec_per_game:.1f}",
                    help="Average receptions per game (2025)"
                )
            
            with metric_col3:
                total_tds = season_2025_data['rec_td'].sum() if 'rec_td' in season_2025_data.columns else 0
                st.metric(
                    label="Total TDs",
                    value=f"{total_tds:.0f}",
                    help="Total receiving touchdowns (2025)"
                )
        else:
            st.markdown("#### 📊 2025 Season Stats")
            st.info("No 2025 season data available yet")
        
        # Add some spacing before the chart
        st.markdown("")
        
        # Then show the graph
        last_10_games, fig_last_10 = fetch_last_10_games_and_plot(player_name)
        if fig_last_10 is not None:
            st.plotly_chart(fig_last_10, use_container_width=True)

st.divider()

# 2. Fetch last 10 games function
def fetch_last_10_games(player_name):
    if player_name is None:
        return None
    
    # Get recent games data (current season + previous season if needed)
    recent_games = get_recent_games_data(player_name, 10)
    
    if recent_games is None or recent_games.empty:
        return None
    
    # Select relevant columns for display
    display_columns = ['year', 'week', 'team', 'opponent_team', 'rec', 'rec_yds', 'rec_td', 'rec_long', 'targets']
    available_columns = [col for col in display_columns if col in recent_games.columns]
    
    # Reverse the order so most recent games appear first
    return recent_games[available_columns].iloc[::-1]

last_10_games = fetch_last_10_games(player_name)
if last_10_games is not None:
    # st.subheader('Last 10 Games:')
    st.subheader(f"Last 10 Games for {player_name}")
    st.write("")
    st.dataframe(last_10_games, use_container_width=True)

st.divider()

# 3. Get player longest reception stats for the last 10 games across all opponents
if player_name is not None:
    st.subheader(f"Longest Receptions for {player_name}:")
else:
    st.subheader("Longest Reception Stats:")

def plot_last_20_games_reception_trend(player_name):
    if player_name is None:
        return None
    
    # Get recent games data (current season + previous season if needed)
    recent_games = get_recent_games_data(player_name, 10)
    
    if recent_games is None or recent_games.empty:
        return None
    
    # Filter to games with reception data
    recent_games = recent_games.dropna(subset=['rec_long'])
    recent_games = recent_games.drop_duplicates(subset=['game_id']).sort_values(by='game_id', ascending=True)
    
    # Create columns with spacing between graph and table
    graph_col, spacer_col, table_col = st.columns([3.5, 0.05, 1])
    
    with graph_col:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=recent_games['game_id'],
            y=recent_games['rec_long'],
            mode='lines+markers+text',
            marker=dict(color='#800080'),
            name=player_name,
            text=recent_games['rec_long'].astype(int),
            textposition='top center',
            textfont=dict(color='#800080', size=12)
        ))
        fig.update_layout(
            # title=f'Longest Reception in Last 15 Games for {player_name}',
            xaxis_title='Game ID',
            yaxis_title='Longest Reception (yards)',
            xaxis_tickangle=-90,
            template='plotly_dark',
            height=500,  # Fixed height for better tiling
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with spacer_col:
        st.write("")  # Empty spacer column
    
    with table_col:
        # st.markdown("**Game Data**")
        # Display only essential columns for the narrow table
        st.markdown("")
        st.markdown("")
        st.markdown(" ")
        st.markdown(" ")
        st.markdown(" ")
        st.markdown(" ")
        st.write("")
        st.write("")
        table_data = recent_games[['game_id', 'rec_long']].copy()
        # Reverse order to show most recent games first
        table_data = table_data.iloc[::-1]
        st.dataframe(table_data, use_container_width=True, height=350)

if player_name is not None:
    plot_last_20_games_reception_trend(player_name)
    st.divider()
    st.write("")
    st.write("")
    
    st.subheader(f"Reception Distribution for {player_name} (L20 Games):")

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
        # title=f'Reception Distribution for {player_name}',
        xaxis_title='Number of Receptions',
        yaxis_title='Frequency',
        template='plotly_dark',
        height=400,  # Fixed height for better tiling
    )
    st.plotly_chart(fig, use_container_width=True)

if player_name is not None:
    plot_reception_distribution(player_name)

# Removed get_player_reception_stats function - data now displayed inline with the graph

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
    
    # Sort by year and week descending (most recent first), then reverse for display
    return player_data[available_columns].sort_values(by=['year', 'week'], ascending=[False, False])

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
    
    # Reverse order to show most recent first
    return longest_stats.iloc[::-1]

if player_name is not None:
    st.subheader(f'Longest Receptions Against {opponent_team_abbr}: ')
    longest_reception_stats = get_player_longest_reception_stats(player_name, opponent_team_abbr)
    if longest_reception_stats is not None:
        st.write(longest_reception_stats)
    else:
        st.write("No reception data found for this player against the selected team.")

st.divider()
