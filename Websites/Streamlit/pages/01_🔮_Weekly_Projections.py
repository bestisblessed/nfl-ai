import streamlit as st
import pandas as pd
import numpy as np
import os
import glob
import json
import re
from typing import Any, List, Tuple, Callable, Dict
from pandas.api.types import is_float_dtype, is_integer_dtype
from utils.footer import render_footer
from utils.session_state import persistent_selectbox

PAGE_KEY_PREFIX = "weekly_projections_leaders"

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECTIONS_DIR = os.path.join(BASE_DIR, "data", "projections")


def format_matchup_time(start_time: Any = None, date_value: Any = None, time_value: Any = None) -> str:
    timestamp = None
    if pd.notna(start_time):
        timestamp = pd.to_datetime(start_time, errors='coerce')
    else:
        components = []
        if pd.notna(date_value):
            components.append(str(date_value))
        if pd.notna(time_value):
            components.append(str(time_value))
        if components:
            combined = " ".join(components)
            timestamp = pd.to_datetime(combined, errors='coerce')
    if timestamp is None or pd.isna(timestamp) or timestamp == pd.Timestamp.max:
        return ""
    time_str = timestamp.strftime("%I:%M %p").lstrip("0")
    day_str = timestamp.strftime("%a")
    return f"{day_str} {time_str}"


def build_matchup_option(matchup: str, time_label: str = "") -> Tuple[str, str]:
    if time_label:
        display = f"{matchup} · {time_label}"
    else:
        display = matchup
    return matchup, display


def option_display_label(option: Any) -> str:
    if isinstance(option, tuple):
        return option[1]
    return str(option)


def format_start_time_label(time_value: Any) -> str:
    if not pd.notna(time_value):
        return ""
    try:
        timestamp = pd.to_datetime(time_value)
    except Exception:
        return ""
    if isinstance(timestamp, pd.Timestamp) and timestamp == pd.Timestamp.max:
        return ""
    time_str = timestamp.strftime("%I:%M %p").lstrip("0")
    return time_str


# Load game times from odds JSON files
@st.cache_data
def load_game_times():
    """Load game times from odds JSON files to sort games by start time"""
    games_with_times = {}
    try:
        data_dir = os.path.join(BASE_DIR, "data", "odds")
        json_files = sorted(
            [f for f in os.listdir(data_dir) if f.endswith(".json") and f.startswith('nfl')],
            reverse=True
        )
        if json_files:
            filepath = os.path.join(data_dir, json_files[0])
            with open(filepath) as f:
                data = json.load(f)
                for game in data:
                    game_time = game.get('Time', '')
                    day_and_matchup_key = list(game.keys())[1] if len(game.keys()) > 1 else None
                    if day_and_matchup_key:
                        teams = game[day_and_matchup_key].replace('\n', ' ').strip()
                        if '  ' in teams:
                            teams_list = [team.strip() for team in teams.split('  ') if team.strip()]
                        else:
                            teams_list = [team.strip() for team in re.split(r'\s+|,', teams) if team.strip()]
                        if len(teams_list) == 2:
                            matchup_key = f"{teams_list[0]} vs {teams_list[1]}"
                            games_with_times[matchup_key] = {
                                'time': game_time,
                                'date': day_and_matchup_key.strip()
                            }
    except Exception:
        pass
    return games_with_times


# Load games from Games.csv for a specific week
@st.cache_data
def load_games_for_week(week: int) -> pd.DataFrame:
    """Load games from Games.csv for a specific week in season 2025"""
    games_file = os.path.join(BASE_DIR, "data", "Games.csv")
    if os.path.exists(games_file):
        try:
            games_df = pd.read_csv(games_file)
            # Convert week to numeric in case it's stored as string
            games_df['week'] = pd.to_numeric(games_df['week'], errors='coerce')
            games_df['season'] = pd.to_numeric(games_df['season'], errors='coerce')
            # Filter by season 2025 and week
            week_games = games_df[
                (games_df['season'] == 2025) &
                (games_df['week'] == week)
            ]
            if not week_games.empty:
                result = week_games[['home_team', 'away_team', 'date', 'gametime']].drop_duplicates()
                if not result.empty:
                    return result
            return pd.DataFrame()
        except Exception:
            return pd.DataFrame()
    return pd.DataFrame()


