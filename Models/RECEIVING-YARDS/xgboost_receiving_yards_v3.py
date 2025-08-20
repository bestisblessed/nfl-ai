# run_receiving_from_upcoming.py
# Predict future receiving yards WITHOUT inventing targets/receptions.
# Approach: train on historical per-game rows using ONLY prior (pre-game) info:
#   - trailing averages per player: targets_l5, receptions_l5, yards_l5 (computed with shift)
# Then, for an upcoming schedule (upcoming_games.csv), pull each team's active receivers from last season
# and attach their latest trailing averages (from 2024). Feed those into the model to predict Week 1, 2025.

import os
import pandas as pd
from xgboost import XGBRegressor
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.colors import LinearSegmentedColormap
from tabulate import tabulate

print("=== XGBoost Receiving Yards Prediction with Current Rosters ===")

# Ask user for week number
try:
    week_num = int(input("Enter the week number (1-18): "))
    if week_num < 1 or week_num > 18:
        print("Invalid week number. Using week 1 as default.")
        week_num = 1
except (ValueError, KeyboardInterrupt):
    print("Using week 1 as default.")
    week_num = 1

# Create output directory based on week
output_dir = f"predictions-week-{week_num}"
print(f"Saving files to: {output_dir}/")

# ---------------------------
# Function to create game visualization tables
# ---------------------------
def create_game_wr_table(game_data, team1, team2, game_num):
    """Create a visualization with separate tables for each team side by side"""
    
    # Split data by team and sort by predicted yards (highest to lowest)
    team1_data = game_data[game_data['team'] == team1].sort_values('pred_rec_yards', ascending=False)
    team2_data = game_data[game_data['team'] == team2].sort_values('pred_rec_yards', ascending=False)
    
    # Calculate figure size based on the team with more players
    max_players = max(len(team1_data), len(team2_data))
    fig_height = max(8, max_players * 0.6)
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, fig_height))
    
    # Title for the entire figure
    fig.suptitle(f'Week {week_num} 2025: {team1} vs {team2} - WR Receiving Yards Predictions', 
                 fontsize=18, fontweight='bold', y=0.95)
    
    # Helper function to create a team table
    def create_team_table(ax, team_data, team_name, team_color):
        ax.axis('tight')
        ax.axis('off')
        
        if team_data.empty:
            ax.text(0.5, 0.5, f'No {team_name} WRs found', 
                   ha='center', va='center', fontsize=14, transform=ax.transAxes)
            return
        
        # Prepare data for table
        table_data = []
        for _, row in team_data.iterrows():
            table_data.append([
                row['player_name'],
                f"{row['pred_rec_yards']:.1f}",
                f"{row['targets_l5']:.1f}",
                f"{row['receptions_l5']:.1f}",
                f"{row['yards_l5']:.1f}"
            ])
        
        # Add team name title first (above the table)
        header_colors = {team1: '#1E88E5', team2: '#7B1FA2'}  # Blue for team1, Purple for team2
        header_color = header_colors.get(team_name, '#4CAF50')
        
        ax.text(0.5, 0.9, team_name, ha='center', va='center', 
               fontsize=16, fontweight='bold', transform=ax.transAxes,
               bbox=dict(boxstyle="round,pad=0.4", facecolor=header_color, alpha=0.9, edgecolor='white', linewidth=2),
               color='white')
        
        # Create table with more space at top for title
        table = ax.table(cellText=table_data,
                        colLabels=['Player Name', 'Predicted Yards', 'Targets L5', 'Receptions L5', 'Yards L5'],
                        cellLoc='center',
                        loc='center',
                        bbox=[0.05, 0.05, 0.9, 0.8])  # Adjusted bbox to leave more space at top
        
        # Style the table
        table.auto_set_font_size(False)
        table.set_fontsize(10)
        table.scale(1, 2.0)
        
        # Style header with team colors
        for i in range(5):
            table[(0, i)].set_facecolor(header_color)
            table[(0, i)].set_text_props(weight='bold', color='white', fontsize=9)
        
        # Style all data rows with team color and bold predicted yards column
        for i in range(1, len(table_data) + 1):
            for j in range(5):
                table[(i, j)].set_facecolor(team_color)
                if j == 1:  # Predicted yards column - make bold
                    table[(i, j)].set_text_props(weight='bold')
    
    # Team colors for row backgrounds
    team_colors = {team1: '#E3F2FD', team2: '#F3E5F5'}  # Light blue for team1, Light purple for team2
    
    # Create tables for each team
    create_team_table(ax1, team1_data, team1, team_colors[team1])
    create_team_table(ax2, team2_data, team2, team_colors[team2])
    
    # Save the figure
    plt.tight_layout()
    filename = f"{output_dir}/game_{game_num:02d}_{team1}_vs_{team2}_WR_predictions.png"
    plt.savefig(filename, dpi=300, bbox_inches='tight', facecolor='white', pad_inches=0.3)
    plt.close()
    return filename

