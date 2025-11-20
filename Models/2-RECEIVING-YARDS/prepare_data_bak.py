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

# Vectorized name matching - much faster than nested loops
df['name_normalized'] = df['player_name'].apply(normalize_name)
roster['name_normalized'] = roster['full_name'].apply(normalize_name)

# Merge on team and normalized name to find matches
merged = df.merge(
    roster[['team', 'full_name', 'position', 'name_normalized']],
    on=['team', 'name_normalized'],
    how='left',
    suffixes=('', '_roster')
)

# Create name mapping for mismatched names
name_mapping = {}
mask = (merged['player_name'].notna() & 
        merged['full_name'].notna() & 
        (merged['player_name'] != merged['full_name']))
name_mapping = dict(zip(merged.loc[mask, 'player_name'], merged.loc[mask, 'full_name']))

# Create position mapping
position_mapping = {}
mask = merged['full_name'].notna()
position_mapping = dict(zip(
    zip(merged.loc[mask, 'player_name'], merged.loc[mask, 'team']),
    merged.loc[mask, 'position']
))

# Drop temporary column
df = df.drop(columns=['name_normalized'])

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
# Use player_id (pfr_id + '.htm') to avoid name ambiguity and duplicates
roster_dict = dict(zip(roster['pfr_id'].astype(str).apply(lambda x: f"{x}.htm"), zip(roster['team'], roster['position'])))
transferred_records = []

for player_id, (current_team, position) in roster_dict.items():
    # Find historical data for this player on other teams using player_id
    historical_mask = (df['player_id'] == player_id) & (df['team'] != current_team)
    historical_data = df[historical_mask]
    
    if len(historical_data) > 0:
        # Copy historical data to current team
        historical_data_copy = historical_data.copy()
        historical_data_copy['team'] = current_team
        historical_data_copy['position'] = position
        transferred_records.append(historical_data_copy)
        print(f"Transferred {len(historical_data)} historical records for {player_id} to {current_team}")

if transferred_records:
    old_len = len(df)
    df = pd.concat([df] + transferred_records, ignore_index=True)
    df = df.drop_duplicates()
    print(f"Removed duplicates after transfer: {old_len} -> {len(df)} rows")

print(f"Auto-fixed {len(name_mapping)} name mismatches and {len(position_mapping)} position issues")

# Keep only receiving positions if available (avoid QB noise)
if "position" in df.columns:
    df = df[df["position"].isin(["WR", "RB", "TE"])]

# Select required columns
keep = ["player_id","player_name","team","opp","season","week","targets","receptions","rec_yards","rush_att"]
df = df[keep].copy()

# Ensure numeric types & drop rows without label
for c in ["targets","receptions","rec_yards","rush_att","season","week"]:
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