import streamlit as st
import pandas as pd
import altair as alt
from pathlib import Path

st.set_page_config(page_title="Weekly Model Predictions", layout="wide")
st.title("Weekly Model Predictions")

ROOT_DIR = Path(__file__).resolve().parents[3]
REPORT_DIR = ROOT_DIR / "Models" / "0-FINAL-REPORTS"

summary_files = sorted(REPORT_DIR.glob("week*_all_props_summary.csv"))

if not summary_files:
    st.warning("No weekly reports found in Models/0-FINAL-REPORTS.")
else:
    weeks = [int(f.name.split("_")[0].replace("week", "")) for f in summary_files]
    week_labels = [f"Week {w}" for w in weeks]
    selected_label = st.sidebar.selectbox("Select week", week_labels, index=len(weeks) - 1)
    selected_week = weeks[week_labels.index(selected_label)]

    summary_file = REPORT_DIR / f"week{selected_week}_all_props_summary.csv"
    report_html = REPORT_DIR / f"week{selected_week}_complete_props_report.html"
    report_txt = REPORT_DIR / f"week{selected_week}_complete_props_report.txt"

    df = pd.read_csv(summary_file)

    with st.sidebar.expander("Filters", expanded=False):
        team_filter = st.multiselect("Teams", options=sorted(df["team"].unique()), default=sorted(df["team"].unique()))
        position_filter = st.multiselect(
            "Positions", options=sorted(df["position"].unique()), default=sorted(df["position"].unique())
        )
        prop_filter = st.multiselect(
            "Prop Types", options=sorted(df["prop_type"].unique()), default=sorted(df["prop_type"].unique())
        )

    filtered_df = df[
        df["team"].isin(team_filter)
        & df["position"].isin(position_filter)
        & df["prop_type"].isin(prop_filter)
    ]

    col1, col2, col3 = st.columns(3)
    col1.metric("Predictions", len(filtered_df))
    col2.metric("Teams", filtered_df["team"].nunique())
    col3.metric("Prop Types", filtered_df["prop_type"].nunique())

    tab_table, tab_chart, tab_report = st.tabs(["Table", "Visuals", "Full Report"])

    with tab_table:
        st.dataframe(filtered_df, use_container_width=True)
        st.download_button(
            "Download summary",
            filtered_df.to_csv(index=False).encode("utf-8"),
            file_name=f"week{selected_week}_summary.csv",
            mime="text/csv",
        )

    with tab_chart:
        top_players = filtered_df.sort_values("pred_yards", ascending=False).head(20)
        chart = (
            alt.Chart(top_players)
            .mark_bar()
            .encode(
                x=alt.X("pred_yards:Q", title="Predicted Yards"),
                y=alt.Y("full_name:N", sort="-x", title="Player"),
                color="position:N",
                tooltip=list(top_players.columns),
            )
            .properties(height=600)
        )
        st.altair_chart(chart, use_container_width=True)

    with tab_report:
        if report_html.exists():
            with open(report_html, "r", encoding="utf-8") as f:
                html_content = f.read()
            st.components.v1.html(html_content, height=600, scrolling=True)
            st.download_button(
                "Download full report (HTML)",
                data=html_content.encode("utf-8"),
                file_name=report_html.name,
                mime="text/html",
            )
        elif report_txt.exists():
            with open(report_txt, "r", encoding="utf-8") as f:
                text_content = f.read()
            st.text(text_content)
            st.download_button(
                "Download full report (TXT)",
                data=text_content,
                file_name=report_txt.name,
                mime="text/plain",
            )
        else:
            st.info("No detailed report available for this week.")