# Load upcoming games data for home/away determination
@st.cache_data
def load_upcoming_games():
    """Load upcoming games to determine home/away teams"""
    games_file = os.path.join(BASE_DIR, "upcoming_games.csv")
    if os.path.exists(games_file):
        games_df = pd.read_csv(games_file)
        # Create a mapping from matchup to home/away format
        games_mapping = {}
        for _, row in games_df.iterrows():
            # Store both team orders for lookup
            home, away = row['home_team'], row['away_team']
            games_mapping[(home, away)] = f"{away} @ {home}"
            games_mapping[(away, home)] = f"{away} @ {home}"
        return games_mapping, games_df
    return {}, pd.DataFrame()


@st.cache_data
def load_questionable_players(week: int) -> set[str]:
    """Load players marked as Questionable in the weekly complete props report."""

    questionable_players: set[str] = set()
    txt_path = os.path.join(PROJECTIONS_DIR, f"week{week}_complete_props_report.txt")
    html_path = os.path.join(PROJECTIONS_DIR, f"week{week}_complete_props_report.html")

    def extract_players(text: str) -> None:
        matches = re.findall(
            r"([A-Za-z0-9'.-]+(?:\s+[A-Za-z0-9'.-]+)*)\s+\(Questionable\)", text
        )
        questionable_players.update(name.strip() for name in matches)

    if os.path.exists(txt_path):
        with open(txt_path, "r", encoding="utf-8") as file:
            extract_players(file.read())
    elif os.path.exists(html_path):
        with open(html_path, "r", encoding="utf-8") as file:
            extract_players(file.read())

    return questionable_players


def add_questionable_tag(name: str, questionable_players: set[str]):
    if pd.isna(name):
        return name
    name_str = str(name).strip()
    if "(Q)" in name_str:
        return name_str
    if "(Questionable)" in name_str:
        return name_str.replace("(Questionable)", "(Q)")
    return f"{name_str} (Q)" if name_str in questionable_players else name_str

# Page configuration
st.set_page_config(
    page_title="🔮 Weekly Projections & Leaders",
    page_icon="🏈",
    layout="wide"
)

st.markdown(f"""
    <div style='text-align: center;'>
        <div style='font-size: 3.1rem; font-weight: 800; padding-bottom: 0.5rem;'>
            Weekly Projections & Leaders
        </div>
        <div style='color: #7f8c8d; font-size: 1rem; margin-top: 0; line-height: 1.2;'>
            Weekly Player Projections and Leaderboards Generated by Machine Learning Algorithms
        </div>
    </div>
    """,
    unsafe_allow_html=True
)
st.divider()

# Simple, clean styling
st.markdown("""
<style>
    .data-section {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #e1e8ed;
        margin: 1rem 0;
    }
    .section-title {
        font-size: 2rem;
        font-weight: 700;
        color: #2A3439;
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        text-align: center;
        /* border-bottom: 2px solid #3498db; */
    }
</style>
""", unsafe_allow_html=True)

# Function to load projections data
@st.cache_data
def load_projections_data():
    """Load and process projections data from CSV files"""
    projections_dir = os.path.join(BASE_DIR, "data/projections")

    # Find all projection files
    projection_files = glob.glob(os.path.join(projections_dir, "week*_all_props_summary.csv"))

    if not projection_files:
        st.error(f"No projection files found in {projections_dir}")
        return None, []

    # Extract available weeks
    available_weeks = []
    for file in projection_files:
        week_num = file.split('week')[1].split('_')[0]
        available_weeks.append(int(week_num))

    available_weeks.sort()

    return projection_files, available_weeks

