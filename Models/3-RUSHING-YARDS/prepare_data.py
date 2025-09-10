# make_historical_from_raw.py
# Input:  all_passing_rushing_receiving.csv  (raw per player-game stats)
# Output: model_train.csv        (cleaned for modeling)
# Also downloads and prepares 2025 roster data

import pandas as pd
import requests
import os

RAW = "data/all_passing_rushing_receiving.csv"
OUT = "data/model_train.csv"

df = pd.read_csv(RAW)

# Derive season/week from game_id like "2019_01_GB_CHI" (if not already present)
if "season" not in df.columns and "game_id" in df.columns:
    df["season"] = df["game_id"].str.slice(0, 4).astype(int)
if "week" not in df.columns and "game_id" in df.columns:
    df["week"] = df["game_id"].str.slice(5, 7).astype(int)

# Correct rename for rushing columns
df = df.rename(columns={
    "player": "player_name",
    "opponent_team": "opp",
    "rush_att": "rush_attempts",
    "rush_yds": "rush_yards",
})

# Fix specific name mismatches
df.loc[df['player_name'] == 'Michael Penix', 'player_name'] = 'Michael Penix Jr.'

# Auto-set QB position for starting QBs (from starting_qbs_2025.csv)
starting_qbs = pd.read_csv("data/starting_qbs_2025.csv")
for _, qb in starting_qbs.iterrows():
    team = qb['team']
    qb_name = qb['starting_qb']
    # Set position to QB for this player on this team
    df.loc[(df['team'] == team) & (df['player_name'] == qb_name), 'position'] = 'QB'

# Keep only receiving positions if available (avoid QB noise)
if "position" in df.columns:
    df = df[df["position"].isin(["QB", "RB"])]

# Select required columns
keep = ["player_id","player_name","team","opp","season","week","rush_attempts","rush_yards"]
df = df[keep].copy()

# Ensure numeric types & drop rows without label
for c in ["rush_attempts","rush_yards","season","week"]:
    df[c] = pd.to_numeric(df[c], errors="coerce")
df = df.dropna(subset=["rush_yards"])

# Optional tidy
df = df.sort_values(["season","week","team","player_name"]).reset_index(drop=True)

df.to_csv(OUT, index=False)
print(f"Saved: {OUT}  |  rows={len(df)}")

# ---------------------------
# Download 2025 roster data - DISABLED (using existing data)
# ---------------------------
print("\n=== Using Existing 2025 Roster Data ===")

# Skip download - using existing roster data from copied files
file_path = "data/roster_2025.csv"
print(f"Using existing roster_2025.csv from copied data")

try:
    # Load existing 2025 roster data
    roster_2025 = pd.read_csv(file_path)
    
    # Add URL column
    base_url = "https://www.pro-football-reference.com/players/"
    roster_2025['url'] = roster_2025['pfr_id'].apply(lambda x: f"{base_url}{x[0]}/{x}.htm" if pd.notna(x) else None)
    
    # Standardize team names
    standardize_mapping = {
        'ARZ': 'ARI',  
        'BLT': 'BAL',  
        'CLV': 'CLE',  
        'HST': 'HOU',  
        'LA': 'LAR',   
        'LV': 'LVR',   
        'OAK': 'LVR',  
        'SD': 'LAC',   
        'SL': 'LAR'    
    }
    roster_2025['team'] = roster_2025['team'].replace(standardize_mapping)
    
    # Save standardized 2025 rosters
    roster_2025.to_csv(file_path, index=False)
    print(f"Processed existing roster_2025.csv - Total rows: {len(roster_2025)}")
    
    # Show sample of 2025 RBs to verify
    rb_2025 = roster_2025[roster_2025['position'] == 'RB']
    print(f"\nSample 2025 RBs: {len(rb_2025)} total")
    print(rb_2025[['team', 'full_name']].head(10))
    
except Exception as e:
    print(f"Error processing existing 2025 roster data: {e}")

# os.remove('data/all_passing_rushing_receiving.csv')
# print("Removed all_passing_rushing_receiving.csv")