def create_game_wr_table_cleaned(game_data, team1, team2, game_num):
    """Create a cleaned visualization with only player names and predicted yards"""
    
    # Split data by team and sort by predicted yards (highest to lowest)
    team1_data = game_data[game_data['team'] == team1].sort_values('pred_rec_yards', ascending=False)
    team2_data = game_data[game_data['team'] == team2].sort_values('pred_rec_yards', ascending=False)
    
    # Calculate figure size based on the team with more players
    max_players = max(len(team1_data), len(team2_data))
    fig_height = max(6, max_players * 0.5)
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, fig_height))
    
    # Professional title for the cleaned version
    fig.suptitle(f'{team1} vs {team2} | Week {week_num} 2025 | Projected Receiving Yards', 
                 fontsize=20, fontweight='bold', y=0.95, color='#2C3E50')
    
    # Helper function to create a clean team table
    def create_team_table_cleaned(ax, team_data, team_name, team_color):
        ax.axis('tight')
        ax.axis('off')
        
        if team_data.empty:
            ax.text(0.5, 0.5, f'No {team_name} WRs found', 
                   ha='center', va='center', fontsize=14, transform=ax.transAxes)
            return
        
        # Prepare data for table - only player name and predicted yards
        table_data = []
        for _, row in team_data.iterrows():
            table_data.append([
                row['player_name'],
                f"{row['pred_rec_yards']:.1f}"
            ])
        
        # Professional team name styling
        header_colors = {team1: '#34495E', team2: '#2C3E50'}  # Professional dark grays
        header_color = header_colors.get(team_name, '#34495E')
        
        ax.text(0.5, 0.92, team_name, ha='center', va='center', 
               fontsize=18, fontweight='bold', transform=ax.transAxes,
               bbox=dict(boxstyle="round,pad=0.5", facecolor=header_color, alpha=1.0, edgecolor='none'),
               color='white')
        
        # Create table with only 2 columns
        table = ax.table(cellText=table_data,
                        colLabels=['Player Name', 'Predicted Yards'],
                        cellLoc='center',
                        loc='center',
                        bbox=[0.1, 0.05, 0.8, 0.8])  # Adjusted bbox for 2 columns
        
        # Professional table styling
        table.auto_set_font_size(False)
        table.set_fontsize(12)
        table.scale(1, 2.4)     # Even taller rows for premium look
        
        # Professional header styling
        for i in range(2):  # Only 2 columns now
            table[(0, i)].set_facecolor(header_color)
            table[(0, i)].set_text_props(weight='bold', color='white', fontsize=12)
            table[(0, i)].set_edgecolor('#BDC3C7')
            table[(0, i)].set_linewidth(1)
        
        # Professional data row styling
        for i in range(1, len(table_data) + 1):
            for j in range(2):  # Only 2 columns now
                table[(i, j)].set_facecolor(team_color)
                table[(i, j)].set_edgecolor('#E8E8E8')
                table[(i, j)].set_linewidth(0.5)
                if j == 1:  # Predicted yards column - make bold and larger
                    table[(i, j)].set_text_props(weight='bold', fontsize=14, color='#2C3E50')
                else:  # Player name column
                    table[(i, j)].set_text_props(fontsize=12, color='#34495E')
    
    # Professional team background colors - subtle and clean
    team_colors = {team1: '#FAFAFA', team2: '#F8F9FA'}  # Very light grays for professional look
    
    # Create tables for each team
    create_team_table_cleaned(ax1, team1_data, team1, team_colors[team1])
    create_team_table_cleaned(ax2, team2_data, team2, team_colors[team2])
    
    # Professional figure finishing touches
    plt.tight_layout()
    fig.patch.set_facecolor('#FFFFFF')  # Clean white background
    
    filename = f"{output_dir}/game_{game_num:02d}_{team1}_vs_{team2}_WR_predictions_cleaned.png"
    plt.savefig(filename, dpi=300, bbox_inches='tight', facecolor='#FFFFFF', 
                edgecolor='none', pad_inches=0.4, transparent=False)
    plt.close()
    return filename

