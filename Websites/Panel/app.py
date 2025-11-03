import pandas as pd
import panel as pn
from pathlib import Path

pn.extension("tabulator")

# Data loading
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
    standings = standings.sort_values(
        ["Division", "Wins", "Losses", "Ties"],
        ascending=[True, False, True, True],
    )
    return standings

teams, games = load_data()
standings = compute_standings(teams, games)

# Build UI
divisions = standings["Division"].unique()
tabs = pn.Tabs()
for division in divisions:
    df_div = standings[standings["Division"] == division].drop(columns="Division")
    tabs.append((division, pn.widgets.Tabulator(df_div, show_index=False)))

pn.panel(tabs).servable(title="2024 NFL Standings")
