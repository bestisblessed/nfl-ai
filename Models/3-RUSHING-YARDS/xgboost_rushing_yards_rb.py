import os
import pandas as pd
from xgboost import XGBRegressor
import matplotlib.pyplot as plt
from tabulate import tabulate
import sys

print("=== XGBoost RB Rushing Yards Prediction ===")

# Get week number from command line argument
if len(sys.argv) > 1:
    try:
        week_num = int(sys.argv[1])
        if week_num < 1 or week_num > 18:
            print("Error: Week number must be between 1 and 18")
            sys.exit(1)
    except ValueError:
        print("Error: Week number must be a valid integer")
        sys.exit(1)
else:
    print("Error: Week number must be provided as command line argument")
    print("Usage: python xgboost_receiving_yards_rb_simple.py <week_number>")
    sys.exit(1)

print(f"Processing Week {week_num}...")
output_dir = f"predictions-week-{week_num}-RB"
os.makedirs(output_dir, exist_ok=True)

# Load data
hist = pd.read_csv("data/model_train.csv")
upcoming = pd.read_csv("data/upcoming_games.csv")
rosters = pd.read_csv("data/roster_2025.csv")
injured = None
injured_path = "data/injured_players.csv"
if os.path.exists(injured_path):
    try:
        injured = pd.read_csv(injured_path)["full_name"].dropna().astype(str).str.strip().tolist()
    except Exception:
        injured = None

# Clean historical data
for col in ["rush_attempts", "rush_yards", "season", "week"]:
    hist[col] = pd.to_numeric(hist[col], errors="coerce")
hist = hist.dropna(subset=["rush_yards"])

# Sort and create trailing features
hist = hist.sort_values(["player_id", "season", "week"]).reset_index(drop=True)
windows = [3, 5, 8, 12]

for w in windows:
    hist[f"attempts_l{w}"] = hist.groupby("player_id")["rush_attempts"].transform(lambda s: s.shift(1).rolling(w, min_periods=1).mean())
    hist[f"yards_l{w}"] = hist.groupby("player_id")["rush_yards"].transform(lambda s: s.shift(1).rolling(w, min_periods=1).mean())
    # robust
    hist[f"yards_median_l{w}"] = hist.groupby("player_id")["rush_yards"].transform(lambda s: s.shift(1).rolling(w, min_periods=1).median())

# Feature columns
feature_cols = ([f"attempts_l{w}" for w in windows] + 
               [f"yards_l{w}" for w in windows] +
               [f"yards_median_l{w}" for w in windows])

# Prepare training data
train = hist.dropna(subset=feature_cols + ["rush_yards"])
X = train[feature_cols]
y = train["rush_yards"]

# Train XGBoost model
model = XGBRegressor(
    n_estimators=500, learning_rate=0.05, max_depth=5,
    subsample=0.9, colsample_bytree=0.9, random_state=42,
    objective="reg:absoluteerror")
model.fit(X, y)

# Process upcoming games
if "team" not in upcoming.columns:
    # Convert home/away format to team/opp
    home = upcoming.rename(columns={"home_team": "team", "away_team": "opp"})
    away = upcoming.rename(columns={"away_team": "team", "home_team": "opp"})
    upcoming = pd.concat([home, away], ignore_index=True)

# Get current rosters for RBs only
current_rosters = rosters[rosters["season"] == 2025]
rb_rosters = current_rosters[current_rosters["position"] == "RB"].copy()
rb_rosters["player_id"] = rb_rosters["pfr_id"] + ".htm"

# Exclude injured players by full_name if provided
if injured:
    rb_rosters = rb_rosters[~rb_rosters["full_name"].isin(injured)]

# Get latest trailing features for each player
last_season_data = hist[hist["season"] == hist["season"].max()]
player_stats = last_season_data.sort_values(["player_id", "week"]).groupby("player_id").tail(1)
player_features = player_stats[["player_id"] + feature_cols]

