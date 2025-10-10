import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output
import pandas as pd
from pathlib import Path

dash.register_page(__name__, path="/standings", name="Standings")

ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = ROOT / "Websites" / "Streamlit" / "data"

teams = pd.read_csv(DATA_DIR / "Teams.csv")
games = pd.read_csv(DATA_DIR / "Games.csv")
games = games[(games["season"] == 2024) & (games["week"].between(1, 18))]

team_wins = {team: 0 for team in teams["TeamID"]}
team_losses = {team: 0 for team in teams["TeamID"]}
team_ties = {team: 0 for team in teams["TeamID"]}
for _, game in games.iterrows():
    away_team = game["away_team"]
    home_team = game["home_team"]
    away_score = game["away_score"]
    home_score = game["home_score"]
    if away_score > home_score:
        team_wins[away_team] += 1
        team_losses[home_team] += 1
    elif home_score > away_score:
        team_wins[home_team] += 1
        team_losses[away_team] += 1
    else:
        team_ties[away_team] += 1
        team_ties[home_team] += 1
standings = pd.DataFrame({
    "TeamID": team_wins.keys(),
    "Wins": team_wins.values(),
    "Losses": team_losses.values(),
    "Ties": team_ties.values(),
})
standings = standings.merge(teams[["TeamID", "Division"]], on="TeamID")

layout = html.Div([
    html.H1("2024 NFL Season Division Standings"),
    dcc.Dropdown(
        id="division-dropdown",
        options=[{"label": d, "value": d} for d in sorted(standings["Division"].unique())],
        value=sorted(standings["Division"].unique())[0]
    ),
    dash_table.DataTable(
        id="standings-table",
        columns=[{"name": c, "id": c} for c in ["TeamID", "Wins", "Losses", "Ties"]],
        data=[],
    ),
])

@dash.callback(Output("standings-table", "data"), Input("division-dropdown", "value"))
def update_table(division):
    df = standings[standings["Division"] == division].sort_values(
        ["Wins", "Losses", "Ties"], ascending=[False, True, True]
    )
    return df[["TeamID", "Wins", "Losses", "Ties"]].to_dict("records")