# Function to get projections for a specific week
@st.cache_data
def get_week_projections(week_num):
    """Get projections data for a specific week"""
    file_path = os.path.join(BASE_DIR, f"data/projections/week{week_num}_all_props_summary.csv")

    if not os.path.exists(file_path):
        return None

    try:
        df = pd.read_csv(file_path)

        # Clean and process the data
        df = df.dropna(subset=['pred_yards'])
        df['pred_yards'] = pd.to_numeric(df['pred_yards'], errors='coerce')
        df = df.dropna(subset=['pred_yards'])

        # Add trend (placeholder - could be enhanced with historical data)
        trends = np.random.choice(['↗️', '→', '↘️'], size=len(df), p=[0.3, 0.4, 0.3])
        df['trend'] = trends

        return df
    except Exception as e:
        st.error(f"Error loading week {week_num} data: {str(e)}")
        return None

# Load available data
projection_files, available_weeks = load_projections_data()

if not available_weeks:
    st.error("No projection data available. Please ensure projection files are in data/projections/")
    st.stop()

st.sidebar.markdown("<h2 style='text-align: center;'>Selection</h2>", unsafe_allow_html=True)
week_options = [f"Week {week}" for week in available_weeks]
selected_week_display = persistent_selectbox(
    "Week:",
    options=week_options,
    page=PAGE_KEY_PREFIX,
    widget="week",
    default=week_options[-1] if week_options else None,
    container=st.sidebar,
)

# Get the selected week number
selected_week = selected_week_display.replace("Week ", "")

# Load data for selected week
projections_df = get_week_projections(int(selected_week))

if projections_df is None:
    st.error(f"No data available for {selected_week_display}")
    st.stop()

# Load games mapping for correct home/away designation
games_mapping, upcoming_games_df = load_upcoming_games()
game_times = load_game_times()

# Try to get games from Games.csv first (for historical weeks)
week_games_df = load_games_for_week(int(selected_week))

# Create matchup options - prioritize Games.csv, then upcoming_games.csv, then projections data
matchups: List[Tuple[str, str]] = []
if not week_games_df.empty and "home_team" in week_games_df.columns and "away_team" in week_games_df.columns:
    week_games_df = week_games_df.copy()
    if 'date' in week_games_df.columns and 'gametime' in week_games_df.columns:
        week_games_df['start_time'] = pd.to_datetime(
            week_games_df['date'].astype(str) + " " + week_games_df['gametime'].astype(str),
            errors='coerce'
        )
        week_games_df['start_time'] = week_games_df['start_time'].fillna(pd.Timestamp.max)
        week_games_df = week_games_df.sort_values(['start_time', 'home_team', 'away_team'])
    for _, row in week_games_df.iterrows():
        matchup = f"{row['away_team']} @ {row['home_team']}"
        time_label = format_matchup_time(start_time=row.get('start_time'))
        matchups.append(build_matchup_option(matchup, time_label))
elif not upcoming_games_df.empty:
    games_list = []
    for _, row in upcoming_games_df.iterrows():
        away, home = row['away_team'], row['home_team']
        matchup_str = f"{away} @ {home}"
        time_info = None
        for key, value in game_times.items():
            teams_in_key = [t.strip() for t in re.split(r'\s+vs\s+', key, flags=re.IGNORECASE)]
            if len(teams_in_key) == 2:
                time_info = value
                break
        games_list.append({
            'matchup': matchup_str,
            'time': time_info['time'] if time_info else '',
            'date': time_info['date'] if time_info else '',
            'sort_key': (time_info['date'] if time_info else '', time_info['time'] if time_info else '')
        })
    games_list.sort(key=lambda x: x['sort_key'])
    for entry in games_list:
        time_label = format_matchup_time(date_value=entry.get('date'), time_value=entry.get('time'))
        matchups.append(build_matchup_option(entry['matchup'], time_label))