def create_game_wr_table_text(game_data, team1, team2, game_num):
    """Create a text-based tabulated table file with teams side by side"""
    
    # Split data by team and sort by predicted yards (highest to lowest)
    team1_data = game_data[game_data['team'] == team1].sort_values('pred_rec_yards', ascending=False)
    team2_data = game_data[game_data['team'] == team2].sort_values('pred_rec_yards', ascending=False)
    
    filename = f"{output_dir}/game_{game_num:02d}_{team1}_vs_{team2}_WR_predictions.txt"
    
    with open(filename, 'w') as f:
        # Write header
        f.write("=" * 80 + "\n")
        f.write(f"{team1} vs {team2} | Week {week_num} 2025 | Projected Receiving Yards\n")
        f.write("=" * 80 + "\n\n")
        
        # Prepare data for side-by-side tables
        team1_table_data = []
        for _, row in team1_data.iterrows():
            team1_table_data.append([
                row['player_name'], 
                f"{row['pred_rec_yards']:.1f}"
            ])
        
        team2_table_data = []
        for _, row in team2_data.iterrows():
            team2_table_data.append([
                row['player_name'], 
                f"{row['pred_rec_yards']:.1f}"
            ])
        
        # Create individual tables for each team
        if team1_table_data:
            team1_table = tabulate(
                team1_table_data,
                headers=[f"{team1} Player", "Pred Yards"],
                tablefmt='outline',
                stralign='left',
                numalign='center'
            )
        else:
            team1_table = f"No {team1} WRs found"
        
        if team2_table_data:
            team2_table = tabulate(
                team2_table_data,
                headers=[f"{team2} Player", "Pred Yards"],
                tablefmt='outline',
                stralign='left',
                numalign='center'
            )
        else:
            team2_table = f"No {team2} WRs found"
        
        # Split tables into lines for side-by-side display
        team1_lines = team1_table.split('\n')
        team2_lines = team2_table.split('\n')
        
        # Pad the shorter table with empty lines
        max_lines = max(len(team1_lines), len(team2_lines))
        team1_lines += [''] * (max_lines - len(team1_lines))
        team2_lines += [''] * (max_lines - len(team2_lines))
        
        # Calculate column width (find the longest line in team1)
        team1_width = max(len(line) for line in team1_lines) if team1_lines else 0
        
        # Prepare content for both printing and writing
        content_lines = []
        
        # Write side-by-side tables
        for line1, line2 in zip(team1_lines, team2_lines):
            # Pad team1 line to consistent width and add spacing
            padded_line1 = line1.ljust(team1_width)
            content_line = f"{padded_line1}    {line2}"
            content_lines.append(content_line)
            f.write(content_line + "\n")
        
        # Summary section
        summary_lines = [
            "",
            "=" * 80,
            "GAME SUMMARY",
            "-" * 15,
            f"Total WRs: {len(team1_data) + len(team2_data)} ({len(team1_data)} {team1}, {len(team2_data)} {team2})"
        ]
        
        if len(team1_data) + len(team2_data) > 0:
            top_wr = game_data.loc[game_data['pred_rec_yards'].idxmax()]
            summary_lines.append(f"Top Projection: {top_wr['player_name']} ({top_wr['team']}) - {top_wr['pred_rec_yards']:.1f} yards")
        
        summary_lines.append("=" * 80)
        
        for line in summary_lines:
            f.write(line + "\n")
    
    # Print to terminal as well
    print(f"\n{'='*80}")
    print(f"{team1} vs {team2} | Week {week_num} 2025 | Projected Receiving Yards")
    print(f"{'='*80}")
    print()
    
    for content_line in content_lines:
        print(content_line)
    
    for summary_line in summary_lines:
        print(summary_line)
    
    return filename

# ---------------------------
# 0) Paths
# ---------------------------
HIST = "data/model_train.csv"                     # pre-processed training data
UPCOMING = "data/upcoming_games.csv"               # schedule-style file (home/away or team/opp)
ROSTERS = "data/rosters_2025.csv"                  # current 2025 team rosters
OUT = f"{output_dir}/prop_projections_receiving.csv"

