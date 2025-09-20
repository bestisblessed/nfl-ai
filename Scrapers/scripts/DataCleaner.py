#!/usr/bin/env python3
"""
NFL Data Cleaner - Team Abbreviation Standardization
====================================================

This script standardizes team abbreviations across all CSV files to ensure consistency.
It maps various team name formats to standardized 3-letter abbreviations.

Standard Team Abbreviations:
ARI, ATL, BAL, BUF, CAR, CHI, CIN, CLE, DAL, DEN, DET, GB, HOU, IND, JAX, KC, 
LAC, LAR, LVR, MIA, MIN, NE, NO, NYG, NYJ, PHI, PIT, SEA, SF, TB, TEN, WAS
"""

import pandas as pd
import os
import shutil
from datetime import datetime

# Comprehensive team abbreviation mapping
TEAM_MAPPING = {
    # Full team names (from box scores)
    'Arizona Cardinals': 'ARI',
    'Atlanta Falcons': 'ATL',
    'Baltimore Ravens': 'BAL',
    'Buffalo Bills': 'BUF',
    'Carolina Panthers': 'CAR',
    'Chicago Bears': 'CHI',
    'Cincinnati Bengals': 'CIN',
    'Cleveland Browns': 'CLE',
    'Dallas Cowboys': 'DAL',
    'Denver Broncos': 'DEN',
    'Detroit Lions': 'DET',
    'Green Bay Packers': 'GB',
    'Houston Texans': 'HOU',
    'Indianapolis Colts': 'IND',
    'Jacksonville Jaguars': 'JAX',
    'Kansas City Chiefs': 'KC',
    'Los Angeles Chargers': 'LAC',
    'Los Angeles Rams': 'LAR',
    'Las Vegas Raiders': 'LVR',
    'Oakland Raiders': 'LVR',
    'Miami Dolphins': 'MIA',
    'Minnesota Vikings': 'MIN',
    'New England Patriots': 'NE',
    'New Orleans Saints': 'NO',
    'New York Giants': 'NYG',
    'New York Jets': 'NYJ',
    'Philadelphia Eagles': 'PHI',
    'Pittsburgh Steelers': 'PIT',
    'Seattle Seahawks': 'SEA',
    'San Francisco 49ers': 'SF',
    'Tampa Bay Buccaneers': 'TB',
    'Tennessee Titans': 'TEN',
    'Washington Commanders': 'WAS',
    'Washington Football Team': 'WAS',
    'Washington Redskins': 'WAS',
    'St. Louis Rams': 'LAR',
    'San Diego Chargers': 'LAC',
    
    # Abbreviated names (from scoring tables)
    'Cardinals': 'ARI',
    'Falcons': 'ATL',
    'Ravens': 'BAL',
    'Bills': 'BUF',
    'Panthers': 'CAR',
    'Bears': 'CHI',
    'Bengals': 'CIN',
    'Browns': 'CLE',
    'Cowboys': 'DAL',
    'Broncos': 'DEN',
    'Lions': 'DET',
    'Packers': 'GB',
    'Texans': 'HOU',
    'Colts': 'IND',
    'Jaguars': 'JAX',
    'Chiefs': 'KC',
    'Chargers': 'LAC',
    'Rams': 'LAR',
    'Raiders': 'LVR',
    'Dolphins': 'MIA',
    'Vikings': 'MIN',
    'Patriots': 'NE',
    'Saints': 'NO',
    'Giants': 'NYG',
    'Jets': 'NYJ',
    'Eagles': 'PHI',
    'Steelers': 'PIT',
    'Seahawks': 'SEA',
    '49ers': 'SF',
    'Buccaneers': 'TB',
    'Titans': 'TEN',
    'Commanders': 'WAS',
    'Football Team': 'WAS',
    'Redskins': 'WAS',
    'Washington': 'WAS',
    
    # 3-letter codes (from team stats/conversions)
    'crd': 'ARI',  # Cardinals
    'atl': 'ATL',  # Falcons
    'bal': 'BAL',  # Ravens
    'buf': 'BUF',  # Bills
    'car': 'CAR',  # Panthers
    'chi': 'CHI',  # Bears
    'cin': 'CIN',  # Bengals
    'cle': 'CLE',  # Browns
    'dal': 'DAL',  # Cowboys
    'den': 'DEN',  # Broncos
    'det': 'DET',  # Lions
    'gnb': 'GB',   # Green Bay Packers
    'htx': 'HOU',  # Texans (alternative)
    'hou': 'HOU',  # Texans
    'clt': 'IND',  # Indianapolis Colts (alternative)
    'ind': 'IND',  # Colts
    'jax': 'JAX',  # Jaguars
    'kan': 'KC',   # Kansas City Chiefs
    'lac': 'LAC',  # Chargers
    'lar': 'LAR',  # Rams
    'lvr': 'LVR',  # Raiders
    'mia': 'MIA',  # Dolphins
    'min': 'MIN',  # Vikings
    'nwe': 'NE',   # New England Patriots
    'nor': 'NO',   # New Orleans Saints
    'nyg': 'NYG',  # Giants
    'nyj': 'NYJ',  # Jets
    'oti': 'TEN',  # Tennessee Titans
    'phi': 'PHI',  # Eagles
    'pit': 'PIT',  # Steelers
    'rai': 'LVR',  # Raiders (alternative)
    'ram': 'LAR',  # Rams (alternative)
    'rav': 'BAL',  # Ravens (alternative)
    'sdg': 'LAC',  # San Diego Chargers
    'sea': 'SEA',  # Seahawks
    'sf': 'SF',    # 49ers
    'sfo': 'SF',   # 49ers (alternative)
    'tam': 'TB',   # Tampa Bay Buccaneers
    'ten': 'TEN',  # Titans
    'was': 'WAS',  # Washington
    
    # Additional uppercase mappings found in defense game logs
    'KAN': 'KC',   # Kansas City Chiefs (uppercase)
    'TAM': 'TB',   # Tampa Bay Buccaneers (uppercase)
    'NOR': 'NO',   # New Orleans Saints (uppercase)
    'SFO': 'SF',   # San Francisco 49ers (uppercase)
    'GNB': 'GB',   # Green Bay Packers (uppercase)
    'NWE': 'NE',   # New England Patriots (uppercase)
    'OAK': 'LVR',  # Oakland Raiders (uppercase)
    'SDG': 'LAC',  # San Diego Chargers (uppercase)
    'STL': 'LAR'   # St. Louis Rams (uppercase)
}

