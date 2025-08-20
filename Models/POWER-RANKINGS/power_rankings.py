import pandas as pd
import numpy as np
from scipy.stats import norm
import sqlite3
import matplotlib.pyplot as plt
import matplotlib.backends.backend_agg as agg
import os

os.makedirs("output", exist_ok=True)

# Elo parameters
k_factor = 20
hfa = 2.5
vig = 1.04

# Ask user for week number for file naming
week_number = input("Enter the week number for these matchups (e.g., 1): ").strip()
if not week_number.isdigit():
    week_number = "1"
    
# Download and process historical data from the database
# Use absolute path for database
DB_PATH = "/Users/td/Code/nfl-ai/Models/data/nfl.db"
conn = sqlite3.connect(DB_PATH)
query = "SELECT home_team, away_team, home_score, away_score, season, week, game_type FROM Games ORDER BY season, week"
nfl_data = pd.read_sql_query(query, conn)
conn.close()

print(f"Initial data shape: {nfl_data.shape}")

# Ensure 'season' and 'week' are numeric and handle potential NaNs
nfl_data['season'] = pd.to_numeric(nfl_data['season'], errors='coerce')
nfl_data['week'] = pd.to_numeric(nfl_data['week'], errors='coerce')
nfl_data.dropna(subset=['season', 'week'], inplace=True)
nfl_data['season'] = nfl_data['season'].astype(int)
nfl_data['week'] = nfl_data['week'].astype(int)
print(f"Data shape after numeric conversion and NaN drop: {nfl_data.shape}")

# Filter for regular season games and weeks 1-18
nfl_data = nfl_data[nfl_data["game_type"] == "REG"]
print(f"Data shape after game_type filter: {nfl_data.shape}")
nfl_data = nfl_data[nfl_data["week"] <= 18]
print(f"Data shape after week filter: {nfl_data.shape}")

# Initialize Elo ratings for all teams
all_teams = pd.concat([nfl_data["home_team"], nfl_data["away_team"]]).unique()
team_elos = {team: 1500 for team in all_teams}

# Elo update loop
for idx, row in nfl_data.iterrows():
    home = row["home_team"]
    away = row["away_team"]
    home_score = row["home_score"]
    away_score = row["away_score"]
    home_elo = team_elos.get(home, 1500)
    away_elo = team_elos.get(away, 1500)
    home_elo_adj = home_elo + hfa
    expected_home = 1 / (1 + 10 ** ((away_elo - home_elo_adj) / 400))
    expected_away = 1 / (1 + 10 ** ((home_elo_adj - away_elo) / 400))
    if home_score > away_score:
        score_diff = home_score - away_score
        actual_home = 1
        actual_away = 0
    elif away_score > home_score:
        score_diff = away_score - home_score
        actual_home = 0
        actual_away = 1
    else:
        score_diff = 0
        actual_home = 0.5
        actual_away = 0.5
    k_adj_factor = 1 + np.log(abs(score_diff) + 1) / 10
    team_elos[home] = home_elo + k_factor * k_adj_factor * (actual_home - expected_home)
    team_elos[away] = away_elo + k_factor * k_adj_factor * (actual_away - expected_away)

# Power rankings
power_rankings = sorted(team_elos.items(), key=lambda x: x[1], reverse=True)
print("\nNFL Power Rankings (Full 32 Teams):")
for team, elo in power_rankings:    
    print(f"{team}: {round(elo):.0f}")

# Export power rankings to CSV (rounded Elo)
power_rankings_csv_path = f"output/power_rankings_week{week_number}.csv"
power_rankings_png_path = f"output/power_rankings_week{week_number}.png"
power_rankings_df = pd.DataFrame([(team, round(elo)) for team, elo in power_rankings], columns=["Team", "Elo"])
power_rankings_df.to_csv(power_rankings_csv_path, index=False)

