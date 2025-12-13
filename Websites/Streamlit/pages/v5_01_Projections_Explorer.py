import streamlit as st
import pandas as pd
import os
import glob
from utils.footer import render_footer
from utils.session_state import persistent_selectbox

PAGE_KEY_PREFIX = "v5_proj_explorer"
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECTIONS_DIR = os.path.join(BASE_DIR, "data", "projections")

st.set_page_config(page_title="Projections Explorer (V5)", page_icon="🔭", layout="wide")

@st.cache_data
def load_projections(week):
    path = os.path.join(PROJECTIONS_DIR, f"week{week}_all_props_summary.csv")
    if not os.path.exists(path): return None
    df = pd.read_csv(path)
    df['pred_yards'] = pd.to_numeric(df['pred_yards'], errors='coerce')
    return df.dropna(subset=['pred_yards'])

# Sidebar
files = glob.glob(os.path.join(PROJECTIONS_DIR, "week*_all_props_summary.csv"))
weeks = sorted([int(f.split('week')[1].split('_')[0]) for f in files])
if not weeks: st.stop()

st.sidebar.markdown("## Configuration")
week_str = persistent_selectbox("Week", [f"Week {w}" for w in weeks], PAGE_KEY_PREFIX, "week", container=st.sidebar, default=f"Week {weeks[-1]}")
week_num = int(week_str.replace("Week ", ""))

df = load_projections(week_num)
if df is None: st.stop()

# Filters
st.sidebar.divider()
st.sidebar.markdown("### Filters")
all_pos = sorted(df['position'].unique())
sel_pos = st.sidebar.multiselect("Positions", all_pos, default=all_pos, key="v5_pos")

all_teams = sorted(df['team'].unique())
sel_teams = st.sidebar.multiselect("Teams", all_teams, key="v5_teams")

# Filtering Logic
filtered_df = df[df['position'].isin(sel_pos)]
if sel_teams:
    filtered_df = filtered_df[filtered_df['team'].isin(sel_teams)]

st.title("Projections Explorer")
st.markdown("Explore player projections with dynamic filtering.")
st.divider()

# Master Table View
# Organize by Prop Type tabs to compare apples to apples
props = sorted(filtered_df['prop_type'].unique())
tabs = st.tabs(props)

for prop, tab in zip(props, tabs):
    with tab:
        d = filtered_df[filtered_df['prop_type'] == prop].sort_values('pred_yards', ascending=False)
        d = d.reset_index(drop=True)
        d['Rank'] = d.index + 1
        
        st.dataframe(
            d[['Rank', 'full_name', 'position', 'team', 'opp', 'pred_yards']].rename(columns={
                'full_name': 'Player', 'position': 'Pos', 'team': 'Team', 'opp': 'Opp', 'pred_yards': 'Proj Yards'
            }),
            use_container_width=True,
            hide_index=True,
            column_config={
                "Proj Yards": st.column_config.NumberColumn(format="%.1f"),
                "Rank": st.column_config.NumberColumn(width=50)
            }
        )

st.caption(f"Showing {len(filtered_df)} projections.")
render_footer()