def create_backup(file_path):
    """Create a backup of the original file"""
    backup_path = f"{file_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(file_path, backup_path)
    print(f"   Backup created: {backup_path}")
    return backup_path

def standardize_team_names(df, team_column, file_name):
    """Standardize team names in a dataframe"""
    print(f"   Processing {file_name}...")
    
    # Check if team column exists
    if team_column not in df.columns:
        print(f"     Warning: Column '{team_column}' not found in {file_name}")
        return df
    
    # Count unique teams before standardization
    unique_teams_before = df[team_column].nunique()
    
    # Create a copy to avoid modifying original
    df_clean = df.copy()
    
    # Standardize team names
    df_clean[team_column] = df_clean[team_column].map(TEAM_MAPPING).fillna(df_clean[team_column])
    
    # Count unique teams after standardization
    unique_teams_after = df_clean[team_column].nunique()
    
    # Check for unmapped teams
    unmapped_teams = df_clean[df_clean[team_column].isin(TEAM_MAPPING.values()) == False][team_column].unique()
    
    print(f"     Teams before: {unique_teams_before}, after: {unique_teams_after}")
    if len(unmapped_teams) > 0:
        print(f"     Warning: {len(unmapped_teams)} unmapped teams: {unmapped_teams}")
    
    return df_clean

def clean_box_scores():
    """Clean box scores file"""
    print("\n1. Cleaning Box Scores...")
    file_path = 'data/all_box_scores.csv'
    
    if not os.path.exists(file_path):
        print(f"   File not found: {file_path}")
        return
    
    # Create backup
    backup_path = create_backup(file_path)
    
    # Load and clean data
    df = pd.read_csv(file_path)
    df_clean = standardize_team_names(df, 'Team', 'Box Scores')
    
    # Save cleaned data
    df_clean.to_csv(file_path, index=False)
    print(f"   Cleaned data saved to: {file_path}")

def clean_scoring_tables():
    """Clean scoring tables file"""
    print("\n2. Cleaning Scoring Tables...")
    file_path = 'data/all_scoring_tables.csv'
    
    if not os.path.exists(file_path):
        print(f"   File not found: {file_path}")
        return
    
    # Create backup
    backup_path = create_backup(file_path)
    
    # Load and clean data
    df = pd.read_csv(file_path)
    df_clean = standardize_team_names(df, 'Team', 'Scoring Tables')
    
    # Save cleaned data
    df_clean.to_csv(file_path, index=False)
    print(f"   Cleaned data saved to: {file_path}")

def clean_team_game_logs():
    """Clean team game logs file"""
    print("\n3. Cleaning Team Game Logs...")
    file_path = 'data/all_team_game_logs.csv'
    
    if not os.path.exists(file_path):
        print(f"   File not found: {file_path}")
        return
    
    # Create backup
    backup_path = create_backup(file_path)
    
    # Load and clean data
    df = pd.read_csv(file_path)
    
    # This file should already have standardized team IDs, but let's verify
    if 'home_team_id' in df.columns and 'away_team_id' in df.columns:
        print("   File already has standardized team IDs (home_team_id, away_team_id)")
        return
    
    print(f"   File structure: {list(df.columns)}")
    print("   No team name standardization needed for this file")

