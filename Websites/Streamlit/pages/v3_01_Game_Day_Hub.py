import streamlit as st
import pandas as pd
import os
import glob
import json
import re
from utils.footer import render_footer
from utils.session_state import persistent_selectbox

PAGE_KEY_PREFIX = "v3_game_day"
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECTIONS_DIR = os.path.join(BASE_DIR, "data", "projections")

st.set_page_config(page_title="Game Day Hub (V3)", page_icon="🏈", layout="wide")

# Reuse shared logic (condensed for brevity in these variations)
@st.cache_data
def load_all_data(week):
    # Projections
    p_path = os.path.join(PROJECTIONS_DIR, f"week{week}_all_props_summary.csv")
    proj_df = pd.read_csv(p_path) if os.path.exists(p_path) else None
    
    # Values
    v_path = os.path.join(PROJECTIONS_DIR, f"week{week}_value_opportunities.csv")
    val_df = pd.read_csv(v_path) if os.path.exists(v_path) else None
    
    # Questionable
    q = set()
    q_path = os.path.join(PROJECTIONS_DIR, f"week{week}_complete_props_report.txt")
    if os.path.exists(q_path):
        with open(q_path) as f: q.update(re.findall(r"([A-Za-z0-9'.-]+(?:\s+[A-Za-z0-9'.-]+)*)\s+\(Questionable\)", f.read()))
        
    return proj_df, val_df, q

# Sidebar
files = glob.glob(os.path.join(PROJECTIONS_DIR, "week*_all_props_summary.csv"))
weeks = sorted([int(f.split('week')[1].split('_')[0]) for f in files])
if not weeks: st.stop()

st.sidebar.markdown("## Selection")
week_str = persistent_selectbox("Week", [f"Week {w}" for w in weeks], PAGE_KEY_PREFIX, "week", container=st.sidebar, default=f"Week {weeks[-1]}")
week_num = int(week_str.replace("Week ", ""))

proj_df, val_df, q_players = load_all_data(week_num)

if proj_df is None: st.error("No data"); st.stop()

# Game Selector Logic
games = set()
for _, row in proj_df.iterrows():
    games.add(tuple(sorted([row['team'], row['opp']])))
sorted_games = sorted(list(games), key=lambda x: x[0])
game_opts = [f"{g[0]} @ {g[1]}" for g in sorted_games]

sel_game = persistent_selectbox("Game", game_opts, PAGE_KEY_PREFIX, "game", container=st.sidebar)

# Main Content
t1, t2 = sel_game.split(" @ ")
st.title(f"{t1} @ {t2}")

# 1. Projections Section
st.subheader("📊 Statistical Projections")
p_sub = proj_df[((proj_df['team'] == t1) & (proj_df['opp'] == t2)) | ((proj_df['team'] == t2) & (proj_df['opp'] == t1))].copy()
p_sub['full_name'] = p_sub['full_name'].apply(lambda n: f"{n} (Q)" if n in q_players else n)

def render_proj(pos, prop, title):
    d = p_sub[(p_sub['position'] == pos) & (p_sub['prop_type'] == prop)].sort_values('pred_yards', ascending=False)
    if not d.empty:
        st.caption(title)
        st.dataframe(d[['full_name', 'team', 'pred_yards']].rename(columns={'full_name': 'Player', 'pred_yards': 'Yds'}), use_container_width=True, hide_index=True)

c1, c2, c3 = st.columns(3)
with c1: render_proj('QB', 'Passing Yards', 'QB Pass'); render_proj('RB', 'Rushing Yards', 'RB Rush')
with c2: render_proj('QB', 'Rushing Yards', 'QB Rush'); render_proj('RB', 'Receiving Yards', 'RB Rec')
with c3: render_proj('WR', 'Receiving Yards', 'WR Rec'); render_proj('TE', 'Receiving Yards', 'TE Rec')

st.divider()

# 2. Betting Edges Section
st.subheader("💎 Betting Edges")
if val_df is not None:
    v_sub = val_df[((val_df['team'] == t1) & (val_df['opp'] == t2)) | ((val_df['team'] == t2) & (val_df['opp'] == t1))].copy()
    if not v_sub.empty:
        v_sub['edge_yards'] = pd.to_numeric(v_sub['edge_yards'], errors='coerce').fillna(0)
        v_sub['predicted_yards'] = pd.to_numeric(v_sub['predicted_yards'], errors='coerce')
        
        # Simple Styling
        def get_emoji(row):
            y = row['edge_yards']
            prop = row['prop_type']
            if prop == 'Passing Yards': return "💎" if y >= 75 else ("⚡️" if y >= 45 else "")
            return "💎" if y >= 25 else ("⚡️" if y >= 15 else "")
            
        v_sub['Ind'] = v_sub.apply(get_emoji, axis=1)
        v_sub['Side'] = v_sub['side'].apply(lambda s: f"{s} ⬆️" if "OVER" in str(s).upper() else (f"{s} ⬇️" if "UNDER" in str(s).upper() else s))
        
        st.dataframe(
            v_sub.sort_values('edge_yards', ascending=False)[['Ind', 'player', 'prop_type', 'predicted_yards', 'best_point', 'edge_yards', 'Side']]
            .rename(columns={'predicted_yards': 'Proj', 'best_point': 'Line', 'edge_yards': 'Edge'}),
            use_container_width=True, hide_index=True
        )
    else:
        st.info("No value edges found for this game.")
else:
    st.info("Value data not available.")

render_footer()
