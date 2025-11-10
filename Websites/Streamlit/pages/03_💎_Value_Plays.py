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

# Get unique games for selector
if "home_team" in value_opportunities.columns and "away_team" in value_opportunities.columns:
    games_df = value_opportunities[["home_team", "away_team"]].drop_duplicates()
    game_options = ["All Games"] + [
        f"{row['away_team']} @ {row['home_team']}"
        for _, row in games_df.iterrows()
    ]
else:
    # Fallback: create games from team/opp pairs
    games_set = set()
    for _, row in value_opportunities.iterrows():
        if pd.notna(row.get("team")) and pd.notna(row.get("opp")):
            games_set.add(f"{row['team']} vs {row['opp']}")
    game_options = ["All Games"] + sorted(games_set)

all_prop_types = sorted(value_opportunities["prop_type"].dropna().unique())

# Game selector in sidebar
selected_game = st.sidebar.selectbox(
    "Select Game:",
    options=game_options,
    index=0,
)

st.divider()

# Filter by selected game if not "All Games"
if selected_game != "All Games":
    # Parse the game selection
    if " @ " in selected_game:
        # Format: "Away Team @ Home Team"
        away_team_full, home_team_full = selected_game.split(" @ ")
        game_data = value_opportunities[
            ((value_opportunities["home_team"] == home_team_full) & 
             (value_opportunities["away_team"] == away_team_full))
        ].copy()
    else:
        # Fallback format: "Team1 vs Team2"
        parts = selected_game.replace(" vs ", " ").split()
        if len(parts) >= 2:
            team1, team2 = parts[0], parts[-1]
            game_data = value_opportunities[
                ((value_opportunities["team"] == team1) & (value_opportunities["opp"] == team2)) |
                ((value_opportunities["team"] == team2) & (value_opportunities["opp"] == team1))
            ].copy()
        else:
            game_data = value_opportunities.copy()
    
    # Show game-specific view organized by prop type (all on one page)
    st.markdown(f"""
        <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        padding: 1px;
                        border-radius: 15px;
                        margin: 10px 0 25px 0;
                        text-align: center;
                        box-shadow: 0 4px 6px rgba(0,0,0,0.08);'>
            <h2 style='color: white; margin: 0; font-size: 2em; text-shadow: 2px 2px 4px rgba(0,0,0,0.3); letter-spacing: 1px;'>
                {selected_game}
            </h2>
        </div>
        """,
        unsafe_allow_html=True
    )
    st.write("")
    
    for prop_type in all_prop_types:
        prop_data = game_data[game_data["prop_type"] == prop_type].copy()
        
        if prop_data.empty:
            continue
        
        # Sort by edge yards descending and add ranking
        prop_data = prop_data.sort_values(by="edge_yards", ascending=False).reset_index(drop=True)
        prop_data["rank"] = range(1, len(prop_data) + 1)
        
        # Section header for prop type
        st.markdown(f"### {prop_type.upper()}")
        
        display_df = prop_data[
            [
                "rank",
                "player",
                "position",
                "team",
                "opp",
                "side",
                "best_point",
                "best_price",
                "bookmaker",
                "predicted_yards",
                "edge_yards",
            ]
        ].rename(
            columns={
                "rank": "#",
                "player": "Player",
                "position": "Pos",
                "team": "Team",
                "opp": "Opp",
                "side": "Side",
                "best_point": "Line",
                "best_price": "Odds",
                "bookmaker": "Book",
                "predicted_yards": "Pred",
                "edge_yards": "Edge",
            }
        )
        
        display_df["Line"] = display_df["Line"].round(1)
        display_df["Odds"] = display_df["Odds"].round().astype("Int64")
        display_df["Pred"] = display_df["Pred"].round(1)
        display_df["Edge"] = display_df["Edge"].round(1)
        
        # Reorder columns to put Book last
        display_df = display_df[["#", "Player", "Pos", "Team", "Opp", "Side", "Line", "Odds", "Pred", "Edge", "Book"]]
        
        # Add emoji indicators to Side column
        def format_side_with_emoji(side_value):
            if pd.isna(side_value) or side_value == "-":
                return "-"
            side_str = str(side_value).strip().upper()
            if side_str == "OVER":
                return "Over  ⬆️"
            elif side_str == "UNDER":
                return "Under  ⬇️"
            return str(side_value)
        
        display_df["Side"] = display_df["Side"].apply(format_side_with_emoji)
        
        # Apply color styling to Side column using pandas Styler
        def style_side_cell(val):
            if pd.isna(val) or val == "-":
                return 'color: #666;'
            val_str = str(val).upper()
            if "OVER" in val_str:
                return 'color: #2e7d32; font-weight: 500;'
            elif "UNDER" in val_str:
                return 'color: #c62828; font-weight: 500;'
            return ''
        
        styled_df = display_df.style.applymap(style_side_cell, subset=["Side"])
        
        st.dataframe(
            styled_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "#": st.column_config.NumberColumn("#"),
                "Line": st.column_config.NumberColumn("Line", format="%.1f"),
                "Odds": st.column_config.NumberColumn("Odds"),
                "Pred": st.column_config.NumberColumn("Pred", format="%.1f"),
                "Edge": st.column_config.NumberColumn("Edge", format="%.1f"),
            },
        )
        st.write("")
    
    # Update CSV data for download
    csv_data = game_data.to_csv(index=False).encode("utf-8")
