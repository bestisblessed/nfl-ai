"""Gradio version of a small subset of the NFL AI app."""

import os

import gradio as gr
import pandas as pd
import plotly.express as px


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
teams_path = os.path.join(BASE_DIR, "..", "Streamlit", "data", "Teams.csv")
df = pd.read_csv(teams_path)

division_counts = df["Division"].value_counts().reset_index()
division_counts.columns = ["Division", "Count"]
fig = px.bar(
    division_counts,
    x="Division",
    y="Count",
    title="Teams by Division",
    labels={"Count": "Number of Teams"},
)

with gr.Blocks() as home:
    gr.Markdown("# NFL AI\nWelcome to NFL AI.")

with gr.Blocks() as team_analysis:
    gr.Plot(fig)

demo = gr.TabbedInterface([home, team_analysis], ["Home", "Team Analysis"])

if __name__ == "__main__":
    demo.launch()

