# make_historical_from_raw.py
# Input:  player_stats_pfr.csv  (raw per player-game stats)
# Output: model_train.csv        (cleaned for modeling)
# Also downloads and prepares 2025 roster data

import pandas as pd
import requests
import os

RAW = "data/player_stats_pfr.csv"
OUT = "data/model_train.csv"

df = pd.read_csv(RAW)

# Derive season/week from game_id like "2019_01_GB_CHI" (if not already present)
if "season" not in df.columns and "game_id" in df.columns:
    df["season"] = df["game_id"].str.slice(0, 4).astype(int)
if "week" not in df.columns and "game_id" in df.columns:
    df["week"] = df["game_id"].str.slice(5, 7).astype(int)

# Rename to model schema
df = df.rename(columns={
    "player": "player_name",
    "opponent_team": "opp",
    "rec": "receptions",
    "rec_yds": "rec_yards",
})

# Fix specific name mismatches
df.loc[df['player_name'] == 'Michael Penix', 'player_name'] = 'Michael Penix Jr.'
df.loc[df['player_name'] == 'D.J. Moore', 'player_name'] = 'DJ Moore'

# Auto-fix name mismatches between roster and raw data
def normalize_name(name):
    """Normalize name for comparison by removing punctuation and converting to lowercase"""
    if pd.isna(name):
        return name
    return name.lower().replace('.', '').replace(',', '').replace("'", '').replace('-', ' ')

# Load roster to get correct names and positions
roster = pd.read_csv("data/roster_2025.csv")

# Create name mapping from raw data to roster data
name_mapping = {}
position_mapping = {}

for _, roster_row in roster.iterrows():
    roster_name = roster_row['full_name']
    roster_pos = roster_row['position']
    roster_team = roster_row['team']
    
    # Find matching player in raw data
    raw_match = df[(df['team'] == roster_team) & (df['player_name'].notna())]
    
    for _, raw_row in raw_match.iterrows():
        raw_name = raw_row['player_name']
        
        # Check if names are the same person (normalized comparison)
        if normalize_name(roster_name) == normalize_name(raw_name):
            if roster_name != raw_name:
                name_mapping[raw_name] = roster_name
            # Always use roster position as source of truth
            position_mapping[(raw_name, roster_team)] = roster_pos

# Apply name fixes
for raw_name, roster_name in name_mapping.items():
    df.loc[df['player_name'] == raw_name, 'player_name'] = roster_name

# Apply position fixes (use roster as source of truth)
# Note: Use the NEW name after name fixes
for (raw_name, team), roster_pos in position_mapping.items():
    # Find the new name after name fixes
    new_name = name_mapping.get(raw_name, raw_name)
    df.loc[(df['player_name'] == new_name) & (df['team'] == team), 'position'] = roster_pos

# Transfer historical data for players who changed teams
# This handles cases like DK Metcalf (SEA -> PIT)
for _, roster_row in roster.iterrows():
    roster_name = roster_row['full_name']
    roster_team = roster_row['team']
    
    # Find historical data for this player on other teams
    historical_data = df[(df['player_name'] == roster_name) & (df['team'] != roster_team)]
    
    if len(historical_data) > 0:
        # Copy historical data to current team
        historical_data_copy = historical_data.copy()
        historical_data_copy['team'] = roster_team
        historical_data_copy['position'] = roster_row['position']
        
        # Add to dataframe
        df = pd.concat([df, historical_data_copy], ignore_index=True)
        
        print(f"Transferred {len(historical_data)} historical records for {roster_name} to {roster_team}")

print(f"Auto-fixed {len(name_mapping)} name mismatches and {len(position_mapping)} position issues")

# Keep only receiving positions if available (avoid QB noise)
if "position" in df.columns:
    df = df[df["position"].isin(["WR", "RB", "TE"])]

# Select required columns
keep = ["player_id","player_name","team","opp","season","week","targets","receptions","rec_yards"]
df = df[keep].copy()

# Ensure numeric types & drop rows without label
for c in ["targets","receptions","rec_yards","season","week"]:
    df[c] = pd.to_numeric(df[c], errors="coerce")
df = df.dropna(subset=["rec_yards"])

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
    
    # Show sample of 2025 WRs to verify
    wr_2025 = roster_2025[roster_2025['position'] == 'WR']
    print(f"\nSample 2025 WRs: {len(wr_2025)} total")
    print(wr_2025[['team', 'full_name']].head(10))
    
except Exception as e:
    print(f"Error processing existing 2025 roster data: {e}")

# os.remove('data/player_stats_pfr.csv')
# print("Removed player_stats_pfr.csv")