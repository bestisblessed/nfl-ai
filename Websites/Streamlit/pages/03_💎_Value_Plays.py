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
            Model-generated edges highlighting the best projected betting values each week
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

all_positions = sorted(value_opportunities["position"].dropna().unique())
ev_min = (
    float(np.floor(value_opportunities["ev_per_1"].min()))
    if not value_opportunities["ev_per_1"].empty
    else 0.0
)
ev_max = (
    float(np.ceil(value_opportunities["ev_per_1"].max()))
    if not value_opportunities["ev_per_1"].empty
    else 1.0
)
if ev_max <= ev_min:
    ev_max = ev_min + 1.0

default_ev = 0.0 if ev_min <= 0 <= ev_max else ev_min

min_ev = st.sidebar.slider(
    "Minimum Expected Value per $1",
    min_value=ev_min,
    max_value=ev_max,
    value=default_ev,
    step=0.05,
)

filters = (
    value_opportunities["ev_per_1"] >= min_ev
)

filtered_opportunities = value_opportunities.loc[filters].copy()

if filtered_opportunities.empty:
    st.warning("No value plays match the current filter set. Try relaxing one of the filters.")

st.divider()

st.subheader("Top Value Opportunities")

position_tab_labels = ["All"] + [pos for pos in all_positions if pos]
position_tabs = st.tabs(position_tab_labels)

for tab_label, tab in zip(position_tab_labels, position_tabs):
    with tab:
        subset = (
            filtered_opportunities
            if tab_label == "All"
            else filtered_opportunities[filtered_opportunities["position"] == tab_label]
        )

        if subset.empty:
            st.info("No value plays match the current filters for this position.")
            continue

        display_df = subset[
            [
                "player",
                "position",
                "team",
                "opp",
                "prop_type",
                "side",
                "predicted_yards",
                "best_point",
                "best_price",
                "bookmaker",
                "edge_yards",
                "ev_per_1",
                "implied_prob",
            ]
        ].rename(
            columns={
                "player": "Player",
                "position": "Pos",
                "team": "Team",
                "opp": "Opponent",
                "prop_type": "Prop Type",
                "side": "Side",
                "predicted_yards": "Model Projection",
                "best_point": "Best Line",
                "best_price": "Best Price",
                "bookmaker": "Sportsbook",
                "edge_yards": "Edge (Yards)",
                "ev_per_1": "EV per $1",
                "implied_prob": "Implied Probability",
            }
        )

        display_df["Model Projection"] = display_df["Model Projection"].round(1)
        display_df["Best Line"] = display_df["Best Line"].round(1)
        display_df["Best Price"] = display_df["Best Price"].round().astype("Int64")
        display_df["Edge (Yards)"] = display_df["Edge (Yards)"].round(2)
        display_df["EV per $1"] = display_df["EV per $1"].round(3)
        display_df["Implied Probability"] = (display_df["Implied Probability"] * 100).round(1)

        st.dataframe(
            display_df.sort_values(by="EV per $1", ascending=False),
            use_container_width=True,
            hide_index=True,
            column_config={
                "Model Projection": st.column_config.NumberColumn(
                    "Model Projection", format="%.1f"
                ),
                "Best Line": st.column_config.NumberColumn("Best Line", format="%.1f"),
                "Best Price": st.column_config.NumberColumn("Best Price"),
                "Edge (Yards)": st.column_config.NumberColumn(
                    "Edge (Yards)", format="%.2f"
                ),
                "EV per $1": st.column_config.NumberColumn("EV per $1", format="%.3f"),
                "Implied Probability": st.column_config.NumberColumn(
                    "Implied Probability", format="%.1f%%"
                ),
            },
        )

csv_data = filtered_opportunities.to_csv(index=False).encode("utf-8")
st.download_button(
    label="⬇️ Download Filtered Opportunities (CSV)",
    data=csv_data,
    file_name=f"week{selected_week_number}_value_opportunities_filtered.csv",
    mime="text/csv",
)

st.divider()

st.subheader("Prop Type Value Leaders")

prop_leaders = (
    filtered_opportunities.groupby("prop_type")
    .agg(
        Opportunities=("player", "count"),
        Avg_Edge=("edge_yards", "mean"),
        Best_EV=("ev_per_1", "max"),
        Total_Positive_EV=("ev_per_1", lambda x: x[x > 0].sum()),
    )
    .reset_index()
)

