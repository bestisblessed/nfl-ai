import glob
import os
from typing import List, Optional, Tuple

import numpy as np
import pandas as pd
import streamlit as st

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECTIONS_DIR = os.path.join(BASE_DIR, "data", "projections")

st.set_page_config(
    page_title="💎 Value Play Finder",
    page_icon="💎",
    layout="wide",
)

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


@st.cache_data
def discover_value_weeks(directory: str) -> List[int]:
    pattern = os.path.join(directory, "week*_value_opportunities.csv")
    weeks: List[int] = []
    for file_path in glob.glob(pattern):
        try:
            week_str = os.path.basename(file_path).split("week")[1].split("_")[0]
            weeks.append(int(week_str))
        except (IndexError, ValueError):
            continue
    return sorted(set(weeks))


@st.cache_data
def load_value_data(week: int) -> Tuple[pd.DataFrame, Optional[pd.DataFrame]]:
    opportunities_path = os.path.join(
        PROJECTIONS_DIR, f"week{week}_value_opportunities.csv"
    )
    edges_path = os.path.join(
        PROJECTIONS_DIR, f"week{week}_top_edges_by_prop.csv"
    )

    if not os.path.exists(opportunities_path):
        raise FileNotFoundError(
            f"Could not locate value opportunities for week {week}: {opportunities_path}"
        )

    value_df = pd.read_csv(opportunities_path)

    numeric_columns = [
        "predicted_yards",
        "best_point",
        "best_price",
        "edge_yards",
        "implied_prob",
        "ev_per_1",
        "over_implied_prob",
        "under_implied_prob",
        "over_ev_per_1",
        "under_ev_per_1",
    ]

    for column in numeric_columns:
        if column in value_df.columns:
            value_df[column] = pd.to_numeric(value_df[column], errors="coerce")

    edges_df: Optional[pd.DataFrame] = None
    if os.path.exists(edges_path):
        edges_df = pd.read_csv(edges_path)
        for column in numeric_columns:
            if column in edges_df.columns:
                edges_df[column] = pd.to_numeric(edges_df[column], errors="coerce")

    return value_df, edges_df


available_weeks = discover_value_weeks(PROJECTIONS_DIR)
if not available_weeks:
    st.error(
        "No value projection files found. Please add weekly value files to data/projections/."
    )
    st.stop()

st.sidebar.header("Week & Filters")
selected_week = st.sidebar.selectbox(
    "Select Week:",
    options=[f"Week {week}" for week in available_weeks],
    index=len(available_weeks) - 1,
)

selected_week_number = int(selected_week.replace("Week ", ""))

try:
    value_opportunities, value_edges = load_value_data(selected_week_number)
except FileNotFoundError as exc:
    st.error(str(exc))
    st.stop()

value_opportunities["bookmaker"] = value_opportunities["bookmaker"].fillna("-")
value_opportunities["side"] = value_opportunities["side"].fillna("-")
value_opportunities["ev_per_1"] = value_opportunities["ev_per_1"].fillna(0.0)
value_opportunities["edge_yards"] = value_opportunities["edge_yards"].fillna(0.0)

all_prop_types = sorted(value_opportunities["prop_type"].dropna().unique())

st.divider()

st.subheader("Top Value Opportunities")

prop_type_tabs = st.tabs(all_prop_types)

for tab_label, tab in zip(all_prop_types, prop_type_tabs):
    with tab:
        subset = value_opportunities[value_opportunities["prop_type"] == tab_label].copy()

        if subset.empty:
            st.info("No value plays available for this prop type.")
            continue

        # Sort by edge yards descending and add ranking
        subset = subset.sort_values(by="edge_yards", ascending=False).reset_index(drop=True)
        subset["rank"] = range(1, len(subset) + 1)

        display_df = subset[
            [
                "rank",
                "player",
                "position",
                "team",
                "opp",
                "side",
                "predicted_yards",
                "best_point",
                "best_price",
                "bookmaker",
                "edge_yards",
            ]
        ].rename(
            columns={
                "rank": "#",
                "player": "Player",
                "position": "Pos",
                "team": "Team",
                "opp": "Opponent",
                "side": "Side",
                "predicted_yards": "Model Projection",
                "best_point": "Best Line",
                "best_price": "Best Price",
                "bookmaker": "Sportsbook",
                "edge_yards": "Edge (Yards)",
            }
        )

        display_df["Model Projection"] = display_df["Model Projection"].round(1)
        display_df["Best Line"] = display_df["Best Line"].round(1)
        display_df["Best Price"] = display_df["Best Price"].round().astype("Int64")
        display_df["Edge (Yards)"] = display_df["Edge (Yards)"].round(2)

        st.dataframe(
            display_df,
            use_container_width=True,
            height=800,
            hide_index=True,
            column_config={
                "#": st.column_config.NumberColumn("#"),
                "Model Projection": st.column_config.NumberColumn(
                    "Model Projection", format="%.1f"
                ),
                "Best Line": st.column_config.NumberColumn("Best Line", format="%.1f"),
                "Best Price": st.column_config.NumberColumn("Best Price"),
                "Edge (Yards)": st.column_config.NumberColumn(
                    "Edge (Yards)", format="%.2f"
                ),
            },
        )

csv_data = value_opportunities.to_csv(index=False).encode("utf-8")
col1, col2, col3 = st.columns([1, 0.5, 1])
with col2:
    st.download_button(
        label="Download (CSV)",
        data=csv_data,
        file_name=f"week{selected_week_number}_value_opportunities.csv",
        mime="text/csv",
        use_container_width=True,
    )

st.divider()

with st.sidebar:
    st.markdown("### Download Reports")
    value_html_path = os.path.join(
        PROJECTIONS_DIR, f"week{selected_week_number}_value_complete_props_report.html"
    )
    value_pdf_path = os.path.join(
        PROJECTIONS_DIR, f"week{selected_week_number}_value_leader_tables.pdf"
    )

    if os.path.exists(value_html_path):
        with open(value_html_path, "rb") as html_file:
            st.download_button(
                "📄 Value Props HTML Report",
                data=html_file.read(),
                file_name=os.path.basename(value_html_path),
                mime="text/html",
            )

    if os.path.exists(value_pdf_path):
        with open(value_pdf_path, "rb") as pdf_file:
            st.download_button(
                "📑 Value Leader Tables (PDF)",
                data=pdf_file.read(),
                file_name=os.path.basename(value_pdf_path),
                mime="application/pdf",
            )
