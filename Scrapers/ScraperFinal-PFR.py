'''
**PFR-Only NFL Data Scraper**
Creates CSV files using only Pro Football Reference (PFR) data
This script uses existing PFR-scraped data files to build comprehensive CSV datasets
Filters out unplayed games based on week limit provided as command line argument
'''

import pandas as pd
import os
import sys
from datetime import datetime

# Get week limit from command line argument
if len(sys.argv) > 1:
    try:
        WEEK_LIMIT = int(sys.argv[1])
        print(f"🎯 Filtering out unplayed games after week {WEEK_LIMIT}")
    except ValueError:
        print("❌ Error: Week limit must be a number")
        sys.exit(1)
else:
    WEEK_LIMIT = None
    print("⚠️  No week limit provided - keeping all games (including unplayed)")

print("="*80)
print("CREATING PFR-ONLY NFL CSV FILES")
print("="*80)

final_pfr_dir = 'final_data_pfr'
if not os.path.exists(final_pfr_dir):
    os.makedirs(final_pfr_dir)

##### Create 'Teams' CSV #####
print("\n1. Creating Teams CSV...")
standardize_mapping = {
    'OAK': 'LVR',  
    'SD': 'LAC',   
    'STL': 'LAR',  
    'LA': 'LAR',   
    'LV': 'LVR',
    'ARZ': 'ARI',  
    'BLT': 'BAL',  
    'CLV': 'CLE',  
    'HST': 'HOU',  
    'SL': 'LAR'    
}
teams = [
    ['ARI', 'Arizona Cardinals', 'NFC West'],
    ['ATL', 'Atlanta Falcons', 'NFC South'],
    ['BAL', 'Baltimore Ravens', 'AFC North'],
    ['BUF', 'Buffalo Bills', 'AFC East'],
    ['CAR', 'Carolina Panthers', 'NFC South'],
    ['CHI', 'Chicago Bears', 'NFC North'],
    ['CIN', 'Cincinnati Bengals', 'AFC North'],
    ['CLE', 'Cleveland Browns', 'AFC North'],
    ['DAL', 'Dallas Cowboys', 'NFC East'],
    ['DEN', 'Denver Broncos', 'AFC West'],
    ['DET', 'Detroit Lions', 'NFC North'],
    ['GB', 'Green Bay Packers', 'NFC North'],
    ['HOU', 'Houston Texans', 'AFC South'],
    ['IND', 'Indianapolis Colts', 'AFC South'],
    ['JAX', 'Jacksonville Jaguars', 'AFC South'],
    ['KC', 'Kansas City Chiefs', 'AFC West'],
    ['LAC', 'Los Angeles Chargers', 'AFC West'],
    ['LAR', 'Los Angeles Rams', 'NFC West'],
    ['LVR', 'Las Vegas Raiders', 'AFC West'],
    ['MIA', 'Miami Dolphins', 'AFC East'],
    ['MIN', 'Minnesota Vikings', 'NFC North'],
    ['NE', 'New England Patriots', 'AFC East'],
    ['NO', 'New Orleans Saints', 'NFC South'],
    ['NYG', 'New York Giants', 'NFC East'],
    ['NYJ', 'New York Jets', 'AFC East'],
    ['PHI', 'Philadelphia Eagles', 'NFC East'],
    ['PIT', 'Pittsburgh Steelers', 'AFC North'],
    ['SF', 'San Francisco 49ers', 'NFC West'],
    ['SEA', 'Seattle Seahawks', 'NFC West'],
    ['TB', 'Tampa Bay Buccaneers', 'NFC South'],
    ['TEN', 'Tennessee Titans', 'AFC South'],
    ['WAS', 'Washington Commanders', 'NFC East']
]
df_teams = pd.DataFrame(teams, columns=['TeamID', 'Team', 'Division'])
df_teams.to_csv(f'{final_pfr_dir}/teams_pfr.csv', index=False)
print(f"✅ Teams CSV created with {len(df_teams)} teams")