def clean_team_stats():
    """Clean team stats file"""
    print("\n4. Cleaning Team Stats...")
    file_path = 'data/all_team_stats.csv'
    
    if not os.path.exists(file_path):
        print(f"   File not found: {file_path}")
        return
    
    # Create backup
    backup_path = create_backup(file_path)
    
    # Load and clean data
    df = pd.read_csv(file_path)
    df_clean = standardize_team_names(df, 'Team', 'Team Stats')
    
    # Save cleaned data
    df_clean.to_csv(file_path, index=False)
    print(f"   Cleaned data saved to: {file_path}")

def clean_team_conversions():
    """Clean team conversions file"""
    print("\n5. Cleaning Team Conversions...")
    file_path = 'data/all_team_conversions.csv'
    
    if not os.path.exists(file_path):
        print(f"   File not found: {file_path}")
        return
    
    # Create backup
    backup_path = create_backup(file_path)
    
    # Load and clean data
    df = pd.read_csv(file_path)
    df_clean = standardize_team_names(df, 'Team', 'Team Conversions')
    
    # Save cleaned data
    df_clean.to_csv(file_path, index=False)
    print(f"   Cleaned data saved to: {file_path}")

def clean_passing_rushing_receiving():
    """Clean passing/rushing/receiving file"""
    print("\n6. Cleaning Passing/Rushing/Receiving...")
    file_path = 'data/all_passing_rushing_receiving.csv'
    
    if not os.path.exists(file_path):
        print(f"   File not found: {file_path}")
        return
    
    # Create backup
    backup_path = create_backup(file_path)
    
    # Load and clean data
    df = pd.read_csv(file_path)
    
    # Check for team columns
    team_columns = [col for col in df.columns if 'team' in col.lower()]
    if team_columns:
        print(f"   Found team columns: {team_columns}")
        for col in team_columns:
            df = standardize_team_names(df, col, f'Passing/Rushing/Receiving ({col})')
    else:
        print("   No team columns found")
    
    # Save cleaned data
    df.to_csv(file_path, index=False)
    print(f"   Cleaned data saved to: {file_path}")

def clean_defense_game_logs():
    """Clean defense game logs file"""
    print("\n7. Cleaning Defense Game Logs...")
    file_path = 'data/all_defense-game-logs.csv'
    
    if not os.path.exists(file_path):
        print(f"   File not found: {file_path}")
        return
    
    # Create backup
    backup_path = create_backup(file_path)
    
    # Load and clean data
    df = pd.read_csv(file_path)
    
    # Check for team columns
    team_columns = [col for col in df.columns if 'team' in col.lower()]
    if team_columns:
        print(f"   Found team columns: {team_columns}")
        for col in team_columns:
            df = standardize_team_names(df, col, f'Defense Game Logs ({col})')
    else:
        print("   No team columns found")
    
    # Save cleaned data
    df.to_csv(file_path, index=False)
    print(f"   Cleaned data saved to: {file_path}")

def validate_standardization():
    """Validate that all files now have consistent team abbreviations"""
    print("\n=== VALIDATION ===\n")
    
    files_to_check = [
        ('data/all_box_scores.csv', 'Team'),
        ('data/all_scoring_tables.csv', 'Team'),
        ('data/all_team_stats.csv', 'Team'),
        ('data/all_team_conversions.csv', 'Team')
    ]
    
    all_teams = set()
    
    for file_path, team_column in files_to_check:
        if os.path.exists(file_path):
            try:
                df = pd.read_csv(file_path)
                if team_column in df.columns:
                    teams = set(df[team_column].unique())
                    all_teams.update(teams)
                    print(f"{file_path}: {len(teams)} unique teams")
                    print(f"  Sample teams: {sorted(list(teams))[:5]}")
                else:
                    print(f"{file_path}: Column '{team_column}' not found")
            except Exception as e:
                print(f"{file_path}: Error reading file - {e}")
        else:
            print(f"{file_path}: File not found")
    
    print(f"\nTotal unique team abbreviations across all files: {len(all_teams)}")
    print(f"All team abbreviations: {sorted(list(all_teams))}")
    
    # Check if all are in our standard set
    standard_teams = set(TEAM_MAPPING.values())
    non_standard = all_teams - standard_teams
    if non_standard:
        print(f"Warning: Non-standard team abbreviations found: {non_standard}")
    else:
        print("✅ All team abbreviations are now standardized!")

def main():
    """Main function to run the data cleaning process"""
    print("NFL Data Cleaner - Team Abbreviation Standardization")
    print("=" * 60)
    print(f"Started at: {datetime.now()}")
    
    # Create backups directory if it doesn't exist
    if not os.path.exists('backups'):
        os.makedirs('backups')
    
    try:
        # Clean all files
        clean_box_scores()
        clean_scoring_tables()
        clean_team_game_logs()
        clean_team_stats()
        clean_team_conversions()
        clean_passing_rushing_receiving()
        clean_defense_game_logs()
        
        # Validate the standardization
        validate_standardization()
        
        print(f"\n✅ Data cleaning completed successfully at: {datetime.now()}")
        print("All files have been backed up and standardized team abbreviations.")
        
    except Exception as e:
        print(f"\n❌ Error during data cleaning: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
