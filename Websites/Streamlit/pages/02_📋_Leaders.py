import io
from typing import Callable, Dict, List

import pandas as pd
from pandas.api.types import is_float_dtype, is_integer_dtype
import streamlit as st
import os
import glob

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# st.set_page_config(page_title="Leader Projections", layout="centered")
st.set_page_config(page_title="Leader Projections", layout="wide")

# st.title("NFL Leader Projections")

st.markdown("""
    <div style='text-align: center;'>
        <div style='font-size: 3.1rem; font-weight: 800; padding-bottom: 0.5rem;'>
            NFL Leader Projections
        </div>
        <div style='color: #7f8c8d; font-size: 1rem; margin-top: 0; line-height: 1.2;'>
            Top 25 Player Projections Across All Categories
        </div>
    </div>
    """,
    unsafe_allow_html=True
)
st.divider()
st.write("")
# st.write("")

# Function to load projections data (following same pattern as Projections page)
@st.cache_data
def load_projections_data():
    """Load and process projections data from CSV files"""
    projections_dir = os.path.join(BASE_DIR, "data/projections")

    # Find all projection files
    projection_files = glob.glob(os.path.join(projections_dir, "week*_all_props_summary.csv"))

    if not projection_files:
        return None, []

    # Extract available weeks
    available_weeks = []
    for file in projection_files:
        week_num = file.split('week')[1].split('_')[0]
        available_weeks.append(int(week_num))

    available_weeks.sort()

    return projection_files, available_weeks

# Load available data
projection_files, available_weeks = load_projections_data()

if not available_weeks:
    st.error("No projection data available. Please ensure projection files are in data/projections/")
    st.stop()

# Get the latest week automatically
latest_week = f"Week {available_weeks[-1]}"

# Show current week info
st.markdown(f"""
    <div style='background-color: #f0f8ff; padding: 15px; border-radius: 10px; margin-bottom: 20px; text-align: center;'>
        <strong style='color: #1f77b4; font-size: 1.2em;'>{latest_week} Projections</strong>
    </div>
    """,
    unsafe_allow_html=True
)

# Function to get projections for a specific week
@st.cache_data
def get_week_projections(week_num):
    """Get projections data for a specific week"""
    file_path = os.path.join(BASE_DIR, f"data/projections/week{week_num}_all_props_summary.csv")

    if not os.path.exists(file_path):
        return None

    try:
        df = pd.read_csv(file_path)

        # Clean and process the data
        df = df.dropna(subset=['pred_yards'])
        df['pred_yards'] = pd.to_numeric(df['pred_yards'], errors='coerce')
        df = df.dropna(subset=['pred_yards'])

        return df
    except Exception as e:
        st.error(f"Error loading week {week_num} data: {str(e)}")
        return None

# Load data for the latest week
with st.spinner("Loading projections…"):
    week_num = latest_week.replace("Week ", "")
    projections_df = get_week_projections(int(week_num))

    if projections_df is None:
        st.error(f"No data available for {latest_week}")
        st.stop()

# Create leaderboards from projections data
def create_leaderboard_from_projections(df, prop_type, title, position_filter=None, top_n=25):
    """Create a leaderboard DataFrame from projections data"""
    # Filter by prop type
    prop_data = df[df['prop_type'] == prop_type].copy()

    # Apply position filter if provided
    if position_filter:
        prop_data = position_filter(prop_data)

    if prop_data.empty:
        return None

    # Sort by predicted yards and take top N
    leaderboard_df = prop_data.nlargest(top_n, 'pred_yards').copy()

    # Add rank column
    leaderboard_df['Rank'] = range(1, len(leaderboard_df) + 1)

    # Reorder columns to match expected format
    cols = ['Rank', 'full_name', 'team', 'opp', 'position', 'pred_yards']
    leaderboard_df = leaderboard_df[cols]

    # Rename columns for display
    leaderboard_df.columns = ['Rank', 'Player', 'Team', 'Opponent', 'Position', 'Projected Yards']

    return {
        'title': title,
        'dataframe': leaderboard_df
    }

# Create leaderboards for each category
leaderboards = []

# Quarterback Passing Yards
qb_board = create_leaderboard_from_projections(
    projections_df, 'Passing Yards', 'Top 25 QB Passing Yards'
)
if qb_board:
    leaderboards.append(qb_board)

# Wide Receiver Receiving Yards
wr_board = create_leaderboard_from_projections(
    projections_df, 'Receiving Yards',
    'Top 25 WR Receiving Yards',
    lambda df: df[df['position'] == 'WR']
)
if wr_board:
    leaderboards.append(wr_board)

# Tight End Receiving Yards
te_board = create_leaderboard_from_projections(
    projections_df, 'Receiving Yards',
    'Top 25 TE Receiving Yards',
    lambda df: df[df['position'] == 'TE']
)
if te_board:
    leaderboards.append(te_board)

# Running Back Rushing Yards (assuming this is a separate prop type)
rb_rush_board = create_leaderboard_from_projections(
    projections_df, 'Rushing Yards', 'Top 25 RB Rushing Yards'
)
if rb_rush_board:
    leaderboards.append(rb_rush_board)

# Running Back Receiving Yards
rb_rec_board = create_leaderboard_from_projections(
    projections_df, 'Receiving Yards',
    'Top 25 RB Receiving Yards',
    lambda df: df[df['position'] == 'RB']
)
if rb_rec_board:
    leaderboards.append(rb_rec_board)

