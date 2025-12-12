import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os
# from Home import df_teams, df_games, df_playerstats, df_team_game_logs, df_schedule_and_game_results
import plotly
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from PIL import Image
import sqlite3
from utils.footer import render_footer
from utils.session_state import ensure_option_state, widget_key

# Page configuration
st.set_page_config(
    page_title="🥇 Player Dashboard",
    page_icon="🏈",
    layout="wide"
    # layout="centered"
)

PAGE_KEY_PREFIX = "player_dashboard"

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

# Always use the most recent season available

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

# Load headshot map from Rosters.csv - single source of truth
@st.cache_data(show_spinner=False)
def load_headshot_map() -> dict[str, str]:
    """Load headshot map from Rosters.csv.
    
    Returns a dict mapping player names to headshot URLs.
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    roster_path = os.path.join(current_dir, '../data', 'Rosters.csv')
    
    try:
        df_roster = pd.read_csv(roster_path)
    except FileNotFoundError:
        return {}
    
    if df_roster.empty or 'full_name' not in df_roster.columns or 'headshot_url' not in df_roster.columns:
        return {}
    
    headshot_map: dict[str, str] = {}
    
    # Clean and filter roster data
    roster_clean = df_roster[['full_name', 'status', 'headshot_url']].copy()
    roster_clean['headshot_url'] = roster_clean['headshot_url'].astype(str).str.strip()
    roster_clean['full_name'] = roster_clean['full_name'].astype(str).str.strip()
    
    # Filter out inactive players
    if 'status' in roster_clean.columns:
        roster_clean = roster_clean[~roster_clean['status'].isin(['CUT', 'RET'])]
    
    # Filter to players with valid headshots
    roster_clean = roster_clean[
        (roster_clean['headshot_url'] != '') & 
        (roster_clean['headshot_url'] != 'nan') &
        (roster_clean['headshot_url'].notna())
    ]
    roster_clean = roster_clean[roster_clean['full_name'].notna()]
    
    # Create mapping (case-insensitive lookup ready)
    for _, row in roster_clean.iterrows():
        full_name = row['full_name']
        headshot_url = row['headshot_url']
        headshot_map[full_name] = headshot_url
    
    return headshot_map


def get_player_position(player_name: str | None) -> str | None:
    """Return the player's position if available.
    
    Uses the same approach as get_recent_games_data and other functions.
    """
    if player_name is None:
        return None

    # Get player data the same way get_recent_games_data does
    player_data = df_player_data[df_player_data['player'] == player_name].copy()
    if player_data.empty or 'position' not in player_data.columns:
        return None

    # Extract position the same way other functions do (iloc[-1] on non-null positions)
    non_null_positions = player_data['position'].dropna()
    if non_null_positions.empty:
        return None

    return non_null_positions.iloc[-1]

# Extract year and week from game_id (format: YYYY_WW_TEAM1_TEAM2)
df_player_data['year'] = df_player_data['game_id'].str.split('_').str[0].astype(int)
df_player_data['week'] = df_player_data['game_id'].str.split('_').str[1].astype(int)

# Season selector removed; use most recent available year
available_years = df_player_data['year'].dropna()
selected_season = int(available_years.max()) if not available_years.empty else 2025

# Filter to selected season (all positions now available)
df_player_data_filtered = df_player_data[df_player_data['year'] == selected_season]


def get_player_season_data(player_name: str, target_year: int) -> tuple[pd.DataFrame | None, int | None]:
    """Return season data for the player for the target year or fallback to their latest season."""
    player_data = df_player_data[df_player_data['player'] == player_name]
    if player_data.empty:
        return None, None

    season_data = player_data[player_data['year'] == target_year]
    if season_data.empty:
        latest_year = int(player_data['year'].max())
        season_data = player_data[player_data['year'] == latest_year]
        return season_data, latest_year

    return season_data, target_year

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

# Fetch player names from CSV data and headshots from database/roster
def fetch_player_names_and_image():
    # Get all players from the full dataset
    all_players_data = df_player_data[
        df_player_data['year'].isin([selected_season, selected_season - 1])
    ]
    
    if all_players_data.empty:
        st.warning(f"No player data available for {selected_season} season yet.")
        return None, None
    
    # Get unique player names from CSV
    player_names = all_players_data['player'].unique().tolist()
    player_names.sort()  # Sort alphabetically
    
    # Try to set default to Justin Jefferson, otherwise use first player
    default_player = None
    if player_names:
        default_player = "Justin Jefferson" if "Justin Jefferson" in player_names else player_names[0]

    player_key = widget_key(PAGE_KEY_PREFIX, "player")
    ensure_option_state(player_key, player_names, default=default_player)

    selected_player = st.selectbox("Select Player", options=player_names, key=player_key)
    
    # Get headshot URL from Rosters.csv (single source of truth)
    headshot_map = load_headshot_map()
    headshot_url = None
    
    # Try exact match first
    if selected_player in headshot_map:
        headshot_url = headshot_map[selected_player]
    else:
        # Try case-insensitive match
        selected_lower = selected_player.strip().lower()
        for name, url in headshot_map.items():
            if name.strip().lower() == selected_lower:
                headshot_url = url
                break
    
    return selected_player, headshot_url

# 1. Fetch last 10 games and generate a graph using Plotly
def fetch_last_10_games_and_plot(player_name, player_position=None):
    if player_name is None:
        return None, None

    # Get recent games data (current season + previous season if needed)
    recent_games = get_recent_games_data(player_name, 10)

    if recent_games is None or recent_games.empty:
        return None, None

    # Get player position if not supplied
    if player_position is None and 'position' in recent_games.columns:
        non_null_positions = recent_games['position'].dropna()
        if not non_null_positions.empty:
            player_position = non_null_positions.iloc[-1]

    # Create a plot with optional secondary axis support
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    if player_position == 'QB':
        if 'pass_yds' in recent_games.columns and recent_games['pass_yds'].notna().any():
            fig.add_trace(
                go.Scatter(
                    x=recent_games['x_position'],
                    y=recent_games['pass_yds'],
                    mode='lines+markers+text',
                    name='Passing Yards',
                    line=dict(color='#FFA500'),
                    text=recent_games['pass_yds'].fillna(0).astype(int),
                    textposition='top center',
                    textfont=dict(color='#FFA500', size=10),
                ),
                secondary_y=False,
            )

        if 'pass_cmp' in recent_games.columns and recent_games['pass_cmp'].notna().any():
            fig.add_trace(
                go.Scatter(
                    x=recent_games['x_position'],
                    y=recent_games['pass_cmp'],
                    mode='lines+markers+text',
                    name='Completions',
                    line=dict(color='#1F77B4'),
                    text=recent_games['pass_cmp'].fillna(0).astype(int),
                    textposition='top center',
                    textfont=dict(color='#1F77B4', size=10),
                ),
                secondary_y=False,
            )

        if 'pass_td' in recent_games.columns and recent_games['pass_td'].notna().any():
            fig.add_trace(
                go.Bar(
                    x=recent_games['x_position'],
                    y=recent_games['pass_td'],
                    name='Pass TDs',
                    marker_color='#6C5CE7',
                    text=recent_games['pass_td'].fillna(0).astype(int),
                    textposition='outside',
                    opacity=0.8,
                ),
                secondary_y=True,
            )
    else:
        # Always show receiving yards and receptions for WR/TE/RB
        if 'rec_yds' in recent_games.columns and recent_games['rec_yds'].notna().any():
            fig.add_trace(
                go.Scatter(
                    x=recent_games['x_position'],
                    y=recent_games['rec_yds'],
                    mode='lines+markers+text',
                    name='Receiving Yards',
                    line=dict(color='#FF4444'),
                    text=recent_games['rec_yds'].fillna(0).astype(int),
                    textposition='top center',
                    textfont=dict(color='#FF4444', size=10),
                ),
                secondary_y=False,
            )

        if 'rec' in recent_games.columns and recent_games['rec'].notna().any():
            fig.add_trace(
                go.Scatter(
                    x=recent_games['x_position'],
                    y=recent_games['rec'],
                    mode='lines+markers+text',
                    name='Receptions',
                    line=dict(color='#4444FF'),
                    text=recent_games['rec'].fillna(0).astype(int),
                    textposition='top center',
                    textfont=dict(color='#4444FF', size=10),
                ),
                secondary_y=False,
            )

        # Add rushing yards for RBs
        if player_position == 'RB' and 'rush_yds' in recent_games.columns and recent_games['rush_yds'].notna().any():
            fig.add_trace(
                go.Scatter(
                    x=recent_games['x_position'],
                    y=recent_games['rush_yds'],
                    mode='lines+markers+text',
                    name='Rushing Yards',
                    line=dict(color='green'),  # Green color for rushing
                    text=recent_games['rush_yds'].fillna(0).astype(int),
                    textposition='top center',
                    textfont=dict(color='green', size=10),
                ),
                secondary_y=False,
            )

    # Create custom x-axis labels showing year and week
    x_labels = [f"{int(year)}-W{int(week):02d}" for year, week in zip(recent_games['year'], recent_games['week'])]

    fig.update_layout(
        title=f"Last 10 Games for {player_name}",
        # xaxis_title='Game (Year-Week)',
        yaxis_title='Yards',
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
        ),
    )

    if player_position == 'QB':
        fig.update_yaxes(title_text='Yards / Completions', secondary_y=False)
        fig.update_yaxes(title_text='Passing TDs', secondary_y=True, showgrid=False)
    else:
        fig.update_yaxes(secondary_y=True, visible=False)

    return recent_games, fig

# 0. Player Input - Better organized layout
col1, spacer_col, col2 = st.columns([1, 0.1, 2])
with col1:
    player_name, headshot_url = fetch_player_names_and_image()
    player_position = get_player_position(player_name)
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
        season_data, season_year = get_player_season_data(player_name, selected_season)
        
        if season_data is not None and not season_data.empty:
            season_label = season_year if season_year is not None else selected_season
            st.markdown("")
            st.markdown(f"#### {season_label} Season Stats")
            st.markdown("")
            
            # Determine player position for metric context
            position_for_metrics = player_position
            if position_for_metrics is None and 'position' in season_data.columns:
                non_null_positions = season_data['position'].dropna()
                if not non_null_positions.empty:
                    position_for_metrics = non_null_positions.iloc[-1]

            if position_for_metrics == 'QB':
                metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)

                with metric_col1:
                    total_pass_yds = season_data['pass_yds'].sum() if 'pass_yds' in season_data.columns else 0
                    st.metric(
                        label="Total Pass Yards",
                        value=f"{total_pass_yds:.0f}",
                        help=f"Total passing yards ({season_label})",
                    )

                with metric_col2:
                    avg_pass_yds_per_game = season_data['pass_yds'].mean() if 'pass_yds' in season_data.columns else 0
                    st.metric(
                        label="Avg Pass Yds/Game",
                        value=f"{avg_pass_yds_per_game:.1f}",
                        help=f"Average passing yards per game ({season_label})",
                    )

                with metric_col3:
                    total_pass_tds = season_data['pass_td'].sum() if 'pass_td' in season_data.columns else 0
                    st.metric(
                        label="Pass TDs",
                        value=f"{total_pass_tds:.0f}",
                        help=f"Total passing touchdowns ({season_label})",
                    )

                with metric_col4:
                    total_cmp = season_data['pass_cmp'].sum() if 'pass_cmp' in season_data.columns else 0
                    total_att = season_data['pass_att'].sum() if 'pass_att' in season_data.columns else 0
                    completion_pct = (total_cmp / total_att * 100) if total_att else 0
                    st.metric(
                        label="Completion %",
                        value=f"{completion_pct:.1f}%",
                        help=f"Completion percentage ({season_label})",
                    )

            elif position_for_metrics == 'RB':
                # Show rushing and receiving stats for RBs
                metric_col1, metric_col2, metric_col3 = st.columns(3)

                with metric_col1:
                    total_rush_yds = season_data['rush_yds'].sum() if 'rush_yds' in season_data.columns else 0
                    st.metric(
                        label="Total Rush Yards",
                        value=f"{total_rush_yds:.0f}",
                        help=f"Total rushing yards ({season_label})"
                    )

                with metric_col2:
                    avg_rush_yds_per_game = season_data['rush_yds'].mean() if 'rush_yds' in season_data.columns else 0
                    st.metric(
                        label="Avg Rush Yds/Game",
                        value=f"{avg_rush_yds_per_game:.1f}",
                        help=f"Average rushing yards per game ({season_label})"
                    )

                with metric_col3:
                    total_rush_tds = season_data['rush_td'].sum() if 'rush_td' in season_data.columns else 0
                    total_rec_tds = season_data['rec_td'].sum() if 'rec_td' in season_data.columns else 0
                    total_tds = total_rush_tds + total_rec_tds
                    st.metric(
                        label="Total TDs",
                        value=f"{total_tds:.0f}",
                        help=f"Total rushing + receiving touchdowns ({season_label})"
                    )
            else:
                # Show receiving stats for WR/TE and other positions
                metric_col1, metric_col2, metric_col3 = st.columns(3)

                with metric_col1:
                    total_rec_yds = season_data['rec_yds'].sum() if 'rec_yds' in season_data.columns else 0
                    st.metric(
                        label="Total Rec Yards",
                        value=f"{total_rec_yds:.0f}",
                        help=f"Total receiving yards ({season_label})"
                    )

                with metric_col2:
                    avg_rec_per_game = season_data['rec'].mean() if 'rec' in season_data.columns else 0
                    st.metric(
                        label="Avg Rec/Game",
                        value=f"{avg_rec_per_game:.1f}",
                        help=f"Average receptions per game ({season_label})"
                    )

                with metric_col3:
                    total_tds = season_data['rec_td'].sum() if 'rec_td' in season_data.columns else 0
                    st.metric(
                        label="Total TDs",
                        value=f"{total_tds:.0f}",
                        help=f"Total receiving touchdowns ({season_label})"
                    )
        else:
            st.markdown("#### 📊 Season Stats")
            st.info("No season data available for this player yet")
        
        # Add some spacing before the chart
        st.markdown("")
        
        # Then show the graph
        last_10_games, fig_last_10 = fetch_last_10_games_and_plot(player_name, player_position)
        if fig_last_10 is not None:
            st.plotly_chart(fig_last_10, use_container_width=True)

st.divider()

# 2. Fetch last 10 games function
def fetch_last_10_games(player_name, player_position=None):
    if player_name is None:
        return None

    # Get recent games data (current season + previous season if needed)
    recent_games = get_recent_games_data(player_name, 10)

    if recent_games is None or recent_games.empty:
        return None

    # Get player position if not supplied
    if player_position is None and 'position' in recent_games.columns:
        non_null_positions = recent_games['position'].dropna()
        if not non_null_positions.empty:
            player_position = non_null_positions.iloc[-1]

    # Select relevant columns for display based on position
    base_columns = ['year', 'week', 'team', 'opponent_team']

    if player_position == 'QB':
        display_columns = base_columns + ['pass_cmp', 'pass_att', 'pass_yds', 'pass_td', 'pass_int', 'rush_yds']
    elif player_position == 'RB':
        # Include rushing and receiving columns for RBs
        display_columns = base_columns + ['rush_att', 'rush_yds', 'rush_td', 'rec', 'rec_yds', 'rec_td', 'targets']
    else:
        # Include receiving columns for WR/TE and other positions
        display_columns = base_columns + ['rec', 'rec_yds', 'rec_td', 'rec_long', 'targets']

    available_columns = [col for col in display_columns if col in recent_games.columns]

    # Reverse the order so most recent games appear first
    return recent_games[available_columns].iloc[::-1]

last_10_games = fetch_last_10_games(player_name, player_position)
if last_10_games is not None:
    # st.subheader('Last 10 Games:')
    st.subheader(f"Last 10 Games for {player_name}")
    st.write("")
    st.dataframe(last_10_games, use_container_width=True, hide_index=True)

st.divider()

# 3. Position-specific prop trends and distributions
if player_name is not None:
    if player_position == 'QB':
        st.subheader(f"Pass Attempts and Completions (Last 10 Games) for {player_name}:")
    else:
        st.subheader(f"Longest Receptions for {player_name}:")
else:
    st.subheader("Player Prop Trend:")


def plot_last_20_games_prop_trend(player_name, player_position=None):
    if player_name is None:
        return None

    # Get recent games data (current season + previous season if needed)
    recent_games = get_recent_games_data(player_name, 10)

    if recent_games is None or recent_games.empty:
        return None

    if player_position is None and 'position' in recent_games.columns:
        non_null_positions = recent_games['position'].dropna()
        if not non_null_positions.empty:
            player_position = non_null_positions.iloc[-1]

    # Create columns with spacing between graph and table
    graph_col, spacer_col, table_col = st.columns([3.5, 0.05, 1])

    # QB: show Attempts vs Completions over last 10 games
    if player_position == 'QB':
        # Keep original order by game for the timeline
        recent_games = recent_games.drop_duplicates(subset=['game_id']).sort_values(by='game_id', ascending=True)

        with graph_col:
            fig = go.Figure()
            # Attempts
            if 'pass_att' in recent_games.columns:
                fig.add_trace(go.Scatter(
                    x=recent_games['game_id'],
                    y=recent_games['pass_att'],
                    mode='lines+markers+text',
                    name='Attempts',
                    marker=dict(color='#888888'),
                    text=recent_games['pass_att'].fillna(0).astype(int),
                    textposition='top center',
                    textfont=dict(color='#888888', size=12)
                ))
            # Completions
            if 'pass_cmp' in recent_games.columns:
                fig.add_trace(go.Scatter(
                    x=recent_games['game_id'],
                    y=recent_games['pass_cmp'],
                    mode='lines+markers+text',
                    name='Completions',
                    marker=dict(color='#1F77B4'),
                    text=recent_games['pass_cmp'].fillna(0).astype(int),
                    textposition='top center',
                    textfont=dict(color='#1F77B4', size=12)
                ))

            fig.update_layout(
                xaxis_title='Game ID',
                yaxis_title='Attempts / Completions',
                xaxis_tickangle=-90,
                template='plotly_dark',
                height=500,
                legend_title=''
            )
            st.plotly_chart(fig, use_container_width=True)

        with spacer_col:
            st.write("")

        with table_col:
            st.markdown("")
            st.markdown("")
            st.markdown(" ")
            st.markdown(" ")
            st.markdown(" ")
            st.markdown(" ")
            st.write("")
            st.write("")
            table_columns = ['game_id', 'pass_att', 'pass_cmp', 'pass_yds']
            available_columns = [col for col in table_columns if col in recent_games.columns]
            table_data = recent_games[available_columns].copy().iloc[::-1]
            st.dataframe(table_data, use_container_width=True, height=350, hide_index=True)
        return None

    # Non-QB: keep longest reception trend
    metric_column = 'rec_long'
    metric_label = 'Longest Reception (yards)'
    metric_color = '#800080'
    table_columns = ['game_id', 'rec_long']

    if metric_column not in recent_games.columns:
        return None

    # Filter to games with relevant data
    recent_games = recent_games.dropna(subset=[metric_column])
    recent_games = recent_games.drop_duplicates(subset=['game_id']).sort_values(by='game_id', ascending=True)

    with graph_col:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=recent_games['game_id'],
            y=recent_games[metric_column],
            mode='lines+markers+text',
            marker=dict(color=metric_color),
            name=player_name,
            text=recent_games[metric_column].fillna(0).astype(int),
            textposition='top center',
            textfont=dict(color=metric_color, size=12)
        ))
        fig.update_layout(
            xaxis_title='Game ID',
            yaxis_title=metric_label,
            xaxis_tickangle=-90,
            template='plotly_dark',
            height=500,
        )
        st.plotly_chart(fig, use_container_width=True)

    with spacer_col:
        st.write("")

    with table_col:
        st.markdown("")
        st.markdown("")
        st.markdown(" ")
        st.markdown(" ")
        st.markdown(" ")
        st.markdown(" ")
        st.write("")
        st.write("")
        available_columns = [col for col in table_columns if col in recent_games.columns]
        table_data = recent_games[available_columns].copy()
        table_data = table_data.iloc[::-1]
        st.dataframe(table_data, use_container_width=True, height=350, hide_index=True)

if player_name is not None:
    plot_last_20_games_prop_trend(player_name, player_position)
    st.divider()
    st.write("")
    st.write("")

    if player_position == 'QB':
        st.subheader(f"Passing Yards Distribution for {player_name} (L20 Games):")
    else:
        st.subheader(f"Reception Distribution for {player_name} (L20 Games):")


def plot_reception_distribution(player_name, player_position=None):
    if player_name is None:
        return None
    
    # Get recent games data (current season + previous season if needed)
    recent_games = get_recent_games_data(player_name, 20)  # Get more games for better distribution
    
    if recent_games is None or recent_games.empty:
        return None
    
    if player_position is None and 'position' in recent_games.columns:
        non_null_positions = recent_games['position'].dropna()
        if not non_null_positions.empty:
            player_position = non_null_positions.iloc[-1]

    if player_position == 'QB':
        metric_column = 'pass_yds'
        metric_label = 'Passing Yards'
        color = '#FFA500'
    else:
        metric_column = 'rec'
        metric_label = 'Number of Receptions'
        color = '#FF4444'

    if metric_column not in recent_games.columns:
        return None

    # Filter to games with relevant data
    recent_games = recent_games.dropna(subset=[metric_column])

    fig = go.Figure(data=[go.Histogram(
        x=recent_games[metric_column],
        nbinsx=10,
        marker_color=color,
        opacity=0.75
    )])

    fig.update_layout(
        xaxis_title=metric_label,
        yaxis_title='Frequency',
        template='plotly_dark',
        height=400,  # Fixed height for better tiling
    )
    st.plotly_chart(fig, use_container_width=True)

if player_name is not None:
    plot_reception_distribution(player_name, player_position)

# Removed get_player_reception_stats function - data now displayed inline with the graph

st.divider()

# 4. Fetch historical performance function
def fetch_historical_performance(player_name, opponent_team_abbr, player_position=None):
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
    
    # Get player position
    if player_position is None and 'position' in player_data.columns:
        non_null_positions = player_data['position'].dropna()
        if not non_null_positions.empty:
            player_position = non_null_positions.iloc[-1]

    # Select relevant columns based on position
    if player_position == 'QB':
        display_columns = ['year', 'week', 'pass_cmp', 'pass_att', 'pass_yds', 'pass_td', 'pass_int']
    elif player_position == 'RB':
        # Include rushing and receiving columns for RBs
        display_columns = ['year', 'week', 'rush_att', 'rush_yds', 'rush_td', 'rec_yds', 'rec_td', 'rec']
    else:
        # Include receiving columns for WR/TE and other positions
        display_columns = ['year', 'week', 'rec_yds', 'rec_td', 'rec', 'rec_long']

    available_columns = [col for col in display_columns if col in player_data.columns]
    
    # Sort by year and week descending (most recent first), then reverse for display
    return player_data[available_columns].sort_values(by=['year', 'week'], ascending=[False, False])

if player_name is not None:
    st.subheader(f'Historical Performance')
    team_abbr_list = df_teams['TeamID'].tolist()
    opponent_key = widget_key(PAGE_KEY_PREFIX, "opponent")
    default_opponent = team_abbr_list[0] if team_abbr_list else None
    ensure_option_state(opponent_key, team_abbr_list, default=default_opponent)
    opponent_team_abbr = st.selectbox("Select Opponent:", options=team_abbr_list, key=opponent_key)
    st.write("")
    if player_position == 'QB':
        stats_label = 'Passing Stats'
    else:
        stats_label = 'General Stats'

    st.markdown(
        f'<span style="font-size: 1em; font-weight: bold;">{stats_label} Against {opponent_team_abbr}: </span>',
        unsafe_allow_html=True
    )
    historical_performance = fetch_historical_performance(player_name, opponent_team_abbr, player_position)
    if historical_performance is not None:
        st.dataframe(historical_performance, use_container_width=True, hide_index=True)
    else:
        st.write("No historical data found for this player against the selected team.")

# st.divider()

# 5. Get player prop highlight function
def get_player_prop_highlight(player_name, opponent_team=None, player_position=None):
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

    if player_position is None and 'position' in player_data.columns:
        non_null_positions = player_data['position'].dropna()
        if not non_null_positions.empty:
            player_position = non_null_positions.iloc[-1]

    if player_position == 'QB':
        highlight_columns = [col for col in ['game_id', 'pass_yds', 'pass_td', 'pass_long'] if col in player_data.columns]
        if not highlight_columns:
            return None
        highlight_stats = player_data[highlight_columns].dropna(subset=['pass_yds'])
        highlight_stats = highlight_stats.sort_values(by='pass_yds', ascending=False).head(1)
    else:
        highlight_stats = player_data[['game_id', 'rec_yds', 'rec_long']].dropna(subset=['rec_yds'])
        highlight_stats = highlight_stats.sort_values(by='rec_yds', ascending=False).head(1)

    # Reverse order to show most recent first
    return highlight_stats.iloc[::-1]

if player_name is not None:
    if player_position == 'QB':
        header_text = f'Top Passing Game Against {opponent_team_abbr}:'
    else:
        header_text = f'Longest Receptions Against {opponent_team_abbr}:'

    st.markdown(
        f'<span style="font-size: 1em; font-weight: bold;">{header_text} </span>',
        unsafe_allow_html=True
    )
    prop_highlight = get_player_prop_highlight(player_name, opponent_team_abbr, player_position)
    if prop_highlight is not None:
        st.dataframe(prop_highlight, use_container_width=True, hide_index=True)
    else:
        st.write("No data found for this player against the selected team.")

st.divider()

# Footer
render_footer()