# Export power rankings to PNG with formatting (rounded Elo)
try:
    import matplotlib.patches as mpatches
    import matplotlib.image as mpimg
    fig, ax = plt.subplots(figsize=(6, len(power_rankings_df)*0.4+2))
    ax.axis('off')
    tbl = ax.table(cellText=power_rankings_df.values, colLabels=power_rankings_df.columns, loc='center', cellLoc='center', cellColours=[["#f0f6fa" if i%2==0 else "#e3e8ee" for _ in power_rankings_df.columns] for i in range(len(power_rankings_df))])
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(12)
    tbl.scale(1, 1.3)
    for (row, col), cell in tbl.get_celld().items():
        if row == 0:
            cell.set_text_props(weight='bold', color='#002244')
            cell.set_facecolor('#d6e4f0')
        if col == 0 and row > 0:
            cell.set_text_props(weight='bold')
    plt.title(f"NFL Power Rankings (Elo) - Week {week_number}", fontsize=16, weight='bold', color='#002244', pad=20)
    for i, team in enumerate(power_rankings_df['Team']):
        logo_path = f"logos/{team}.png"
        if os.path.exists(logo_path):
            img = mpimg.imread(logo_path)
            ax.imshow(img, aspect='auto', extent=(0.05, 0.13, len(power_rankings_df)-i-0.7, len(power_rankings_df)-i-0.3), zorder=10)
    plt.tight_layout()
    plt.savefig(power_rankings_png_path, bbox_inches='tight', dpi=200)
    plt.close(fig)
    print(f"\nPower rankings table image saved as {os.path.abspath(power_rankings_png_path)}")
except Exception as e:
    print(f"Could not save power rankings table as image: {e}")

# Generate betting lines for Week 1 of the upcoming season
latest_season = nfl_data["season"].max()
week1_query = f"SELECT home_team, away_team, home_score, away_score FROM Games WHERE season = {latest_season + 1} AND week = '01' AND game_type = 'REG'"
conn = sqlite3.connect(DB_PATH)
upcoming_games_df = pd.read_sql_query(week1_query, conn)
conn.close()

results = []
if not upcoming_games_df.empty:
    for idx, row in upcoming_games_df.iterrows():
        home = row["home_team"]
        away = row["away_team"]
        home_elo = team_elos.get(home, 1500)
        away_elo = team_elos.get(away, 1500)
        home_elo_adj = home_elo + hfa
        elo_diff = home_elo_adj - away_elo
        point_spread = elo_diff / 25
        implied_prob_home_cover = norm.cdf(0, loc=-point_spread, scale=13.8)
        implied_prob_home_cover = min(max(implied_prob_home_cover, 0), 1)
        odds_home = implied_prob_home_cover * vig
        odds_away = (1 - implied_prob_home_cover) * vig
        # Convert to American odds
        if odds_home >= 1:
            home_odds = -10000
        elif odds_home > 0.5:
            home_odds = int(-100 * (odds_home / (1 - odds_home)))
        else:
            home_odds = int((1 - odds_home) / odds_home * 100)
        if odds_away >= 1:
            away_odds = -10000
        elif odds_away > 0.5:
            away_odds = int(-100 * (odds_away / (1 - odds_away)))
        else:
            away_odds = int((1 - odds_away) / odds_away * 100)
        results.append({
            "Home Team": home,
            "Away Team": away,
            "Home Spread": f"{-point_spread:+.2f}",
            "Home Odds": f"+{home_odds}" if home_odds > 0 else str(home_odds),
            "Away Odds": f"+{away_odds}" if away_odds > 0 else str(away_odds)
        })
