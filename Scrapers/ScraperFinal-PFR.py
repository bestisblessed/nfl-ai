# **PFR-Only NFL Data Scraper**
# Creates nfl-db-pfr.db database using only Pro Football Reference (PFR) data
# This script uses existing PFR-scraped data files to build a consistent database

import pandas as pd
import sqlite3
import os
from datetime import datetime

print("="*80)
print("CREATING PFR-ONLY NFL DATABASE")
print("="*80)

# Create database connection
db_path = 'nfl-db-pfr.db'

# Team name standardization mapping
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

##### Create 'Teams' table #####
print("\n1. Creating Teams table...")
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
with sqlite3.connect(db_path) as conn:
    df_teams.to_sql('Teams', conn, if_exists='replace', index=False)
print(f"✅ Teams table created with {len(df_teams)} teams")

##### Create 'Games' table from PFR team game logs #####
print("\n2. Creating Games table from PFR team game logs...")
game_dataframes = []

for year in range(2018, 2026):
    file_path = f'./data/SR-game-logs/all_teams_game_logs_{year}.csv'
    # Always process 2025 data even if file exists, skip historical data if file exists
    if year == 2025 or os.path.exists(file_path):
        if year == 2025:
            print(f"   Loading {year} game logs (always processing 2025 data)...")
        else:
            print(f"   Loading {year} game logs...")
        df = pd.read_csv(file_path)
        
        # Create game records from team game logs
        df['season'] = year
        df['week'] = df['week']
        df['date'] = pd.to_datetime(df['date'])
        
        # Extract team abbreviation from team name
        df['home_team'] = df['team_name'].str.extract(r'(\w+)')[0]
        df['away_team'] = df['opp']
        df['home_score'] = df['pts']
        df['away_score'] = df['pts_opp']
        df['game_location'] = df['game_location']
        df['result'] = df['result']
        df['overtime'] = df['ot'].fillna(0)
        
        # Create game_id
        df['game_id'] = df.apply(lambda row: f"{year}_{row['week']:02d}_{row['away_team']}_{row['home_team']}", axis=1)
        
        game_dataframes.append(df[['game_id', 'season', 'week', 'date', 'home_team', 'away_team', 'home_score', 'away_score', 'game_location', 'result', 'overtime']])
    else:
        print(f"   ⚠️  No game log data found for {year}")

if game_dataframes:
    df_games = pd.concat(game_dataframes, ignore_index=True)
    # Remove duplicates (each game appears twice - once for each team)
    df_games = df_games.drop_duplicates(subset=['game_id'], keep='first')
    df_games = df_games.sort_values(['season', 'week', 'date'])
    
    # Apply team name standardization
    df_games['away_team'] = df_games['away_team'].replace(standardize_mapping)
    df_games['home_team'] = df_games['home_team'].replace(standardize_mapping)
    
    # Save to database
    with sqlite3.connect(db_path) as conn:
        df_games.to_sql('Games', conn, if_exists='replace', index=False)
    
    # Save to CSV for reference
    df_games.to_csv('./data/games-pfr.csv', index=False)
    print(f"✅ Games table created with {len(df_games)} games")
else:
    print("❌ No PFR game log data found")
    exit()

##### Create 'PlayerStats' table from PFR passing/rushing/receiving data #####
print("\n3. Creating PlayerStats table from PFR passing/rushing/receiving data...")

