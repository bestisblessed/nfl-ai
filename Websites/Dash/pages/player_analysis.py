'''
Bootstrap Grid System
Bootstrap is a grid-based layout system that divides the page into 12 columns. The dbc.Row creates horizontal sections, while dbc.Col specifies how much of the row width each component should take up.

Code Breakdown:
dbc.Row: Defines a new row on the page. Rows ensure that columns are aligned horizontally.
dbc.Col: Defines columns inside the row. The width argument specifies how many of the 12 available columns the component should occupy.
For example, dbc.Col(dcc.Graph(figure=heatmap_fig), width=6) means the heatmap will take up 6 out of 12 columns, and the radar chart next to it will also take 6 out of 12 columns, making them side-by-side with equal width.
'''

# Graph 1: Last 6 games ppr, receiving yards, touchdowns (rushing & receiving)
# Graph 2: Upcoming opponent matchup trends
# Graph 3: Longest reception stats (career, last 6 weeks, avg reception yards)
# Graph 4: Career yearly averages (to show progression or decline)

import plotly.express as px
import dash
from dash import html, dcc, Input, Output
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import pandas as pd
import sqlite3
from dash import dash_table

# Register the Team Analysis page
dash.register_page(__name__, path="/player-analysis")

# Set the hardcoded path for images
image_folder = '/assets/'

# Fetch player names
def fetch_player_names():
    conn = sqlite3.connect('data/nfl.db')
    query = """
    SELECT DISTINCT player_display_name
    FROM PlayerStats
    WHERE position IN ('WR', 'TE')
    AND season = 2023
    """
    player_names = pd.read_sql_query(query, conn)
    conn.close()
    return [{"label": name, "value": name} for name in player_names['player_display_name'].tolist()]

# Check if a player's image exists
def get_player_image(player_name):
    first_name, last_name = player_name.lower().split(' ')
    for ext in ['png', 'jpg', 'jpeg']:
        image_path = f"{image_folder}{first_name}_{last_name}.{ext}"
        return image_path

# Fetch last 6 games for the selected player
def fetch_last_6_games(player_name):
    conn = sqlite3.connect('data/nfl.db')
    query = f"""
    SELECT week, receiving_yards, receiving_tds, rushing_tds, fantasy_points_ppr
    FROM PlayerStats
    WHERE player_display_name = '{player_name}'
    AND season = 2023
    ORDER BY week DESC
    LIMIT 6;
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

# Fetch historical performance
def fetch_historical_performance(player_name, opponent_team_abbr):
    conn = sqlite3.connect('data/nfl.db')
    query = f"""
    SELECT season, week, receiving_yards, receiving_tds, fantasy_points_ppr
    FROM PlayerStats
    WHERE player_display_name = '{player_name}'
    AND (home_team = '{opponent_team_abbr}' OR away_team = '{opponent_team_abbr}')
    ORDER BY season, week;
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

# Fetch player's next opponent
def fetch_next_opponent(player_name):
    conn = sqlite3.connect('data/nfl.db')
    
    team_query = f"""
    SELECT DISTINCT player_current_team
    FROM PlayerStats
    WHERE player_display_name = '{player_name}'
    AND season = 2023;
    """
    team_df = pd.read_sql_query(team_query, conn)
    
    if team_df.empty:
        conn.close()
        return None
    
    team_abbr = team_df['player_current_team'].iloc[0]
    
    recent_game_query = f"""
    SELECT date
    FROM Games
    WHERE (home_team = '{team_abbr}' OR away_team = '{team_abbr}')
    AND home_score IS NOT NULL AND away_score IS NOT NULL
    ORDER BY date DESC
    LIMIT 1;
    """
    recent_game_df = pd.read_sql_query(recent_game_query, conn)
    
    if recent_game_df.empty:
        conn.close()
        return None
    
    recent_game_date = recent_game_df['date'].iloc[0]
    
    next_game_query = f"""
    SELECT home_team, away_team
    FROM Games
    WHERE (home_team = '{team_abbr}' OR away_team = '{team_abbr}')
    AND home_score IS NULL AND away_score IS NULL
    AND date > '{recent_game_date}'
    ORDER BY date ASC
    LIMIT 1;
    """
    next_game_df = pd.read_sql_query(next_game_query, conn)
    conn.close()
    
    if next_game_df.empty:
        return None
    
    if next_game_df['home_team'].iloc[0] == team_abbr:
        opponent_team_abbr = next_game_df['away_team'].iloc[0]
    else:
        opponent_team_abbr = next_game_df['home_team'].iloc[0]
    
    return opponent_team_abbr

# Get player's longest reception stats
def get_player_longest_reception_stats(player_name, opponent_team=None):
    all_stats_df = pd.read_csv('data/player_stats_pfr.csv')

    player_data = all_stats_df[all_stats_df['player'] == player_name]

    if 'rec_long' not in player_data.columns:
        return f"No reception data available for {player_name}"

    longest_reception = player_data['rec_long'].max()
    total_games = player_data.shape[0]

    opponent_insights = None
    opponent_data = None
    if opponent_team:
        opponent_data = player_data[player_data['opponent_team'] == opponent_team].drop_duplicates(subset=['game_id', 'rec_yds'])
        
        if opponent_data.empty:
            opponent_insights = f"No data available for {player_name} against {opponent_team}"
        else:
            opponent_insights = {
                "Opponent": opponent_team,
                "Longest Reception vs Opponent": opponent_data['rec_long'].max(),
                "Average Longest Reception vs Opponent": opponent_data['rec_long'].mean(),
                "Total Games vs Opponent": opponent_data.shape[0],
                "Games with 30+ Yard Reception vs Opponent": opponent_data[opponent_data['rec_long'] >= 30].shape[0],
                "Average Receptions per Game vs Opponent": opponent_data['rec'].mean(),
                "Average Receiving Yards per Game vs Opponent": opponent_data['rec_yds'].mean(),
                "Receiving Touchdowns vs Opponent": opponent_data['rec_td'].sum(),
                "Average Targets per Game vs Opponent": opponent_data['targets'].mean() if 'targets' in opponent_data.columns else "N/A",
            }

    else:
        opponent_insights = "No opponent provided."

    career_insights = {
        "Player": player_name,
        "Career Longest Reception": longest_reception,
        "Total Games Played": total_games,
    }

    return career_insights, opponent_insights, opponent_data