else:
    # Try to read upcoming games from CSV
    upcoming_games_path = "upcoming_games.csv"
    if os.path.exists(upcoming_games_path):
        print(f"Using upcoming games from {upcoming_games_path} for predictions:")
        upcoming_games_file_df = pd.read_csv(upcoming_games_path)
        for _, row in upcoming_games_file_df.iterrows():
            home = row["home_team"]
            away = row["away_team"]
            home_elo = team_elos.get(home, 1500)
            away_elo = team_elos.get(away, 1500)
            home_elo_adj = home_elo + hfa
            elo_diff = home_elo_adj - away_elo
            point_spread = elo_diff / 25
            implied_prob_home_cover = norm.cdf(0, loc=-point_spread, scale=13.8)
            implied_prob_home_cover = min(max(implied_prob_home_cover, 0), 1)
            odds_home = implied_prob_home_cover * vig
            odds_away = (1 - implied_prob_home_cover) * vig
            if odds_home >= 1:
                home_odds = -10000
            elif odds_home > 0.5:
                home_odds = int(-100 * (odds_home / (1 - odds_home)))
            else:
                home_odds = int((1 - odds_home) / odds_home * 100)
            if odds_away >= 1:
                away_odds = -10000
            elif odds_away > 0.5:
                away_odds = int(-100 * (odds_away / (1 - odds_away)))
            else:
                away_odds = int((1 - odds_away) / odds_away * 100)
            results.append({
                "Home Team": home,
                "Away Team": away,
                "Home Spread": f"{-point_spread:+.2f}",
                "Home Odds": f"+{home_odds}" if home_odds > 0 else str(home_odds),
                "Away Odds": f"+{away_odds}" if away_odds > 0 else str(away_odds)
            })
    else:
        print(f"No Week 1 games found for the upcoming season in the database and no upcoming_games.csv found at {upcoming_games_path}.")

# Export to CSV and image
if results:
    df_results = pd.DataFrame(results)
    df_results = df_results[["Home Team", "Away Team", "Home Spread", "Home Odds", "Away Odds"]]
    csv_path = f"output/2025_week{week_number}_model_lines.csv"
    png_path = f"output/2025_week{week_number}_model_lines.png"
    df_results.to_csv(csv_path, index=False)
    print(f"Model lines exported to {csv_path}")
    print("\nModel Lines Table:")
    print(df_results.to_string(index=False))
    try:
        fig, ax = plt.subplots(figsize=(12, len(df_results)*0.5+2))
        ax.axis('off')
        cell_colours = [["#f0f6fa" if i%2==0 else "#e3e8ee" for _ in df_results.columns] for i in range(len(df_results))]
        favorite_cells = []
        for i, row in df_results.iterrows():
            spread = float(row["Home Spread"])
            if spread < 0:
                cell_colours[i][0] = "#0073CF"
                favorite_cells.append((i+1, 0))
            elif spread > 0:
                cell_colours[i][1] = "#0073CF"
                favorite_cells.append((i+1, 1))
        tbl = ax.table(cellText=df_results.values, colLabels=df_results.columns, loc='center', cellLoc='center', cellColours=cell_colours)
        tbl.auto_set_font_size(False)
        tbl.set_fontsize(12)
        tbl.scale(1, 1.3)
        for (row, col), cell in tbl.get_celld().items():
            if row == 0:
                cell.set_text_props(weight='bold', color='#002244')
                cell.set_facecolor('#d6e4f0')
        for (row, col) in favorite_cells:
            cell = tbl[row, col]
            cell.set_text_props(weight='bold', color='white')
        plt.title(f"NFL 2025 Week {week_number} Model Lines", fontsize=16, weight='bold', color='#002244', pad=20)
        from matplotlib.patches import Patch
        legend_patch = Patch(facecolor='#0073CF', edgecolor='none', label='Highlight = Favorite')
        plt.legend(handles=[legend_patch], loc='lower center', bbox_to_anchor=(0.5, -0.08), fontsize=12, frameon=False)
        plt.tight_layout()
        plt.savefig(png_path, bbox_inches='tight', dpi=200)
        plt.close(fig)
        print(f"\nTable image saved as {png_path}")
    except Exception as e:
        print(f"Could not save table as image: {e}")