# Use the clean PFR passing/rushing/receiving data (without NFLverse position data)
if os.path.exists('./data/all_passing_rushing_receiving_pfr_clean.csv'):
    print("   Loading clean PFR passing/rushing/receiving data (no NFLverse contamination)...")
    df_pfr_stats = pd.read_csv('./data/all_passing_rushing_receiving_pfr_clean.csv')
    
    # Create a simplified PlayerStats structure from PFR data
    df_pfr_stats['player_display_name'] = df_pfr_stats['player']
    df_pfr_stats['player_current_team'] = df_pfr_stats['team']
    df_pfr_stats['season'] = df_pfr_stats['game_id'].str.split('_').str[0].astype(int)
    df_pfr_stats['week'] = df_pfr_stats['game_id'].str.split('_').str[1].astype(int)
    # df_pfr_stats['position'] = df_pfr_stats['position']
    # Position column will be None since we're using clean PFR data without NFLverse position info
    df_pfr_stats['position'] = None
    df_pfr_stats['headshot_url'] = None
    df_pfr_stats['completions'] = df_pfr_stats['pass_cmp'].fillna(0)
    df_pfr_stats['attempts'] = df_pfr_stats['pass_att'].fillna(0)
    df_pfr_stats['passing_yards'] = df_pfr_stats['pass_yds'].fillna(0)
    df_pfr_stats['passing_tds'] = df_pfr_stats['pass_td'].fillna(0)
    df_pfr_stats['interceptions'] = df_pfr_stats['pass_int'].fillna(0)
    df_pfr_stats['sacks'] = df_pfr_stats['pass_sacked'].fillna(0)
    df_pfr_stats['carries'] = df_pfr_stats['rush_att'].fillna(0)
    df_pfr_stats['rushing_yards'] = df_pfr_stats['rush_yds'].fillna(0)
    df_pfr_stats['rushing_tds'] = df_pfr_stats['rush_td'].fillna(0)
    df_pfr_stats['rushing_fumbles'] = df_pfr_stats['fumbles'].fillna(0)
    df_pfr_stats['receptions'] = df_pfr_stats['rec'].fillna(0)
    df_pfr_stats['targets'] = df_pfr_stats['targets'].fillna(0)
    df_pfr_stats['receiving_yards'] = df_pfr_stats['rec_yds'].fillna(0)
    df_pfr_stats['receiving_tds'] = df_pfr_stats['rec_td'].fillna(0)
    df_pfr_stats['receiving_fumbles'] = df_pfr_stats['fumbles'].fillna(0)
    df_pfr_stats['fantasy_points_ppr'] = None  # Would need to calculate
    
    # Get home/away teams from game_id
    df_pfr_stats['home_team'] = df_pfr_stats['game_id'].str.split('_').str[3]
    df_pfr_stats['away_team'] = df_pfr_stats['game_id'].str.split('_').str[2]
    
    # Apply team name standardization
    df_pfr_stats['home_team'] = df_pfr_stats['home_team'].replace(standardize_mapping)
    df_pfr_stats['away_team'] = df_pfr_stats['away_team'].replace(standardize_mapping)
    df_pfr_stats['player_current_team'] = df_pfr_stats['player_current_team'].replace(standardize_mapping)
    
    # Save to CSV for reference
    df_pfr_stats.to_csv('./data/player_stats-pfr.csv', index=False)
    
    # Create table structure
    create_table_sql = '''
    CREATE TABLE IF NOT EXISTS PlayerStats (
        player_display_name TEXT,
        game_id TEXT,
        season INTEGER,
        week INTEGER,
        position TEXT,
        headshot_url TEXT,
        completions INTEGER,
        attempts INTEGER,
        passing_yards INTEGER,
        passing_tds INTEGER,
        interceptions INTEGER,
        sacks INTEGER,
        carries INTEGER,
        rushing_yards INTEGER,
        rushing_tds INTEGER,
        rushing_fumbles INTEGER,
        receptions INTEGER,
        targets INTEGER,
        receiving_yards INTEGER,
        receiving_tds INTEGER,
        receiving_fumbles INTEGER,
        fantasy_points_ppr REAL,
        home_team TEXT,
        away_team TEXT,
        player_current_team TEXT
    );
    '''
    
    # Save to database
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(create_table_sql)
        columns_to_import = ['player_display_name', 'player_current_team', 'game_id', 'season', 'week', 
                           'position', 'headshot_url', 'completions', 'attempts', 'passing_yards', 
                           'passing_tds', 'interceptions', 'sacks', 'carries', 'rushing_yards', 
                           'rushing_tds', 'rushing_fumbles', 'receptions', 'targets', 'receiving_yards', 
                           'receiving_tds', 'receiving_fumbles', 'fantasy_points_ppr', 'home_team', 'away_team']
        df_pfr_to_import = df_pfr_stats[columns_to_import]
        df_pfr_to_import.to_sql('PlayerStats', conn, if_exists='replace', index=False)
    
    print(f"✅ PlayerStats table created with {len(df_pfr_stats)} records")
else:
    print("❌ No clean PFR passing/rushing/receiving data found")
    print("   Make sure ScraperFinal.py has been run to create the clean PFR data file")
    exit()

##### Create additional PFR tables #####
print("\n4. Creating additional PFR tables...")

# Box Scores
if os.path.exists('./data/all_box_scores.csv'):
    box_scores_df = pd.read_csv('./data/all_box_scores.csv')
    with sqlite3.connect(db_path) as conn:
        box_scores_df.to_sql('BoxScores', conn, if_exists='replace', index=False)
    print(f"✅ BoxScores table created with {len(box_scores_df)} records")

# Scoring Tables
if os.path.exists('./data/all_scoring_tables.csv'):
    scoring_tables_df = pd.read_csv('./data/all_scoring_tables.csv')
    with sqlite3.connect(db_path) as conn:
        scoring_tables_df.to_sql('ScoringTables', conn, if_exists='replace', index=False)
    print(f"✅ ScoringTables table created with {len(scoring_tables_df)} records")

# Team Game Logs
if os.path.exists('./data/all_team_game_logs.csv'):
    team_game_logs_df = pd.read_csv('./data/all_team_game_logs.csv')
    with sqlite3.connect(db_path) as conn:
        team_game_logs_df.to_sql('TeamGameLogs', conn, if_exists='replace', index=False)
    print(f"✅ TeamGameLogs table created with {len(team_game_logs_df)} records")

