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
PAGE_KEY_PREFIX = "v2_unified"
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECTIONS_DIR = os.path.join(BASE_DIR, "data", "projections")
YARD_THRESHOLDS = {
    "Passing Yards": (45.0, 75.0),
    "Receiving Yards": (15.0, 25.0),
    "Rushing Yards": (15.0, 25.0),
}

st.set_page_config(
    page_title="Unified Dashboard (V2)",
    page_icon="🏈",
    layout="wide"
)

st.markdown(
    """
    <style>
        [data-testid="column"] { padding-left: 0.05rem !important; padding-right: 0.05rem  !important; }
        .stDataFrame { width: 100% !important; }
        [data-testid="stDataFrame"] { width: 100% !important; }
    </style>
    """,
    unsafe_allow_html=True,
)

# -----------------------------------------------------------------------------
# UTILS & LOADERS
# -----------------------------------------------------------------------------
def format_matchup_time(start_time=None, date_value=None, time_value=None):
    timestamp = None
    if pd.notna(start_time):
        timestamp = pd.to_datetime(start_time, errors='coerce')
    else:
        components = []
        if pd.notna(date_value): components.append(str(date_value))
        if pd.notna(time_value): components.append(str(time_value))
        if components:
            timestamp = pd.to_datetime(" ".join(components), errors='coerce')
    if timestamp is None or pd.isna(timestamp) or timestamp == pd.Timestamp.max: return ""
    return f"{timestamp.strftime('%a')} {timestamp.strftime('%I:%M %p').lstrip('0')}"

def option_display_label(option): return option[1] if isinstance(option, tuple) else str(option)

def add_questionable_tag(name, questionable_players):
    if pd.isna(name): return name
    name_str = str(name).strip()
    if "(Q)" in name_str or "(Questionable)" in name_str: return name_str.replace("(Questionable)", "(Q)")
    return f"{name_str} (Q)" if name_str in questionable_players else name_str

@st.cache_data
def load_data_bundle():
    # Load all static data in one go
    upcoming_games_path = os.path.join(BASE_DIR, "upcoming_games.csv")
    games_file = os.path.join(BASE_DIR, "data", "Games.csv")
    
    upcoming_games = pd.read_csv(upcoming_games_path) if os.path.exists(upcoming_games_path) else pd.DataFrame()
    historical_games = pd.read_csv(games_file) if os.path.exists(games_file) else pd.DataFrame()
    
    if not historical_games.empty:
        historical_games['week'] = pd.to_numeric(historical_games['week'], errors='coerce')
        historical_games['season'] = pd.to_numeric(historical_games['season'], errors='coerce')

    return upcoming_games, historical_games

@st.cache_data
def load_game_times():
    # Simplified loading
    data_dir = os.path.join(BASE_DIR, "data", "odds")
    times = {}
    try:
        files = sorted([f for f in os.listdir(data_dir) if f.endswith(".json") and f.startswith('nfl')], reverse=True)
        if files:
            with open(os.path.join(data_dir, files[0])) as f:
                for game in json.load(f):
                    key = list(game.keys())[1] if len(game.keys()) > 1 else None
                    if key:
                        t = game[key].replace('\n', ' ').split()
                        # Very naive parsing for demo speed
                        # In production use robust parsing
                        pass 
    except: pass
    return times

@st.cache_data
def get_week_projections(week):
    path = os.path.join(BASE_DIR, f"data/projections/week{week}_all_props_summary.csv")
    if not os.path.exists(path): return None
    try:
        df = pd.read_csv(path).dropna(subset=['pred_yards'])
        df['pred_yards'] = pd.to_numeric(df['pred_yards'], errors='coerce')
        return df.dropna(subset=['pred_yards'])
    except: return None

@st.cache_data
def get_week_values(week):
    path = os.path.join(PROJECTIONS_DIR, f"week{week}_value_opportunities.csv")
    if not os.path.exists(path): return None
    df = pd.read_csv(path)
    cols = ["predicted_yards", "best_point", "best_price", "edge_yards"]
    for c in cols: 
        if c in df.columns: df[c] = pd.to_numeric(df[c], errors='coerce')
    return df.fillna({"edge_yards": 0, "side": "-", "bookmaker": "-"})