if not prop_leaders.empty:
    prop_leaders = prop_leaders.rename(columns={"prop_type": "Prop Type"})
    prop_leaders["Avg_Edge"] = prop_leaders["Avg_Edge"].round(2)
    prop_leaders["Best_EV"] = prop_leaders["Best_EV"].round(3)
    prop_leaders["Total_Positive_EV"] = prop_leaders["Total_Positive_EV"].round(3)
    prop_leaders = prop_leaders.sort_values(by="Total_Positive_EV", ascending=False)

    st.dataframe(
        prop_leaders,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Opportunities": st.column_config.NumberColumn("Opportunities"),
            "Avg_Edge": st.column_config.NumberColumn("Avg Edge (yds)", format="%.2f"),
            "Best_EV": st.column_config.NumberColumn("Best EV per $1", format="%.3f"),
            "Total_Positive_EV": st.column_config.NumberColumn(
                "Total Positive EV", format="%.3f"
            ),
        },
    )
else:
    st.info("Prop type leaders will appear once there are opportunities for the selected filters.")

st.divider()

st.subheader("Team Value Spotlight")

team_summary = (
    filtered_opportunities.groupby("team")
    .agg(
        Opportunities=("player", "count"),
        Avg_Edge=("edge_yards", "mean"),
        Total_Positive_EV=("ev_per_1", lambda x: x[x > 0].sum()),
    )
    .reset_index()
)

if not team_summary.empty:
    team_summary = team_summary.rename(columns={"team": "Team"})
    team_summary["Avg_Edge"] = team_summary["Avg_Edge"].round(2)
    team_summary["Total_Positive_EV"] = team_summary["Total_Positive_EV"].round(3)
    team_summary = team_summary.sort_values(by="Total_Positive_EV", ascending=False)

    st.dataframe(
        team_summary,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Opportunities": st.column_config.NumberColumn("Opportunities"),
            "Avg_Edge": st.column_config.NumberColumn("Avg Edge (yds)", format="%.2f"),
            "Total_Positive_EV": st.column_config.NumberColumn(
                "Total Positive EV", format="%.3f"
            ),
        },
    )
else:
    st.info("Team value leaders will appear once there are opportunities for the selected filters.")

st.divider()

with st.expander("Prop Type Leaderboards"):
    if value_edges is not None and not value_edges.empty:
        prop_names = sorted(value_edges["prop_type"].dropna().unique())
        prop_tabs = st.tabs(prop_names)
        for tab, prop_type in zip(prop_tabs, prop_names):
            with tab:
                subset = (
                    value_edges[value_edges["prop_type"] == prop_type]
                    .copy()
                    .sort_values(by="ev_per_1", ascending=False)
                )
                if subset.empty:
                    st.write("No edges available for this prop type yet.")
                    continue

                leaderboard = subset[
                    [
                        "player",
                        "team",
                        "side",
                        "predicted_yards",
                        "best_point",
                        "best_price",
                        "bookmaker",
                        "edge_yards",
                        "ev_per_1",
                    ]
                ].rename(
                    columns={
                        "player": "Player",
                        "team": "Team",
                        "side": "Side",
                        "predicted_yards": "Model Projection",
                        "best_point": "Best Line",
                        "best_price": "Best Price",
                        "bookmaker": "Sportsbook",
                        "edge_yards": "Edge (Yards)",
                        "ev_per_1": "EV per $1",
                    }
                )
                leaderboard["Model Projection"] = leaderboard["Model Projection"].round(1)
                leaderboard["Best Line"] = leaderboard["Best Line"].round(1)
                leaderboard["Best Price"] = leaderboard["Best Price"].round().astype("Int64")
                leaderboard["Edge (Yards)"] = leaderboard["Edge (Yards)"].round(2)
                leaderboard["EV per $1"] = leaderboard["EV per $1"].round(3)

                st.dataframe(
                    leaderboard,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Model Projection": st.column_config.NumberColumn(
                            "Model Projection", format="%.1f"
                        ),
                        "Best Line": st.column_config.NumberColumn("Best Line", format="%.1f"),
                        "Best Price": st.column_config.NumberColumn("Best Price"),
                        "Edge (Yards)": st.column_config.NumberColumn(
                            "Edge (Yards)", format="%.2f"
                        ),
                        "EV per $1": st.column_config.NumberColumn(
                            "EV per $1", format="%.3f"
                        ),
                    },
                )
    else:
        st.info("Weekly edge leaderboards will appear once the top_edges_by_prop file is available.")

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