##### Create 'PlayerStats' CSV from PFR passing/rushing/receiving data #####
print("\n2. Creating PlayerStats CSV from PFR passing/rushing/receiving data...")
if os.path.exists('./data/all_passing_rushing_receiving.csv'):
    print("   Loading PFR passing/rushing/receiving data...")
    df_pfr_stats = pd.read_csv('./data/all_passing_rushing_receiving.csv')
    df_pfr_stats['season'] = df_pfr_stats['game_id'].str.split('_').str[0].astype(int)
    df_pfr_stats['week'] = df_pfr_stats['game_id'].str.split('_').str[1].astype(int)
    df_pfr_stats['position'] = None
    df_pfr_stats['headshot_url'] = None
    # df_pfr_stats['completions'] = df_pfr_stats['pass_cmp'].fillna(0)
    # df_pfr_stats['attempts'] = df_pfr_stats['pass_att'].fillna(0)
    # df_pfr_stats['passing_yards'] = df_pfr_stats['pass_yds'].fillna(0)
    # df_pfr_stats['passing_tds'] = df_pfr_stats['pass_td'].fillna(0)
    # df_pfr_stats['interceptions'] = df_pfr_stats['pass_int'].fillna(0)
    # df_pfr_stats['sacks'] = df_pfr_stats['pass_sacked'].fillna(0)
    # df_pfr_stats['carries'] = df_pfr_stats['rush_att'].fillna(0)
    # df_pfr_stats['rushing_yards'] = df_pfr_stats['rush_yds'].fillna(0)
    # df_pfr_stats['rushing_tds'] = df_pfr_stats['rush_td'].fillna(0)
    # df_pfr_stats['rushing_fumbles'] = df_pfr_stats['fumbles'].fillna(0)
    # df_pfr_stats['receptions'] = df_pfr_stats['rec'].fillna(0)
    # df_pfr_stats['targets'] = df_pfr_stats['targets'].fillna(0)
    # df_pfr_stats['receiving_yards'] = df_pfr_stats['rec_yds'].fillna(0)
    # df_pfr_stats['receiving_tds'] = df_pfr_stats['rec_td'].fillna(0)
    # df_pfr_stats['receiving_fumbles'] = df_pfr_stats['fumbles'].fillna(0)
    df_pfr_stats['fantasy_points_ppr'] = None  # Would need to calculate
    df_pfr_stats['home_team'] = df_pfr_stats['game_id'].str.split('_').str[3]
    df_pfr_stats['away_team'] = df_pfr_stats['game_id'].str.split('_').str[2]
    df_pfr_stats['home_team'] = df_pfr_stats['home_team'].replace(standardize_mapping)
    df_pfr_stats['away_team'] = df_pfr_stats['away_team'].replace(standardize_mapping)
    # df_pfr_stats['player_current_team'] = df_pfr_stats['player_current_team'].replace(standardize_mapping)
    df_pfr_stats['team'] = df_pfr_stats['team'].replace(standardize_mapping)
    numeric_columns = ['pass_cmp', 'pass_att', 'pass_yds', 'pass_td', 'pass_int', 'pass_sacked',
                      'rush_att', 'rush_yds', 'rush_td', 'rec', 'targets', 'rec_yds', 'rec_td', 'fumbles']
    for col in numeric_columns:
        if col in df_pfr_stats.columns:
            df_pfr_stats[col] = df_pfr_stats[col].fillna(0)
    df_pfr_stats.to_csv(f'{final_pfr_dir}/player_stats_pfr.csv', index=False)
    print(f"✅ PlayerStats CSV created with {len(df_pfr_stats)} records")
else:
    print("❌ No PFR passing/rushing/receiving data found")
    print("   Make sure ScraperFinal.py has been run to create the PFR data file")
    exit()

##### Create additional PFR CSV files #####
print("\n3. Creating additional PFR CSV files...")

# Box Scores
if os.path.exists('./data/all_box_scores.csv'):
    box_scores_df = pd.read_csv('./data/all_box_scores.csv')
    box_scores_df.to_csv(f'{final_pfr_dir}/box_scores_pfr.csv', index=False)
    print(f"✅ BoxScores CSV created with {len(box_scores_df)} records")

# Scoring Tables
if os.path.exists('./data/all_scoring_tables.csv'):
    scoring_tables_df = pd.read_csv('./data/all_scoring_tables.csv')
    scoring_tables_df.to_csv(f'{final_pfr_dir}/scoring_tables_pfr.csv', index=False)
    print(f"✅ ScoringTables CSV created with {len(scoring_tables_df)} records")

# Team Stats
if os.path.exists('./data/all_team_stats.csv'):
    team_stats_df = pd.read_csv('./data/all_team_stats.csv')
    team_stats_df.to_csv(f'{final_pfr_dir}/team_stats_pfr.csv', index=False)
    print(f"✅ TeamStats CSV created with {len(team_stats_df)} records")

# Team Conversions
if os.path.exists('./data/all_team_conversions.csv'):
    team_conversions_df = pd.read_csv('./data/all_team_conversions.csv')
    team_conversions_df.to_csv(f'{final_pfr_dir}/team_conversions_pfr.csv', index=False)
    print(f"✅ TeamConversions CSV created with {len(team_conversions_df)} records")

# Defense Game Logs
if os.path.exists('./data/all_defense-game-logs.csv'):
    defense_df = pd.read_csv('./data/all_defense-game-logs.csv')
    defense_df.to_csv(f'{final_pfr_dir}/defense_game_logs_pfr.csv', index=False)
    print(f"✅ DefenseGameLogs CSV created with {len(defense_df)} records")