# ---------------------------
# 1) Load historical data
# ---------------------------
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# Always use the pre-processed historical player games file
if not os.path.exists(HIST):
    raise FileNotFoundError(f"Required file not found: {HIST}. Run prepare_data.py first to generate this file.")
    
hist = pd.read_csv(HIST)
print(f"Loaded historical data: {len(hist)} rows")

# Ensure numeric
for c in ["targets","receptions","rec_yards","season","week"]:
    hist[c] = pd.to_numeric(hist[c], errors="coerce")

# Drop rows with no label
hist = hist.dropna(subset=["rec_yards"]).copy()

# ---------------------------
# 2) Build PRE-GAME features (no lookahead): trailing means shifted by 1
# ---------------------------
# Sort for rolling
hist = hist.sort_values(["player_id","season","week"]).reset_index(drop=True)

# Trailing windows (you can tweak sizes)
windows = [3,5,8]
for w in windows:
    hist[f"targets_l{w}"] = hist.groupby("player_id")["targets"].transform(lambda s: s.shift(1).rolling(w,min_periods=1).mean())
    hist[f"receptions_l{w}"] = hist.groupby("player_id")["receptions"].transform(lambda s: s.shift(1).rolling(w,min_periods=1).mean())
    hist[f"yards_l{w}"] = hist.groupby("player_id")["rec_yards"].transform(lambda s: s.shift(1).rolling(w,min_periods=1).mean())

feature_cols = [f"targets_l{w}" for w in windows] + [f"receptions_l{w}" for w in windows] + [f"yards_l{w}" for w in windows]

train = hist.dropna(subset=feature_cols + ["rec_yards"]).copy()
X = train[feature_cols]
y = train["rec_yards"].astype(float)

# ---------------------------
# 3) Train model
# ---------------------------
model = XGBRegressor(
    n_estimators=500,
    learning_rate=0.05,
    max_depth=5,
    subsample=0.9,
    colsample_bytree=0.9,
    objective="reg:squarederror",
    random_state=42,
    tree_method="hist",
)
model.fit(X, y)

# ---------------------------
# 4) Build upcoming player rows using CURRENT ROSTERS
# ---------------------------
up = pd.read_csv(UPCOMING)

# Bring to team rows
if not {"team","opp"}.issubset(up.columns):
    if {"home_team","away_team"}.issubset(up.columns):
        base = [c for c in up.columns if c not in ["home_team","away_team"]]
        home = up[base+ ["home_team","away_team"]].rename(columns={"home_team":"team","away_team":"opp"})
        away = up[base+ ["home_team","away_team"]].rename(columns={"away_team":"team","home_team":"opp"})
        up = pd.concat([home[base+["team","opp"]], away[base+["team","opp"]]], ignore_index=True)
    else:
        raise ValueError("upcoming_games.csv must include ['team','opp'] or ['home_team','away_team']")

# Set season/week defaults if missing
if "season" not in up.columns:
    up["season"] = int(hist["season"].max()) + 1  # e.g., 2025
if "week" not in up.columns:
    up["week"] = 1

# ---------------------------
# 4a) Load current rosters to get proper team assignments
# ---------------------------
if not os.path.exists(ROSTERS):
    raise FileNotFoundError(f"Rosters file not found: {ROSTERS}")

rosters = pd.read_csv(ROSTERS)
# Use 2025 roster data
current_season = 2025
current_rosters = rosters[rosters["season"] == current_season].copy()

print(f"Using {current_season} rosters as current team assignments...")

# Filter for skill positions only (WR, RB, TE)
skill_positions = ["WR", "RB", "TE"]
current_skill = current_rosters[current_rosters["position"].isin(skill_positions)].copy()

# Create player-team mapping using pfr_id (matches player_id in historical data)
roster_mapping = current_skill[["pfr_id", "full_name", "team", "position"]].copy()
roster_mapping = roster_mapping.dropna(subset=["pfr_id"])  # Remove players without pfr_id

# Fix player_id format: add .htm extension to match historical data format
roster_mapping["pfr_id"] = roster_mapping["pfr_id"] + ".htm"
roster_mapping = roster_mapping.rename(columns={"pfr_id": "player_id", "full_name": "player_name"})

print(f"Found {len(roster_mapping)} skill position players in current rosters")

