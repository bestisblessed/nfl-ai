import streamlit as st
import pandas as pd
import os
import glob
import re
from utils.footer import render_footer
from utils.session_state import persistent_selectbox

PAGE_KEY_PREFIX = "v4_models"
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECTIONS_DIR = os.path.join(BASE_DIR, "data", "projections")

st.set_page_config(page_title="Weekly Models (V4)", page_icon="🏈", layout="wide")

# -----------------------------------------------------------------------------
# DATA LOADING
# -----------------------------------------------------------------------------
@st.cache_data
def load_data(week):
    p_path = os.path.join(PROJECTIONS_DIR, f"week{week}_all_props_summary.csv")
    proj_df = pd.read_csv(p_path) if os.path.exists(p_path) else None
    if proj_df is not None:
        proj_df['pred_yards'] = pd.to_numeric(proj_df['pred_yards'], errors='coerce')

    v_path = os.path.join(PROJECTIONS_DIR, f"week{week}_value_opportunities.csv")
    val_df = pd.read_csv(v_path) if os.path.exists(v_path) else None
    if val_df is not None:
        cols = ["predicted_yards", "best_point", "best_price", "edge_yards"]
        for c in cols: val_df[c] = pd.to_numeric(val_df[c], errors='coerce')
        val_df = val_df.fillna({"edge_yards": 0, "side": "-"})

    return proj_df, val_df

# -----------------------------------------------------------------------------
# SIDEBAR CONTROLS
# -----------------------------------------------------------------------------
files = glob.glob(os.path.join(PROJECTIONS_DIR, "week*_all_props_summary.csv"))
weeks = sorted([int(f.split('week')[1].split('_')[0]) for f in files])

if not weeks: st.error("No data found."); st.stop()

st.sidebar.title("Configuration")
week_str = persistent_selectbox("Week", [f"Week {w}" for w in weeks], PAGE_KEY_PREFIX, "week", container=st.sidebar, default=f"Week {weeks[-1]}")
week_num = int(week_str.replace("Week ", ""))

# View Mode Toggle
view_mode = st.sidebar.radio("View Mode", ["Matchup Analysis", "League Leaders", "Betting Value"], key="v4_view_mode")

proj_df, val_df = load_data(week_num)

if proj_df is None: st.error("Data loading failed."); st.stop()

st.title(f"Weekly Models: {view_mode}")
st.divider()

# -----------------------------------------------------------------------------
# VIEW 1: MATCHUP ANALYSIS
# -----------------------------------------------------------------------------
if view_mode == "Matchup Analysis":
    # Game Selector specific to this view
    games = set()
    for _, row in proj_df.iterrows():
        games.add(tuple(sorted([row['team'], row['opp']])))
    game_list = sorted([f"{g[0]} @ {g[1]}" for g in games])
    
    sel_game = st.selectbox("Select Matchup", game_list, key="v4_matchup_sel")
    
    if sel_game:
        t1, t2 = sel_game.split(" @ ")
        subset = proj_df[((proj_df['team'] == t1) & (proj_df['opp'] == t2)) | ((proj_df['team'] == t2) & (proj_df['opp'] == t1))]
        
        def render_grid(pos, prop, title):
            d = subset[(subset['position'] == pos) & (subset['prop_type'] == prop)].sort_values('pred_yards', ascending=False)
            if not d.empty:
                st.markdown(f"**{title}**")
                st.dataframe(d[['full_name', 'team', 'pred_yards']].rename(columns={'full_name': 'Player', 'pred_yards': 'Yds'}), use_container_width=True, hide_index=True)

        c1, c2 = st.columns(2)
        with c1: render_grid('QB', 'Passing Yards', 'QB Pass'); render_grid('RB', 'Rushing Yards', 'RB Rush'); render_grid('WR', 'Receiving Yards', 'WR Rec')
        with c2: render_grid('QB', 'Rushing Yards', 'QB Rush'); render_grid('RB', 'Receiving Yards', 'RB Rec'); render_grid('TE', 'Receiving Yards', 'TE Rec')

# -----------------------------------------------------------------------------
# VIEW 2: LEAGUE LEADERS
# -----------------------------------------------------------------------------
elif view_mode == "League Leaders":
    # Optional Position Filter in main area
    pos_tabs = st.tabs(["Quarterbacks", "Running Backs", "Wide Receivers", "Tight Ends"])
    
    def render_leaderboard(pos, prop, title):
        d = proj_df[(proj_df['position'] == pos) & (proj_df['prop_type'] == prop)].nlargest(25, 'pred_yards')
        d['Rank'] = range(1, len(d)+1)
        st.dataframe(d[['Rank', 'full_name', 'team', 'opp', 'pred_yards']].rename(columns={'full_name': 'Player', 'pred_yards': 'Yards'}), use_container_width=True, hide_index=True)

    with pos_tabs[0]:
        c1, c2 = st.columns(2)
        with c1: st.markdown("#### Passing"); render_leaderboard('QB', 'Passing Yards', '')
        with c2: st.markdown("#### Rushing"); render_leaderboard('QB', 'Rushing Yards', '')
    with pos_tabs[1]:
        c1, c2 = st.columns(2)
        with c1: st.markdown("#### Rushing"); render_leaderboard('RB', 'Rushing Yards', '')
        with c2: st.markdown("#### Receiving"); render_leaderboard('RB', 'Receiving Yards', '')
    with pos_tabs[2]: render_leaderboard('WR', 'Receiving Yards', '')
    with pos_tabs[3]: render_leaderboard('TE', 'Receiving Yards', '')

# -----------------------------------------------------------------------------
# VIEW 3: BETTING VALUE
# -----------------------------------------------------------------------------
elif view_mode == "Betting Value":
    if val_df is None:
        st.info("Value data not available.")
    else:
        # Filter Logic (Optional sidebar expansion)
        filter_game = st.sidebar.selectbox("Filter Game (Value)", ["All Games"] + sorted([f"{g[0]} vs {g[1]}" for g in games]), key="v4_val_game")
        
        subset = val_df.copy()
        if filter_game != "All Games":
            t1, t2 = filter_game.split(" vs ")
            subset = subset[((subset['team'] == t1) & (subset['opp'] == t2)) | ((subset['team'] == t2) & (subset['opp'] == t1))]
        
        # Display
        subset['Side'] = subset['side'].apply(lambda s: f"{s} ⬆️" if "OVER" in str(s).upper() else (f"{s} ⬇️" if "UNDER" in str(s).upper() else s))
        
        # Simple list view
        ptabs = st.tabs(sorted(subset['prop_type'].unique()))
        for pt, tab in zip(sorted(subset['prop_type'].unique()), ptabs):
            with tab:
                d = subset[subset['prop_type'] == pt].sort_values('edge_yards', ascending=False)
                st.dataframe(
                    d[['player', 'team', 'predicted_yards', 'best_point', 'edge_yards', 'Side']].rename(columns={'predicted_yards': 'Proj', 'best_point': 'Line', 'edge_yards': 'Edge'}),
                    use_container_width=True, hide_index=True
                )

render_footer()