# Merge rosters with historical features
rb_data = rb_rosters.merge(player_features, on="player_id", how="left")

# Filter out players without historical data (instead of filling with zeros)
rb_data = rb_data.dropna(subset=feature_cols)

print(f"Filtered to {len(rb_data)} RBs with historical data (removed {len(rb_rosters) - len(rb_data)} without history)")

# Attach to upcoming games
games = upcoming[["team", "opp"]].drop_duplicates()
predictions = games.merge(rb_data, on="team", how="inner")

# Make predictions
predictions["pred_rush_yards"] = model.predict(predictions[feature_cols])

# Sort by predicted yards
predictions = predictions.sort_values("pred_rush_yards", ascending=False)

# Save overall CSV with proper naming convention
output_cols = ["full_name", "team", "opp", "pred_rush_yards"] + feature_cols
predictions[output_cols].to_csv(f"{output_dir}/final_week{week_num}_RB_rush_yards_report.csv", index=False)

# Create game-by-game visualizations (preserve original schedule order)
unique_games = []
processed_games = set()

# Use the original upcoming games order to preserve schedule sequence
for _, row in upcoming[['team', 'opp']].drop_duplicates().iterrows():
    team1, team2 = row['team'], row['opp']
    game_key = f"{min(team1, team2)}_{max(team1, team2)}"  # Consistent key without changing order
    if game_key not in processed_games:
        unique_games.append((team1, team2))  # Keep original order
        processed_games.add(game_key)

print(f"\nCreating visualizations for {len(unique_games)} games...")
created_files = []

