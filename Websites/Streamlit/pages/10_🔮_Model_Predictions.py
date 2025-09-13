import streamlit as st
import pandas as pd
from pathlib import Path


st.set_page_config(page_title="Model Predictions", layout="wide")
st.title("Weekly Model Predictions")

ROOT_DIR = Path(__file__).resolve().parents[3]
REPORT_DIR = ROOT_DIR / "Models" / "0-FINAL-REPORTS"


@st.cache_data
def _discover_weeks():
    files = sorted(REPORT_DIR.glob("week*_all_props_summary.csv"))
    weeks = [int(f.name.split("_")[0].replace("week", "")) for f in files]
    return weeks


weeks = _discover_weeks()
if not weeks:
    st.warning("No weekly reports found in Models/0-FINAL-REPORTS.")
    st.stop()

week_labels = [f"Week {w}" for w in weeks]
selected_label = st.selectbox("Select week", week_labels, index=len(weeks) - 1)
selected_week = weeks[week_labels.index(selected_label)]


@st.cache_data
def _load_week(week: int):
    summary_file = REPORT_DIR / f"week{week}_all_props_summary.csv"
    df = pd.read_csv(summary_file)
    report_html = REPORT_DIR / f"week{week}_complete_props_report.html"
    report_txt = REPORT_DIR / f"week{week}_complete_props_report.txt"
    html_content = report_html.read_text(encoding="utf-8") if report_html.exists() else None
    txt_content = report_txt.read_text(encoding="utf-8") if report_txt.exists() else None
    return df, summary_file, html_content, report_html, txt_content, report_txt


df, summary_file, html_content, report_html, txt_content, report_txt = _load_week(selected_week)

col1, col2, col3 = st.columns(3)
col1.metric("Predictions", len(df))
col2.metric("Teams", df["team"].nunique())
col3.metric("Prop Types", df["prop_type"].nunique())

with st.sidebar:
    st.header("Filters")
    teams = st.multiselect("Team", sorted(df["team"].unique()))
    positions = st.multiselect("Position", sorted(df["position"].unique()))
    props = st.multiselect("Prop Type", sorted(df["prop_type"].unique()))
    min_pred, max_pred = st.slider(
        "Predicted yards",
        float(df["pred_yards"].min()),
        float(df["pred_yards"].max()),
        (float(df["pred_yards"].min()), float(df["pred_yards"].max())),
    )

filtered = df.copy()
if teams:
    filtered = filtered[filtered["team"].isin(teams)]
if positions:
    filtered = filtered[filtered["position"].isin(positions)]
if props:
    filtered = filtered[filtered["prop_type"].isin(props)]
filtered = filtered[(filtered["pred_yards"] >= min_pred) & (filtered["pred_yards"] <= max_pred)]

tabs = st.tabs(["Summary", "Visualization", "Full Report"])

with tabs[0]:
    st.dataframe(filtered, use_container_width=True)
    st.download_button("Download summary CSV", summary_file.read_bytes(), file_name=summary_file.name)

with tabs[1]:
    top_n = st.slider("Top N players", 5, min(25, len(filtered)), 10)
    chart_data = (
        filtered.nlargest(top_n, "pred_yards").set_index("full_name")["pred_yards"]
    )
    st.bar_chart(chart_data)

with tabs[2]:
    if html_content:
        st.components.v1.html(html_content, height=600, scrolling=True)
        st.download_button(
            "Download HTML report", report_html.read_bytes(), file_name=report_html.name
        )
    elif txt_content:
        st.text(txt_content)
        st.download_button(
            "Download text report", report_txt.read_bytes(), file_name=report_txt.name
        )
    else:
        st.info("No detailed report available for this week.")

