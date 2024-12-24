import dash
from dash import html
import dash_bootstrap_components as dbc

# Register the Team Analysis page
dash.register_page(__name__, path="/team-analysis")

# Define the layout for the Team Analysis page
layout = dbc.Container(
    [
        dbc.Row(
        dbc.Col(html.H2("Team Analysis", className="text-center text-white my-5"))
        ),
        dbc.Row(
            dbc.Col(html.P("This is the Team Analysis page.", className="lead text-light"))
        ),
        dbc.Row(
            dbc.Col(html.P("Detailed analysis for teams will go here.", className="text-muted"))
        ),
    ],
    fluid=True,
)
