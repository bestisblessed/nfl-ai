import dash
from dash import html
import dash_bootstrap_components as dbc

# Register the home page
dash.register_page(__name__, path="/")

# Define the layout for the Home page
layout = dbc.Container(
    [
        dbc.Row(
            # dbc.Col(html.H1("Welcome to My NFL Dashboard", className="text-center text-light my-5"))
            dbc.Col(html.H2("NFLAI", style={'color': 'white', 'textAlign': 'center', 'marginTop': '36px', 'marginBottom': '40px'}))
            # dbc.Col(html.H1("NFLAI", className="text-center text-muted my-5", style={'textAlign': 'center', 'marginTop': '40px'}))
        ),
        dbc.Row(
            dbc.Col(
                html.P(
                    "Welcome to NFLAI.",
                    className="lead text-muted"
                    # style={'color': 'white', 'fontSize': '18px'}
                )
            )
        ),
    ],
    fluid=True,
)