# Schedule & Game Results
if os.path.exists('./data/SR-schedule-and-game-results/all_teams_schedule_and_game_results_merged.csv'):
    schedule_df = pd.read_csv('./data/SR-schedule-and-game-results/all_teams_schedule_and_game_results_merged.csv')
    schedule_df.to_csv(f'{final_pfr_dir}/schedule_game_results_pfr.csv', index=False)
    print(f"✅ ScheduleGameResults CSV created with {len(schedule_df)} records")

##### Create comprehensive game logs CSV #####
print("\n4. Creating comprehensive game logs CSV...")
if os.path.exists('./data/all_team_game_logs.csv'):
    comprehensive_games_df = pd.read_csv('./data/all_team_game_logs.csv')
    comprehensive_games_df.to_csv(f'{final_pfr_dir}/game_logs_pfr.csv', index=False)
    print(f"✅ Created game_logs_pfr.csv: {len(comprehensive_games_df)} records with {len(comprehensive_games_df.columns)} columns")
else:
    print("⚠️  Cannot create comprehensive game logs - missing all_team_game_logs.csv data")



##### Clean up redundant files #####
# games_pfr.csv
# team_game_logs_pfr.csv
# passing_rushing_receiving_pfr.csv
print("\n6. Cleaning up redundant files...")
# if os.path.exists(f'{final_pfr_dir}/games_pfr.csv'):
#     os.remove(f'{final_pfr_dir}/games_pfr.csv')
#     print("✅ Removed redundant games_pfr.csv (data included in game_logs_pfr.csv)")
# if os.path.exists(f'{final_pfr_dir}/team_game_logs_pfr.csv'):
#     os.remove(f'{final_pfr_dir}/team_game_logs_pfr.csv')
#     print("✅ Removed redundant team_game_logs_pfr.csv (data included in game_logs_pfr.csv)")
if os.path.exists(f'{final_pfr_dir}/passing_rushing_receiving_pfr.csv'):
    os.remove(f'{final_pfr_dir}/passing_rushing_receiving_pfr.csv')
    print("✅ Removed redundant passing_rushing_receiving_pfr.csv (data included in player_stats_pfr.csv)")


