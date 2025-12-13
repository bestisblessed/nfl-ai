import streamlit as st
import pandas as pd
import numpy as np
import os
import glob
import json
import re
from typing import Any, List, Tuple, Optional
from utils.footer import render_footer
from utils.session_state import persistent_selectbox

# -----------------------------------------------------------------------------
# CONFIG
# -----------------------------------------------------------------------------
PAGE_KEY_PREFIX = "v1_value_plays"
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECTIONS_DIR = os.path.join(BASE_DIR, "data", "projections")
YARD_THRESHOLDS = {
    "Passing Yards": (45.0, 75.0),
    "Receiving Yards": (15.0, 25.0),
    "Rushing Yards": (15.0, 25.0),
}

st.set_page_config(
    page_title="Betting Value (V1)",
    page_icon="💎",
    layout="wide"
)

st.markdown(
    """
    <style>
        [data-testid="column"] { padding-left: 0.05rem !important; padding-right: 0.05rem  !important; }
        .stDataFrame { width: 100% !important; }
        [data-testid="stDataFrame"] { width: 100% !important; }
        [data-testid="column"] > div { padding-left: 0.05rem !important; padding-right: 0.05rem !important; }
    </style>
    """,
    unsafe_allow_html=True,
)

# -----------------------------------------------------------------------------
# UTILS
# -----------------------------------------------------------------------------
def format_game_time_label(start_time: Any = None, date_value: Any = None, time_value: Any = None) -> str:
    timestamp = None
    if pd.notna(start_time):
        timestamp = pd.to_datetime(start_time, errors="coerce")
    else:
        components = []
        if pd.notna(date_value): components.append(str(date_value))
        if pd.notna(time_value): components.append(str(time_value))
        if components:
            combined = " ".join(components)
            timestamp = pd.to_datetime(combined, errors="coerce")
    if timestamp is None or pd.isna(timestamp) or timestamp == pd.Timestamp.max:
        return ""
    time_str = timestamp.strftime("%I:%M %p").lstrip("0")
    day_str = timestamp.strftime("%a")
    return f"{day_str} {time_str}"

def build_game_option_label(matchup: str, time_label: str = "") -> Tuple[str, str]:
    display = f"{matchup} · {time_label}" if time_label else matchup
    return matchup, display

def option_display_label(option: Any) -> str:
    return option[1] if isinstance(option, tuple) else str(option)

@st.cache_data
def load_game_times():
    games_with_times = {}
    try:
        data_dir = os.path.join(BASE_DIR, "data", "odds")
        json_files = sorted([f for f in os.listdir(data_dir) if f.endswith(".json") and f.startswith('nfl')], reverse=True)
        if json_files:
            filepath = os.path.join(data_dir, json_files[0])
            with open(filepath) as f:
                data = json.load(f)
                for game in data:
                    game_time = game.get('Time', '')
                    day_and_matchup_key = list(game.keys())[1] if len(game.keys()) > 1 else None
                    if day_and_matchup_key:
                        teams = game[day_and_matchup_key].replace('\n', ' ').strip()
                        teams_list = [team.strip() for team in (re.split(r'\s+|,', teams) if '  ' not in teams else teams.split('  ')) if team.strip()]
                        if len(teams_list) == 2:
                            games_with_times[f"{teams_list[0]} vs {teams_list[1]}"] = {'time': game_time, 'date': day_and_matchup_key.strip()}
    except Exception: pass
    return games_with_times

@st.cache_data
def load_questionable_players(week: int) -> set[str]:
    questionable_players: set[str] = set()
    txt_path = os.path.join(PROJECTIONS_DIR, f"week{week}_complete_props_report.txt")
    html_path = os.path.join(PROJECTIONS_DIR, f"week{week}_complete_props_report.html")
    def extract_players(text: str) -> None:
        matches = re.findall(r"([A-Za-z0-9'.-]+(?:\s+[A-Za-z0-9'.-]+)*)\s+\(Questionable\)", text)
        questionable_players.update(name.strip() for name in matches)
    if os.path.exists(txt_path):
        with open(txt_path, "r", encoding="utf-8") as file: extract_players(file.read())
    elif os.path.exists(html_path):
        with open(html_path, "r", encoding="utf-8") as file: extract_players(file.read())
    return questionable_players

