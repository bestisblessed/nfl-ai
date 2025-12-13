import streamlit as st
import pandas as pd
import os
import glob
from utils.footer import render_footer
from utils.session_state import persistent_selectbox

PAGE_KEY_PREFIX = "v5_value_finder"
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECTIONS_DIR = os.path.join(BASE_DIR, "data", "projections")

st.set_page_config(page_title="Value Finder (V5)", page_icon="💰", layout="wide")

@st.cache_data
def load_values(week):
    path = os.path.join(PROJECTIONS_DIR, f"week{week}_value_opportunities.csv")
    if not os.path.exists(path): return None
    df = pd.read_csv(path)
    cols = ["predicted_yards", "best_point", "best_price", "edge_yards"]
    for c in cols: df[c] = pd.to_numeric(df[c], errors='coerce')
    return df.fillna({"edge_yards": 0, "side": "-", "bookmaker": "-"})

# Sidebar
files = glob.glob(os.path.join(PROJECTIONS_DIR, "week*_value_opportunities.csv"))
weeks = sorted([int(f.split('week')[1].split('_')[0]) for f in files])
if not weeks: st.stop()

st.sidebar.markdown("## Configuration")
week_str = persistent_selectbox("Week", [f"Week {w}" for w in weeks], PAGE_KEY_PREFIX, "week", container=st.sidebar, default=f"Week {weeks[-1]}")
week_num = int(week_str.replace("Week ", ""))

df = load_values(week_num)
if df is None: st.stop()

# Filters
st.sidebar.divider()
st.sidebar.markdown("### Filters")
min_edge = st.sidebar.slider("Min Edge (Yards)", 0.0, 50.0, 10.0, 1.0)

all_props = sorted(df['prop_type'].unique())
sel_props = st.sidebar.multiselect("Prop Types", all_props, default=all_props)

# Filtering
filtered_df = df[
    (df['edge_yards'] >= min_edge) &
    (df['prop_type'].isin(sel_props))
]

st.title("Value Finder")
st.markdown(f"Found **{len(filtered_df)}** opportunities with edge > {min_edge} yds.")
st.divider()

if not filtered_df.empty:
    filtered_df = filtered_df.sort_values('edge_yards', ascending=False)
    filtered_df['Side'] = filtered_df['side'].apply(lambda s: f"{s} ⬆️" if "OVER" in str(s).upper() else (f"{s} ⬇️" if "UNDER" in str(s).upper() else s))
    
    # Clean formatting
    display_df = filtered_df[['player', 'prop_type', 'team', 'opp', 'predicted_yards', 'best_point', 'edge_yards', 'Side', 'best_price']].rename(columns={
        'player': 'Player', 'prop_type': 'Prop', 'team': 'Tm', 'opp': 'Opp',
        'predicted_yards': 'Proj', 'best_point': 'Line', 'edge_yards': 'Edge', 'best_price': 'Odds'
    })
    
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Proj": st.column_config.NumberColumn(format="%.1f"),
            "Line": st.column_config.NumberColumn(format="%.1f"),
            "Edge": st.column_config.NumberColumn(format="%.1f"),
            "Odds": st.column_config.NumberColumn(format="%d")
        }
    )
else:
    st.info("No plays match criteria.")

render_footer()
