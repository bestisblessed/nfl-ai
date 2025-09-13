from pathlib import Path
import pandas as pd
from shiny import App, ui, render

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "Websites" / "Streamlit" / "data"

def load_data():
    teams = pd.read_csv(DATA_DIR / "Teams.csv")
    games = pd.read_csv(DATA_DIR / "Games.csv")
    games = games[(games["season"] == 2024) & (games["week"].between(1, 18))]
    return teams, games

def compute_standings(teams: pd.DataFrame, games: pd.DataFrame) -> pd.DataFrame:
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
    return standings

teams, games = load_data()
standings = compute_standings(teams, games)

app_ui = ui.page_fluid(
    ui.h2("2024 NFL Season Division Standings"),
    ui.input_select("division", "Division", sorted(standings["Division"].unique())),
    ui.output_table("table"),
)

def server(input, output, session):
    @output
    @render.table
    def table():
        division = input.division()
        df = standings[standings["Division"] == division].drop(columns="Division")
        df = df.sort_values(["Wins", "Losses", "Ties"], ascending=[False, True, True])
        return df

app = App(app_ui, server)
