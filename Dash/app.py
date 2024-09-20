import dash
import dash_bootstrap_components as dbc
from dash import dcc, html
import dash_labs as dl  # Dash Pages feature

# Initialize the Dash app
app = dash.Dash(__name__, use_pages=True, external_stylesheets=[dbc.themes.CYBORG])

# Define a basic navigation bar
navbar = dbc.NavbarSimple(
    children=[
        dbc.NavItem(dbc.NavLink("Home", href="/")),
        dbc.NavItem(dbc.NavLink("Team Analysis", href="/team-analysis")),
        dbc.NavItem(dbc.NavLink("Player Analysis", href="/player-analysis")),
        dbc.NavItem(dbc.NavLink("Player Analysis Testing", href="/player-analysis-testing")),
    ],
    brand="My NFL Dashboard",
    color="primary",
    dark=True,
)

# Main layout that includes the navbar and the dynamic page content
app.layout = dbc.Container(
    [
        navbar,  # Navbar at the top
        dcc.Location(id="url"),  # Tracks the current page
        dash.page_container  # Renders the content of the current page
    ],
    fluid=True
)

# Run the app
if __name__ == "__main__":
    app.run_server(debug=True)


# import dash
# from dash import html
# import dash_bootstrap_components as dbc

# # Bootstrap theme
# app = dash.Dash(__name__, external_stylesheets=[dbc.themes.SOLAR])
# # app = dash.Dash(__name__, external_stylesheets=[dbc.themes.CYBORG])
# # app = dash.Dash(__name__, external_stylesheets=[dbc.themes.VAPOR])

# # Define the layout using Dash Bootstrap Components
# app.layout = dbc.Container(
#     [
#         dbc.Row(
#             dbc.Col(
#                 html.H1("Welcome to My Dashboard", className="text-center text-light my-5")
#             )
#         ),
#         dbc.Row(
#             dbc.Col(
#                 html.P("This is a simple Dash homepage with a theme applied.", className="lead text-light")
#             )
#         ),
#         dbc.Row(
#             dbc.Col(
#                 html.P("You can add charts, tables, and interactive components here.", className="text-muted")
#             )
#         ),
#     ],
#     fluid=True,  # Makes the container fluid to fit the width of the screen
# )

# # Run the app
# if __name__ == '__main__':
#     app.run_server(debug=True)


# Basic Charts
# import dash
# from dash import html
# import dash_bootstrap_components as dbc
# from dash import dash_table
# import pandas as pd
# import sqlite3

# # Initialize Dash app with a theme
# app = dash.Dash(__name__, external_stylesheets=[dbc.themes.SOLAR])

# # Connect to the NFL dataset
# db_path = 'nfl.db'
# conn = sqlite3.connect(db_path)

# # 1. Against the Spread (ATS) Performance by Team per Year (2020-2024)
# ats_query = """
# SELECT season, home_team AS team, COUNT(*) AS games_played,
# SUM(CASE WHEN team_covered = home_team THEN 1 ELSE 0 END) AS ats_wins,
# ROUND(AVG(CASE WHEN team_covered = home_team THEN 1.0 ELSE 0 END), 2) AS ats_win_pct
# FROM Games
# WHERE season BETWEEN 2020 AND 2024
# GROUP BY season, home_team
# ORDER BY season, ats_win_pct DESC;
# """
# ats_df = pd.read_sql(ats_query, conn)

# # 2. Over/Under Performance per Year (2020-2024)
# ou_query = """
# SELECT season, home_team AS team, COUNT(*) AS games_played,
# SUM(CASE WHEN home_score + away_score > total_line THEN 1 ELSE 0 END) AS over_hits,
# SUM(CASE WHEN home_score + away_score < total_line THEN 1 ELSE 0 END) AS under_hits,
# ROUND(SUM(CASE WHEN home_score + away_score > total_line THEN 1 ELSE 0 END) * 1.0 / COUNT(*), 2) AS over_pct,
# ROUND(SUM(CASE WHEN home_score + away_score < total_line THEN 1 ELSE 0 END) * 1.0 / COUNT(*), 2) AS under_pct
# FROM Games
# WHERE season BETWEEN 2020 AND 2024
# GROUP BY season, home_team
# ORDER BY season, over_pct DESC;
# """
# ou_df = pd.read_sql(ou_query, conn)

# # 3. Rest Days Impact on ATS per Year (2020-2024)
# rest_query = """
# SELECT season, home_team AS team, home_rest, COUNT(*) AS games_played,
# SUM(CASE WHEN team_covered = home_team THEN 1 ELSE 0 END) AS ats_wins,
# ROUND(AVG(CASE WHEN team_covered = home_team THEN 1.0 ELSE 0 END), 2) AS ats_win_pct
# FROM Games
# WHERE season BETWEEN 2020 AND 2024
# GROUP BY season, home_team, home_rest
# ORDER BY season, home_rest ASC, ats_win_pct DESC;
# """
# rest_df = pd.read_sql(rest_query, conn)

# # Function to create the DataTable with additional features
# def create_table(df, title):
#     return dbc.Card(
#         [
#             dbc.CardHeader(html.H4(title, className="text-center")),
#             dash_table.DataTable(
#                 data=df.to_dict('records'),
#                 columns=[{"name": i, "id": i} for i in df.columns],
#                 style_table={'overflowX': 'auto', 'minWidth': '100%'},
#                 style_cell={'textAlign': 'center', 'padding': '5px', 'fontFamily': 'Arial', 'fontSize': '14px'},
#                 style_header={
#                     'backgroundColor': '#343a40', 
#                     'color': 'white', 
#                     'fontWeight': 'bold', 
#                     'textAlign': 'center'
#                 },
#                 style_data_conditional=[
#                     {
#                         'if': {'row_index': 'odd'},
#                         'backgroundColor': '#f9f9f9'
#                     },
#                     {
#                         'if': {'row_index': 'even'},
#                         'backgroundColor': '#e9ecef'
#                     }
#                 ],
#                 page_size=5,  # Pagination
#                 sort_action='native',  # Allow sorting
#                 filter_action='native',  # Enable filtering
#                 style_as_list_view=True,  # Slimmer table view
#                 tooltip_delay=0,
#                 tooltip_duration=None,
#                 tooltip_data=[
#                     {
#                         column: {'value': str(value), 'type': 'markdown'}
#                         for column, value in row.items()
#                     } for row in df.to_dict('records')
#                 ]
#             ),
#         ],
#         body=True, className="mt-4"
#     )

# # Define the layout using Dash Bootstrap Components
# app.layout = dbc.Container(
#     [
#         dbc.Row(
#             dbc.Col(html.H1("Advanced NFL Betting Trends by Year (2020-2024)", className="text-center text-light my-5"))
#         ),
        
#         # ATS Performance Table per Year
#         dbc.Row(
#             dbc.Col(create_table(ats_df, "Teams Against the Spread (ATS) Performance per Year (2020-2024)"))
#         ),
        
#         # Over/Under Performance Table per Year
#         dbc.Row(
#             dbc.Col(create_table(ou_df, "Teams Over/Under Performance per Year (2020-2024)"))
#         ),

#         # Rest Days Impact Table per Year
#         dbc.Row(
#             dbc.Col(create_table(rest_df, "Rest Days Impact on ATS per Year (2020-2024)"))
#         ),
#     ],
#     fluid=True,
# )

# # Run the app
# if __name__ == '__main__':
#     app.run_server(debug=True)