if not leaderboards:
    st.error("No leaderboard data could be created from the projections.")
    st.stop()

# Organize leaderboards by category for clean display
qb_boards = [lb for lb in leaderboards if "qb" in lb['title'].lower()]
wr_boards = [lb for lb in leaderboards if "wr" in lb['title'].lower() and "receiving" in lb['title'].lower()]
te_boards = [lb for lb in leaderboards if "te" in lb['title'].lower()]
rb_boards = [lb for lb in leaderboards if "rb" in lb['title'].lower() and "rushing" in lb['title'].lower()]
rb_rec_boards = [lb for lb in leaderboards if "rb" in lb['title'].lower() and "receiving" in lb['title'].lower()]

# Create sections for each position type
sections = [
    ("Quarterbacks", qb_boards),
    ("Wide Receivers", wr_boards),
    ("Tight Ends", te_boards),
    ("Running Backs", rb_boards),
    ("RB Receiving", rb_rec_boards),
]

def create_styled_dataframe(leaderboard):
    """Create a beautifully styled dataframe for display."""
    df = leaderboard['dataframe']

    # Format numeric columns
    def _float_formatter(value: float) -> str:
        if pd.isna(value):
            return ""
        return f"{value:,.1f}"

    def _int_formatter(value: float) -> str:
        if pd.isna(value):
            return ""
        return f"{int(value):,}"

    formatters: Dict[str, Callable[[float], str]] = {}
    numeric_columns = [
        column for column in df.columns
        if pd.api.types.is_numeric_dtype(df[column])
    ]

    for column in numeric_columns:
        if is_float_dtype(df[column]):
            formatters[column] = _float_formatter
        elif is_integer_dtype(df[column]):
            formatters[column] = _int_formatter

    # Apply styling
    styled_df = (
        df.style
        .format(formatters, na_rep="")
        .set_table_styles([
            {"selector": "th", "props": [
                ("text-align", "center"),
                ("background-color", "#1f77b4"),
                ("color", "white"),
                ("font-weight", "bold"),
                ("padding", "12px"),
                ("border", "1px solid #ddd")
            ]},
            {"selector": "td", "props": [
                ("text-align", "center"),
                ("padding", "8px"),
                ("border", "1px solid #eee")
            ]},
            {"selector": "tr:nth-child(even)", "props": [("background-color", "#f9f9f9")]},
            {"selector": "tr:hover", "props": [("background-color", "#e6f7ff")]},
        ])
        .set_properties(**{
            "text-align": "center",
            "font-size": "14px"
        })
    )
    return styled_df

# Display each section
for section_title, section_boards in sections:
    if section_boards:
        st.markdown(f"""
            <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        padding: 20px;
                        border-radius: 15px;
                        margin: 25px 0;
                        text-align: center;
                        box-shadow: 0 4px 6px rgba(0,0,0,0.1);'>
                <h2 style='color: white; margin: 0; font-size: 2em; text-shadow: 2px 2px 4px rgba(0,0,0,0.3);'>
                    {section_title}
                </h2>
            </div>
            """,
            unsafe_allow_html=True
        )

        # Create columns for multiple leaderboards in a section
        cols = st.columns(len(section_boards))

        for i, (col, leaderboard) in enumerate(zip(cols, section_boards)):
            with col:
                # Card-style container for each leaderboard
                st.markdown(f"""
                    <div style='background-color: white;
                               border-radius: 12px;
                               padding: 20px;
                               margin: 10px 0;
                               box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                               border: 1px solid #e0e0e0;'>
                        <h3 style='text-align: center;
                                 color: #1f77b4;
                                 margin-bottom: 15px;
                                 font-size: 1.3em;
                                 text-transform: uppercase;
                                 letter-spacing: 1px;'>
                            {leaderboard['title'].replace("Top 25 ", "")}
                        </h3>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                # Show top performer
                df = leaderboard.dataframe
                if not df.empty and len(df) > 0:
                    player_column = "Player" if "Player" in df.columns else df.columns[1]
                    numeric_columns = [
                        column for column in df.columns
                        if pd.api.types.is_numeric_dtype(df[column])
                    ]

                    if numeric_columns:
                        metric_column = numeric_columns[-1]
                        top_row = df.nsmallest(1, "Rank") if "Rank" in df.columns else df.head(1)
                        if not top_row.empty:
                            metric_value = top_row.iloc[0][metric_column]
                            player_value = top_row.iloc[0][player_column]

                            # Format the value
                            if is_float_dtype(df[metric_column]):
                                formatted_value = f"{metric_value:,.1f}"
                            elif is_integer_dtype(df[metric_column]):
                                formatted_value = f"{int(metric_value):,}"
                            else:
                                formatted_value = str(metric_value)

                            st.write("")
                            # Show top performer metric
                            st.metric(
                                label="Top Projection",
                                value=f"{formatted_value} {metric_column}",
                                delta=player_value
                            )

                # Display the styled dataframe
                styled_df = create_styled_dataframe(leaderboard)
                st.dataframe(styled_df, use_container_width=True, height=400)


# Footer
st.markdown("""
    <div style='text-align: center; margin-top: 40px; padding: 20px; color: #666;'>
        <hr style='margin-bottom: 20px;'>
        <p><strong>NFL Leader Projections</strong> - Powered by advanced analytics</p>
        <p style='font-size: 0.9em;'>Data updated weekly • All projections are estimates and subject to change</p>
    </div>
    """,
    unsafe_allow_html=True
)