for i, (team1, team2) in enumerate(unique_games, 1):
    # Get RBs from both teams for this game
    game_rbs = predictions[
        ((predictions['team'] == team1) & (predictions['opp'] == team2)) |
        ((predictions['team'] == team2) & (predictions['opp'] == team1))
    ].copy()
    
    if not game_rbs.empty:
        game_rbs = game_rbs.sort_values('pred_rush_yards', ascending=False)
        
        # Create full PNG table
        team1_data = game_rbs[game_rbs['team'] == team1].sort_values('pred_rush_yards', ascending=False)
        team2_data = game_rbs[game_rbs['team'] == team2].sort_values('pred_rush_yards', ascending=False)
        
        max_players = max(len(team1_data), len(team2_data))
        fig_height = max(8, max_players * 0.6)
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, fig_height))
        fig.suptitle(f'Week {week_num} 2025: {team1} vs {team2} - RB Rushing Yards Predictions', 
                     fontsize=18, fontweight='bold', y=0.95)
        
        # Team 1 table
        ax1.axis('tight'); ax1.axis('off')
        if not team1_data.empty:
            table_data1 = [[row['full_name'], f"{row['pred_rush_yards']:.1f}", 
                           f"{row['attempts_l5']:.1f}", f"{row['yards_l5']:.1f}"] 
                          for _, row in team1_data.iterrows()]
            ax1.text(0.5, 0.9, team1, ha='center', va='center', fontsize=16, fontweight='bold', 
                    transform=ax1.transAxes, bbox=dict(boxstyle="round,pad=0.4", facecolor='#1E88E5', alpha=0.9), color='white')
            table1 = ax1.table(cellText=table_data1, colLabels=['Player', 'Pred Yards', 'Attempts L5', 'Yards L5'],
                               cellLoc='center', loc='center', bbox=[0.05, 0.05, 0.9, 0.8])
            table1.auto_set_font_size(False); table1.set_fontsize(10); table1.scale(1, 2.0)
            for j in range(4):
                table1[(0, j)].set_facecolor('#1E88E5'); table1[(0, j)].set_text_props(weight='bold', color='white')
            for k in range(1, len(table_data1) + 1):
                for j in range(4):
                    table1[(k, j)].set_facecolor('#E3F2FD')
                    if j == 1: table1[(k, j)].set_text_props(weight='bold')
        
        # Team 2 table
        ax2.axis('tight'); ax2.axis('off')
        if not team2_data.empty:
            table_data2 = [[row['full_name'], f"{row['pred_rush_yards']:.1f}", 
                           f"{row['attempts_l5']:.1f}", f"{row['yards_l5']:.1f}"] 
                          for _, row in team2_data.iterrows()]
            ax2.text(0.5, 0.9, team2, ha='center', va='center', fontsize=16, fontweight='bold', 
                    transform=ax2.transAxes, bbox=dict(boxstyle="round,pad=0.4", facecolor='#7B1FA2', alpha=0.9), color='white')
            table2 = ax2.table(cellText=table_data2, colLabels=['Player', 'Pred Yards', 'Attempts L5', 'Yards L5'],
                               cellLoc='center', loc='center', bbox=[0.05, 0.05, 0.9, 0.8])
            table2.auto_set_font_size(False); table2.set_fontsize(10); table2.scale(1, 2.0)
            for j in range(4):
                table2[(0, j)].set_facecolor('#7B1FA2'); table2[(0, j)].set_text_props(weight='bold', color='white')
            for k in range(1, len(table_data2) + 1):
                for j in range(4):
                    table2[(k, j)].set_facecolor('#F3E5F5')
                    if j == 1: table2[(k, j)].set_text_props(weight='bold')
        
        plt.tight_layout()
        filename_full = f"{output_dir}/game_{i:02d}_{team1}_vs_{team2}_RB_predictions.png"
        plt.savefig(filename_full, dpi=300, bbox_inches='tight', facecolor='white', pad_inches=0.3)
        plt.close()
        created_files.append(filename_full)
        
        # Create cleaned PNG table (name + yards only)
        fig_height = max(6, max_players * 0.5)
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, fig_height))
        fig.suptitle(f'{team1} vs {team2} | Week {week_num} 2025 | RB Projected Rushing Yards', 
                     fontsize=20, fontweight='bold', y=0.95, color='#2C3E50')
        
        # Team 1 cleaned
        ax1.axis('tight'); ax1.axis('off')
        if not team1_data.empty:
            clean_data1 = [[row['full_name'], f"{row['pred_rush_yards']:.1f}"] for _, row in team1_data.iterrows()]
            ax1.text(0.5, 0.92, team1, ha='center', va='center', fontsize=18, fontweight='bold', 
                    transform=ax1.transAxes, bbox=dict(boxstyle="round,pad=0.5", facecolor='#34495E'), color='white')
            clean_table1 = ax1.table(cellText=clean_data1, colLabels=['Player Name', 'Predicted Yards'],
                                    cellLoc='center', loc='center', bbox=[0.1, 0.05, 0.8, 0.8])
            clean_table1.auto_set_font_size(False); clean_table1.set_fontsize(12); clean_table1.scale(1, 2.4)
            for j in range(2):
                clean_table1[(0, j)].set_facecolor('#34495E'); clean_table1[(0, j)].set_text_props(weight='bold', color='white')
            for k in range(1, len(clean_data1) + 1):
                for j in range(2):
                    clean_table1[(k, j)].set_facecolor('#FAFAFA')
                    if j == 1: clean_table1[(k, j)].set_text_props(weight='bold', fontsize=14, color='#2C3E50')
        
        # Team 2 cleaned
        ax2.axis('tight'); ax2.axis('off')  
        if not team2_data.empty:
            clean_data2 = [[row['full_name'], f"{row['pred_rush_yards']:.1f}"] for _, row in team2_data.iterrows()]
            ax2.text(0.5, 0.92, team2, ha='center', va='center', fontsize=18, fontweight='bold', 
                    transform=ax2.transAxes, bbox=dict(boxstyle="round,pad=0.5", facecolor='#2C3E50'), color='white')
            clean_table2 = ax2.table(cellText=clean_data2, colLabels=['Player Name', 'Predicted Yards'],
                                    cellLoc='center', loc='center', bbox=[0.1, 0.05, 0.8, 0.8])
            clean_table2.auto_set_font_size(False); clean_table2.set_fontsize(12); clean_table2.scale(1, 2.4)
            for j in range(2):
                clean_table2[(0, j)].set_facecolor('#2C3E50'); clean_table2[(0, j)].set_text_props(weight='bold', color='white')
            for k in range(1, len(clean_data2) + 1):
                for j in range(2):
                    clean_table2[(k, j)].set_facecolor('#F8F9FA')
                    if j == 1: clean_table2[(k, j)].set_text_props(weight='bold', fontsize=14, color='#2C3E50')
        
        plt.tight_layout()
        filename_clean = f"{output_dir}/game_{i:02d}_{team1}_vs_{team2}_RB_predictions_cleaned.png"
        plt.savefig(filename_clean, dpi=300, bbox_inches='tight', facecolor='#FFFFFF', pad_inches=0.4)
        plt.close()
        created_files.append(filename_clean)
        
        # Create text table
        filename_text = f"{output_dir}/game_{i:02d}_{team1}_vs_{team2}_RB_predictions.txt"
        
        with open(filename_text, 'w') as f:
            f.write("=" * 80 + "\n")
            f.write(f"{team1} vs {team2} | Week {week_num} 2025 | RB Projected Rushing Yards\n")
            f.write("=" * 80 + "\n\n")
            
            # Create side-by-side tables
            team1_table_data = [[row['full_name'], f"{row['pred_rush_yards']:.1f}"] for _, row in team1_data.iterrows()]
            team2_table_data = [[row['full_name'], f"{row['pred_rush_yards']:.1f}"] for _, row in team2_data.iterrows()]
            
            team1_table = tabulate(team1_table_data, headers=[f"{team1} Player", "Pred Yards"], 
                                 tablefmt='outline', stralign='left') if team1_table_data else f"No {team1} RBs"
            team2_table = tabulate(team2_table_data, headers=[f"{team2} Player", "Pred Yards"], 
                                 tablefmt='outline', stralign='left') if team2_table_data else f"No {team2} RBs"
            
            # Write side by side
            team1_lines = team1_table.split('\n')
            team2_lines = team2_table.split('\n')
            max_lines = max(len(team1_lines), len(team2_lines))
            team1_lines += [''] * (max_lines - len(team1_lines))
            team2_lines += [''] * (max_lines - len(team2_lines))
            team1_width = max(len(line) for line in team1_lines)
            
            for line1, line2 in zip(team1_lines, team2_lines):
                f.write(f"{line1.ljust(team1_width)}    {line2}\n")
            
            f.write(f"\n{'='*80}\n")
            f.write("GAME SUMMARY\n")
            f.write("-" * 15 + "\n")
            f.write(f"Total RBs: {len(game_rbs)} ({len(team1_data)} {team1}, {len(team2_data)} {team2})\n")
            if len(game_rbs) > 0:
                top_rb = game_rbs.iloc[0]
                f.write(f"Top Projection: {top_rb['full_name']} ({top_rb['team']}) - {top_rb['pred_rush_yards']:.1f} yards\n")
            f.write("=" * 80 + "\n")
        
        created_files.append(filename_text)
        
        # Print to terminal
        print(f"\n{'='*80}")
        print(f"{team1} vs {team2} | Week {week_num} 2025 | RB Projected Rushing Yards")
        print(f"{'='*80}")
        for line1, line2 in zip(team1_lines, team2_lines):
            print(f"{line1.ljust(team1_width)}    {line2}")
        
        print(f"  Created game {i:02d}: {len(game_rbs)} RBs")

print(f"\n{len(predictions)} RB predictions saved")
print(f"Created {len(created_files)} files: {len(created_files)//3} games × (PNG + cleaned PNG + text)")