else:
    # Show all games view (original behavior)
    st.markdown(f"""
        <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        padding: 1px;
                        border-radius: 15px;
                        margin: 10px 0 25px 0;
                        text-align: center;
                        box-shadow: 0 4px 6px rgba(0,0,0,0.08);'>
            <h2 style='color: white; margin: 0; font-size: 2em; text-shadow: 2px 2px 4px rgba(0,0,0,0.3); letter-spacing: 1px;'>
                Week {selected_week_number}
            </h2>
        </div>
        """,
        unsafe_allow_html=True
    )
    
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
            
            # Reorder columns to put Sportsbook last
            display_df = display_df[["#", "Player", "Pos", "Team", "Opponent", "Side", "Model Projection", "Best Line", "Best Price", "Edge (Yards)", "Sportsbook"]]
            
            # Add emoji indicators to Side column
            def format_side_with_emoji(side_value):
                if pd.isna(side_value) or side_value == "-":
                    return "-"
                side_str = str(side_value).strip().upper()
                if side_str == "OVER":
                    return "Over  ⬆️"
                elif side_str == "UNDER":
                    return "Under  ⬇️"
                return str(side_value)
            
            display_df["Side"] = display_df["Side"].apply(format_side_with_emoji)
            
            # Apply color styling to Side column using pandas Styler
            def style_side_cell(val):
                if pd.isna(val) or val == "-":
                    return 'color: #666;'
                val_str = str(val).upper()
                if "OVER" in val_str:
                    return 'color: #2e7d32; font-weight: 500;'
                elif "UNDER" in val_str:
                    return 'color: #c62828; font-weight: 500;'
                return ''
            
            styled_df = display_df.style.applymap(style_side_cell, subset=["Side"])
            
            st.dataframe(
                styled_df,
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
    
    # CSV data for all games
    csv_data = value_opportunities.to_csv(index=False).encode("utf-8")

col1, col2, col3 = st.columns([1, 0.5, 1])
with col2:
    if selected_game != "All Games":
        # Clean game name for filename
        game_filename = selected_game.replace(" @ ", "_at_").replace(" vs ", "_vs_").replace(" ", "_")
        filename = f"week{selected_week_number}_{game_filename}_value_opportunities.csv"
    else:
        filename = f"week{selected_week_number}_value_opportunities.csv"
    
    st.download_button(
        label="Download (CSV)",
        data=csv_data,
        file_name=filename,
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
