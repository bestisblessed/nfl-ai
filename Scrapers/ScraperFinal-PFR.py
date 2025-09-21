'''
**PFR-Only NFL Data Scraper**
Creates CSV files using only Pro Football Reference (PFR) data
This script uses existing PFR-scraped data files to build comprehensive CSV datasets
'''

import pandas as pd
import os
from datetime import datetime

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
if os.path.exists('./data/all_passing_rushing_receiving_pfr_clean.csv'):
    print("   Loading clean PFR passing/rushing/receiving data (no NFLverse contamination)...")
    df_pfr_stats = pd.read_csv('./data/all_passing_rushing_receiving_pfr_clean.csv')
    # df_pfr_stats['player_display_name'] = df_pfr_stats['player']
    # df_pfr_stats['player_current_team'] = df_pfr_stats['team']
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
    print("❌ No clean PFR passing/rushing/receiving data found")
    print("   Make sure ScraperFinal.py has been run to create the clean PFR data file")
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

# Passing/Rushing/Receiving
if os.path.exists('./data/all_passing_rushing_receiving_pfr_clean.csv'):
    print("   Loading clean Passing/Rushing/Receiving data (no NFLverse contamination)...")
    passing_rushing_receiving_df = pd.read_csv('./data/all_passing_rushing_receiving_pfr_clean.csv')
    passing_rushing_receiving_df.to_csv(f'{final_pfr_dir}/passing_rushing_receiving_pfr.csv', index=False)
    print(f"✅ PassingRushingReceiving CSV created with {len(passing_rushing_receiving_df)} records")

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
    # Use the aggregated team game logs directly as the comprehensive game logs
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


# ##### Final Print
# print(f"📁 Final data: {final_pfr_dir}/")
# print(f"📊 Available datasets:")
# print("  • teams_pfr - Team information")
# # print("  • games_pfr - Game results and metadata")
# print("  • player_stats_pfr - Player statistics from PFR data (enhanced with season/week/team context)")
# print("  • box_scores_pfr - Quarter-by-quarter scoring")
# print("  • scoring_tables_pfr - Play-by-play scoring details")
# # print("  • team_game_logs_pfr - Team performance by game")
# print("  • team_stats_pfr - Team statistics and rankings")
# print("  • team_conversions_pfr - 3rd/4th down efficiency")
# # print("  • passing_rushing_receiving_pfr - Offensive player stats")
# print("  • defense_game_logs_pfr - Defensive player stats")
# print("  • schedule_game_results_pfr - Schedule and game results data")
# print("  • game_logs_pfr - Comprehensive game data (games + team stats)")