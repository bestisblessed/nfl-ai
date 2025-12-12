import glob
import hashlib
import json
import os
import re
from typing import List, Optional, Tuple
import numpy as np
import pandas as pd
import streamlit as st
# from st_aggrid import AgGrid, GridOptionsBuilder
from utils.footer import render_footer
from utils.session_state import persistent_selectbox

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECTIONS_DIR = os.path.join(BASE_DIR, "data", "projections")
PAGE_KEY_PREFIX = "value_plays"
YARD_THRESHOLDS = {
    "Passing Yards": (45.0, 75.0),
    "Receiving Yards": (15.0, 25.0),
    "Rushing Yards": (15.0, 25.0),
}

st.set_page_config(
    page_title="💎 Value Play Finder",
    page_icon="🏈",
    layout="wide",
)

# # Compact dataframe styling for better fit on smaller screens
# st.markdown("""
#     <style>
#     .stDataFrame table {
#         font-size: 0.8rem;
#     }
#     .stDataFrame tbody tr td {
#         padding: 0.25rem 0.5rem;
#     }
#     </style>
# """, unsafe_allow_html=True)

# st.markdown(
#     """
#     <style>
#         .block-container {
#             max-width: 1400px;
#             padding-top: 1.5rem;
#             padding-bottom: 1.5rem;
#         }
#     </style>
#     """,
#     unsafe_allow_html=True,
# )
# Maximize width for individual game table columns only
st.markdown(
    """
    <style>
        /* Only target columns used for individual game tables - reduce gaps */
        [data-testid="column"] {
            padding-left: 0.05rem !important;
            padding-right: 0.05rem  !important;
        }
        /* Make tables use full available width */
        .stDataFrame {
            width: 100% !important;
        }
        /* Ensure dataframe containers use full width */
        [data-testid="stDataFrame"] {
            width: 100% !important;
        }
        /* Reduce gap between side-by-side columns */
        [data-testid="column"] > div {
            padding-left: 0.05rem !important;
            padding-right: 0.05rem !important;
        }
    </style>
    """,
    unsafe_allow_html=True,
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

# # Center all dataframe column headers
# st.markdown(
#     """
#     <style>
#     .stDataFrame th {
#         text-align: center !important;
#     }
#     </style>
#     """,
#     unsafe_allow_html=True,
# )


@st.cache_data
def load_game_times():
    """Load game times from odds JSON files to sort games by start time"""
    games_with_times = {}
    try:
        data_dir = os.path.join(BASE_DIR, "data", "odds")
        json_files = sorted(
            [f for f in os.listdir(data_dir) if f.endswith(".json") and f.startswith('nfl')],
            reverse=True
        )
        if json_files:
            filepath = os.path.join(data_dir, json_files[0])
            with open(filepath) as f:
                data = json.load(f)
                for game in data:
                    game_time = game.get('Time', '')
                    day_and_matchup_key = list(game.keys())[1] if len(game.keys()) > 1 else None
                    if day_and_matchup_key:
                        teams = game[day_and_matchup_key].replace('\n', ' ').strip()
                        if '  ' in teams:
                            teams_list = [team.strip() for team in teams.split('  ') if team.strip()]
                        else:
                            teams_list = [team.strip() for team in re.split(r'\s+|,', teams) if team.strip()]
                        if len(teams_list) == 2:
                            # Create matchup key with abbreviations (need to map full names to abbreviations)
                            matchup_key = f"{teams_list[0]} vs {teams_list[1]}"
                            games_with_times[matchup_key] = {
                                'time': game_time,
                                'date': day_and_matchup_key.strip()
                            }
    except Exception:
        pass
    return games_with_times


@st.cache_data
def load_upcoming_games_with_times():
    """Load upcoming games and try to get times for sorting"""
    games_file = os.path.join(BASE_DIR, "upcoming_games.csv")
    if os.path.exists(games_file):
        games_df = pd.read_csv(games_file)
        game_times = load_game_times()
        
        # Create list of games with time info for sorting
        games_list = []
        for _, row in games_df.iterrows():
            away, home = row['away_team'], row['home_team']
            matchup_str = f"{away} @ {home}"
            
            # Try to find time from odds data
            time_info = None
            for key, value in game_times.items():
                # Check if teams match (handling full names vs abbreviations)
                teams_in_key = [t.strip() for t in re.split(r'\s+vs\s+', key, flags=re.IGNORECASE)]
                if len(teams_in_key) == 2:
                    # Simple matching - could be improved
                    time_info = value
                    break
            
            games_list.append({
                'matchup': matchup_str,
                'away': away,
                'home': home,
                'time': time_info['time'] if time_info else '',
                'date': time_info['date'] if time_info else '',
                'sort_key': (time_info['date'] if time_info else '', time_info['time'] if time_info else '')
            })
        
        # Sort by date and time
        games_list.sort(key=lambda x: x['sort_key'])
        return [g['matchup'] for g in games_list], games_df
    return [], pd.DataFrame()


@st.cache_data
def load_questionable_players(week: int) -> set[str]:
    """Load players marked as Questionable in the weekly complete props report."""

    questionable_players: set[str] = set()
    txt_path = os.path.join(PROJECTIONS_DIR, f"week{week}_complete_props_report.txt")
    html_path = os.path.join(PROJECTIONS_DIR, f"week{week}_complete_props_report.html")

    def extract_players(text: str) -> None:
        matches = re.findall(
            r"([A-Za-z0-9'.-]+(?:\s+[A-Za-z0-9'.-]+)*)\s+\(Questionable\)", text
        )
        questionable_players.update(name.strip() for name in matches)

    if os.path.exists(txt_path):
        with open(txt_path, "r", encoding="utf-8") as file:
            extract_players(file.read())
    elif os.path.exists(html_path):
        with open(html_path, "r", encoding="utf-8") as file:
            extract_players(file.read())

    return questionable_players


def append_questionable_tag(name: str, questionable_players: set[str]) -> str:
    """Append a compact questionable tag to player names when applicable."""

    if pd.isna(name):
        return name

    name_str = str(name).strip()

    if "(Q)" in name_str or "(Questionable)" in name_str:
        return name_str

    return f"{name_str} (Q)" if name_str in questionable_players else name_str


@st.cache_data
def load_games_for_week(week: int) -> pd.DataFrame:
    """Load games from Games.csv for a specific week in season 2025"""
    games_file = os.path.join(BASE_DIR, "data", "Games.csv")
    if os.path.exists(games_file):
        try:
            games_df = pd.read_csv(games_file)
            # Convert week to numeric in case it's stored as string
            games_df['week'] = pd.to_numeric(games_df['week'], errors='coerce')
            games_df['season'] = pd.to_numeric(games_df['season'], errors='coerce')
            # Filter by season 2025 and week
            week_games = games_df[
                (games_df['season'] == 2025) &
                (games_df['week'] == week)
            ]
            if not week_games.empty:
                result = week_games[['home_team', 'away_team', 'date', 'gametime']].drop_duplicates()
                if not result.empty:
                    return result
            return pd.DataFrame()
        except Exception:
            return pd.DataFrame()
    return pd.DataFrame()


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

# st.sidebar.header("Filters")
st.sidebar.markdown(
    "<h2 style='text-align: center;'>Selection</h2>",
    unsafe_allow_html=True
)
week_options = [f"Week {week}" for week in available_weeks]
selected_week = persistent_selectbox(
    "Week:",
    options=week_options,
    page=PAGE_KEY_PREFIX,
    widget="week",
    default=week_options[-1] if week_options else None,
    container=st.sidebar,
)

selected_week_number = int(selected_week.replace("Week ", ""))

try:
    value_opportunities, value_edges = load_value_data(selected_week_number)
except FileNotFoundError as exc:
    st.error(str(exc))
    st.stop()

questionable_players = load_questionable_players(selected_week_number)

value_opportunities["bookmaker"] = value_opportunities["bookmaker"].fillna("-")
value_opportunities["side"] = value_opportunities["side"].fillna("-")
value_opportunities["edge_yards"] = value_opportunities["edge_yards"].fillna(0.0)

# Get unique games for selector from the selected week's value opportunities data
# Try to get home/away info from Games.csv first, then fallback to other methods
week_games_df = load_games_for_week(selected_week_number)

if not week_games_df.empty and "home_team" in week_games_df.columns and "away_team" in week_games_df.columns:
    # Use Games.csv to get correct home/away designation and sort by start time
    week_games_df = week_games_df.copy()
    if 'date' in week_games_df.columns and 'gametime' in week_games_df.columns:
        week_games_df['start_time'] = pd.to_datetime(
            week_games_df['date'].astype(str) + " " + week_games_df['gametime'].astype(str),
            errors='coerce'
        )
        week_games_df['start_time'] = week_games_df['start_time'].fillna(pd.Timestamp.max)
        week_games_df = week_games_df.sort_values(['start_time', 'home_team', 'away_team'])
    games_list = [
        f"{row['away_team']} @ {row['home_team']}"
        for _, row in week_games_df.iterrows()
    ]
    game_options = ["All Games"] + games_list
elif "team" in value_opportunities.columns and "opp" in value_opportunities.columns:
    # Fallback: create games from team/opp pairs (using abbreviations)
    # Use sorted tuple to ensure uniqueness regardless of order
    games_set = set()
    for _, row in value_opportunities.iterrows():
        if pd.notna(row.get("team")) and pd.notna(row.get("opp")):
            team1, team2 = row['team'], row['opp']
            # Sort teams alphabetically to create unique pair
            pair = tuple(sorted([team1, team2]))
            games_set.add(pair)
    # Format as "Team1 vs Team2" (sorted alphabetically) - fallback format
    game_options = ["All Games"] + sorted([f"{pair[0]} vs {pair[1]}" for pair in games_set])
elif "home_team" in value_opportunities.columns and "away_team" in value_opportunities.columns:
    # Fallback: use home_team/away_team from value_opportunities if available
    games_df = value_opportunities[["home_team", "away_team"]].drop_duplicates()
    game_options = ["All Games"] + [
        f"{row['away_team']} @ {row['home_team']}"
        for _, row in games_df.iterrows()
    ]
else:
    # Final fallback: use upcoming_games.csv if value_opportunities doesn't have game info
    game_options_list, upcoming_games_df = load_upcoming_games_with_times()
    if game_options_list:
        game_options = ["All Games"] + game_options_list
    else:
        game_options = ["All Games"]

all_prop_types = sorted(value_opportunities["prop_type"].dropna().unique())

# Game selector in sidebar
selected_game = persistent_selectbox(
    "Game:",
    options=game_options,
    page=PAGE_KEY_PREFIX,
    widget="game",
    default=game_options[0] if game_options else None,
    container=st.sidebar,
)
st.sidebar.write("")

# Legend for edge indicators in sidebar
# st.sidebar.markdown("---")
# st.sidebar.markdown("### Edge % Indicators")
st.sidebar.markdown("""
    <div style='text-align: center; font-size: 0.92rem;'>
        <div style='font-size: 1.2rem; font-weight: 600; margin-bottom: 4px;'>Legend</div>
        <div style='display: flex; flex-direction: column; gap: 3px; margin-top: 2px;'>
            <div style='background: #f5f7fb; border: 1px solid #d6dcf2; border-radius: 8px; padding: 4px 6px;'>
                <div style='font-weight: 600; color: #34495e; margin-bottom: 2px; font-size: 0.92em;'>Passing</div>
                <div style='color: #6c7a89; font-size: 0.91em;'>💎 ≥ 75 yds&nbsp;|&nbsp;⚡️ ≥ 45 yds</div>
            </div>
            <div style='background: #f5f7fb; border: 1px solid #d6dcf2; border-radius: 8px; padding: 4px 6px;'>
                <div style='font-weight: 600; color: #34495e; margin-bottom: 2px; font-size: 0.92em;'>Receiving</div>
                <div style='color: #6c7a89; font-size: 0.91em;'>💎 ≥ 25 yds&nbsp;|&nbsp;⚡️ ≥ 15 yds</div>
            </div>
            <div style='background: #f5f7fb; border: 1px solid #d6dcf2; border-radius: 8px; padding: 4px 6px;'>
                <div style='font-weight: 600; color: #34495e; margin-bottom: 2px; font-size: 0.92em;'>Rushing</div>
                <div style='color: #6c7a89; font-size: 0.91em;'>💎 ≥ 25 yds&nbsp;|&nbsp;⚡️ ≥ 15 yds</div>
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)
# st.sidebar.markdown("⚡️ Edge > 25%")
# st.sidebar.markdown("💎 Edge > 50%")
st.sidebar.write("")
st.sidebar.write("")

st.divider()

# Filter by selected game if not "All Games"
if selected_game != "All Games":
    team_pairs: List[Tuple[str, str]] = []
    # Parse the game selection (format: "Away @ Home" with abbreviations)
    if " @ " in selected_game:
        away_team_abbrev, home_team_abbrev = selected_game.split(" @ ")
        team_pairs = [
            (away_team_abbrev, f"{away_team_abbrev} Players"),
            (home_team_abbrev, f"{home_team_abbrev} Players"),
        ]
        game_data = value_opportunities[
            ((value_opportunities["team"] == away_team_abbrev) & (value_opportunities["opp"] == home_team_abbrev)) |
            ((value_opportunities["team"] == home_team_abbrev) & (value_opportunities["opp"] == away_team_abbrev))
        ].copy()
    elif " vs " in selected_game:
        team1, team2 = selected_game.split(" vs ")
        team_pairs = [
            (team1, f"{team1} Players"),
            (team2, f"{team2} Players"),
        ]
        game_data = value_opportunities[
            ((value_opportunities["team"] == team1) & (value_opportunities["opp"] == team2)) |
            ((value_opportunities["team"] == team2) & (value_opportunities["opp"] == team1))
        ].copy()
    else:
        game_data = value_opportunities.copy()
    
    # Show game-specific view organized by position/prop combinations like Weekly Projections
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

    def format_side_with_emoji(side_value):
        if pd.isna(side_value) or side_value == "-":
            return "-"
        side_str = str(side_value).strip().upper()
        if side_str == "OVER":
            return "Over  ⬆️"
        if side_str == "UNDER":
            return "Under  ⬇️"
        return str(side_value)

    def style_side_cell(val):
        if pd.isna(val) or val == "-":
            return 'color: #666;'
        val_str = str(val).upper()
        if "OVER" in val_str:
            return 'color: #2e7d32; font-weight: 500;'
        if "UNDER" in val_str:
            return 'color: #c62828; font-weight: 500;'
        return ''

    def build_display_table(df_slice: pd.DataFrame, prop_type: str) -> pd.DataFrame:
        display_df = df_slice[
            [
                "player",
                # "team",
                # "position",
                # "opp",
                "side",
                "best_point",
                "best_price",
                "predicted_yards",
                "edge_yards",
                "edge_pct_norm",
                "bookmaker",
            ]
        ].rename(
            columns={
                "player": "Player",
                # "team": "Tm",
                # "position": "Pos",
                # "opp": "Opp",
                # "best_point": "Best Line (yds)",
                "predicted_yards": "Proj (yds)",
                # "best_price": "Best Odds",
                "edge_yards": "Edge (yds)",
                "edge_pct_norm": "Edge %",
                "side": "Side",
                "bookmaker": "Book",
            }
        )
        if display_df.empty:
            return display_df

        if questionable_players:
            display_df["Player"] = display_df["Player"].apply(
                lambda name: append_questionable_tag(name, questionable_players)
            )

        # Add emoji indicators to individual player rows based on edge_yards
        thresholds = YARD_THRESHOLDS.get(prop_type)
        if thresholds is not None:
            low_thr, high_thr = thresholds
            def add_emoji_to_player(row):
                edge = row["Edge (yds)"]
                player_name = row["Player"]
                if pd.notna(edge) and edge >= high_thr:
                    return f"💎 {player_name}"
                elif pd.notna(edge) and edge >= low_thr:
                    return f"⚡️ {player_name}"
                return player_name
            display_df["Player"] = display_df.apply(add_emoji_to_player, axis=1)
        
        # Combine Best Line and Best Odds into one column
        def format_best_line_odds(row):
            best_line = row["best_point"]
            best_odds = row["best_price"]
            if pd.notna(best_line) and pd.notna(best_odds):
                line_str = f"{best_line:.1f}"
                odds_int = int(best_odds)
                odds_str = f"{odds_int:+d}" if odds_int >= 0 else f"{odds_int}"
                # return f"{line_str}  {odds_str}".strip()
                return f" {line_str}   {odds_str}"
            elif pd.notna(best_line):
                return f"{best_line:.1f}".strip()
            elif pd.notna(best_odds):
                odds_int = int(best_odds)
                return (f"{odds_int:+d}" if odds_int >= 0 else f"{odds_int}").strip()
            return "-"
        
        display_df["Best Line"] = display_df.apply(format_best_line_odds, axis=1)
        display_df["Proj (yds)"] = display_df["Proj (yds)"].round(1)
        display_df["Edge (yds)"] = display_df["Edge (yds)"].round(1)
        display_df["Side"] = display_df["Side"].apply(format_side_with_emoji)
        display_df = display_df[["Player", "Side", "Proj (yds)", "Edge (yds)", "Edge %", "Best Line", "Book"]]
        display_df = display_df.sort_values(by="Edge (yds)", ascending=False, na_position='last')
        return display_df
    
    # Define the position-prop combinations we want to show (same as Weekly Projections)
    position_prop_combinations = [
        ('QB', 'Passing Yards'),
        ('QB', 'Rushing Yards'),
        ('RB', 'Rushing Yards'),
        ('RB', 'Receiving Yards'),
        ('WR', 'Receiving Yards'),
        ('TE', 'Receiving Yards')
    ]

    # QB sections - side by side
    qb_cols = st.columns(2)

    # QB Passing Yards
    with qb_cols[0]:
        qb_passing_data = game_data[
            (game_data['position'] == 'QB') &
            (game_data['prop_type'] == 'Passing Yards')
        ].copy()

        if not qb_passing_data.empty:
            # Sort by edge yards descending and add ranking
            qb_passing_data = qb_passing_data.sort_values(by="edge_yards", ascending=False).reset_index(drop=True)
            qb_passing_data["rank"] = range(1, len(qb_passing_data) + 1)

            # Calculate % edge
            denom = np.maximum(qb_passing_data["predicted_yards"].abs(), qb_passing_data["best_point"].abs())
            qb_passing_data["edge_pct_norm"] = (qb_passing_data["edge_yards"] / denom * 100).round(1)

            st.markdown('<h4 style="text-align: center; font-size: 1.1em; margin-bottom: 0.5em;">QB Passing Yards</h4>', unsafe_allow_html=True)
            display_df = build_display_table(qb_passing_data, 'Passing Yards')
            styled_df = (
                display_df.style
                .set_properties(**{
                    "color": "black",
                })
                .set_table_styles([
                    {
                        "selector": "td, th",
                        "props": [("text-align", "center")]
                    }
                ])
                .map(style_side_cell, subset=["Side"])
            )
            st.dataframe(
                styled_df,
                width='stretch',
                hide_index=True,
                column_config={
                    "Player": st.column_config.TextColumn(width=None),
                    # "Tm": st.column_config.TextColumn(width=35),
                    "Side": st.column_config.TextColumn(width=60),
                    "Proj (yds)": st.column_config.NumberColumn("Proj (yds)", format="%.1f", width=65),
                    "Edge (yds)": st.column_config.NumberColumn("Edge (yds)", format="%.1f", width=65),
                    "Edge %": st.column_config.NumberColumn("Edge %", format="%.1f", width=60),
                    "Best Line": st.column_config.TextColumn("Best Line", width="small"),
                    "Book": st.column_config.TextColumn(width="small"),
                },
            )

    # QB Rushing Yards
    with qb_cols[1]:
        qb_rushing_data = game_data[
            (game_data['position'] == 'QB') &
            (game_data['prop_type'] == 'Rushing Yards')
        ].copy()

        if not qb_rushing_data.empty:
            # Sort by edge yards descending and add ranking
            qb_rushing_data = qb_rushing_data.sort_values(by="edge_yards", ascending=False).reset_index(drop=True)
            qb_rushing_data["rank"] = range(1, len(qb_rushing_data) + 1)

            # Calculate % edge
            denom = np.maximum(qb_rushing_data["predicted_yards"].abs(), qb_rushing_data["best_point"].abs())
            qb_rushing_data["edge_pct_norm"] = (qb_rushing_data["edge_yards"] / denom * 100).round(1)

            st.markdown('<h4 style="text-align: center; font-size: 1.1em; margin-bottom: 0.5em;">QB Rushing Yards</h4>', unsafe_allow_html=True)
            display_df = build_display_table(qb_rushing_data, 'Rushing Yards')
            styled_df = (
                display_df.style
                .set_properties(**{
                    "color": "black",
                })
                .set_table_styles([
                    {
                        "selector": "td, th",
                        "props": [("text-align", "center")]
                    }
                ])
                .map(style_side_cell, subset=["Side"])
            )
            st.dataframe(
                styled_df,
                width='stretch',
                hide_index=True,
                column_config={
                    "Player": st.column_config.TextColumn(width=None),
                    # "Tm": st.column_config.TextColumn(width=35),
                    "Side": st.column_config.TextColumn(width=60),
                    "Proj (yds)": st.column_config.NumberColumn("Proj (yds)", format="%.1f", width=65),
                    "Edge (yds)": st.column_config.NumberColumn("Edge (yds)", format="%.1f", width=65),
                    "Edge %": st.column_config.NumberColumn("Edge %", format="%.1f", width=60),
                    "Best Line": st.column_config.TextColumn("Best Line", width="small"),
                    "Book": st.column_config.TextColumn(width="small"),
                },
            )

    # RB sections - side by side
    rb_cols = st.columns(2)

    # RB Rushing Yards
    with rb_cols[0]:
        rb_rushing_data = game_data[
            (game_data['position'] == 'RB') &
            (game_data['prop_type'] == 'Rushing Yards')
        ].copy()

        if not rb_rushing_data.empty:
            # Sort by edge yards descending and add ranking
            rb_rushing_data = rb_rushing_data.sort_values(by="edge_yards", ascending=False).reset_index(drop=True)
            rb_rushing_data["rank"] = range(1, len(rb_rushing_data) + 1)

            # Calculate % edge
            denom = np.maximum(rb_rushing_data["predicted_yards"].abs(), rb_rushing_data["best_point"].abs())
            rb_rushing_data["edge_pct_norm"] = (rb_rushing_data["edge_yards"] / denom * 100).round(1)

            st.markdown('<h4 style="text-align: center; font-size: 1.1em; margin-bottom: 0.5em;">RB Rushing Yards</h4>', unsafe_allow_html=True)
            display_df = build_display_table(rb_rushing_data, 'Rushing Yards')
            styled_df = (
                display_df.style
                .set_properties(**{
                    "color": "black",
                })
                .set_table_styles([
                    {
                        "selector": "td, th",
                        "props": [("text-align", "center")]
                    }
                ])
                .map(style_side_cell, subset=["Side"])
            )
            st.dataframe(
                styled_df,
                width='stretch',
                hide_index=True,
                column_config={
                    "Player": st.column_config.TextColumn(width=None),
                    # "Tm": st.column_config.TextColumn(width=35),
                    "Side": st.column_config.TextColumn(width=60),
                    "Proj (yds)": st.column_config.NumberColumn("Proj (yds)", format="%.1f", width=65),
                    "Edge (yds)": st.column_config.NumberColumn("Edge (yds)", format="%.1f", width=65),
                    "Edge %": st.column_config.NumberColumn("Edge %", format="%.1f", width=60),
                    "Best Line": st.column_config.TextColumn("Best Line", width="small"),
                    "Book": st.column_config.TextColumn(width="small"),
                },
            )

    # RB Receiving Yards
    with rb_cols[1]:
        rb_receiving_data = game_data[
            (game_data['position'] == 'RB') &
            (game_data['prop_type'] == 'Receiving Yards')
        ].copy()

        if not rb_receiving_data.empty:
            # Sort by edge yards descending and add ranking
            rb_receiving_data = rb_receiving_data.sort_values(by="edge_yards", ascending=False).reset_index(drop=True)
            rb_receiving_data["rank"] = range(1, len(rb_receiving_data) + 1)

            # Calculate % edge
            denom = np.maximum(rb_receiving_data["predicted_yards"].abs(), rb_receiving_data["best_point"].abs())
            rb_receiving_data["edge_pct_norm"] = (rb_receiving_data["edge_yards"] / denom * 100).round(1)

            st.markdown('<h4 style="text-align: center; font-size: 1.1em; margin-bottom: 0.5em;">RB Receiving Yards</h4>', unsafe_allow_html=True)
            display_df = build_display_table(rb_receiving_data, 'Receiving Yards')
            styled_df = (
                display_df.style
                .set_properties(**{
                    "color": "black",
                })
                .set_table_styles([
                    {
                        "selector": "td, th",
                        "props": [("text-align", "center")]
                    }
                ])
                .map(style_side_cell, subset=["Side"])
            )
            st.dataframe(
                styled_df,
                width='stretch',
                hide_index=True,
                column_config={
                    "Player": st.column_config.TextColumn(width=None),
                    # "Tm": st.column_config.TextColumn(width=35),
                    "Side": st.column_config.TextColumn(width=60),
                    "Proj (yds)": st.column_config.NumberColumn("Proj (yds)", format="%.1f", width=65),
                    "Edge (yds)": st.column_config.NumberColumn("Edge (yds)", format="%.1f", width=65),
                    "Edge %": st.column_config.NumberColumn("Edge %", format="%.1f", width=60),
                    "Best Line": st.column_config.TextColumn("Best Line", width="small"),
                    "Book": st.column_config.TextColumn(width="small"),
                },
            )

    # WR and TE Receiving Yards (side by side)
    wr_te_cols = st.columns(2)

    # WR Receiving Yards
    with wr_te_cols[0]:
        wr_receiving_data = game_data[
            (game_data['position'] == 'WR') &
            (game_data['prop_type'] == 'Receiving Yards')
        ].copy()

        if not wr_receiving_data.empty:
            # Sort by edge yards descending and add ranking
            wr_receiving_data = wr_receiving_data.sort_values(by="edge_yards", ascending=False).reset_index(drop=True)
            wr_receiving_data["rank"] = range(1, len(wr_receiving_data) + 1)

            # Calculate % edge
            denom = np.maximum(wr_receiving_data["predicted_yards"].abs(), wr_receiving_data["best_point"].abs())
            wr_receiving_data["edge_pct_norm"] = (wr_receiving_data["edge_yards"] / denom * 100).round(1)

            st.markdown('<h4 style="text-align: center; font-size: 1.1em; margin-bottom: 0.5em;">WR Receiving Yards</h4>', unsafe_allow_html=True)
            display_df = build_display_table(wr_receiving_data, 'Receiving Yards')
            styled_df = (
                display_df.style
                .set_properties(**{
                    "color": "black",
                })
                .set_table_styles([
                    {
                        "selector": "td, th",
                        "props": [("text-align", "center")]
                    }
                ])
                .map(style_side_cell, subset=["Side"])
            )
            st.dataframe(
                styled_df,
                width='stretch',
                hide_index=True,
                column_config={
                    "Player": st.column_config.TextColumn(width=None),
                    # "Tm": st.column_config.TextColumn(width=35),
                    "Side": st.column_config.TextColumn(width=60),
                    "Proj (yds)": st.column_config.NumberColumn("Proj (yds)", format="%.1f", width=65),
                    "Edge (yds)": st.column_config.NumberColumn("Edge (yds)", format="%.1f", width=65),
                    "Edge %": st.column_config.NumberColumn("Edge %", format="%.1f", width=60),
                    "Best Line": st.column_config.TextColumn("Best Line", width="small"),
                    "Book": st.column_config.TextColumn(width="small"),
                },
            )

    # TE Receiving Yards
    with wr_te_cols[1]:
        te_receiving_data = game_data[
            (game_data['position'] == 'TE') &
            (game_data['prop_type'] == 'Receiving Yards')
        ].copy()

        if not te_receiving_data.empty:
            # Sort by edge yards descending and add ranking
            te_receiving_data = te_receiving_data.sort_values(by="edge_yards", ascending=False).reset_index(drop=True)
            te_receiving_data["rank"] = range(1, len(te_receiving_data) + 1)

            # Calculate % edge
            denom = np.maximum(te_receiving_data["predicted_yards"].abs(), te_receiving_data["best_point"].abs())
            te_receiving_data["edge_pct_norm"] = (te_receiving_data["edge_yards"] / denom * 100).round(1)

            st.markdown('<h4 style="text-align: center; font-size: 1.1em; margin-bottom: 0.5em;">TE Receiving Yards</h4>', unsafe_allow_html=True)
            display_df = build_display_table(te_receiving_data, 'Receiving Yards')
            styled_df = (
                display_df.style
                .set_properties(**{
                    "color": "black",
                })
                .set_table_styles([
                    {
                        "selector": "td, th",
                        "props": [("text-align", "center")]
                    }
                ])
                .map(style_side_cell, subset=["Side"])
            )
            st.dataframe(
                styled_df,
                width='stretch',
                hide_index=True,
                column_config={
                    "Player": st.column_config.TextColumn(width="None"),
                    # "Player": st.column_config.TextColumn(width="medium"),
                    # "Tm": st.column_config.TextColumn(width=35),
                    "Side": st.column_config.TextColumn(width=60),
                    "Proj (yds)": st.column_config.NumberColumn("Proj (yds)", format="%.1f", width=65),
                    "Edge (yds)": st.column_config.NumberColumn("Edge (yds)", format="%.1f", width=65),
                    "Edge %": st.column_config.NumberColumn("Edge %", format="%.1f", width=60),
                    "Best Line": st.column_config.TextColumn("Best Line", width="small"),
                    "Book": st.column_config.TextColumn(width="small"),
                },
            )
    
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
            
            # Normalized % edge (prevents tiny-line explosions)
            denom = np.maximum(subset["predicted_yards"].abs(), subset["best_point"].abs())
            subset["edge_pct_norm"] = (subset["edge_yards"] / denom * 100).round(1)
            thresholds = YARD_THRESHOLDS.get(tab_label)
            if thresholds is None:
                subset["edge_indicator"] = ""
            else:
                low_thr, high_thr = thresholds
                subset["edge_indicator"] = subset["edge_yards"].apply(
                    lambda yards: "💎" if pd.notna(yards) and yards >= high_thr else (
                        "⚡️" if pd.notna(yards) and yards >= low_thr else ""
                    )
                )

            if questionable_players:
                subset["player"] = subset["player"].apply(
                    lambda name: append_questionable_tag(name, questionable_players)
                )
            
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
                    "edge_yards",
                    "edge_pct_norm",
                    "edge_indicator",
                    "bookmaker",
                ]
            ].rename(
                columns={
                    "rank": "#",
                    "player": "Player",
                    "position": "Pos",
                    "team": "Team",
                    "opp": "Opp",
                    "best_point": "Best Line (yds)",
                    "predicted_yards": "Projection (yds)",
                    "best_price": "Best Odds",
                    "edge_yards": "Edge (yds)",
                    "edge_pct_norm": "Edge % (norm)",
                    "edge_indicator": "Indicator",
                    "side": "Side",
                    "bookmaker": "Book",
                }
            )
            
            display_df["Projection (yds)"] = display_df["Projection (yds)"].round(1)
            display_df["Best Line (yds)"] = display_df["Best Line (yds)"].round(1)
            display_df["Best Odds"] = display_df["Best Odds"].round().astype("Int64")
            display_df["Edge (yds)"] = display_df["Edge (yds)"].round(2)
            display_df = display_df[["#", "Player", "Pos", "Team", "Opp", "Projection (yds)", "Best Line (yds)", "Best Odds", "Edge (yds)", "Edge % (norm)", "Indicator", "Side", "Book"]]
            
            # Sort FIRST by Edge (yds) before formatting
            display_df = display_df.sort_values(by="Edge (yds)", ascending=False, na_position='last')
            
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
            display_df = display_df.drop(columns=["Indicator"])
            
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
            
            # Create styled dataframe with centered text and custom style for Side
            styled_df = (
                display_df.style
                .set_properties(**{
                    "color": "black",
                    # "text-align": "center"
                    # "background-color": "white",
                    # 'background-color': '#f0f0f0',
                    # 'background-color': 'black',
                    # "color": "black",
                    # "border-color": "black",
                })
                .set_table_styles([
                    {
                        "selector": "td, th",
                        "props": [("text-align", "center")]
                    }
                ])
                .map(style_side_cell, subset=["Side"])
            )
            st.write("")
            col1, col2, col3 = st.columns([0.1, 3, 0.1])
            with col2:
                st.dataframe(
                    styled_df,
                    width='stretch',
                    height="content",
                    hide_index=True,
                    column_config={
                        # "#": st.column_config.TextColumn(label="", width=None),
                        "#": st.column_config.TextColumn(label="", width=20),
                        "Player": st.column_config.TextColumn(width=None),
                        "Pos": st.column_config.TextColumn(width=None),
                        "Team": st.column_config.TextColumn(width=None),
                        "Opp": st.column_config.TextColumn(width=None),
                        "Best Line (yds)": st.column_config.NumberColumn("Best Line (yds)", format="%.1f", width=None),
                        "Projection (yds)": st.column_config.NumberColumn("Projection (yds)", format="%.1f", width=None),
                        "Best Odds": st.column_config.NumberColumn("Best Odds", width=None),
                        "Edge (yds)": st.column_config.NumberColumn("Edge (yds)", format="%.2f", width=None),
                        "Edge % (norm)": st.column_config.NumberColumn("Edge % (norm)", format="%.1f", width=None),
                        "Side": st.column_config.TextColumn(width=None),
                    },
                )

            # # Use AgGrid for better centering and styling
            # gb = GridOptionsBuilder.from_dataframe(display_df)
            # gb.configure_default_column(
            #     resizable=True,
            #     sortable=True,
            #     filterable=False,
            # )
            # gb.configure_column("#", width=50, pinned="left")
            # gb.configure_column("Player", width=150)
            # gb.configure_column("Pos", width=60)
            # gb.configure_column("Team", width=60)
            # gb.configure_column("Opp", width=60)
            # gb.configure_column("Best Line (yds)", width=100)
            # gb.configure_column("Projection (yds)", width=100)
            # gb.configure_column("Best Odds", width=80)
            # gb.configure_column("Edge (yds)", width=90)
            # gb.configure_column("Edge % (norm)", width=100)
            # # Style the Side column with colors
            # gb.configure_column("Side", width=80, cellStyle={
            #     "function": """
            #         function(params) {
            #             if (params.value) {
            #                 var val = params.value.toString().toUpperCase();
            #                 if (val.includes('OVER')) {
            #                     return {color: '#2e7d32', fontWeight: '500'};
            #                 } else if (val.includes('UNDER')) {
            #                     return {color: '#c62828', fontWeight: '500'};
            #                 }
            #             }
            #             return {color: '#666'};
            #         }
            #     """
            # })
            
            # grid_options = gb.build()
            
            # AgGrid(
            #     display_df,
            #     gridOptions=grid_options,
            #     height=400,
            #     theme='streamlit',
            #     allow_unsafe_jscode=True,
            # )

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
        width='stretch',
    )

st.divider()

with st.sidebar:
    st.markdown(
        "<div style='font-size: 1.2rem; font-weight: 600; margin-bottom: 12px; text-align: center;'>Export</div>"
        "<div style='height: 5px;'></div>",  # small space after the title
        unsafe_allow_html=True
    )
    # st.markdown("######")
    # st.write("")
    value_html_path = os.path.join(
        PROJECTIONS_DIR, f"week{selected_week_number}_value_complete_props_report.html"
    )
    value_pdf_path = os.path.join(
        PROJECTIONS_DIR, f"week{selected_week_number}_value_leader_tables.pdf"
    )

    # Just use download buttons, no additional HTML or CSS
    if os.path.exists(value_html_path):
        with open(value_html_path, "rb") as html_file:
            st.download_button(
                label="Value Prop Report (HTML)",
                data=html_file.read(),
                file_name=os.path.basename(value_html_path),
                mime="text/html",
                # width='stretch',
                # width=150
                width='stretch'
            )

    if os.path.exists(value_pdf_path):
        with open(value_pdf_path, "rb") as pdf_file:
            st.download_button(
                label="Value Leader Tables (PDF)",
                data=pdf_file.read(),
                file_name=os.path.basename(value_pdf_path),
                mime="application/pdf",
                # width='stretch','
                # width=150
                width='stretch'
            )

# Footer
render_footer()
