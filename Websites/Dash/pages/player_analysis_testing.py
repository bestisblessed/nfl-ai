import dash
from dash import html, dcc, Input, Output
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import pandas as pd
import sqlite3
from dash import dash_table
import plotly.express as px

dash.register_page(__name__, path="/player-analysis-testing")

# Sample radar chart
radar_fig = px.line_polar(
    r=[1, 2, 3, 4, 5],  # Sample data
    theta=['N', 'NE', 'E', 'SE', 'S'],  # Directions like a rose plot
    line_close=True,
    title="Directional Passing Tendencies"
)

# Sample heatmap (use real data later)
heatmap_fig = px.density_heatmap(
    z=[1, 2, 3, 4],  # Dummy data
    x=[10, 20, 30, 40],
    y=[5, 15, 25, 35],
    title="Player Passing Hotspots"
)

# Sample histogram
histogram_fig = px.histogram(
    x=[5, 10, 15, 20, 25],  # Sample data for pass times
    title="Pass Distribution by Quarter"
)

# New sample figure to fill the remaining space
another_fig = px.scatter(
    x=[10, 20, 30, 40, 50],  # Sample data
    y=[3, 7, 2, 8, 1],
    title="Another Figure Example"
)

# Define the layout for the Player Analysis page
layout = dbc.Container(
    [
        # Title with extra space below
        dbc.Row(
            dbc.Col(html.H2("Player Analysis", className="text-center text-white my-5"), style={'marginBottom': '30px'})
        ),
        
        dbc.Row(
            [
                dbc.Col(
                    dbc.Card(
                        [
                            dbc.CardBody(
                                [
                                    html.H4("Pick a Player", className="card-title"),
                                    dcc.Dropdown(
                                        id="player-dropdown",
                                        options=[
                                            {"label": "Player 1", "value": "player1"},
                                            {"label": "Player 2", "value": "player2"},
                                            {"label": "Player 3", "value": "player3"},
                                        ],
                                        value="player1",  # Default selection
                                        className="mb-3",
                                        # style={'height': '300px'}  # Adjust this height as needed
                                    ),
                                    
                                    html.H5("Date Filter:", style={'marginTop': '20px'}),  
                                    dcc.DatePickerRange(
                                        id="date-picker",
                                        start_date="2020-01-01",
                                        end_date="2021-12-31",
                                        className="mb-3"
                                    ),
                                    
                                    html.H5("Time Filters:", style={'marginTop': '20px'}),  
                                    dcc.RangeSlider(
                                        id="time-slider",
                                        min=0,
                                        max=60,
                                        step=1,
                                        value=[15, 45],
                                        marks={i: f'{i} min' for i in range(0, 61, 10)}
                                    )
                                ],
                                # style={'height': '300px'}  # Increase the overall card height
                            )
                        ]
                    ),
                    width=4,  # Adjust player selection to take 1/3 of the row
                    style={'marginBottom': '30px'}
                    # style={'height': '100px', 'marginBottom': '30px'}  # Set the column to full height
                    # style={'height': '100%'}  # Column will use the full height within its 1/3 section
                ),
                # Add new column for the figure that takes up the remaining 2/3 of the row
                dbc.Col(
                    dcc.Graph(figure=another_fig), 
                    width=8,  # Use remaining 2/3 of the row
                    style={'marginBottom': '30px'}
                )
            ]
        ),

        dbc.Row(
            [
                dbc.Col(dcc.Graph(figure=heatmap_fig), width=6, style={'marginBottom': '30px'}),  # Space after Heatmap
                dbc.Col(dcc.Graph(figure=radar_fig), width=6, style={'marginBottom': '30px'})  # Space after Radar Chart
            ]
        ),

        dbc.Row(
            dbc.Col(dcc.Graph(figure=histogram_fig), width=12, style={'marginBottom': '30px'})  # Space after Histogram
        ),
        
        # Space for more advanced filters and custom insights
        dbc.Row(
            dbc.Col(
                html.P("Detailed analysis for players will go here.", className="text-muted", style={'marginTop': '30px'})  # Add space before detailed analysis
            )
        ),
    ],
    fluid=True,
)