# Team Stats
if os.path.exists('./data/all_team_stats.csv'):
    team_stats_df = pd.read_csv('./data/all_team_stats.csv')
    with sqlite3.connect(db_path) as conn:
        team_stats_df.to_sql('TeamStats', conn, if_exists='replace', index=False)
    print(f"✅ TeamStats table created with {len(team_stats_df)} records")

# Team Conversions
if os.path.exists('./data/all_team_conversions.csv'):
    team_conversions_df = pd.read_csv('./data/all_team_conversions.csv')
    with sqlite3.connect(db_path) as conn:
        team_conversions_df.to_sql('TeamConversions', conn, if_exists='replace', index=False)
    print(f"✅ TeamConversions table created with {len(team_conversions_df)} records")

# Passing/Rushing/Receiving
if os.path.exists('./data/all_passing_rushing_receiving_pfr_clean.csv'):
    print("   Loading clean Passing/Rushing/Receiving data (no NFLverse contamination)...")
    passing_rushing_receiving_df = pd.read_csv('./data/all_passing_rushing_receiving_pfr_clean.csv')
    with sqlite3.connect(db_path) as conn:
        passing_rushing_receiving_df.to_sql('PassingRushingReceiving', conn, if_exists='replace', index=False)
    print(f"✅ PassingRushingReceiving table created with {len(passing_rushing_receiving_df)} records")

# Defense Game Logs
if os.path.exists('./data/all_defense-game-logs.csv'):
    defense_df = pd.read_csv('./data/all_defense-game-logs.csv')
    with sqlite3.connect(db_path) as conn:
        defense_df.to_sql('DefenseGameLogs', conn, if_exists='replace', index=False)
    print(f"✅ DefenseGameLogs table created with {len(defense_df)} records")

# Schedule & Game Results
if os.path.exists('./data/SR-schedule-and-game-results/all_teams_schedule_and_game_results_merged.csv'):
    schedule_df = pd.read_csv('./data/SR-schedule-and-game-results/all_teams_schedule_and_game_results_merged.csv')
    with sqlite3.connect(db_path) as conn:
        schedule_df.to_sql('ScheduleGameResults', conn, if_exists='replace', index=False)
    print(f"✅ ScheduleGameResults table created with {len(schedule_df)} records")

##### Create PFR final data export #####
print("\n5. Creating PFR final data export...")
final_pfr_dir = 'final_data_pfr'

if not os.path.exists(final_pfr_dir):
    os.makedirs(final_pfr_dir)

# Export all tables to CSV
with sqlite3.connect(db_path) as conn:
    # Games
    games_df = pd.read_sql_query("SELECT * FROM Games", conn)
    games_df.to_csv(f"{final_pfr_dir}/games_pfr.csv", index=False)
    print(f"✅ Exported Games: {len(games_df)} records")
    
    # PlayerStats
    playerstats_df = pd.read_sql_query("SELECT * FROM PlayerStats", conn)
    playerstats_df.to_csv(f"{final_pfr_dir}/player_stats_pfr.csv", index=False)
    print(f"✅ Exported PlayerStats: {len(playerstats_df)} records")
    
    # Teams
    teams_df = pd.read_sql_query("SELECT * FROM Teams", conn)
    teams_df.to_csv(f"{final_pfr_dir}/teams_pfr.csv", index=False)
    print(f"✅ Exported Teams: {len(teams_df)} records")
    
    # Additional tables
    table_mappings = {
        'BoxScores': 'box_scores_pfr',
        'ScoringTables': 'scoring_tables_pfr', 
        'TeamGameLogs': 'team_game_logs_pfr',
        'TeamStats': 'team_stats_pfr',
        'TeamConversions': 'team_conversions_pfr',
        'PassingRushingReceiving': 'passing_rushing_receiving_pfr',
        'DefenseGameLogs': 'defense_game_logs_pfr',
        'ScheduleGameResults': 'schedule_game_results_pfr'
    }
    
    for table_name, export_name in table_mappings.items():
        try:
            df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
            df.to_csv(f"{final_pfr_dir}/{export_name}.csv", index=False)
            print(f"✅ Exported {export_name}: {len(df)} records")
        except:
            print(f"⚠️  Table {table_name} not found")

print(f"\n🎉 PFR database creation completed!")
print(f"📁 Database: {db_path}")
print(f"📁 Final data: {final_pfr_dir}/")
print(f"📊 Available datasets:")
print("  • Games - Game schedules and results from PFR team logs")
print("  • PlayerStats - Player statistics from PFR passing/rushing/receiving data")
print("  • Teams - Team information")
print("  • BoxScores - Quarter-by-quarter scoring")
print("  • ScoringTables - Play-by-play scoring details")
print("  • TeamGameLogs - Team performance logs")
print("  • TeamStats - Team statistics and rankings")
print("  • TeamConversions - 3rd/4th down efficiency")
print("  • PassingRushingReceiving - Offensive player stats")
print("  • DefenseGameLogs - Defensive player stats")
print("  • ScheduleGameResults - Schedule and game results data")