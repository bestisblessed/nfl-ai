# 1. League scoring by week and league average.
# 2. Top 5 highest-total games.
# 3. Top 5 closest games by margin.
# 4. Top 10 offenses by points per game.
# 5. Top 10 point differential per game.
# 6. Average total points by week. (chart)

import sqlite3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

conn = sqlite3.connect("data/nfl.db")
games = pd.read_sql("SELECT game_id, season, CAST(week AS INT) as week, date, home_team, away_team, home_score, away_score FROM Games WHERE season=2025;", conn)
conn.close()

games["total"] = games["home_score"] + games["away_score"]
games["margin_abs"] = (games["home_score"] - games["away_score"]).abs()

latest_week = int(games["week"].max())

# League scoring
scoring_week = games.groupby("week", as_index=False)["total"].mean().rename(columns={"total":"avg_total"})
league_avg = float(scoring_week["avg_total"].mean())

# Highest scoring games
top_totals = games.nlargest(5, "total")[["week","game_id","home_team","home_score","away_team","away_score","total"]]

# Closest games
closest = games.nsmallest(5, "margin_abs")[["week","game_id","home_team","home_score","away_team","away_score","margin_abs"]]

# Team points for and against
home = games[["home_team","home_score","away_score"]].rename(columns={"home_team":"team","home_score":"pf","away_score":"pa"})
away = games[["away_team","home_score","away_score"]].rename(columns={"away_team":"team","away_score":"pf","home_score":"pa"})
team_pf_pa = pd.concat([home,away], ignore_index=True).groupby("team", as_index=False).agg(
    games=("pf","count"),
    pts_for=("pf","sum"),
    pts_against=("pa","sum"),
)
team_pf_pa["pts_per_game"] = team_pf_pa["pts_for"]/team_pf_pa["games"]
team_pf_pa = team_pf_pa.sort_values("pts_per_game", ascending=False).head(10)

# Team point differential per game
team_diff = pd.concat([home,away], ignore_index=True)
team_diff["diff"] = team_diff["pf"] - team_diff["pa"]
team_diff = team_diff.groupby("team", as_index=False).agg(games=("diff","count"), diff=("diff","sum"))
team_diff["diff_per_game"] = team_diff["diff"]/team_diff["games"]
team_diff = team_diff.sort_values("diff_per_game", ascending=False).head(10)

# Print concise markdown
def md(df):
    return df.to_markdown(index=False)
print(f"**Coverage:** 2025 Weeks 1–{latest_week}\n")
print(f"**League avg total points:** {league_avg:.1f}\n")
print("**Average total points by week:**")
print(scoring_week.to_markdown(index=False), "\n")
print("**Highest scoring games (Top 5):**")
print(md(top_totals), "\n")
print("**Closest games by margin (Top 5):**")
print(md(closest), "\n")
print("**Top scoring offenses by PPG (Top 10):**")
print(md(team_pf_pa[["team","games","pts_for","pts_per_game"]]), "\n")
print("**Best point differential per game (Top 10):**")
print(md(team_diff[["team","games","diff","diff_per_game"]]), "\n")

# Average total points by week. (chart)
plt.figure()
plt.plot(scoring_week["week"], scoring_week["avg_total"], marker="o")
plt.title("2025 NFL — Average Total Points per Game by Week")
plt.xlabel("Week")
plt.ylabel("Average total points")
plt.grid(True, linestyle=":")
plt.show()
