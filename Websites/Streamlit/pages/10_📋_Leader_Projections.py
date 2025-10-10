import io
from typing import Callable, Dict, List

import pandas as pd
from pandas.api.types import is_float_dtype, is_integer_dtype
import streamlit as st

from utils.pdf_leaders import Leaderboard, leaderboard_summary, parse_leader_pdf

st.set_page_config(page_title="Daily Leader Projections", page_icon="📋")

st.title("📋 Daily Leader Projections")
st.caption(
    "Upload the latest projection PDF to automatically convert each leaderboard "
    "into a sortable, searchable table with quick insights."
)

with st.expander("How to use", expanded=False):
    st.markdown(
        """
        1. Export your daily leader projections as a PDF (one or more leaderboards per page).
        2. Upload the PDF below. Tables are parsed automatically — no manual data entry needed.
        3. Explore the leaderboards, download cleansed CSVs, and share quick takeaways with your team.
        """
    )

uploaded_file = st.file_uploader("Upload leader projections (PDF)", type="pdf")

@st.cache_data(show_spinner=False)
def _parse_pdf(content: bytes) -> List[Leaderboard]:
    return parse_leader_pdf(content)

if uploaded_file is None:
    st.info(
        "Waiting for a PDF upload. Once you provide a file, each leaderboard will "
        "appear below with formatted tables and key takeaways."
    )
    st.stop()

with st.spinner("Parsing leaderboards…"):
    leaderboards = _parse_pdf(uploaded_file.read())

if not leaderboards:
    st.error(
        "We couldn't detect any tables in the PDF. Make sure the document contains "
        "clearly formatted tables with headers such as Rank, Player, Opponent, etc."
    )
    st.stop()

leaderboard_titles = [leaderboard.title for leaderboard in leaderboards]
selected_titles = st.multiselect(
    "Select which leaderboards to display",
    options=leaderboard_titles,
    default=leaderboard_titles,
)

if not selected_titles:
    st.warning("Select at least one leaderboard to view the projections.")
    st.stop()

leaderboard_lookup = {leaderboard.title: leaderboard for leaderboard in leaderboards}

tabs = st.tabs(selected_titles)

for title, tab in zip(selected_titles, tabs):
    leaderboard = leaderboard_lookup[title]
    with tab:
        st.subheader(leaderboard.title)

        summary = leaderboard_summary(leaderboard)
        if summary:
            st.markdown(
                "**Quick hitters**"
            )
            st.markdown("\n".join([f"- {item}" for item in summary]))

        df = leaderboard.dataframe
        player_column = "Player" if "Player" in df.columns else df.columns[1]
        numeric_columns = [
            column
            for column in df.columns
            if pd.api.types.is_numeric_dtype(df[column])
        ]

        if numeric_columns:
            metric_column = numeric_columns[-1]
            top_row = df.nsmallest(1, "Rank") if "Rank" in df.columns else df.head(1)
            metric_value = top_row.iloc[0][metric_column]
            player_value = top_row.iloc[0][player_column]
            if is_float_dtype(df[metric_column]):
                formatted_value = f"{metric_value:,.1f}"
            elif is_integer_dtype(df[metric_column]):
                formatted_value = f"{int(metric_value):,}"
            else:
                formatted_value = str(metric_value)
            st.metric(label=f"{player_value} leads {metric_column}", value=formatted_value)

        def _float_formatter(value: float) -> str:
            if pd.isna(value):
                return ""
            return f"{value:,.1f}"

        def _int_formatter(value: float) -> str:
            if pd.isna(value):
                return ""
            return f"{int(value):,}"

        formatters: Dict[str, Callable[[float], str]] = {}
        for column in numeric_columns:
            if is_float_dtype(df[column]):
                formatters[column] = _float_formatter
            elif is_integer_dtype(df[column]):
                formatters[column] = _int_formatter

        styled_df = (
            df.style.format(formatters, na_rep="")
            .set_table_styles(
                [{"selector": "th", "props": "text-align: center; background-color: #0d1b2a; color: white;"}]
            )
            .set_properties(**{"text-align": "center"})
        )
        st.dataframe(styled_df, use_container_width=True)

        buffer = io.StringIO()
        df.to_csv(buffer, index=False)
        st.download_button(
            label="Download leaderboard as CSV",
            data=buffer.getvalue(),
            file_name=f"{leaderboard.title.replace(' ', '_').lower()}.csv",
            mime="text/csv",
        )

st.success("Leader projections loaded successfully.")