else:
    matchup_set = set()
    fallback_options = []
    for _, row in projections_df.iterrows():
        team1, team2 = row['team'], row['opp']
        matchup = games_mapping.get((team1, team2))
        if matchup is None:
            matchup = games_mapping.get((team2, team1))
        if matchup is None:
            team1_sorted, team2_sorted = sorted([team1, team2])
            matchup = f"{team1_sorted} @ {team2_sorted}"
        if matchup not in matchup_set:
            matchup_set.add(matchup)
            fallback_options.append(build_matchup_option(matchup))
    matchups = sorted(fallback_options, key=lambda option: option[1])

# Add "All Games" option at the beginning
all_games_option = ("", "Leaders (All Games)")
matchups.insert(0, all_games_option)

selected_matchup_option = persistent_selectbox(
    "Game:",
    options=matchups,
    page=PAGE_KEY_PREFIX,
    widget="matchup",
    default=all_games_option if matchups else None,
    container=st.sidebar,
    format_func=option_display_label,
)
selected_matchup_key = selected_matchup_option[0] if selected_matchup_option else ""
selected_matchup_label = selected_matchup_option[1] if selected_matchup_option else "All Games"

st.sidebar.write("")
st.sidebar.write("")

# Add download button to sidebar after week selection
with st.sidebar:
    st.markdown(
        "<div style='font-size: 1.2rem; font-weight: 600; margin-bottom: 12px; text-align: center;'>Export</div>"
        "<div style='height: 5px;'></div>",
        unsafe_allow_html=True
    )
    html_filename = f"week{selected_week}_complete_props_report.html"
    html_path = os.path.join(BASE_DIR, "data/projections", html_filename)

    if os.path.exists(html_path):
        with open(html_path, "rb") as html_file:
            st.download_button(
                label="Download HTML",
                data=html_file.read(),
                file_name=html_filename,
                mime="text/html",
                width='stretch'
            )
    else:
        st.info("HTML report not available for this week")

# Determine if we should show projections or leaders
show_leaders = selected_matchup_key == ""

