import streamlit as st
import pandas as pd
import numpy as np
import os
import glob
import json
import re
from typing import Any, List, Tuple, Dict, Callable, Optional
from pandas.api.types import is_float_dtype, is_integer_dtype
from utils.footer import render_footer
from utils.session_state import persistent_selectbox

# -----------------------------------------------------------------------------
# CONSTANTS & CONFIG
# -----------------------------------------------------------------------------
PAGE_KEY_PREFIX = "v1_analysis_hub"
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECTIONS_DIR = os.path.join(BASE_DIR, "data", "projections")

st.set_page_config(
    page_title="Analysis Hub (V1)",
    page_icon="🔮",
    layout="wide"
)

# -----------------------------------------------------------------------------
# SHARED UTILS
# -----------------------------------------------------------------------------
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

def add_questionable_tag(name: str, questionable_players: set[str]):
    if pd.isna(name):
        return name
    name_str = str(name).strip()
    if "(Q)" in name_str:
        return name_str
    if "(Questionable)" in name_str:
        return name_str.replace("(Questionable)", "(Q)")
    return f"{name_str} (Q)" if name_str in questionable_players else name_str

# -----------------------------------------------------------------------------
# DATA LOADING FUNCTIONS
# -----------------------------------------------------------------------------
@st.cache_data
def load_game_times():
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

@st.cache_data
def load_games_for_week(week: int) -> pd.DataFrame:
    games_file = os.path.join(BASE_DIR, "data", "Games.csv")
    if os.path.exists(games_file):
        try:
            games_df = pd.read_csv(games_file)
            games_df['week'] = pd.to_numeric(games_df['week'], errors='coerce')
            games_df['season'] = pd.to_numeric(games_df['season'], errors='coerce')
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

@st.cache_data
def load_upcoming_games():
    games_file = os.path.join(BASE_DIR, "upcoming_games.csv")
    if os.path.exists(games_file):
        games_df = pd.read_csv(games_file)
        games_mapping = {}
        for _, row in games_df.iterrows():
            home, away = row['home_team'], row['away_team']
            games_mapping[(home, away)] = f"{away} @ {home}"
            games_mapping[(away, home)] = f"{away} @ {home}"
        return games_mapping, games_df
    return {}, pd.DataFrame()

@st.cache_data
def load_questionable_players(week: int) -> set[str]:
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

@st.cache_data
def load_projections_data():
    projections_dir = os.path.join(BASE_DIR, "data/projections")
    projection_files = glob.glob(os.path.join(projections_dir, "week*_all_props_summary.csv"))
    if not projection_files:
        return None, []
    available_weeks = []
    for file in projection_files:
        week_num = file.split('week')[1].split('_')[0]
        available_weeks.append(int(week_num))
    available_weeks.sort()
    return projection_files, available_weeks

@st.cache_data
def get_week_projections(week_num):
    file_path = os.path.join(BASE_DIR, f"data/projections/week{week_num}_all_props_summary.csv")
    if not os.path.exists(file_path):
        return None
    try:
        df = pd.read_csv(file_path)
        df = df.dropna(subset=['pred_yards'])
        df['pred_yards'] = pd.to_numeric(df['pred_yards'], errors='coerce')
        df = df.dropna(subset=['pred_yards'])
        return df
    except Exception:
        return None

# -----------------------------------------------------------------------------
# MAIN APP
# -----------------------------------------------------------------------------
st.markdown(f"""
    <div style='text-align: center;'>
        <div style='font-size: 3.1rem; font-weight: 800; padding-bottom: 0.5rem;'>
            NFL Analysis Hub
        </div>
        <div style='color: #7f8c8d; font-size: 1rem; margin-top: 0; line-height: 1.2;'>
            Comprehensive Projections & Weekly Leaders
        </div>
    </div>
    """, unsafe_allow_html=True)
st.divider()

# Sidebar
projection_files, available_weeks = load_projections_data()
if not available_weeks:
    st.error("No projection data available.")
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
selected_week = selected_week_display.replace("Week ", "")
projections_df = get_week_projections(int(selected_week))

if projections_df is None:
    st.error(f"No data available for {selected_week_display}")
    st.stop()

# -----------------------------------------------------------------------------
# TABS
# -----------------------------------------------------------------------------
tab1, tab2 = st.tabs(["🔮 Game Matchups", "📋 League Leaders"])