# Define the layout for the Player Analysis page
layout = dbc.Container(
    [
        dbc.Row(
            dbc.Col(html.H2("Player Analysis Testing", className="text-center text-white my-5"), style={'marginBottom': '30px'})
        ),
        
        dbc.Row(
            [
                dbc.Col(
                    dbc.Card(
                        [
                            dbc.CardBody(
                                [
                                    html.H4("Select Player", className="card-title"),
                                    dcc.Dropdown(
                                        id="player-dropdown",
                                        options=fetch_player_names(),
                                        value="Justin Jefferson",
                                        className="mb-3",
                                    ),
                                    html.Div(id="player-image")
                                ]
                            )
                        ]
                    ),
                    width=4,
                    style={'marginBottom': '30px'},
                ),
                
                dbc.Col(
                    dcc.Graph(id="last-6-games-graph"), 
                    width=8,
                    style={'marginBottom': '30px'},
                )
            ]
        ),

        dbc.Row(
            dbc.Col(
                html.Div(id="graph-3"),
                width=12,
                style={'marginBottom': '30px'}
            )
        ),

        dbc.Row(
            dbc.Col(
                html.P("Graph 4: Career yearly averages will go here.", className="text-white"),
                width=12,
                style={'marginBottom': '30px'}
            )
        ),
    ],
    fluid=True,
)

# Update player image
@dash.callback(
    Output("player-image", "children"),
    [Input("player-dropdown", "value")]
)
def update_player_image(player_name):
    image_src = get_player_image(player_name)
    if image_src:
        return html.Img(
            src=image_src, 
            style={
                'width': '350px', 
                'height': '450px',
                'display': 'block', 
                'margin': '0 auto'
            }
        )
    else:
        return html.P("No image available", style={'color': 'white', 'fontSize': '16px'})

# Update Graph 1
@dash.callback(
    Output("last-6-games-graph", "figure"),
    [Input("player-dropdown", "value")]
)
def update_last_6_games_graph(player_name):
    df = fetch_last_6_games(player_name)
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df['week'], y=df['receiving_yards'], mode='lines+markers', name='Receiving Yards'))
    fig.add_trace(go.Scatter(x=df['week'], y=df['fantasy_points_ppr'], mode='lines+markers', name='Fantasy Points (PPR)'))
    df['total_tds'] = df['receiving_tds'] + df['rushing_tds']
    fig.add_trace(go.Scatter(x=df['week'], y=df['total_tds'], mode='lines+markers', name='Total Touchdowns'))

    fig.update_layout(
        title=f"Last 6 Games for {player_name}",
        xaxis_title="Week",
        yaxis_title="Value",
        template="plotly_dark",
        legend_title="Metrics"
    )
    return fig

# Update Graph 3
@dash.callback(
    Output("graph-3", "children"),
    [Input("player-dropdown", "value")]
)
def update_matchup_stats(player_name):
    opponent_team_abbr = fetch_next_opponent(player_name)

    if opponent_team_abbr is None:
        return html.P(f"No upcoming opponent found for {player_name}.", style={'color': 'red'})

    career_insights, opponent_insights, opponent_data = get_player_longest_reception_stats(player_name, opponent_team_abbr)

    if isinstance(opponent_insights, str) and "No data available" in opponent_insights:
        return html.P(f"{player_name} has never played against {opponent_team_abbr}.", style={'color': 'red'})

    career_insights_rows = [
        dbc.Row([dbc.Col(html.B(key)), dbc.Col(value)]) for key, value in career_insights.items()
    ]

    if isinstance(opponent_insights, dict):
        opponent_insights_rows = [
            dbc.Row([dbc.Col(html.B(key)), dbc.Col(value)]) for key, value in opponent_insights.items()
        ]
    else:
        opponent_insights_rows = [html.P(opponent_insights)]

    if opponent_data is not None and not opponent_data.empty:
        fig = go.Figure([go.Bar(
            x=opponent_data['game_id'], 
            y=opponent_data['rec_yds'], 
            name="Receiving Yards",
            text=opponent_data['rec_yds'],
            textposition='outside'
        )])
        fig.update_layout(
            title=f"Receiving Yards vs {opponent_team_abbr}",
            xaxis_title="Game ID",
            yaxis_title="Receiving Yards",
            template="plotly_dark"
        )
        bar_chart = dcc.Graph(figure=fig)
    else:
        bar_chart = html.P(f"No games played against {opponent_team_abbr} to display stats.", style={'color': 'red'})

    return dbc.Row([
        dbc.Col(
            html.Div([
                html.H4(f"Career Insights for {player_name}", style={'fontSize': '16px', 'marginBottom': '10px'}),
                dbc.Container(career_insights_rows, fluid=True)
            ]),
            width=3
        ),
        dbc.Col(
            html.Div([
                html.H4(f"Opponent Insights vs {opponent_team_abbr}", style={'fontSize': '16px', 'marginBottom': '10px'}),
                dbc.Container(opponent_insights_rows, fluid=True)
            ]),
            width=3
        ),
        dbc.Col(
            html.Div([
                bar_chart
            ]),
            width=6
        )
    ], justify="center")
