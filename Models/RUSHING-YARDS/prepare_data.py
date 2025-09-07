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
# Download 2025 roster data
# ---------------------------
print("\n=== Downloading 2025 Roster Data ===")

# Download 2025 roster data directly
year = 2025
file_path = "data/rosters_2025.csv"
url = f"https://github.com/nflverse/nflverse-data/releases/download/rosters/roster_{year}.csv"

print(f"Downloading 2025 roster data from: {url}")
try:
    response = requests.get(url)
    if response.status_code == 200:
        with open(file_path, 'wb') as file:
            file.write(response.content)
        print(f"Downloaded and saved rosters_2025.csv")
        
        # Load 2025 roster data
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
        print(f"Saved standardized rosters_2025.csv - Total rows: {len(roster_2025)}")
        
        # Show sample of 2025 WRs to verify
        wr_2025 = roster_2025[roster_2025['position'] == 'WR']
        print(f"\nSample 2025 WRs: {len(wr_2025)} total")
        print(wr_2025[['team', 'full_name']].head(10))
        
    else:
        print(f"Failed to download 2025 roster data (status: {response.status_code})")
        
except Exception as e:
    print(f"Error downloading 2025 roster data: {e}")

# os.remove('data/all_passing_rushing_receiving.csv')
# print("Removed all_passing_rushing_receiving.csv")