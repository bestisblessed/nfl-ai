import io
from typing import Callable, Dict, List

import pandas as pd
from pandas.api.types import is_float_dtype, is_integer_dtype
import streamlit as st

from utils.pdf_leaders import Leaderboard, leaderboard_summary, parse_leader_pdf

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

# Get the latest week automatically
import os
projections_dir = "data/projections"
latest_week = None
if os.path.exists(projections_dir):
    week_files = [f for f in os.listdir(projections_dir) if f.endswith("_leader_tables.pdf")]
    if week_files:
        # Sort by week number and get the latest
        week_nums = sorted([int(f.replace("_leader_tables.pdf", "").replace("week", "")) for f in week_files])
        latest_week = f"Week {week_nums[-1]}"

if not latest_week:
    st.error("No projection files found in data/projections/ directory.")
    st.stop()

# Show current week info
st.markdown(f"""
    <div style='background-color: #f0f8ff; padding: 15px; border-radius: 10px; margin-bottom: 20px; text-align: center;'>
        <strong style='color: #1f77b4; font-size: 1.2em;'>{latest_week} Projections</strong>
    </div>
    """,
    unsafe_allow_html=True
)

@st.cache_data(show_spinner=False)
def _parse_pdf(content: bytes) -> List[Leaderboard]:
    return parse_leader_pdf(content)

@st.cache_data(show_spinner=False)
def _load_week_pdf(week_str: str):
    """Load PDF content for the selected week."""
    week_num = week_str.replace("Week ", "")
    pdf_path = f"data/projections/week{week_num}_leader_tables.pdf"
    try:
        with open(pdf_path, "rb") as f:
            return f.read()
    except FileNotFoundError:
        st.error(f"PDF file for {week_str} not found.")
        return None

with st.spinner("Loading projections…"):
    pdf_content = _load_week_pdf(latest_week)
    if pdf_content is None:
        st.stop()

    leaderboards = _parse_pdf(pdf_content)

if not leaderboards:
    st.error(
        "We couldn't detect any tables in the PDF. Make sure the document contains "
        "clearly formatted tables with headers such as Rank, Player, Opponent, etc."
    )
    st.stop()

# Organize leaderboards by category for clean display
qb_boards = [lb for lb in leaderboards if "qb" in lb.title.lower()]
wr_boards = [lb for lb in leaderboards if "wr" in lb.title.lower()]
te_boards = [lb for lb in leaderboards if "te" in lb.title.lower()]
rb_boards = [lb for lb in leaderboards if "rb" in lb.title.lower() and "receiving" not in lb.title.lower()]
rb_rec_boards = [lb for lb in leaderboards if "rb" in lb.title.lower() and "receiving" in lb.title.lower()]

# Create sections for each position type
sections = [
    ("Quarterbacks", qb_boards),
    ("Wide Receivers", wr_boards),
    ("Tight Ends", te_boards),
    ("Running Backs", rb_boards),
    ("RB Receiving", rb_rec_boards),
]

def create_styled_dataframe(leaderboard: Leaderboard):
    """Create a beautifully styled dataframe for display."""
    df = leaderboard.dataframe

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
                            {leaderboard.title.replace("Top 25 ", "")}
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