if show_leaders:
    # ===== WEEKLY LEADERS VIEW =====
    # Create leaderboards from projections data
    def create_leaderboard_from_projections(df, prop_type, title, position_filter=None, top_n=25):
        """Create a leaderboard DataFrame from projections data"""
        # Filter by prop type
        prop_data = df[df['prop_type'] == prop_type].copy()

        # Apply position filter if provided
        if position_filter:
            prop_data = position_filter(prop_data)

        if prop_data.empty:
            return None

        # Sort by predicted yards and take top N
        leaderboard_df = prop_data.nlargest(top_n, 'pred_yards').copy()

        # Add rank column
        leaderboard_df['Rank'] = range(1, len(leaderboard_df) + 1)

        # Reorder columns to match expected format
        cols = ['Rank', 'full_name', 'team', 'opp', 'pred_yards']
        leaderboard_df = leaderboard_df[cols]

        # Rename columns for display
        leaderboard_df.columns = ['Rank', 'Player', 'Team', 'Opponent', 'Projected Yards']

        return {
            'title': title,
            'dataframe': leaderboard_df
        }

    # Create leaderboards for each category
    leaderboards = []

    # Quarterback Passing Yards
    qb_board = create_leaderboard_from_projections(
        projections_df, 'Passing Yards', 'Top QB Passing Yards', top_n=1000
    )
    if qb_board:
        leaderboards.append(qb_board)

    # Quarterback Rushing Yards
    qb_rush_board = create_leaderboard_from_projections(
        projections_df, 'Rushing Yards', 'Top QB Rushing Yards',
        lambda df: df[df['position'] == 'QB'], top_n=1000
    )
    if qb_rush_board:
        leaderboards.append(qb_rush_board)

    # Wide Receiver Receiving Yards
    wr_board = create_leaderboard_from_projections(
        projections_df, 'Receiving Yards',
        'Top 25 WR Receiving Yards',
        lambda df: df[df['position'] == 'WR']
    )
    if wr_board:
        leaderboards.append(wr_board)

    # Tight End Receiving Yards
    te_board = create_leaderboard_from_projections(
        projections_df, 'Receiving Yards',
        'Top 25 TE Receiving Yards',
        lambda df: df[df['position'] == 'TE']
    )
    if te_board:
        leaderboards.append(te_board)

    # Running Back Rushing Yards
    rb_rush_board = create_leaderboard_from_projections(
        projections_df, 'Rushing Yards', 'Top 25 RB Rushing Yards'
    )
    if rb_rush_board:
        leaderboards.append(rb_rush_board)

    # Running Back Receiving Yards
    rb_rec_board = create_leaderboard_from_projections(
        projections_df, 'Receiving Yards',
        'Top 25 RB Receiving Yards',
        lambda df: df[df['position'] == 'RB']
    )
    if rb_rec_board:
        leaderboards.append(rb_rec_board)

    if not leaderboards:
        st.error("No leaderboard data could be created from the projections.")
        st.stop()

    # Organize leaderboards by category for clean display
    qb_boards = [lb for lb in leaderboards if "qb" in lb['title'].lower()]
    wr_boards = [lb for lb in leaderboards if "wr" in lb['title'].lower() and "receiving" in lb['title'].lower()]
    te_boards = [lb for lb in leaderboards if "te" in lb['title'].lower()]
    rb_boards = [lb for lb in leaderboards if "rb" in lb['title'].lower()]

    # Create tabs for each position type
    tab_names = ["Quarterbacks", "Running Backs", "Wide Receivers", "Tight Ends"]
    tab_boards = [qb_boards, rb_boards, wr_boards, te_boards]

    def create_styled_dataframe(leaderboard):
        """Create a beautifully styled dataframe for display."""
        df = leaderboard['dataframe']

        # Format numeric columns
        def _float_formatter(value: float) -> str:
            if pd.isna(value):
                return ""
            return f"{value:,.1f}"

        def _int_formatter(value: float) -> str:
            if pd.isna(value):
                return ""
            return f"{int(value):,}"

        formatters: Dict[str, Callable[[float], str]] = {}
        numeric_columns = [
            column for column in df.columns
            if pd.api.types.is_numeric_dtype(df[column])
        ]

        for column in numeric_columns:
            if is_float_dtype(df[column]):
                formatters[column] = _float_formatter
            elif is_integer_dtype(df[column]):
                formatters[column] = _int_formatter

        # Apply styling
        styled_df = (
            df.style
            .format(formatters, na_rep="")
            .set_table_styles([
                {"selector": "th", "props": [
                    ("text-align", "center"),
                    ("background-color", "#1f77b4"),
                    ("color", "white"),
                    ("font-weight", "bold"),
                    ("padding", "12px"),
                    ("border", "1px solid #ddd")
                ]},
                {"selector": "td", "props": [
                    ("text-align", "center"),
                    ("padding", "8px"),
                    ("border", "1px solid #eee")
                ]},
                {"selector": "tr:nth-child(even)", "props": [("background-color", "#f9f9f9")]},
                {"selector": "tr:hover", "props": [("background-color", "#e6f7ff")]},
            ])
            .set_properties(**{
                "text-align": "center",
                "font-size": "14px"
            })
        )
        return styled_df

    # Add a stylized week title box above the tabs
    st.markdown(f"""
        <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        padding: 1px;
                        border-radius: 15px;
                        margin: 10px 0 25px 0;
                        text-align: center;
                        box-shadow: 0 4px 6px rgba(0,0,0,0.08);'>
            <h2 style='color: white; margin: 0; font-size: 2em; text-shadow: 2px 2px 4px rgba(0,0,0,0.3); letter-spacing: 1px;'>
                {selected_week_display} Leaders
            </h2>
        </div>
        """,
        unsafe_allow_html=True
    )
    st.write("")

    # Create tabs for each position
    tabs = st.tabs(tab_names)

    for tab, (tab_name, boards) in zip(tabs, zip(tab_names, tab_boards)):
        with tab:
            if boards:
                # Display all top projections in a row at the top
                if len(boards) > 1:
                    cols = st.columns(len(boards))
                    for i, (col, leaderboard) in enumerate(zip(cols, boards)):
                        with col:
                            df = leaderboard['dataframe']
                            if not df.empty and len(df) > 0:
                                player_column = "Player" if "Player" in df.columns else df.columns[1]
                                numeric_columns = [
                                    column for column in df.columns
                                    if pd.api.types.is_numeric_dtype(df[column])
                                ]

                                if numeric_columns:
                                    metric_column = numeric_columns[-1]
                                    top_row = df.nsmallest(1, "Rank") if "Rank" in df.columns else df.head(1)
                                    if not top_row.empty:
                                        metric_value = top_row.iloc[0][metric_column]
                                        player_value = top_row.iloc[0][player_column]

                                        # Format the value
                                        if is_float_dtype(df[metric_column]):
                                            formatted_value = f"{metric_value:,.1f}"
                                        elif is_integer_dtype(df[metric_column]):
                                            formatted_value = f"{int(metric_value):,}"
                                        else:
                                            formatted_value = str(metric_value)

                                        # Show top performer metric
                                        st.metric(
                                            label=leaderboard['title'].replace("Top 25 ", ""),
                                            value=f"{formatted_value} {metric_column}",
                                            delta=player_value
                                        )
                else:
                    # Single board - just show the metric centered
                    leaderboard = boards[0]
                    df = leaderboard['dataframe']
                    if not df.empty and len(df) > 0:
                        player_column = "Player" if "Player" in df.columns else df.columns[1]
                        numeric_columns = [
                            column for column in df.columns
                            if pd.api.types.is_numeric_dtype(df[column])
                        ]

                        if numeric_columns:
                            metric_column = numeric_columns[-1]
                            top_row = df.nsmallest(1, "Rank") if "Rank" in df.columns else df.head(1)
                            if not top_row.empty:
                                metric_value = top_row.iloc[0][metric_column]
                                player_value = top_row.iloc[0][player_column]

                                # Format the value
                                if is_float_dtype(df[metric_column]):
                                    formatted_value = f"{metric_value:,.1f}"
                                elif is_integer_dtype(df[metric_column]):
                                    formatted_value = f"{int(metric_value):,}"
                                else:
                                    formatted_value = str(metric_value)

                                # Show top performer metric
                                st.metric(
                                    label=leaderboard['title'].replace("Top 25 ", ""),
                                    value=f"{formatted_value} {metric_column}",
                                    delta=player_value
                                )

                # Display tables side by side for QB and RB (multi-stat positions)
                if tab_name in ["Quarterbacks", "Running Backs"] and len(boards) > 1:
                    cols = st.columns(len(boards))
                    for i, (col, leaderboard) in enumerate(zip(cols, boards)):
                        with col:
                            # Table title
                            st.markdown(f"""
                                <div style='text-align: center; margin: 20px 0 10px 0;'>
                                    <h4 style='color: #333; margin: 0; font-size: 1.1em; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;'>
                                        {leaderboard['title'].replace("Top 25 ", "")}
                                    </h4>
                                </div>
                                """,
                                unsafe_allow_html=True
                            )

                            # Display the full expanded dataframe
                            styled_df = create_styled_dataframe(leaderboard)
                            st.dataframe(styled_df, width='stretch', height=910, hide_index=True)
                else:
                    # Display tables vertically for single-stat positions (WR, TE)
                    for leaderboard in boards:
                        # Table title
                        st.markdown(f"""
                            <div style='text-align: center; margin: 20px 0 10px 0;'>
                                <h4 style='color: #333; margin: 0; font-size: 1.1em; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;'>
                                    {leaderboard['title'].replace("Top 25 ", "")}
                                </h4>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

                        # Display the full expanded dataframe
                        styled_df = create_styled_dataframe(leaderboard)
                        st.dataframe(styled_df, width='stretch', height=910, hide_index=True)
            else:
                st.info(f"No {tab_name.lower()} data available for this week.")

    # Add download button at bottom of leaders page
    st.write("")
    st.write("")
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        # PDF download button at bottom
        pdf_filename = f"week{selected_week.lower()}_leader_tables.pdf"
        pdf_path = os.path.join(BASE_DIR, "data/projections", pdf_filename)

        if os.path.exists(pdf_path):
            with open(pdf_path, "rb") as pdf_file:
                pdf_data = pdf_file.read()
            st.download_button(
                label="📄 Download Leader Tables PDF",
                data=pdf_data,
                file_name=pdf_filename,
                mime="application/pdf",
                help=f"Download the {selected_week_display} leader tables PDF report",
                width='stretch'
            )
        else:
            st.info("PDF report not available for this week")

else:
    # ===== GAME-SPECIFIC PROJECTIONS VIEW =====
    # Apply matchup filter
    team1, team2 = selected_matchup_key.split(" @ ")
    filtered_df = projections_df[
        ((projections_df['team'] == team1) & (projections_df['opp'] == team2)) |
        ((projections_df['team'] == team2) & (projections_df['opp'] == team1))
    ].copy()

    questionable_players = load_questionable_players(int(selected_week))
    filtered_df["full_name"] = filtered_df["full_name"].apply(
        lambda name: add_questionable_tag(name, questionable_players)
    )

    # Main data display
    matchup_heading = selected_matchup_label or selected_matchup_key or "Projections"
    st.markdown(f"""
        <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        padding: 1px;
                        border-radius: 15px;
                        margin: 10px 0 25px 0;
                        text-align: center;
                        box-shadow: 0 4px 6px rgba(0,0,0,0.1);'>
            <h2 style='color: white; margin: 0; font-size: 2em; text-shadow: 2px 2px 4px rgba(0,0,0,0.3);'>
                {matchup_heading} Projections
            </h2>
        </div>
        """,
        unsafe_allow_html=True
    )
    st.write("")

    if filtered_df.empty:
        st.info("No data matches your filters. Try adjusting your selections.")
    else:
        # Define the position-prop combinations we want to show
        position_prop_combinations = [
            ('QB', 'Passing Yards'),
            ('QB', 'Rushing Yards'),
            ('RB', 'Rushing Yards'),
            ('RB', 'Receiving Yards'),
            ('WR', 'Receiving Yards'),
            ('TE', 'Receiving Yards')
        ]

        # QB sections - side by side
        qb_cols = st.columns(2)

        # QB Passing Yards
        with qb_cols[0]:
            qb_passing_data = filtered_df[
                (filtered_df['position'] == 'QB') &
                (filtered_df['prop_type'] == 'Passing Yards')
            ].copy()

            if not qb_passing_data.empty:
                st.markdown('<h4 style="text-align: center; font-size: 1.1em; margin-bottom: 0.5em;">QB Passing Yards</h4>', unsafe_allow_html=True)
                display_df = qb_passing_data.sort_values('pred_yards', ascending=False)

                st.dataframe(
                    display_df[['full_name', 'team', 'pred_yards']].rename(columns={
                        'full_name': 'Player',
                        'team': 'Team',
                        'pred_yards': 'Projected Yards'
                    }),
                    width='stretch',
                    hide_index=True
                )

        # QB Rushing Yards
        with qb_cols[1]:
            qb_rushing_data = filtered_df[
                (filtered_df['position'] == 'QB') &
                (filtered_df['prop_type'] == 'Rushing Yards')
            ].copy()

            if not qb_rushing_data.empty:
                st.markdown('<h4 style="text-align: center; font-size: 1.1em; margin-bottom: 0.5em;">QB Rushing Yards</h4>', unsafe_allow_html=True)
                display_df = qb_rushing_data.sort_values('pred_yards', ascending=False)

                st.dataframe(
                    display_df[['full_name', 'team', 'pred_yards']].rename(columns={
                        'full_name': 'Player',
                        'team': 'Team',
                        'pred_yards': 'Projected Yards'
                    }),
                    width='stretch',
                    hide_index=True
                )

        # RB sections - side by side
        rb_cols = st.columns(2)

        # RB Rushing Yards
        with rb_cols[0]:
            rb_rushing_data = filtered_df[
                (filtered_df['position'] == 'RB') &
                (filtered_df['prop_type'] == 'Rushing Yards')
            ].copy()

            if not rb_rushing_data.empty:
                st.markdown('<h4 style="text-align: center; font-size: 1.1em; margin-bottom: 0.5em;">RB Rushing Yards</h4>', unsafe_allow_html=True)
                display_df = rb_rushing_data.sort_values('pred_yards', ascending=False)

                st.dataframe(
                    display_df[['full_name', 'team', 'pred_yards']].rename(columns={
                        'full_name': 'Player',
                        'team': 'Team',
                        'pred_yards': 'Projected Yards'
                    }),
                    width='stretch',
                    hide_index=True
                )

        # RB Receiving Yards
        with rb_cols[1]:
            rb_receiving_data = filtered_df[
                (filtered_df['position'] == 'RB') &
                (filtered_df['prop_type'] == 'Receiving Yards')
            ].copy()

            if not rb_receiving_data.empty:
                st.markdown('<h4 style="text-align: center; font-size: 1.1em; margin-bottom: 0.5em;">RB Receiving Yards</h4>', unsafe_allow_html=True)
                display_df = rb_receiving_data.sort_values('pred_yards', ascending=False)

                st.dataframe(
                    display_df[['full_name', 'team', 'pred_yards']].rename(columns={
                        'full_name': 'Player',
                        'team': 'Team',
                        'pred_yards': 'Projected Yards'
                    }),
                    width='stretch',
                    hide_index=True
                )

        # WR and TE Receiving Yards (side by side)
        wr_te_cols = st.columns(2)

        # WR Receiving Yards
        with wr_te_cols[0]:
            wr_receiving_data = filtered_df[
                (filtered_df['position'] == 'WR') &
                (filtered_df['prop_type'] == 'Receiving Yards')
            ].copy()

            if not wr_receiving_data.empty:
                st.markdown('<h4 style="text-align: center; font-size: 1.1em; margin-bottom: 0.5em;">WR Receiving Yards</h4>', unsafe_allow_html=True)
                display_df = wr_receiving_data.sort_values('pred_yards', ascending=False)

                st.dataframe(
                    display_df[['full_name', 'team', 'pred_yards']].rename(columns={
                        'full_name': 'Player',
                        'team': 'Team',
                        'pred_yards': 'Projected Yards'
                    }),
                    width='stretch',
                    hide_index=True
                )

        # TE Receiving Yards
        with wr_te_cols[1]:
            te_receiving_data = filtered_df[
                (filtered_df['position'] == 'TE') &
                (filtered_df['prop_type'] == 'Receiving Yards')
            ].copy()

            if not te_receiving_data.empty:
                st.markdown('<h4 style="text-align: center; font-size: 1.1em; margin-bottom: 0.5em;">TE Receiving Yards</h4>', unsafe_allow_html=True)
                display_df = te_receiving_data.sort_values('pred_yards', ascending=False)

                st.dataframe(
                    display_df[['full_name', 'team', 'pred_yards']].rename(columns={
                        'full_name': 'Player',
                        'team': 'Team',
                        'pred_yards': 'Projected Yards'
                    }),
                    width='stretch',
                    hide_index=True
                )

    # Add download button at bottom of projections page
    st.write("")
    st.write("")
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        # HTML report download button at bottom
        html_filename = f"week{selected_week}_complete_props_report.html"
        html_path = os.path.join(BASE_DIR, "data/projections", html_filename)

        if os.path.exists(html_path):
            with open(html_path, "rb") as html_file:
                html_data = html_file.read()
            st.download_button(
                label="📄 Download Report",
                data=html_data,
                file_name=html_filename,
                mime="text/html",
                help=f"Download the {selected_week_display} complete props HTML report",
                width='stretch'
            )
        else:
            st.info("HTML report not available for this week")

# Footer
render_footer()