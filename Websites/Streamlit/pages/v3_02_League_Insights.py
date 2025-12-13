import streamlit as st
import pandas as pd
import os
import glob
import re
from utils.footer import render_footer
from utils.session_state import persistent_selectbox

PAGE_KEY_PREFIX = "v3_league_insights"
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECTIONS_DIR = os.path.join(BASE_DIR, "data", "projections")

st.set_page_config(page_title="League Insights (V3)", page_icon="📋", layout="wide")

@st.cache_data
def load_data(week):
    p_path = os.path.join(PROJECTIONS_DIR, f"week{week}_all_props_summary.csv")
    proj_df = pd.read_csv(p_path) if os.path.exists(p_path) else None
    if proj_df is not None:
        proj_df['pred_yards'] = pd.to_numeric(proj_df['pred_yards'], errors='coerce')
    
    v_path = os.path.join(PROJECTIONS_DIR, f"week{week}_value_opportunities.csv")
    val_df = pd.read_csv(v_path) if os.path.exists(v_path) else None
    
    return proj_df, val_df

# Sidebar
files = glob.glob(os.path.join(PROJECTIONS_DIR, "week*_all_props_summary.csv"))
weeks = sorted([int(f.split('week')[1].split('_')[0]) for f in files])
if not weeks: st.stop()

st.sidebar.markdown("## Selection")
week_str = persistent_selectbox("Week", [f"Week {w}" for w in weeks], PAGE_KEY_PREFIX, "week", container=st.sidebar, default=f"Week {weeks[-1]}")
week_num = int(week_str.replace("Week ", ""))

proj_df, val_df = load_data(week_num)

if proj_df is None: st.error("No data"); st.stop()

st.title("League Insights")
st.divider()

tab1, tab2 = st.tabs(["📋 Statistical Leaders", "💎 Top Value Plays"])

with tab1:
    l_tabs = st.tabs(["Quarterbacks", "Running Backs", "Wide Receivers", "Tight Ends"])
    
    def render_leaderboard(pos, prop, title):
        d = proj_df[(proj_df['position'] == pos) & (proj_df['prop_type'] == prop)].nlargest(25, 'pred_yards')
        d['Rank'] = range(1, len(d)+1)
        st.dataframe(d[['Rank', 'full_name', 'team', 'opp', 'pred_yards']].rename(columns={'full_name': 'Player', 'pred_yards': 'Yards'}), use_container_width=True, hide_index=True)

    with l_tabs[0]:
        c1, c2 = st.columns(2)
        with c1: st.markdown("##### Passing"); render_leaderboard('QB', 'Passing Yards', '')
        with c2: st.markdown("##### Rushing"); render_leaderboard('QB', 'Rushing Yards', '')
    with l_tabs[1]:
        c1, c2 = st.columns(2)
        with c1: st.markdown("##### Rushing"); render_leaderboard('RB', 'Rushing Yards', '')
        with c2: st.markdown("##### Receiving"); render_leaderboard('RB', 'Receiving Yards', '')
    with l_tabs[2]: render_leaderboard('WR', 'Receiving Yards', '')
    with l_tabs[3]: render_leaderboard('TE', 'Receiving Yards', '')

with tab2:
    if val_df is not None:
        val_df['edge_yards'] = pd.to_numeric(val_df['edge_yards'], errors='coerce').fillna(0)
        
        # Tabs by Prop Type
        ptabs = st.tabs(sorted(val_df['prop_type'].unique()))
        for pt, tab in zip(sorted(val_df['prop_type'].unique()), ptabs):
            with tab:
                d = val_df[val_df['prop_type'] == pt].sort_values('edge_yards', ascending=False)
                d['Side'] = d['side'].apply(lambda s: f"{s} ⬆️" if "OVER" in str(s).upper() else (f"{s} ⬇️" if "UNDER" in str(s).upper() else s))
                st.dataframe(
                    d[['player', 'team', 'opp', 'predicted_yards', 'best_point', 'edge_yards', 'Side']].rename(columns={'predicted_yards': 'Proj', 'best_point': 'Line', 'edge_yards': 'Edge'}),
                    use_container_width=True, hide_index=True
                )
    else:
        st.info("No value data found.")

render_footer()