# -----------------------------------------------------------------------------
# TAB 1: GAME MATCHUPS (PROJECTIONS LOGIC)
# -----------------------------------------------------------------------------
with tab1:
    games_mapping, upcoming_games_df = load_upcoming_games()
    game_times = load_game_times()
    week_games_df = load_games_for_week(int(selected_week))

    # Build Matchups
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

    # Game Selector (Inside Tab or Sidebar - Keeping in Sidebar for consistency with Tab usage)
    # But usually filters for tabs are better inside the tab if they are specific. 
    # Since Sidebar is global, we put it there but maybe visually group it?
    # Let's put it at the top of the tab for context specific control
    col_sel, _ = st.columns([1, 2])
    with col_sel:
        selected_matchup_option = st.selectbox(
            "Select Game Matchup:",
            options=matchups,
            format_func=option_display_label,
            key=f"{PAGE_KEY_PREFIX}_matchup_select"
        )
    
    selected_matchup_key = selected_matchup_option[0] if selected_matchup_option else None
    
    # Filter Data
    if selected_matchup_key:
        team1, team2 = selected_matchup_key.split(" @ ")
        filtered_df = projections_df[
            ((projections_df['team'] == team1) & (projections_df['opp'] == team2)) |
            ((projections_df['team'] == team2) & (projections_df['opp'] == team1))
        ].copy()
    else:
        filtered_df = projections_df.copy()

    questionable_players = load_questionable_players(int(selected_week))
    filtered_df["full_name"] = filtered_df["full_name"].apply(
        lambda name: add_questionable_tag(name, questionable_players)
    )

    if filtered_df.empty:
        st.info("No data matches your filters.")
    else:
        # Render Projections Grids
        def render_proj_table(df, title):
            if not df.empty:
                st.markdown(f'<h4 style="text-align: center; font-size: 1.1em; margin-bottom: 0.5em;">{title}</h4>', unsafe_allow_html=True)
                display_df = df.sort_values('pred_yards', ascending=False)
                st.dataframe(
                    display_df[['full_name', 'team', 'pred_yards']].rename(columns={
                        'full_name': 'Player', 'team': 'Team', 'pred_yards': 'Projected Yards'
                    }),
                    use_container_width=True,
                    hide_index=True
                )

        qb_cols = st.columns(2)
        with qb_cols[0]:
            render_proj_table(filtered_df[(filtered_df['position'] == 'QB') & (filtered_df['prop_type'] == 'Passing Yards')], "QB Passing Yards")
        with qb_cols[1]:
            render_proj_table(filtered_df[(filtered_df['position'] == 'QB') & (filtered_df['prop_type'] == 'Rushing Yards')], "QB Rushing Yards")

        rb_cols = st.columns(2)
        with rb_cols[0]:
            render_proj_table(filtered_df[(filtered_df['position'] == 'RB') & (filtered_df['prop_type'] == 'Rushing Yards')], "RB Rushing Yards")
        with rb_cols[1]:
            render_proj_table(filtered_df[(filtered_df['position'] == 'RB') & (filtered_df['prop_type'] == 'Receiving Yards')], "RB Receiving Yards")

        wr_te_cols = st.columns(2)
        with wr_te_cols[0]:
            render_proj_table(filtered_df[(filtered_df['position'] == 'WR') & (filtered_df['prop_type'] == 'Receiving Yards')], "WR Receiving Yards")
        with wr_te_cols[1]:
            render_proj_table(filtered_df[(filtered_df['position'] == 'TE') & (filtered_df['prop_type'] == 'Receiving Yards')], "TE Receiving Yards")

# -----------------------------------------------------------------------------
# TAB 2: LEAGUE LEADERS (LEADERS LOGIC)
# -----------------------------------------------------------------------------
with tab2:
    def create_leaderboard(df, prop_type, title, position_filter=None, top_n=25):
        prop_data = df[df['prop_type'] == prop_type].copy()
        if position_filter:
            prop_data = position_filter(prop_data)
        if prop_data.empty: return None
        leaderboard_df = prop_data.nlargest(top_n, 'pred_yards').copy()
        leaderboard_df['Rank'] = range(1, len(leaderboard_df) + 1)
        leaderboard_df = leaderboard_df[['Rank', 'full_name', 'team', 'opp', 'pred_yards']]
        leaderboard_df.columns = ['Rank', 'Player', 'Team', 'Opponent', 'Projected Yards']
        return {'title': title, 'dataframe': leaderboard_df}

    leaderboards = []
    lb1 = create_leaderboard(projections_df, 'Passing Yards', 'Top QB Passing Yards', top_n=100)
    if lb1: leaderboards.append(lb1)
    lb2 = create_leaderboard(projections_df, 'Rushing Yards', 'Top QB Rushing Yards', lambda df: df[df['position'] == 'QB'], top_n=100)
    if lb2: leaderboards.append(lb2)
    lb3 = create_leaderboard(projections_df, 'Receiving Yards', 'Top 25 WR Receiving Yards', lambda df: df[df['position'] == 'WR'])
    if lb3: leaderboards.append(lb3)
    lb4 = create_leaderboard(projections_df, 'Receiving Yards', 'Top 25 TE Receiving Yards', lambda df: df[df['position'] == 'TE'])
    if lb4: leaderboards.append(lb4)
    lb5 = create_leaderboard(projections_df, 'Rushing Yards', 'Top 25 RB Rushing Yards', lambda df: df[df['position'] == 'RB']) # Fixed filter
    if lb5: leaderboards.append(lb5)
    lb6 = create_leaderboard(projections_df, 'Receiving Yards', 'Top 25 RB Receiving Yards', lambda df: df[df['position'] == 'RB'])
    if lb6: leaderboards.append(lb6)

    # Organized Tabs inside Leaders View
    l_tabs = st.tabs(["Quarterbacks", "Running Backs", "Wide Receivers", "Tight Ends"])
    
    def render_styled_leaderboard(leaderboard):
        df = leaderboard['dataframe']
        # Styling (simplified from original for brevity but preserving structure)
        st.markdown(f"<div style='text-align: center; margin: 10px 0;'><h4 style='color: #333;'>{leaderboard['title'].replace('Top 25 ', '')}</h4></div>", unsafe_allow_html=True)
        st.dataframe(df, use_container_width=True, hide_index=True)

    with l_tabs[0]: # QB
        cols = st.columns(2)
        with cols[0]:
            if lb1: render_styled_leaderboard(lb1)
        with cols[1]:
            if lb2: render_styled_leaderboard(lb2)
    
    with l_tabs[1]: # RB
        cols = st.columns(2)
        with cols[0]:
            if lb5: render_styled_leaderboard(lb5)
        with cols[1]:
            if lb6: render_styled_leaderboard(lb6)
            
    with l_tabs[2]: # WR
        if lb3: render_styled_leaderboard(lb3)
        
    with l_tabs[3]: # TE
        if lb4: render_styled_leaderboard(lb4)

# Footer
render_footer()