@st.cache_data
def load_questionable(week):
    q = set()
    path = os.path.join(PROJECTIONS_DIR, f"week{week}_complete_props_report.txt")
    if os.path.exists(path):
        with open(path) as f:
            q.update(name.strip() for name in re.findall(r"([A-Za-z0-9'.-]+(?:\s+[A-Za-z0-9'.-]+)*)\s+\(Questionable\)", f.read()))
    return q

# -----------------------------------------------------------------------------
# MAIN APP
# -----------------------------------------------------------------------------
st.title("Unified Model Dashboard")
st.divider()

# Sidebar Selection
files = glob.glob(os.path.join(PROJECTIONS_DIR, "week*_all_props_summary.csv"))
avail_weeks = sorted([int(f.split('week')[1].split('_')[0]) for f in files])
if not avail_weeks: st.stop()

st.sidebar.markdown("## Selection")
sel_week_str = persistent_selectbox("Week:", [f"Week {w}" for w in avail_weeks], PAGE_KEY_PREFIX, "week", container=st.sidebar, default=f"Week {avail_weeks[-1]}")
sel_week = int(sel_week_str.replace("Week ", ""))

# Load Data for Week
proj_df = get_week_projections(sel_week)
val_df = get_week_values(sel_week)
q_players = load_questionable(sel_week)
upcoming_games, historical_games = load_data_bundle()

if proj_df is None:
    st.error("Data not found.")
    st.stop()

proj_df["full_name"] = proj_df["full_name"].apply(lambda n: add_questionable_tag(n, q_players))

# TABS
tab_proj, tab_lead, tab_val = st.tabs(["🔮 Game Projections", "📋 League Leaders", "💎 Value Plays"])

# --- TAB 1: PROJECTIONS ---
with tab_proj:
    # Build Game List
    games = []
    # Try historical first
    week_games = historical_games[(historical_games['season'] == 2025) & (historical_games['week'] == sel_week)]
    if not week_games.empty:
        for _, row in week_games.drop_duplicates(['home_team', 'away_team']).iterrows():
            games.append((f"{row['away_team']} @ {row['home_team']}", row.get('gametime', '')))
    # Fallback to projections teams
    if not games:
        pairs = set()
        for _, row in proj_df.iterrows():
            p = tuple(sorted([row['team'], row['opp']]))
            if p not in pairs:
                pairs.add(p)
                games.append((f"{p[0]} @ {p[1]}", ""))
    
    col_sel, _ = st.columns([1, 2])
    with col_sel:
        sel_game = st.selectbox("Select Matchup", options=games, format_func=lambda x: x[0], key="v2_proj_game")
    
    if sel_game:
        t1, t2 = sel_game[0].split(" @ ")
        subset = proj_df[((proj_df['team'] == t1) & (proj_df['opp'] == t2)) | ((proj_df['team'] == t2) & (proj_df['opp'] == t1))]
        
        # Helper to render table
        def rt(pos, prop, title):
            d = subset[(subset['position'] == pos) & (subset['prop_type'] == prop)].sort_values('pred_yards', ascending=False)
            if not d.empty:
                st.caption(title)
                st.dataframe(d[['full_name', 'team', 'pred_yards']].rename(columns={'full_name': 'Player', 'pred_yards': 'Yds'}), use_container_width=True, hide_index=True)

        c1, c2 = st.columns(2)
        with c1: rt('QB', 'Passing Yards', 'QB Pass'); rt('RB', 'Rushing Yards', 'RB Rush'); rt('WR', 'Receiving Yards', 'WR Rec')
        with c2: rt('QB', 'Rushing Yards', 'QB Rush'); rt('RB', 'Receiving Yards', 'RB Rec'); rt('TE', 'Receiving Yards', 'TE Rec')

