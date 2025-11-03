import os

import dash
from dash import dcc, html
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px

# Register the Team Analysis page
dash.register_page(__name__, path="/team-analysis")

# Load team data from the Streamlit app to reuse for visualization
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
teams_path = os.path.join(BASE_DIR, "..", "..", "Streamlit", "data", "Teams.csv")
df_teams = pd.read_csv(teams_path)

# Prepare a simple bar chart showing the number of teams in each division
division_counts = df_teams["Division"].value_counts().reset_index()
division_counts.columns = ["Division", "Count"]
fig = px.bar(
    division_counts,
    x="Division",
    y="Count",
    title="Teams by Division",
    labels={"Count": "Number of Teams"},
)

# Define the layout for the Team Analysis page
layout = dbc.Container(
    [
        dbc.Row(
            dbc.Col(html.H2("Team Analysis", className="text-center text-white my-5"))
        ),
        dbc.Row(
            dbc.Col(dcc.Graph(figure=fig))
        ),
    ],
    fluid=True,
)