# ---------------------------
# 4b) Get trailing features from historical data
# ---------------------------
last_season = int(hist["season"].max())
last = hist[hist["season"] == last_season].copy()

# Keep players with at least 3 games last season
gp = last.groupby("player_id")["rec_yards"].count().rename("games").reset_index()
keep_players = gp[gp["games"] >= 3]["player_id"]
last = last[last["player_id"].isin(keep_players)].copy()

# Take each player's most recent row in last season to grab trailing features
last_recent = last.sort_values(["player_id","week"]).groupby("player_id").tail(1)
player_feats = last_recent[["player_id","player_name"] + feature_cols].copy()

# ---------------------------
# 4c) Merge roster assignments with historical trailing features
# ---------------------------
# Start with roster-based team assignments
roster_with_history = roster_mapping.merge(player_feats, on="player_id", how="left")

# Update player names from roster data (more current)
roster_with_history["player_name"] = roster_with_history["player_name_x"]
roster_with_history = roster_with_history.drop(columns=["player_name_x", "player_name_y"])

# Fill missing trailing features with zeros for players without sufficient history
for col in feature_cols:
    if col in roster_with_history.columns:
        roster_with_history[col] = roster_with_history[col].fillna(0.0)

players_with_data = roster_with_history[feature_cols[0]].notna().sum()
players_without_data = roster_with_history[feature_cols[0]].isna().sum()
print(f"Players with historical data: {players_with_data}, without: {players_without_data}")

# Attach players to the upcoming schedule by team
up_simple = up[["team","opp","season","week"]].drop_duplicates()
upcoming_players = up_simple.merge(roster_with_history, on="team", how="inner")
print(f"Final predictions for {len(upcoming_players)} players across {len(up_simple)} games")

# ---------------------------
# 5) Predict with trailing features
# ---------------------------
upcoming_players["pred_rec_yards"] = model.predict(upcoming_players[feature_cols])

# Save
cols = ["player_id","player_name","team","opp","season","week","pred_rec_yards"] + feature_cols
upcoming_players[cols].to_csv(OUT, index=False)
print(f"Saved: {OUT}")

# ---------------------------
# 6) Create WR game visualization tables
# ---------------------------
# Filter for WRs only (position already included from roster data)
wr_players = upcoming_players[upcoming_players['position'] == 'WR'].copy()

if not wr_players.empty:
    print(f"\nCreating game visualization tables for {len(wr_players)} WRs...")
    
    # Get unique games (both team vs opp and opp vs team represent the same game)
    games = []
    processed_games = set()
    
    for _, row in wr_players[['team', 'opp']].drop_duplicates().iterrows():
        team1, team2 = sorted([row['team'], row['opp']])  # Sort to avoid duplicates
        game_key = f"{team1}_{team2}"
        
        if game_key not in processed_games:
            games.append((team1, team2))
            processed_games.add(game_key)
    
    print(f"Found {len(games)} unique games")
    
    # Create visualization for each game
    created_files = []
    for i, (team1, team2) in enumerate(games, 1):
        # Get WRs from both teams for this game
        game_wrs = wr_players[
            ((wr_players['team'] == team1) & (wr_players['opp'] == team2)) |
            ((wr_players['team'] == team2) & (wr_players['opp'] == team1))
        ].copy()
        
        if not game_wrs.empty:
            # Sort by predicted receiving yards (highest to lowest)
            game_wrs = game_wrs.sort_values('pred_rec_yards', ascending=False)
            
            # Create full visualization table
            filename = create_game_wr_table(game_wrs, team1, team2, i)
            created_files.append(filename)
            print(f"  Created: {filename} ({len(game_wrs)} WRs)")
            
            # Create cleaned visualization table (only name and yards)
            filename_cleaned = create_game_wr_table_cleaned(game_wrs, team1, team2, i)
            created_files.append(filename_cleaned)
            print(f"  Created: {filename_cleaned} ({len(game_wrs)} WRs)")
            
            # Create text-based tabulated table
            filename_text = create_game_wr_table_text(game_wrs, team1, team2, i)
            created_files.append(filename_text)
            print(f"  Created: {filename_text} ({len(game_wrs)} WRs)")
    
    print(f"\nSuccessfully created {len(created_files)} game files ({len(created_files)//3} full PNG + {len(created_files)//3} cleaned PNG + {len(created_files)//3} text)!")
else:
    print("No WRs found in predictions data")
    