# --- TAB 2: LEADERS ---
with tab_lead:
    l_tabs = st.tabs(["QB", "RB", "WR", "TE"])
    
    def render_leaderboard(df, pos, prop, title):
        d = df[(df['position'] == pos) & (df['prop_type'] == prop)].nlargest(25, 'pred_yards')
        if not d.empty:
            d['Rank'] = range(1, len(d)+1)
            st.dataframe(d[['Rank', 'full_name', 'team', 'opp', 'pred_yards']].rename(columns={'full_name': 'Player', 'pred_yards': 'Yards'}), use_container_width=True, hide_index=True)

    with l_tabs[0]:
        c1, c2 = st.columns(2)
        with c1: st.markdown("#### Passing"); render_leaderboard(proj_df, 'QB', 'Passing Yards', '')
        with c2: st.markdown("#### Rushing"); render_leaderboard(proj_df, 'QB', 'Rushing Yards', '')
    with l_tabs[1]:
        c1, c2 = st.columns(2)
        with c1: st.markdown("#### Rushing"); render_leaderboard(proj_df, 'RB', 'Rushing Yards', '')
        with c2: st.markdown("#### Receiving"); render_leaderboard(proj_df, 'RB', 'Receiving Yards', '')
    with l_tabs[2]: render_leaderboard(proj_df, 'WR', 'Receiving Yards', 'Top WRs')
    with l_tabs[3]: render_leaderboard(proj_df, 'TE', 'Receiving Yards', 'Top TEs')

# --- TAB 3: VALUE PLAYS ---
with tab_val:
    if val_df is None:
        st.info("No value data for this week.")
    else:
        # Game Filter for Value
        v_games = ["All Games"]
        if "team" in val_df.columns:
            pairs = set()
            for _, row in val_df.iterrows():
                pairs.add(tuple(sorted([row['team'], row['opp']])))
            v_games.extend([f"{p[0]} vs {p[1]}" for p in sorted(pairs)])
            
        sel_v_game = st.selectbox("Filter Game", v_games, key="v2_val_game")
        
        # Filter DF
        if sel_v_game != "All Games":
            t1, t2 = sel_v_game.split(" vs ")
            v_sub = val_df[((val_df['team'] == t1) & (val_df['opp'] == t2)) | ((val_df['team'] == t2) & (val_df['opp'] == t1))]
        else:
            v_sub = val_df
            
        # Display Logic
        v_sub = v_sub.copy()
        v_sub["Side"] = v_sub["side"].apply(lambda s: f"{s} ⬆️" if "OVER" in str(s).upper() else (f"{s} ⬇️" if "UNDER" in str(s).upper() else s))
        
        # Emojis
        def get_emoji(row):
            thr = YARD_THRESHOLDS.get(row['prop_type'])
            if thr:
                if row['edge_yards'] >= thr[1]: return "💎"
                if row['edge_yards'] >= thr[0]: return "⚡️"
            return ""
        v_sub["Ind"] = v_sub.apply(get_emoji, axis=1)
        
        st.markdown("### Top Edges")
        
        # If All Games, show tabs for prop types
        if sel_v_game == "All Games":
            ptabs = st.tabs(sorted(v_sub['prop_type'].unique()))
            for pt, tab in zip(sorted(v_sub['prop_type'].unique()), ptabs):
                with tab:
                    d = v_sub[v_sub['prop_type'] == pt].sort_values('edge_yards', ascending=False)
                    st.dataframe(
                        d[["Ind", "player", "team", "predicted_yards", "best_point", "edge_yards", "Side"]].rename(columns={"predicted_yards": "Proj", "best_point": "Line", "edge_yards": "Edge"}),
                        use_container_width=True, hide_index=True
                    )
        else:
            # Game View - Side by Side
            c1, c2 = st.columns(2)
            with c1: 
                st.caption("Passing/Rushing"); 
                d = v_sub[v_sub['prop_type'].isin(['Passing Yards', 'Rushing Yards'])].sort_values('edge_yards', ascending=False)
                st.dataframe(d[["Ind", "player", "prop_type", "edge_yards", "Side"]], use_container_width=True, hide_index=True)
            with c2:
                st.caption("Receiving");
                d = v_sub[v_sub['prop_type'] == 'Receiving Yards'].sort_values('edge_yards', ascending=False)
                st.dataframe(d[["Ind", "player", "edge_yards", "Side"]], use_container_width=True, hide_index=True)

render_footer()