@st.cache_data
def discover_value_weeks(directory: str) -> List[int]:
    pattern = os.path.join(directory, "week*_value_opportunities.csv")
    weeks: List[int] = []
    for file_path in glob.glob(pattern):
        try:
            week_str = os.path.basename(file_path).split("week")[1].split("_")[0]
            weeks.append(int(week_str))
        except (IndexError, ValueError): continue
    return sorted(set(weeks))

@st.cache_data
def load_value_data(week: int) -> Tuple[pd.DataFrame, Optional[pd.DataFrame]]:
    opportunities_path = os.path.join(PROJECTIONS_DIR, f"week{week}_value_opportunities.csv")
    if not os.path.exists(opportunities_path):
        raise FileNotFoundError(f"Could not locate value opportunities for week {week}")
    value_df = pd.read_csv(opportunities_path)
    numeric_columns = ["predicted_yards", "best_point", "best_price", "edge_yards", "implied_prob", "ev_per_1"]
    for column in numeric_columns:
        if column in value_df.columns: value_df[column] = pd.to_numeric(value_df[column], errors="coerce")
    return value_df, None

# -----------------------------------------------------------------------------
# MAIN APP
# -----------------------------------------------------------------------------
st.markdown(
    """
    <div style='text-align: center;'>
        <div style='font-size: 3.1rem; font-weight: 800; padding-bottom: 0.5rem;'>
            NFL Value Play Finder
        </div>
        <div style='color: #7f8c8d; font-size: 1rem; margin-top: 0; line-height: 1.2;'>
            Model-generated edges highlighting the best projected opportunities each week
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)
st.divider()

available_weeks = discover_value_weeks(PROJECTIONS_DIR)
if not available_weeks:
    st.error("No value projection files found.")
    st.stop()

st.sidebar.markdown("<h2 style='text-align: center;'>Selection</h2>", unsafe_allow_html=True)
week_options = [f"Week {week}" for week in available_weeks]
selected_week = persistent_selectbox(
    "Week:", options=week_options, page=PAGE_KEY_PREFIX, widget="week",
    default=week_options[-1] if week_options else None, container=st.sidebar
)
selected_week_number = int(selected_week.replace("Week ", ""))

try:
    value_opportunities, _ = load_value_data(selected_week_number)
except FileNotFoundError as exc:
    st.error(str(exc))
    st.stop()

questionable_players = load_questionable_players(selected_week_number)
value_opportunities = value_opportunities.fillna({"bookmaker": "-", "side": "-", "edge_yards": 0.0})

# Game Selection Logic
games_set = set()
matchup_options = []
if "team" in value_opportunities.columns and "opp" in value_opportunities.columns:
    for _, row in value_opportunities.iterrows():
        if pd.notna(row.get("team")) and pd.notna(row.get("opp")):
            pair = tuple(sorted([row['team'], row['opp']]))
            if pair not in games_set:
                games_set.add(pair)
                matchup_options.append(build_game_option_label(f"{pair[0]} vs {pair[1]}"))
else:
    # Fallback to home/away if available
    if "home_team" in value_opportunities.columns:
        games_df = value_opportunities[["home_team", "away_team"]].drop_duplicates()
        for _, row in games_df.iterrows():
            matchup_options.append(build_game_option_label(f"{row['away_team']} @ {row['home_team']}"))

game_options = [build_game_option_label("All Games")] + sorted(matchup_options, key=lambda x: x[1])

selected_game_option = persistent_selectbox(
    "Game:", options=game_options, page=PAGE_KEY_PREFIX, widget="game",
    default=game_options[0] if game_options else None, container=st.sidebar,
    format_func=option_display_label,
)
selected_game_key = selected_game_option[0] if selected_game_option else None

st.sidebar.markdown("""
    <div style='text-align: center; font-size: 0.92rem; margin-top: 1rem;'>
        <div style='font-size: 1.2rem; font-weight: 600; margin-bottom: 4px;'>Legend</div>
        <div style='display: flex; flex-direction: column; gap: 3px;'>
            <div style='background: #f5f7fb; border: 1px solid #d6dcf2; border-radius: 8px; padding: 4px;'>
                <div style='font-weight: 600; color: #34495e;'>Passing</div>
                <div style='color: #6c7a89;'>💎 ≥ 75 yds | ⚡️ ≥ 45 yds</div>
            </div>
            <div style='background: #f5f7fb; border: 1px solid #d6dcf2; border-radius: 8px; padding: 4px;'>
                <div style='font-weight: 600; color: #34495e;'>Receiving/Rushing</div>
                <div style='color: #6c7a89;'>💎 ≥ 25 yds | ⚡️ ≥ 15 yds</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# Helper functions for display
def style_side_cell(val):
    val_str = str(val).upper()
    if "OVER" in val_str: return 'color: #2e7d32; font-weight: 500;'
    if "UNDER" in val_str: return 'color: #c62828; font-weight: 500;'
    return 'color: #666;'

def format_side_with_emoji(side_value):
    if pd.isna(side_value) or side_value == "-": return "-"
    side_str = str(side_value).strip().upper()
    return "Over ⬆️" if "OVER" in side_str else ("Under ⬇️" if "UNDER" in side_str else str(side_value))

# View Rendering
if selected_game_key and selected_game_key != "All Games":
    # Game Specific View
    if " @ " in selected_game_key:
        t1, t2 = selected_game_key.split(" @ ")
        game_data = value_opportunities[((value_opportunities["team"]==t1) & (value_opportunities["opp"]==t2)) | ((value_opportunities["team"]==t2) & (value_opportunities["opp"]==t1))].copy()
    elif " vs " in selected_game_key:
        t1, t2 = selected_game_key.split(" vs ")
        game_data = value_opportunities[((value_opportunities["team"]==t1) & (value_opportunities["opp"]==t2)) | ((value_opportunities["team"]==t2) & (value_opportunities["opp"]==t1))].copy()
    else:
        game_data = value_opportunities.copy()

    st.markdown(f"<h2 style='text-align:center;'>{selected_game_option[1]}</h2>", unsafe_allow_html=True)

    def build_display_table(df_slice, prop_type):
        df_slice = df_slice.copy()
        if questionable_players:
            df_slice["player"] = df_slice["player"].apply(lambda n: f"{n} (Q)" if n in questionable_players else n)
        
        # Add emojis
        thresholds = YARD_THRESHOLDS.get(prop_type)
        if thresholds:
            low, high = thresholds
            df_slice["player"] = df_slice.apply(lambda r: f"💎 {r['player']}" if r['edge_yards'] >= high else (f"⚡️ {r['player']}" if r['edge_yards'] >= low else r['player']), axis=1)

        df_slice["Side"] = df_slice["side"].apply(format_side_with_emoji)
        df_slice["Proj (yds)"] = df_slice["predicted_yards"].round(1)
        df_slice["Edge (yds)"] = df_slice["edge_yards"].round(1)
        
        # Best Line formatting
        df_slice["Best Line"] = df_slice.apply(lambda r: f"{r['best_point']:.1f} ({int(r['best_price']):+d})", axis=1)

        return df_slice[["player", "Side", "Proj (yds)", "Edge (yds)", "Best Line", "bookmaker"]].rename(columns={"player": "Player", "bookmaker": "Book"})

    cols = st.columns(2)
    with cols[0]:
        st.caption("QB Passing Yards")
        qb_pass = game_data[(game_data['position']=='QB') & (game_data['prop_type']=='Passing Yards')].sort_values('edge_yards', ascending=False)
        if not qb_pass.empty:
            st.dataframe(build_display_table(qb_pass, 'Passing Yards').style.map(style_side_cell, subset=["Side"]), use_container_width=True, hide_index=True)
    with cols[1]:
        st.caption("QB Rushing Yards")
        qb_rush = game_data[(game_data['position']=='QB') & (game_data['prop_type']=='Rushing Yards')].sort_values('edge_yards', ascending=False)
        if not qb_rush.empty:
            st.dataframe(build_display_table(qb_rush, 'Rushing Yards').style.map(style_side_cell, subset=["Side"]), use_container_width=True, hide_index=True)
    
    # RBs
    cols = st.columns(2)
    with cols[0]:
        st.caption("RB Rushing Yards")
        rb_rush = game_data[(game_data['position']=='RB') & (game_data['prop_type']=='Rushing Yards')].sort_values('edge_yards', ascending=False)
        if not rb_rush.empty:
            st.dataframe(build_display_table(rb_rush, 'Rushing Yards').style.map(style_side_cell, subset=["Side"]), use_container_width=True, hide_index=True)
    with cols[1]:
        st.caption("RB Receiving Yards")
        rb_rec = game_data[(game_data['position']=='RB') & (game_data['prop_type']=='Receiving Yards')].sort_values('edge_yards', ascending=False)
        if not rb_rec.empty:
            st.dataframe(build_display_table(rb_rec, 'Receiving Yards').style.map(style_side_cell, subset=["Side"]), use_container_width=True, hide_index=True)

    # WR/TE
    cols = st.columns(2)
    with cols[0]:
        st.caption("WR Receiving Yards")
        wr_rec = game_data[(game_data['position']=='WR') & (game_data['prop_type']=='Receiving Yards')].sort_values('edge_yards', ascending=False)
        if not wr_rec.empty:
            st.dataframe(build_display_table(wr_rec, 'Receiving Yards').style.map(style_side_cell, subset=["Side"]), use_container_width=True, hide_index=True)
    with cols[1]:
        st.caption("TE Receiving Yards")
        te_rec = game_data[(game_data['position']=='TE') & (game_data['prop_type']=='Receiving Yards')].sort_values('edge_yards', ascending=False)
        if not te_rec.empty:
            st.dataframe(build_display_table(te_rec, 'Receiving Yards').style.map(style_side_cell, subset=["Side"]), use_container_width=True, hide_index=True)

else:
    # All Games View
    st.markdown(f"<h2 style='text-align:center;'>Week {selected_week_number} Value Plays</h2>", unsafe_allow_html=True)
    prop_tabs = st.tabs(sorted(value_opportunities["prop_type"].unique()))
    for tab, prop_type in zip(prop_tabs, sorted(value_opportunities["prop_type"].unique())):
        with tab:
            subset = value_opportunities[value_opportunities["prop_type"] == prop_type].copy()
            if not subset.empty:
                subset = subset.sort_values(by="edge_yards", ascending=False).reset_index(drop=True)
                subset["Side"] = subset["side"].apply(format_side_with_emoji)
                
                # Indicators
                thresholds = YARD_THRESHOLDS.get(prop_type)
                if thresholds:
                    low, high = thresholds
                    subset["Ind"] = subset["edge_yards"].apply(lambda y: "💎" if y >= high else ("⚡️" if y >= low else ""))
                else:
                    subset["Ind"] = ""

                display_df = subset[[
                    "Ind", "player", "position", "team", "opp", "predicted_yards", "best_point", "best_price", "edge_yards", "Side", "bookmaker"
                ]].rename(columns={
                    "player": "Player", "position": "Pos", "team": "Tm", "opp": "Opp",
                    "predicted_yards": "Proj", "best_point": "Line", "best_price": "Odds",
                    "edge_yards": "Edge", "bookmaker": "Book"
                })
                
                st.dataframe(
                    display_df.style.map(style_side_cell, subset=["Side"]),
                    use_container_width=True,
                    hide_index=True
                )

render_footer()