##### Apply filtering to remove unplayed games #####
if WEEK_LIMIT is not None:
    print(f"\n6. Applying week {WEEK_LIMIT} filtering to remove unplayed games...")
    
    # Filter player_stats_pfr.csv
    if os.path.exists(f'{final_pfr_dir}/player_stats_pfr.csv'):
        df = pd.read_csv(f'{final_pfr_dir}/player_stats_pfr.csv')
        original_count = len(df)
        # Only filter 2025 data, keep all historical seasons (2015-2024)
        df_2025 = df[df['season'] == 2025]
        df_other_seasons = df[df['season'] != 2025]
        df_2025_filtered = df_2025[df_2025['week'] <= WEEK_LIMIT]
        df_2025_filtered = df_2025_filtered[~((df_2025_filtered['home_pts_off'] == 0) & (df_2025_filtered['away_pts_off'] == 0))] if 'home_pts_off' in df_2025_filtered.columns and 'away_pts_off' in df_2025_filtered.columns else df_2025_filtered
        df = pd.concat([df_other_seasons, df_2025_filtered], ignore_index=True)
        df.to_csv(f'{final_pfr_dir}/player_stats_pfr.csv', index=False)
        print(f"✅ Filtered player_stats_pfr.csv: {original_count} → {len(df)} records (only 2025 data filtered)")
    
    # Filter scoring_tables_pfr.csv
    if os.path.exists(f'{final_pfr_dir}/scoring_tables_pfr.csv'):
        df = pd.read_csv(f'{final_pfr_dir}/scoring_tables_pfr.csv')
        original_count = len(df)
        df['week'] = df['Game_ID'].str.extract(r'(\d+)_(\d+)_')[1].astype(int)
        df['season'] = df['Game_ID'].str.extract(r'(\d+)_(\d+)_')[0].astype(int)
        # Only filter 2025 data, keep all historical seasons (2015-2024)
        df_2025 = df[df['season'] == 2025]
        df_other_seasons = df[df['season'] != 2025]
        df_2025_filtered = df_2025[df_2025['week'] <= WEEK_LIMIT]
        df = pd.concat([df_other_seasons, df_2025_filtered], ignore_index=True)
        df = df.drop(['week', 'season'], axis=1)
        df.to_csv(f'{final_pfr_dir}/scoring_tables_pfr.csv', index=False)
        print(f"✅ Filtered scoring_tables_pfr.csv: {original_count} → {len(df)} records (only 2025 data filtered)")
    
    # Filter defense_game_logs_pfr.csv
    if os.path.exists(f'{final_pfr_dir}/defense_game_logs_pfr.csv'):
        df = pd.read_csv(f'{final_pfr_dir}/defense_game_logs_pfr.csv')
        original_count = len(df)
        df['week'] = df['game_id'].str.extract(r'(\d+)_(\d+)_')[1].astype(int)
        df['season'] = df['game_id'].str.extract(r'(\d+)_(\d+)_')[0].astype(int)
        # Only filter 2025 data, keep all historical seasons (2015-2024)
        df_2025 = df[df['season'] == 2025]
        df_other_seasons = df[df['season'] != 2025]
        df_2025_filtered = df_2025[df_2025['week'] <= WEEK_LIMIT]
        df = pd.concat([df_other_seasons, df_2025_filtered], ignore_index=True)
        df = df.drop(['week', 'season'], axis=1)
        df.to_csv(f'{final_pfr_dir}/defense_game_logs_pfr.csv', index=False)
        print(f"✅ Filtered defense_game_logs_pfr.csv: {original_count} → {len(df)} records (only 2025 data filtered)")
    
    # Filter schedule_game_results_pfr.csv
    if os.path.exists(f'{final_pfr_dir}/schedule_game_results_pfr.csv'):
        df = pd.read_csv(f'{final_pfr_dir}/schedule_game_results_pfr.csv')
        original_count = len(df)
        df['Week_numeric'] = pd.to_numeric(df['Week'], errors='coerce')
        # Only filter 2025 data, keep all historical seasons (2015-2024)
        df_2025 = df[df['Season'] == 2025]
        df_other_seasons = df[df['Season'] != 2025]
        df_2025_filtered = df_2025[df_2025['Week_numeric'] <= WEEK_LIMIT]
        df = pd.concat([df_other_seasons, df_2025_filtered], ignore_index=True)
        df = df.drop('Week_numeric', axis=1)
        df.to_csv(f'{final_pfr_dir}/schedule_game_results_pfr.csv', index=False)
        print(f"✅ Filtered schedule_game_results_pfr.csv: {original_count} → {len(df)} records (only 2025 data filtered)")
    
    # Filter game_logs_pfr.csv
    if os.path.exists(f'{final_pfr_dir}/game_logs_pfr.csv'):
        df = pd.read_csv(f'{final_pfr_dir}/game_logs_pfr.csv')
        original_count = len(df)
        df['week'] = df['game_id'].str.extract(r'(\d+)_(\d+)_')[1].astype(int)
        df['season'] = df['game_id'].str.extract(r'(\d+)_(\d+)_')[0].astype(int)
        # Only filter 2025 data, keep all historical seasons (2015-2024)
        df_2025 = df[df['season'] == 2025]
        df_other_seasons = df[df['season'] != 2025]
        df_2025_filtered = df_2025[df_2025['week'] <= WEEK_LIMIT]
        df_2025_filtered = df_2025_filtered[~((df_2025_filtered['home_pts_off'] == 0) & (df_2025_filtered['away_pts_off'] == 0))] if 'home_pts_off' in df_2025_filtered.columns and 'away_pts_off' in df_2025_filtered.columns else df_2025_filtered
        df = pd.concat([df_other_seasons, df_2025_filtered], ignore_index=True)
        df = df.drop(['week', 'season'], axis=1)
        df.to_csv(f'{final_pfr_dir}/game_logs_pfr.csv', index=False)
        print(f"✅ Filtered game_logs_pfr.csv: {original_count} → {len(df)} records (only 2025 data filtered)")

##### Final Summary #####
print(f"\n{'='*80}")
print(f"🎯 FILTERING SUMMARY")
print(f"{'='*80}")
if WEEK_LIMIT:
    print(f"✅ Filtered 2025 data to include only games from weeks 1-{WEEK_LIMIT}")
    print(f"✅ Preserved all historical seasons (2015-2024) completely")
    print(f"✅ Removed unplayed 2025 games (0-0 scores) from all datasets")
    print(f"✅ This ensures only completed 2025 games are included while keeping all historical data")
else:
    print(f"⚠️  No filtering applied - all games (including unplayed) are included")
    print(f"💡 Use: ./scrape.sh <week_number> to filter out unplayed 2025 games")

print(f"\n📁 Final data saved to: {final_pfr_dir}/")
# print(f"📊 Available datasets:")
# print("  • teams_pfr.csv - Team information")
# print("  • player_stats_pfr.csv - Player statistics from PFR data")
# print("  • box_scores_pfr.csv - Quarter-by-quarter scoring")
# print("  • scoring_tables_pfr.csv - Play-by-play scoring details")
# print("  • team_stats_pfr.csv - Team statistics and rankings")
# print("  • team_conversions_pfr.csv - 3rd/4th down efficiency")
# print("  • defense_game_logs_pfr.csv - Defensive player stats")
# print("  • schedule_game_results_pfr.csv - Schedule and game results data")
# print("  • game_logs_pfr.csv - Comprehensive game data (games + team stats)")