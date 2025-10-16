# **Teams Information**
# Scrapes team IDs, names, and divisions to populate the `Teams` table in `nfl.db`.
  
# **Games Data**
# Downloads and processes game information from NFL data sources to populate the `Games` table.
  
# **Player Statistics**
# Downloads, cleans, and merges player statistics data for multiple years to populate the `PlayerStats` table.
  
# **Rosters**
# Downloads and processes team rosters for multiple years to populate the `Rosters` table.
  
# **Box Scores**
# Scrapes box score details for games from Pro-Football-Reference and saves them to CSV and the database.
  
# **Scoring Tables / Touchdown Logs**
# Scrapes scoring play-by-play data for games and saves them to CSV files.
  
# **Team Game Logs**
# Scrapes game logs for each team, including both team and opponent statistics, and aggregates them into CSV files.

# **Team Stats and Rankings**
# Scrapes comprehensive team statistics and rankings for each team and year, saving the data to CSV files.
  
# **Schedule & Game Results**
# Scrapes schedule and game result details for each team and year, saving the data to CSV files.
  
# **Team Conversions**
# Scrapes conversion metrics (e.g., 3rd down, 4th down) for each team and year, saving the data to CSV files.
  
# **Passing, Rushing, and Receiving Game Logs**
# Scrapes individual player game logs for passing, rushing, and receiving statistics, cleans the data, and merges it into consolidated CSV files.
  
# **Defense Game Logs**
# Scrapes defensive statistics for players in each game and saves the data to CSV files.

# **Red Zone Statistics**
# Scrapes red zone passing, rushing, and receiving statistics from Pro-Football-Reference and saves them to CSV files.

# **Note: This scraper focuses on 2025 season updates**
  

import pandas as pd
import sqlite3
import requests
import os
import csv
from bs4 import BeautifulSoup, Comment
import time
from time import sleep
import numpy as np
from datetime import datetime, timedelta
from requests.exceptions import Timeout, RequestException


# Print start time
start_time = datetime.now()
print(f"\nProcess started at: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")

if not os.path.exists('data'):
    os.system('mkdir data')
if not os.path.exists('data/rosters'):
    os.system('mkdir data/rosters')
if not os.path.exists('data/player-stats'):
    os.system('mkdir data/player-stats')
if not os.path.exists('data/SR-scoring-tables'):
    os.system('mkdir data/SR-scoring-tables')
if os.path.exists('nfl.db'):
    os.remove('nfl.db')

##### Create 'Teams' in nfl.db #####
print("\n" + "*"*80 + "\n")
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
    ['SEA', 'Seattle Seahawks', 'NFC West'],
    ['SF', 'San Francisco 49ers', 'NFC West'],
    ['TB', 'Tampa Bay Buccaneers', 'NFC South'],
    ['TEN', 'Tennessee Titans', 'AFC South'],
    ['WAS', 'Washington Commanders', 'NFC East']
]
df_teams = pd.DataFrame(teams, columns=['TeamID', 'Team', 'Division'])
with sqlite3.connect('nfl.db') as conn:
    df_teams.to_sql('Teams', conn, if_exists='replace', index=False)


##### Create 'Games' in nfl.db #####
url = 'https://raw.githubusercontent.com/nflverse/nfldata/master/data/games.csv'
response = requests.get(url)
if response.ok:
    with open('./data/games.csv', 'wb') as file:
        file.write(response.content)
else:
    raise Exception(f"Failed to download the file. Status code: {response.status_code}")
df = pd.read_csv('./data/games.csv')
df = df[df['season'] >= 2017]
standardize_mapping = {
    'OAK': 'LVR',  
    'SD': 'LAC',   
    'STL': 'LAR',  
    'LA': 'LAR',   
    'LV': 'LVR'    
}
df['away_team'] = df['away_team'].replace(standardize_mapping)
df['home_team'] = df['home_team'].replace(standardize_mapping)
df.rename(columns={'gameday': 'date'}, inplace=True)
df = df[df['season'] != 1999]
df['game_id'] = df['game_id'].apply(lambda x: f"{x.split('_')[0]}_{x.split('_')[1]}_{standardize_mapping.get(x.split('_')[2], x.split('_')[2])}_{standardize_mapping.get(x.split('_')[3], x.split('_')[3])}")
df['date'] = pd.to_datetime(df['date'])
df['week'] = df['week'].apply(lambda x: f'{x:02d}')
df['game_id_simple'] = df['season'].astype(str) + "_" + df['week']
df['game_id_team1'] = df['game_id_simple'] + "_" + df['home_team']
df['game_id_team2'] = df['game_id_simple'] + "_" + df['away_team']
selected_columns = [
    'game_id', 'season', 'week', 'game_type', 'date', 'weekday', 'gametime', 
    'away_team', 'away_score', 'home_team', 'home_score', 'location', 'result',	'total', 'overtime', 
    'spread_line', 'total_line', 'away_rest', 'home_rest', 'roof', 'surface', 'temp', 'wind', 
    'away_qb_id', 'home_qb_id', 'away_qb_name', 'home_qb_name', 'away_coach', 'home_coach', 'referee',
    'stadium_id', 'stadium', 'game_id_simple', 'game_id_team1', 'game_id_team2', 'pfr'
]
df_selected = df[selected_columns]
db_path = 'nfl.db'
conn = sqlite3.connect(db_path)
df_selected.to_sql('Games', conn, if_exists='replace', index=False)
conn.close()
# df_selected.to_csv('./data/games_modified.csv', index=False)
df_selected.to_csv('./data/games.csv', index=False)


##### Create 'PlayerStats' in nfl.db #####
dataframes = []
for year in range(2025, 2026):
    file_path = os.path.join('./data/player-stats/', f"player_stats_{year}.csv")
    # Always download current year player stats even if file exists
    url = f"https://github.com/nflverse/nflverse-data/releases/download/player_stats/player_stats_{year}.csv"
    response = requests.get(url)
    if response.ok:
        with open(file_path, 'wb') as file:
            file.write(response.content)
        print(f"Downloaded and saved player_stats_{year}.csv")
        df = pd.read_csv(file_path)
        if 'opponent_team' in df.columns:
            df = df.drop(columns=['opponent_team'])
        dataframes.append(df)
    else:
        print(f"Failed to download data for the year {year}")
if len(dataframes) > 0:
    merged_df = pd.concat(dataframes, ignore_index=True, sort=False)
    standardize_mapping = {
        'OAK': 'LVR',  
        'SD': 'LAC',   
        'STL': 'LAR',  
        'LA': 'LAR',   
        'LV': 'LVR'    
    }
    merged_df['recent_team'] = merged_df['recent_team'].replace(standardize_mapping)
    merged_df['week'] = merged_df['week'].apply(lambda x: f'{x:02d}')
    merged_df['game_id_team'] = merged_df['season'].astype(str) + '_' + merged_df['week'].astype(str) + '_' + merged_df['recent_team']
    merged_df['game_id_simple'] = merged_df['season'].astype(str) + '_' + merged_df['week'].astype(str)
    merged_df.to_csv('./data/player_stats.csv', index=False)
    print("Merged and cleaned player stats saved to './data/player_stats.csv'")
    # games_df = pd.read_csv('./data/games_modified.csv')
    games_df = pd.read_csv('./data/games.csv')
    game_id_map = pd.concat([
        games_df[['game_id_team1', 'game_id', 'home_team', 'away_team']].rename(columns={'game_id_team1': 'game_id_team'}),
        games_df[['game_id_team2', 'game_id', 'home_team', 'away_team']].rename(columns={'game_id_team2': 'game_id_team'})
    ]).drop_duplicates(subset=['game_id_team'])
    merged_df = merged_df.merge(game_id_map, on='game_id_team', how='left')
    position_groups_to_remove = ['SPEC', 'LB', 'DB', 'OL', 'DL']
    df_cleaned = merged_df[~merged_df['position_group'].isin(position_groups_to_remove)].dropna(subset=['position_group'])
    df_cleaned.to_csv('./data/player_stats.csv', index=False)
    print("Final cleaned player stats saved to './data/player_stats.csv'")
else:
    print("No new player stats available; keeping existing './data/player_stats.csv' and continuing.")
conn = sqlite3.connect('nfl.db')
cursor = conn.cursor()
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
cursor.execute(create_table_sql)
df = pd.read_csv('./data/player_stats.csv')
df.rename(columns={'recent_team': 'player_current_team'}, inplace=True)
columns_to_import = ['player_display_name', 'player_current_team', 'game_id', 'season', 'week', 
                     'position', 'headshot_url', 'completions', 'attempts', 'passing_yards', 
                     'passing_tds', 'interceptions', 'sacks', 'carries', 'rushing_yards', 
                     'rushing_tds', 'rushing_fumbles', 'receptions', 'targets', 'receiving_yards', 
                     'receiving_tds', 'receiving_fumbles', 'fantasy_points_ppr', 'home_team', 'away_team']
df_to_import = df[columns_to_import]
df_to_import.to_sql('PlayerStats', conn, if_exists='replace', index=False)
conn.close()
print("Player stats saved to 'PlayerStats' table in nfl.db")


##### Create 'Rosters' in nfl.db (2025) #####
for year in range(2025, 2026):
    file_path = f"./data/rosters/roster_{year}.csv"
    # Always download current year roster data even if it exists
    url = f"https://github.com/nflverse/nflverse-data/releases/download/rosters/roster_{year}.csv"
    response = requests.get(url)
    if response.status_code == 200:
        with open(file_path, 'wb') as file:
            file.write(response.content)
        print(f"Downloaded and saved roster_{year}.csv")
    else:
        print(f"Failed to download data for the year {year}")
dataframes = []
for year in range(2025, 2026):
    file_path = f'./data/rosters/roster_{year}.csv'
    if os.path.exists(file_path):
        df = pd.read_csv(file_path)
        dataframes.append(df)
merged_data = pd.concat(dataframes, ignore_index=True)
base_url = "https://www.pro-football-reference.com/players/"
merged_data['url'] = merged_data['pfr_id'].apply(lambda x: f"{base_url}{x[0]}/{x}.htm" if pd.notna(x) else None)
merged_data.to_csv('./data/rosters.csv', index=False)
print("Final file saved to ./data/rosters.csv")
conn = sqlite3.connect('nfl.db')
cursor = conn.cursor()
cursor.execute("DROP TABLE IF EXISTS rosters")
create_table_sql = '''
CREATE TABLE IF NOT EXISTS Rosters (
    season INTEGER,
    team TEXT,
    position TEXT,
    depth_chart_position TEXT,
    status TEXT,
    full_name TEXT,
    first_name TEXT,
    last_name TEXT,
    birth_date TEXT,
    height REAL,
    weight REAL,
    college TEXT,
    pfr_id TEXT,
    years_exp REAL,
    headshot_url TEXT,
    week INTEGER,
    game_type TEXT,
    entry_year REAL,
    rookie_year REAL,
    draft_club TEXT,
    draft_number REAL,
    url TEXT
);
'''
cursor.execute(create_table_sql)
df = pd.read_csv('data/rosters.csv')
df.to_sql('Rosters', conn, if_exists='replace', index=False)
conn.close()
print("Rosters table created and data inserted successfully.")

##### Standardize Team Names in Rosters table #####
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
conn = sqlite3.connect('nfl.db')
cursor = conn.cursor()
df = pd.read_sql_query("SELECT * FROM Rosters", conn)
df['team'] = df['team'].replace(standardize_mapping)
df['draft_club'] = df['draft_club'].replace(standardize_mapping)
df.to_sql('Rosters', conn, if_exists='replace', index=False)
conn.close()
print("Rosters table standardized and updated successfully.")


##### Standardize Team Names in rosters.csv #####
file_path = 'data/rosters.csv'
rosters_df = pd.read_csv(file_path)
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
rosters_df['team'] = rosters_df['team'].replace(standardize_mapping)
standardized_teams = rosters_df['team'].unique()
standardized_team_list_sorted = sorted(list(standardized_teams))
for idx, team in enumerate(standardized_team_list_sorted, 1):
    print(f"{idx}. {team}")
rosters_df.to_csv('data/rosters.csv', index=False)


##### Scrape Box Scores (2025) #####
print("\n" + "*"*80 + "\n")
os.makedirs('./data/SR-box-scores/', exist_ok=True)
df = pd.read_csv('./data/games.csv')
df['pfr_url'] = 'https://www.pro-football-reference.com/boxscores/' + df['pfr'] + '.htm'
df.to_csv('./data/games.csv', index=False)
# csv_file_path = 'data/SR-box-scores/all_box_scores.csv'
games_csv_path = 'data/games.csv'
headers = ['URL', 'Team', '1', '2', '3', '4', 'OT1', 'OT2', 'OT3', 'OT4', 'Final']

for year_to_scrape in range(2025, 2026):
    output_filename = f'./data/SR-box-scores/all_box_scores_{year_to_scrape}.csv'
    existing_urls = set()
    if os.path.exists(output_filename):
        df_existing = pd.read_csv(output_filename)
        if 'URL' in df_existing.columns:
            existing_urls = set(df_existing['URL'].unique())
    
    mode = 'a' if os.path.exists(output_filename) else 'w'
    with open(output_filename, mode, newline='') as csvfile:
        score_writer = csv.writer(csvfile)
        if mode == 'w':
            score_writer.writerow(headers)
        
        game_urls = []
        with open(games_csv_path, 'r') as csvfile:
            reader = csv.DictReader(csvfile)
            now_dt = datetime.now()
            for row in reader:
                try:
                    game_dt = datetime.fromisoformat(row['date'])
                except Exception:
                    continue
                if row['season'] == str(year_to_scrape) and game_dt <= now_dt:
                    game_urls.append(row['pfr_url'])
        
        for url in game_urls:
            if url in existing_urls:
                print(f"Skipping already scraped game: {url}")
                continue
            try:    
                print(f"Scraping game: {url}")
                response = requests.get(url)
                response.raise_for_status()
                soup = BeautifulSoup(response.content, 'html.parser')
                linescore_table = soup.find('table', class_='linescore')
                if linescore_table:
                    rows = linescore_table.find_all('tr')[1:]
                    for row in rows:
                        cols = row.find_all('td')
                        team_name = cols[1].text.strip()
                        scores = [col.text.strip() for col in cols[2:]]
                        scores += [''] * (len(headers) - 2 - len(scores))
                        score_writer.writerow([url, team_name] + scores)
                time.sleep(2.5)
            except Exception as e:
                print(f"Error scraping {url}: {e}")
            time.sleep(2.5)
    print(f"Scraping completed for {year_to_scrape}. Box scores saved to {output_filename}.")


##### Merge Box Scores #####
input_dir = 'data/SR-box-scores/'
csv_files = [f for f in os.listdir(input_dir) if f.endswith('.csv')]
dataframes = [pd.read_csv(os.path.join(input_dir, file)) for file in csv_files]
merged_dataframe = pd.concat(dataframes, ignore_index=True)
output_file = 'data/all_box_scores.csv'
merged_dataframe.to_csv(output_file, index=False)
print(f"Merged dataset saved as {output_file}")


##### Fix OT Columns in Box Scores ##### 
df = pd.read_csv('data/all_box_scores.csv')
def shift_to_final(row):
    if pd.isna(row['Final']):  
        for col in reversed(row.index[:-1]):
            if pd.notna(row[col]):
                row['Final'] = row[col]
                row[col] = None
                break
    return row
df = df.apply(shift_to_final, axis=1)
df.to_csv('data/all_box_scores.csv', index=False)


##### Scrape Scoring Tables/Touchdown Logs (2025) #####
print("\n" + "*"*80 + "\n")
for year_to_scrape in range(2025, 2026):
    output_filename = f'./data/SR-scoring-tables/all_nfl_scoring_tables_{year_to_scrape}.csv'
    existing_game_ids = set()
    if os.path.exists(output_filename):
        df_existing = pd.read_csv(output_filename)
        if 'Game_ID' in df_existing.columns:
            existing_game_ids = set(df_existing['Game_ID'].unique())
    mode = 'a' if os.path.exists(output_filename) else 'w'
    with open(output_filename, mode, newline='') as output_csvfile:
        csvwriter = csv.writer(output_csvfile)
        if mode == 'w':
            csvwriter.writerow(['Quarter', 'Time', 'Team', 'Detail', 'Team_1', 'Team_2', 'Game_ID'])  
        with open('./data/games.csv', 'r') as csvfile:
            reader = csv.DictReader(csvfile)
            rows = []
            now_dt = datetime.now()
            for row in reader:
                try:
                    game_dt = datetime.fromisoformat(row['date'])
                except Exception:
                    continue
                if int(row['game_id'].split('_')[0]) == year_to_scrape and game_dt <= now_dt:
                    rows.append(row)
            for row in rows:
                pfr_value = row['pfr']
                game_id = row['game_id']
                if game_id in existing_game_ids:
                    print(f"Skipping already scraped game ID: {game_id}")
                    continue
                url = f"https://www.pro-football-reference.com/boxscores/{pfr_value}.htm"
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        response = requests.get(url, timeout=10)
                        response.raise_for_status()
                        soup = BeautifulSoup(response.text, 'html.parser')
                        table = soup.find('table', {'id': 'scoring'})
                        if table is None:
                            print(f"No scoring table found for {url}")
                            break
                        last_quarter = None  
                        for i, tr in enumerate(table.find_all('tr')):
                            if i == 0:  
                                continue
                            cells = tr.find_all(['td', 'th'])
                            if len(cells) > 0:
                                csv_row = [cell.text for cell in cells]
                                if csv_row[0]:
                                    last_quarter = csv_row[0]
                                else:
                                    csv_row[0] = last_quarter
                                csv_row.append(game_id)  
                                csvwriter.writerow(csv_row)
                        print(f"Successfully scraped scoring data for game ID: {game_id}, PFR: {pfr_value}")
                        break
                    except (requests.exceptions.RequestException, Exception) as e:
                        print(f"An error occurred while scraping {url}. Error: {e}")
                        if attempt < max_retries - 1:
                            time.sleep(2 ** attempt)
                        else:
                            break
                time.sleep(2.5)
    print(f"Scraping completed for {year_to_scrape}. Scoring data saved to {output_filename}.")


##### Merge Scoring Tables #####
input_dir = 'data/SR-scoring-tables/'
csv_files = [f for f in os.listdir(input_dir) if f.endswith('.csv')]
dataframes = [pd.read_csv(os.path.join(input_dir, file)) for file in csv_files]
merged_dataframe = pd.concat(dataframes, ignore_index=True)
output_file = 'data/all_scoring_tables.csv'
merged_dataframe.to_csv(output_file, index=False)
print(f"Merged dataset saved as {output_file}")


##### Scrape Team Game Logs (2025) #####
print("\n" + "*"*80 + "\n")
data_dir = './data/SR-game-logs'
os.makedirs(data_dir, exist_ok=True)
opponent_data_dir = './data/SR-opponent-game-logs'
os.makedirs(opponent_data_dir, exist_ok=True)
teams = [
    ['crd', 'Arizona Cardinals'],
    ['atl', 'Atlanta Falcons'],
    ['rav', 'Baltimore Ravens'],
    ['buf', 'Buffalo Bills'],
    ['car', 'Carolina Panthers'],
    ['chi', 'Chicago Bears'],
    ['cin', 'Cincinnati Bengals'],
    ['cle', 'Cleveland Browns'],
    ['dal', 'Dallas Cowboys'],
    ['den', 'Denver Broncos'],
    ['det', 'Detroit Lions'],
    ['gnb', 'Green Bay Packers'],
    ['htx', 'Houston Texans'],
    ['clt', 'Indianapolis Colts'],
    ['jax', 'Jacksonville Jaguars'],
    ['kan', 'Kansas City Chiefs'],
    ['sdg', 'Los Angeles Chargers'],
    ['ram', 'Los Angeles Rams'],
    ['rai', 'Las Vegas Raiders'],
    ['mia', 'Miami Dolphins'],
    ['min', 'Minnesota Vikings'],
    ['nwe', 'New England Patriots'],
    ['nor', 'New Orleans Saints'],
    ['nyg', 'New York Giants'],
    ['nyj', 'New York Jets'],
    ['phi', 'Philadelphia Eagles'],
    ['pit', 'Pittsburgh Steelers'],
    ['sea', 'Seattle Seahawks'],
    ['sfo', 'San Francisco 49ers'],
    ['tam', 'Tampa Bay Buccaneers'],
    ['oti', 'Tennessee Titans'],
    ['was', 'Washington Commanders']
]
# team_game_logs_headers = [
#     'rk', 'gtm', 'week', 'date', 'day', 'game_location', 'opp', 'result', 'pts', 'pts_opp', 'ot', 
#     'pass_cmp', 'pass_att', 'pass_cmp_pct', 'pass_yds', 'pass_td', 'pass_ya', 'pass_aya', 'pass_rate', 
#     'pass_sk', 'pass_sk_yds', 'rush_att', 'rush_yds', 'rush_td', 'rush_ya', 'plays', 'total_yds', 'ypp',
#     'fga', 'fgm', 'xpa', 'xpm', 'punt', 'punt_yds', 'first_downs_pass', 'first_downs_rush', 'first_downs_pen',
#     'first_downs_total', 'third_down_conv', 'third_down_att', 'fourth_down_conv', 'fourth_down_att', 
#     'pen', 'pen_yds', 'fumbles_lost', 'turnovers_int', 'turnovers_total', 'time_of_poss'
#     # 'pen', 'pen_yds', 'fumbles_lost', 'turnovers_int', 'turnovers_total', 'time_of_poss', 'team_name'
# ]
team_game_logs_headers = [
    'rk', 'gtm', 'week', 'date', 'day', 'game_location', 'opp', 'result', 'pts', 'pts_opp', 'ot', 
    'pass_cmp', 'pass_att', 'pass_cmp_pct', 'pass_yds', 'pass_td', 'pass_ya', 'pass_aya', 'pass_rate', 
    'pass_sk', 'pass_sk_yds', 'rush_att', 'rush_yds', 'rush_td', 'rush_ya', 'plays', 'total_yds', 'ypp',
    'fga', 'fgm', 'xpa', 'xpm', 'punt', 'punt_yds', 'first_downs_pass', 'first_downs_rush', 'first_downs_pen',
    'first_downs_total', 'third_down_conv', 'third_down_att', 'fourth_down_conv', 'fourth_down_att', 
    'pen', 'pen_yds', 'fumbles_lost', 'turnovers_int', 'turnovers_total', 'time_of_poss'
]
    # 'week_num', 'game_day_of_week', 'game_date', 'boxscore_word', 'game_outcome', 'overtime', 
    # 'game_location', 'opp', 'pts_off', 'pts_def', 'pass_cmp', 'pass_att', 'pass_yds', 'pass_td', 
    # 'pass_int', 'pass_sacked', 'pass_sacked_yds', 'pass_yds_per_att', 'pass_net_yds_per_att', 
    # 'pass_cmp_perc', 'pass_rating', 'rush_att', 'rush_yds', 'rush_yds_per_att', 'rush_td', 
    # 'fgm', 'fga', 'xpm', 'xpa', 'punt', 'punt_yds', 'third_down_success', 'third_down_att', 
    # 'fourth_down_success', 'fourth_down_att', 'time_of_poss', 'Team_Name'

opponent_game_logs_headers = [
    'rk', 'gtm', 'week', 'date', 'day', 'game_location', 'opp', 'result', 'pts', 'pts_opp', 'ot', 
    'pass_cmp', 'pass_att', 'pass_cmp_pct', 'pass_yds', 'pass_td', 'pass_ya', 'pass_aya', 'pass_rate', 
    'pass_sk', 'pass_sk_yds', 'rush_att', 'rush_yds', 'rush_td', 'rush_ya', 'plays', 'total_yds', 'ypp',
    'fga', 'fgm', 'xpa', 'xpm', 'punt', 'punt_yds', 'first_downs_pass', 'first_downs_rush', 'first_downs_pen',
    'first_downs_total', 'third_down_conv', 'third_down_att', 'fourth_down_conv', 'fourth_down_att', 
    'pen', 'pen_yds', 'fumbles_lost', 'turnovers_int', 'turnovers_total', 'time_of_poss'
]
# opponent_game_logs_headers = [
#     'rk', 'gtm', 'week', 'date', 'day', 'game_location', 'opp', 'result', 'pts', 'pts_opp', 'ot', 
#     'pass_cmp', 'pass_att', 'pass_cmp_pct', 'pass_yds', 'pass_td', 'pass_ya', 'pass_aya', 'pass_rate', 
#     'pass_sk', 'pass_sk_yds', 'rush_att', 'rush_yds', 'rush_td', 'rush_ya', 'plays', 'total_yds', 'ypp',
#     'fga', 'fgm', 'xpa', 'xpm', 'punt', 'punt_yds', 'first_downs_pass', 'first_downs_rush', 'first_downs_pen',
#     'first_downs_total', 'third_down_conv', 'third_down_att', 'fourth_down_conv', 'fourth_down_att', 
#     'pen', 'pen_yds', 'fumbles_lost', 'turnovers_int', 'turnovers_total', 'time_of_poss'
#     # 'pen', 'pen_yds', 'fumbles_lost', 'turnovers_int', 'turnovers_total', 'time_of_poss', 'team_name'
# ]
    # 'week_num', 'game_day_of_week', 'game_date', 'boxscore_word', 'game_outcome', 'overtime', 
    # 'game_location', 'opp', 'pts_off', 'pts_def', 'pass_cmp', 'pass_att', 'pass_yds', 'pass_td', 
    # 'pass_int', 'pass_sacked', 'pass_sacked_yds', 'pass_yds_per_att', 'pass_net_yds_per_att', 
    # 'pass_cmp_perc', 'pass_rating', 'rush_att', 'rush_yds', 'rush_yds_per_att', 'rush_td', 
    # 'fgm', 'fga', 'xpm', 'xpa', 'punt', 'punt_yds', 'third_down_success', 'third_down_att', 
    # 'fourth_down_success', 'fourth_down_att', 'time_of_poss', 'Team_Name'
for year in range(2025, 2026):
    team_file = f'./data/SR-game-logs/all_teams_game_logs_{year}.csv'
    opponent_file = f'./data/SR-opponent-game-logs/all_teams_opponent_game_logs_{year}.csv'
    # Always process current year team game logs even if files exist
    all_team_game_logs = []  
    all_opponent_game_logs = []
    for team in teams:
        abbreviation, name = team
        print(f'Processing {name} for the year {year}')  
        url = f'https://www.pro-football-reference.com/teams/{abbreviation}/{year}/gamelog/'
        
        # Add retry logic for rate limiting
        max_retries = 3
        retry_delay = 10
        for attempt in range(max_retries):
            try:
                response = requests.get(url)
                if response.status_code == 429:
                    print(f'Rate limited for {name}. Waiting {retry_delay} seconds before retry {attempt + 1}/{max_retries}')
                    sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                    continue
                elif response.status_code != 200:
                    print(f'Failed to retrieve page {url} for {name} in {year}: {response.status_code}')
                    break
                else:
                    break
            except Exception as e:
                print(f'Error retrieving {url}: {e}')
                if attempt < max_retries - 1:
                    sleep(retry_delay)
                    retry_delay *= 2
                    continue
                else:
                    break
        
        if response.status_code != 200:
            continue
            
        soup = BeautifulSoup(response.content, 'html.parser')
        warned_team_short = False
        warned_opp_short = False
        for table_id in ['table_pfr_team-year_game-logs_team-year-regular-season-game-log', 'table_pfr_team-year_game-logs_team-year-regular-season-opponent-game-log']:
            table = soup.find('table', {'id': table_id})
            if table is None:
                print(f'Table with id {table_id} not found on page {url} for {name} in {year}')
                continue
            tbody = table.find('tbody')
            if tbody is None:
                print(f'No tbody found for table {table_id} on page {url} for {name} in {year}')
                continue
                
            game_logs = []
            for tr in tbody.find_all('tr'):
                row_data = []  
                for td in tr.find_all(['th', 'td']):  
                    row_data.append(td.text)
                # Filter out empty rows
                if len(row_data) > 0:
                    if table_id == 'table_pfr_team-year_game-logs_team-year-regular-season-game-log':
                        if len(row_data) == 48:  # Expected: 48 total columns (including Rk)
                            row_data.append(name)  # Add team name (now 49 total)
                            game_logs.append(row_data)
                        else:
                            if not warned_team_short:
                                print(f"Warning: Team game log row has {len(row_data)} cells but expected 48")
                                warned_team_short = True
                    elif table_id == 'table_pfr_team-year_game-logs_team-year-regular-season-opponent-game-log':
                        if len(row_data) == 48:  # Expected: 48 total columns (including Rk)
                            row_data.append(name)  # Add team name (now 49 total)
                            all_opponent_game_logs.append(row_data)
                        else:
                            if not warned_opp_short:
                                print(f"Warning: Opponent game log row has {len(row_data)} cells but expected 48")
                                warned_opp_short = True
            if table_id == 'table_pfr_team-year_game-logs_team-year-regular-season-game-log':
                all_team_game_logs.extend(game_logs)
            playoff_table_id = f'playoff_gamelog{year}'
            playoff_table = soup.find('table', {'id': playoff_table_id})
            if playoff_table:
                playoff_tbody = playoff_table.find('tbody')
                playoff_game_logs = []
                for tr in playoff_tbody.find_all('tr'):
                    row_data = []  
                    for td in tr.find_all(['th', 'td']):  
                        row_data.append(td.text)
                    row_data.append(name)  
                    playoff_game_logs.append(row_data)
                all_team_game_logs.extend(playoff_game_logs)
        sleep(2.5)  # Increased delay to avoid rate limiting  
    with open(team_file, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(team_game_logs_headers + ['team_name'])
        writer.writerows(all_team_game_logs)
    with open(opponent_file, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(opponent_game_logs_headers + ['team_name'])
        writer.writerows(all_opponent_game_logs)


##### Create game_id in Game Logs #####
directory = 'data/SR-game-logs/'
df_list = []
for filename in os.listdir(directory):
    if filename.endswith(".csv"):  
        file_path = os.path.join(directory, filename)
        season = filename.split('_')[-1].replace('.csv', '')
        df = pd.read_csv(file_path)
        df['season'] = season
        df_list.append(df)
df = pd.concat(df_list, ignore_index=True)
team_abbreviation_map = {
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
    'San Diego Chargers': 'LAC'
}

# Mapping from Pro Football Reference abbreviations to our standardized abbreviations
pfr_to_standard_abbr = {
    'ARI': 'ARI',
    'ATL': 'ATL', 
    'BAL': 'BAL',
    'BUF': 'BUF',
    'CAR': 'CAR',
    'CHI': 'CHI',
    'CIN': 'CIN',
    'CLE': 'CLE',
    'DAL': 'DAL',
    'DEN': 'DEN',
    'DET': 'DET',
    'GNB': 'GB',   # Green Bay Packers
    'HOU': 'HOU',
    'IND': 'IND',
    'JAX': 'JAX',
    'KAN': 'KC',   # Kansas City Chiefs
    'LA': 'LAR',   # LA → Los Angeles Rams
    'LAC': 'LAC',
    'LAR': 'LAR',
    'LV': 'LVR',   # LV → Las Vegas Raiders
    'LVR': 'LVR',
    'MIA': 'MIA',
    'MIN': 'MIN',
    'NWE': 'NE',   # New England Patriots
    'NOR': 'NO',   # New Orleans Saints
    'NYG': 'NYG',
    'NYJ': 'NYJ',
    'OAK': 'LVR',  # Oakland Raiders → Las Vegas Raiders
    'PHI': 'PHI',
    'PIT': 'PIT',
    'SD': 'LAC',   # San Diego Chargers → Los Angeles Chargers
    'SDG': 'LAC',  # San Diego Chargers → Los Angeles Chargers (alternative)
    'SEA': 'SEA',
    'SF': 'SF',    # San Francisco 49ers
    'SFO': 'SF',   # San Francisco 49ers (alternative)
    'STL': 'LAR',  # St. Louis Rams → Los Angeles Rams
    'TAM': 'TB',   # Tampa Bay Buccaneers
    'TEN': 'TEN',
    'WAS': 'WAS'
}
def determine_home_away(row):
    if row['game_location'] == '@':
        away_team = team_abbreviation_map[row['team_name']]
        home_team = pfr_to_standard_abbr[row['opp']]
    else:
        home_team = team_abbreviation_map[row['team_name']]
        away_team = pfr_to_standard_abbr[row['opp']]
    return pd.Series([home_team, away_team])
df[['home_team_id', 'away_team_id']] = df.apply(determine_home_away, axis=1)
df['week_num'] = df['week'].astype(str).str.zfill(2)
df['game_id'] = df['season'] + '_' + df['week_num'] + '_' + df['away_team_id'] + '_' + df['home_team_id']
output_file_path_with_teams = 'data/all_team_game_logs.csv'
df.to_csv(output_file_path_with_teams, index=False)
print(f"Updated file with home and away teams saved to: {output_file_path_with_teams}")


##### Aggregate all_game_logs.csv to Single Row Per Game #####
df = pd.read_csv('data/all_team_game_logs.csv')
grouped_df = df.groupby('game_id', group_keys=False).apply(lambda x: pd.Series({
    'season': x['season'].iloc[0],  # Ensure the season is included from the first entry
    'home_pts_off': x.loc[x['game_location'].isnull() | (x['game_location'] == ''), 'pts'].sum(),
    'away_pts_off': x.loc[x['game_location'] == '@', 'pts'].sum(),
    'home_pass_cmp': x.loc[x['game_location'].isnull() | (x['game_location'] == ''), 'pass_cmp'].sum(),
    'away_pass_cmp': x.loc[x['game_location'] == '@', 'pass_cmp'].sum(),
    'home_pass_att': x.loc[x['game_location'].isnull() | (x['game_location'] == ''), 'pass_att'].sum(),
    'away_pass_att': x.loc[x['game_location'] == '@', 'pass_att'].sum(),
    'home_pass_yds': x.loc[x['game_location'].isnull() | (x['game_location'] == ''), 'pass_yds'].sum(),
    'away_pass_yds': x.loc[x['game_location'] == '@', 'pass_yds'].sum(),
    'home_pass_td': x.loc[x['game_location'].isnull() | (x['game_location'] == ''), 'pass_td'].sum(),
    'away_pass_td': x.loc[x['game_location'] == '@', 'pass_td'].sum(),
    'home_pass_int': x.loc[x['game_location'].isnull() | (x['game_location'] == ''), 'turnovers_int'].sum(),
    'away_pass_int': x.loc[x['game_location'] == '@', 'turnovers_int'].sum(),
    'home_pass_sacked': x.loc[x['game_location'].isnull() | (x['game_location'] == ''), 'pass_sk'].sum(),
    'away_pass_sacked': x.loc[x['game_location'] == '@', 'pass_sk'].sum(),
    'home_pass_yds_per_att': x.loc[x['game_location'].isnull() | (x['game_location'] == ''), 'pass_ya'].mean(),
    'away_pass_yds_per_att': x.loc[x['game_location'] == '@', 'pass_ya'].mean(),
    'home_pass_net_yds_per_att': x.loc[x['game_location'].isnull() | (x['game_location'] == ''), 'pass_aya'].mean(),
    'away_pass_net_yds_per_att': x.loc[x['game_location'] == '@', 'pass_aya'].mean(),
    'home_pass_cmp_perc': x.loc[x['game_location'].isnull() | (x['game_location'] == ''), 'pass_cmp_pct'].mean(),
    'away_pass_cmp_perc': x.loc[x['game_location'] == '@', 'pass_cmp_pct'].mean(),
    'home_pass_rating': x.loc[x['game_location'].isnull() | (x['game_location'] == ''), 'pass_rate'].mean(),
    'away_pass_rating': x.loc[x['game_location'] == '@', 'pass_rate'].mean(),
    'home_rush_att': x.loc[x['game_location'].isnull() | (x['game_location'] == ''), 'rush_att'].sum(),
    'away_rush_att': x.loc[x['game_location'] == '@', 'rush_att'].sum(),
    'home_rush_yds': x.loc[x['game_location'].isnull() | (x['game_location'] == ''), 'rush_yds'].sum(),
    'away_rush_yds': x.loc[x['game_location'] == '@', 'rush_yds'].sum(),
    'home_rush_yds_per_att': x.loc[x['game_location'].isnull() | (x['game_location'] == ''), 'rush_ya'].mean(),
    'away_rush_yds_per_att': x.loc[x['game_location'] == '@', 'rush_ya'].mean(),
    'home_rush_td': x.loc[x['game_location'].isnull() | (x['game_location'] == ''), 'rush_td'].sum(),
    'away_rush_td': x.loc[x['game_location'] == '@', 'rush_td'].sum(),
}))
grouped_df.to_csv('data/all_team_game_logs.csv', index=True)


##### Team Stats and Rankings #####
print("\n" + "*"*80 + "\n")
data_dir = './data/SR-team-stats'
os.makedirs(data_dir, exist_ok=True)
teams = [
    ['crd', 'Arizona Cardinals'],
    ['atl', 'Atlanta Falcons'],
    ['rav', 'Baltimore Ravens'],
    ['buf', 'Buffalo Bills'],
    ['car', 'Carolina Panthers'],
    ['chi', 'Chicago Bears'],
    ['cin', 'Cincinnati Bengals'],
    ['cle', 'Cleveland Browns'],
    ['dal', 'Dallas Cowboys'],
    ['den', 'Denver Broncos'],
    ['det', 'Detroit Lions'],
    ['gnb', 'Green Bay Packers'],
    ['htx', 'Houston Texans'],
    ['clt', 'Indianapolis Colts'],
    ['jax', 'Jacksonville Jaguars'],
    ['kan', 'Kansas City Chiefs'],
    ['sdg', 'Los Angeles Chargers'],
    ['ram', 'Los Angeles Rams'],
    ['rai', 'Las Vegas Raiders'],
    ['mia', 'Miami Dolphins'],
    ['min', 'Minnesota Vikings'],
    ['nwe', 'New England Patriots'],
    ['nor', 'New Orleans Saints'],
    ['nyg', 'New York Giants'],
    ['nyj', 'New York Jets'],
    ['phi', 'Philadelphia Eagles'],
    ['pit', 'Pittsburgh Steelers'],
    ['sea', 'Seattle Seahawks'],
    ['sfo', 'San Francisco 49ers'],
    ['tam', 'Tampa Bay Buccaneers'],
    ['oti', 'Tennessee Titans'],
    ['was', 'Washington Commanders']
]
team_stats_headers = [
    'Player', 'PF', 'Yds', 'Ply', 'Y/P', 'TO', 'FL', '1stD', 'Cmp', 'Att', 'Yds', 'TD', 'Int', 'NY/A',
    '1stD', 'Att', 'Yds', 'TD', 'Y/A', '1stD', 'Pen', 'Yds', '1stPy', '#Dr', 'Sc%', 'TO%', 'Start', 'Time', 'Plays', 'Yds', 'Pts', 'Team'
]
for year in range(2025, 2026):
    output_file = f'{data_dir}/all_teams_stats_{year}.csv'
    if os.path.exists(output_file):
        print(f"Skipping year {year}, file already exists.")
        continue
    all_team_stats = []  
    for team in teams:
        abbreviation, name = team
        print(f'Processing {name} for the year {year}')  
        url = f'https://www.pro-football-reference.com/teams/{abbreviation}/{year}.htm'
        
        # Add retry logic for rate limiting
        max_retries = 3
        retry_delay = 10
        for attempt in range(max_retries):
            try:
                response = requests.get(url)
                if response.status_code == 429:
                    print(f'Rate limited for {name}. Waiting {retry_delay} seconds before retry {attempt + 1}/{max_retries}')
                    sleep(retry_delay)
                    retry_delay *= 2
                    continue
                elif response.status_code != 200:
                    print(f'Failed to retrieve page {url} for {name} in {year}: {response.status_code}')
                    break
                else:
                    break
            except Exception as e:
                print(f'Error retrieving {url}: {e}')
                if attempt < max_retries - 1:
                    sleep(retry_delay)
                    retry_delay *= 2
                    continue
                else:
                    break
        
        if response.status_code != 200:
            continue
            
        soup = BeautifulSoup(response.content, 'html.parser')
        table = soup.find('table', {'id': 'team_stats'})
        if table is None:
            print(f'Team stats table not found on page {url} for {name} in {year}')
            continue
        tbody = table.find('tbody')
        for tr in tbody.find_all('tr'):
            row_data = [tr.find('th').text.strip()]  
            row_data.extend([td.text.strip() for td in tr.find_all('td')])  
            row_data.append(abbreviation)  
            all_team_stats.append(row_data)
        sleep(2.5)  # Increased delay to avoid rate limiting  
        # sleep(5)  # Increased delay to avoid rate limiting  
    with open(output_file, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(team_stats_headers)
        writer.writerows(all_team_stats)
    print(f'Saved data for all teams for the year {year}')


##### Merge Team Stats and Rankings #####
input_dir = 'data/SR-team-stats/'
csv_files = [f for f in os.listdir(input_dir) if f.endswith('.csv')]
dataframes = []
for file in csv_files:
    df = pd.read_csv(os.path.join(input_dir, file))
    df['Year'] = file.split('_')[-1].split('.')[0]  # Extract year from filename
    dataframes.append(df)
merged_dataframe = pd.concat(dataframes, ignore_index=True)
output_file = 'data/all_team_stats.csv'
merged_dataframe.to_csv(output_file, index=False)
print(f"Merged dataset saved as {output_file}")


##### Schedule & Game Results #####
print("\n" + "*"*80 + "\n")
data_dir = './data/SR-schedule-and-game-results'
os.makedirs(data_dir, exist_ok=True)
teams = [
    ['crd', 'Arizona Cardinals'],
    ['atl', 'Atlanta Falcons'],
    ['rav', 'Baltimore Ravens'],
    ['buf', 'Buffalo Bills'],
    ['car', 'Carolina Panthers'],
    ['chi', 'Chicago Bears'],
    ['cin', 'Cincinnati Bengals'],
    ['cle', 'Cleveland Browns'],
    ['dal', 'Dallas Cowboys'],
    ['den', 'Denver Broncos'],
    ['det', 'Detroit Lions'],
    ['gnb', 'Green Bay Packers'],
    ['htx', 'Houston Texans'],
    ['clt', 'Indianapolis Colts'],
    ['jax', 'Jacksonville Jaguars'],
    ['kan', 'Kansas City Chiefs'],
    ['sdg', 'Los Angeles Chargers'],
    ['ram', 'Los Angeles Rams'],
    ['rai', 'Las Vegas Raiders'],
    ['mia', 'Miami Dolphins'],
    ['min', 'Minnesota Vikings'],
    ['nwe', 'New England Patriots'],
    ['nor', 'New Orleans Saints'],
    ['nyg', 'New York Giants'],
    ['nyj', 'New York Jets'],
    ['phi', 'Philadelphia Eagles'],
    ['pit', 'Pittsburgh Steelers'],
    ['sea', 'Seattle Seahawks'],
    ['sfo', 'San Francisco 49ers'],
    ['tam', 'Tampa Bay Buccaneers'],
    ['oti', 'Tennessee Titans'],
    ['was', 'Washington Commanders']
]
schedule_headers = [
    'Week', 'Day', 'Date', 'Time', 'Boxscore', 'Outcome', 'OT', 'Rec', 'Home/Away', 'Opp', 
    'Tm', 'OppPts', '1stD', 'TotYd', 'PassY', 'RushY', 'TO_lost', 
    'Opp1stD', 'OppTotYd', 'OppPassY', 'OppRushY', 'TO_won',
    'Offense', 'Defense', 'Sp. Tms'
]
for year in range(2025, 2026):
    all_games = []  
    for team in teams:
        abbreviation, name = team
        print(f'Processing {name} for the year {year}')  
        url = f'https://www.pro-football-reference.com/teams/{abbreviation}/{year}.htm'
        
        # Add retry logic for rate limiting (same pattern as other scrapers)
        max_retries = 3
        retry_delay = 10
        response = None
        
        for attempt in range(max_retries):
            try:
                response = requests.get(url, timeout=10)
                if response.status_code == 429:
                    print(f'Rate limited for {name}. Waiting {retry_delay} seconds before retry {attempt + 1}/{max_retries}')
                    sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                    continue
                elif response.status_code != 200:
                    print(f'Failed to retrieve page {url} for {name} in {year}: {response.status_code}')
                    break
                else:
                    break
            except Exception as e:
                print(f'Error retrieving {url}: {e}')
                if attempt < max_retries - 1:
                    sleep(retry_delay)
                    retry_delay *= 2
                    continue
                else:
                    break
        
        if response is None or response.status_code != 200:
            continue
            
        soup = BeautifulSoup(response.content, 'html.parser')
        table = soup.find('table', {'id': 'games'})
        
        if table is None:
            print(f'Schedule & Game Results table not found on page {url} for {name} in {year}')
            sleep(2.5)
            continue
            
        tbody = table.find('tbody')
        if tbody is None:
            print(f'No tbody found for games table on page {url} for {name} in {year}')
            sleep(2.5)
            continue
            
        team_games = []  
        for tr in tbody.find_all('tr'):
            row_data = []
            week_th = tr.find('th', {'data-stat': 'week_num'})
            week_num = week_th.text.strip() if week_th else ''
            row_data.append(week_num)
            
            for td in tr.find_all('td'):
                row_data.append(td.text.strip())
            
            # Ensure we have the right number of columns
            if len(row_data) != len(schedule_headers):
                row_data += [''] * (len(schedule_headers) - len(row_data))
            
            team_games.append(row_data)
            all_games.append(row_data)  
        
        # Save individual team file
        team_file_path = f'{data_dir}/{abbreviation}_{year}_schedule_and_game_results.csv'
        with open(team_file_path, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(schedule_headers)
            writer.writerows(team_games)
        
        print(f'Saved schedule data for {name} for the year {year}')
        sleep(2.5)  # Rate limiting delay

# Merge all team files
print(f"\nMerging all team files...")
all_games = []
for filename in os.listdir(data_dir):
    if filename.endswith("_schedule_and_game_results.csv"):
        team_abbr = filename.split('_')[0]
        season_year = filename.split('_')[1]
        file_path = os.path.join(data_dir, filename)
        df = pd.read_csv(file_path)
        df['Team'] = team_abbr
        df['Season'] = season_year
        all_games.append(df)

if all_games:
    merged_df = pd.concat(all_games, ignore_index=True)
    # Save to subdirectory
    merged_output_path = os.path.join(data_dir, 'all_teams_schedule_and_game_results_merged.csv')
    merged_df.to_csv(merged_output_path, index=False)
    print(f"Successfully merged all team files into {merged_output_path}")
    # Also save to main data directory
    main_data_path = 'data/all_teams_schedule_and_game_results_merged.csv'
    merged_df.to_csv(main_data_path, index=False)
    print(f"Also saved to main data directory: {main_data_path}")
    print(f"Total records: {len(merged_df)}")
else:
    print("No team files found to merge")


##### Team Conversions #####
print("\n" + "*"*80 + "\n")
data_dir = './data/SR-team-conversions'
os.makedirs(data_dir, exist_ok=True)
teams = [
    ['crd', 'Arizona Cardinals'],
    ['atl', 'Atlanta Falcons'],
    ['rav', 'Baltimore Ravens'],
    ['buf', 'Buffalo Bills'],
    ['car', 'Carolina Panthers'],
    ['chi', 'Chicago Bears'],
    ['cin', 'Cincinnati Bengals'],
    ['cle', 'Cleveland Browns'],
    ['dal', 'Dallas Cowboys'],
    ['den', 'Denver Broncos'],
    ['det', 'Detroit Lions'],
    ['gnb', 'Green Bay Packers'],
    ['htx', 'Houston Texans'],
    ['clt', 'Indianapolis Colts'],
    ['jax', 'Jacksonville Jaguars'],
    ['kan', 'Kansas City Chiefs'],
    ['sdg', 'Los Angeles Chargers'],
    ['ram', 'Los Angeles Rams'],
    ['rai', 'Las Vegas Raiders'],
    ['mia', 'Miami Dolphins'],
    ['min', 'Minnesota Vikings'],
    ['nwe', 'New England Patriots'],
    ['nor', 'New Orleans Saints'],
    ['nyg', 'New York Giants'],
    ['nyj', 'New York Jets'],
    ['phi', 'Philadelphia Eagles'],
    ['pit', 'Pittsburgh Steelers'],
    ['sea', 'Seattle Seahawks'],
    ['sfo', 'San Francisco 49ers'],
    ['tam', 'Tampa Bay Buccaneers'],
    ['oti', 'Tennessee Titans'],
    ['was', 'Washington Commanders']
]
team_conversions_headers = [
    'Player', '3DAtt', '3DConv', '4DAtt', '4DConv', '4D%', 'RZAtt', 'RZTD', 'RZPct', 'Team'
    # 'Player', '3DAtt', '3DConv', '3D%', '4DAtt', '4DConv', '4D%', 'RZAtt', 'RZTD', 'RZPct', 'Team'
]
for year in range(2025, 2026):
    for team in teams:
        abbreviation, name = team
        team_file = f'{data_dir}/{abbreviation}_{year}_team_conversions.csv'
        # Always process current year team conversions even if file exists
        print(f'Processing {name} for the year {year}')  
        url = f'https://www.pro-football-reference.com/teams/{abbreviation}/{year}.htm'
        response = requests.get(url)
        if response.status_code != 200:
            print(f'Failed to retrieve page {url} for {name} in {year}: {response.status_code}')
            continue
        soup = BeautifulSoup(response.content, 'html.parser')
        table = soup.find('table', {'id': 'team_conversions'})
        if table is None:
            print(f'Team Conversions table not found on page {url} for {name} in {year}')
            sleep(2.5)
            continue
        all_conversions = []
        tbody = table.find('tbody')
        for tr in tbody.find_all('tr'):
            row_data = [td.text.strip() for td in tr.find_all(['th', 'td'])]  
            row_data.append(abbreviation)  
            all_conversions.append(row_data)
        with open(team_file, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(team_conversions_headers)
            writer.writerows(all_conversions)
        print(f'Saved team conversions data for {name} for the year {year} to {team_file}')
        sleep(3)  

##### Merge Team Conversions #####
input_dir = 'data/SR-team-conversions/'
csv_files = [f for f in os.listdir(input_dir) if f.endswith('.csv')]
dataframes = []
for file in csv_files:
    df = pd.read_csv(os.path.join(input_dir, file))
    df['Year'] = file.split('_')[1]  # Extract year from filename
    dataframes.append(df)
merged_dataframe = pd.concat(dataframes, ignore_index=True)
output_file = 'data/all_team_conversions.csv'
merged_dataframe.to_csv(output_file, index=False)
print(f"Merged dataset saved as {output_file}")


##### Creating home_spread, away_spread, team_favorite columns in nfl.db #####
print("\n" + "*"*80 + "\n")
def calculate_spreads_and_favorite(spread_line, home_team, away_team, home_score, away_score):
    if spread_line is None or home_score is None or away_score is None:
        return "N/A", "N/A", "N/A", "N/A"
    spread_line = float(spread_line)
    abs_spread = abs(spread_line)  
    if spread_line > 0:
        home_spread = f"-{spread_line}"  
        away_spread = f"+{spread_line}"  
        team_favorite = home_team
        if home_score > away_score + abs_spread:
            team_covered = home_team
        elif away_score > home_score - abs_spread:
            team_covered = away_team
        else:
            team_covered = "Push"
    else:
        home_spread = f"+{-spread_line}"  
        away_spread = f"-{-spread_line}"  
        team_favorite = away_team
        if away_score > home_score + abs_spread:
            team_covered = away_team
        elif home_score > away_score - abs_spread:
            team_covered = home_team
        else:
            team_covered = "Push"
    return home_spread, away_spread, team_favorite, team_covered
db_path = 'nfl.db'  
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
try:
    cursor.execute("ALTER TABLE Games ADD COLUMN home_spread TEXT;")
except sqlite3.OperationalError:
    pass  
try:
    cursor.execute("ALTER TABLE Games ADD COLUMN away_spread TEXT;")
except sqlite3.OperationalError:
    pass  
try:
    cursor.execute("ALTER TABLE Games ADD COLUMN team_favorite TEXT;")
except sqlite3.OperationalError:
    pass  
try:
    cursor.execute("ALTER TABLE Games ADD COLUMN team_covered TEXT;")
except sqlite3.OperationalError:
    pass  
cursor.execute("SELECT game_id, spread_line, home_team, away_team, home_score, away_score FROM Games;")
games = cursor.fetchall()
for game in games:
    game_id, spread_line, home_team, away_team, home_score, away_score = game
    home_spread, away_spread, team_favorite, team_covered = calculate_spreads_and_favorite(spread_line, home_team, away_team, home_score, away_score)
    update_query = "UPDATE Games SET home_spread = ?, away_spread = ?, team_favorite = ?, team_covered = ? WHERE game_id = ?;"
    cursor.execute(update_query, (home_spread, away_spread, team_favorite, team_covered, game_id))
conn.commit()
conn.close()
print("Columns 'home_spread', 'away_spread', 'team_favorite', and 'team_covered' have been added and updated for all rows in the 'Games' table.")


##### Passing/Rushing/Receiving #####
print("\n" + "*"*80 + "\n")
os.makedirs('./data/SR-passing-rushing-receiving-game-logs/', exist_ok=True)
for year_to_scrape in range(2025, 2026):
    output_filename = f'./data/SR-passing-rushing-receiving-game-logs/all_passing_rushing_receiving_{year_to_scrape}.csv'
    existing_game_ids = set()
    if os.path.exists(output_filename):
        df_existing = pd.read_csv(output_filename)
        if 'game_id' in df_existing.columns:
            existing_game_ids = set(df_existing['game_id'].unique())
    mode = 'a' if os.path.exists(output_filename) else 'w'
    with open(output_filename, mode, newline='') as output_csvfile:
        csvwriter = csv.writer(output_csvfile)
        if mode == 'w':
            csvwriter.writerow([
                'player', 'player_id', 'team', 'pass_cmp', 'pass_att', 'pass_yds', 'pass_td', 'pass_int', 
                'pass_sacked', 'pass_sacked_yds', 'pass_long', 'pass_rating', 'rush_att', 'rush_yds', 'rush_td', 
                'rush_long', 'targets', 'rec', 'rec_yds', 'rec_td', 'rec_long', 'fumbles', 'fumbles_lost', 'game_id'
            ])  
        with open('./data/games.csv', 'r') as csvfile:
            reader = csv.DictReader(csvfile)
            rows = []
            now_dt = datetime.now()
            for row in reader:
                try:
                    game_dt = datetime.fromisoformat(row['date'])
                except Exception:
                    continue
                if int(row['game_id'].split('_')[0]) == year_to_scrape and game_dt <= now_dt:
                    rows.append(row)
            for row in rows:
                pfr_value = row['pfr']
                game_id = row['game_id']
                if game_id in existing_game_ids:
                    print(f"Skipping already scraped game ID: {game_id}")
                    continue
                url = f"https://www.pro-football-reference.com/boxscores/{pfr_value}.htm"
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        response = requests.get(url, timeout=10)
                        if response.status_code == 429:
                            print(f"Rate limit exceeded for URL {url}. Please try again later.")
                            time.sleep(60)
                            continue
                        soup = BeautifulSoup(response.text, 'html.parser')
                        table = soup.find('div', id='div_player_offense')
                        if table:
                            for i, tr in enumerate(table.find_all('tr')):
                                if i == 0:  
                                    continue
                                player_cell = tr.find('th')
                                if player_cell:
                                    player_name = player_cell.get_text()
                                    player_link = player_cell.find('a')
                                    player_id = player_link['href'].split('/')[-1] if player_link else None  
                                    stats = [td.get_text() for td in tr.find_all('td')]
                                    row_data = [player_name, player_id] + stats + [game_id]  
                                    csvwriter.writerow(row_data)
                            print(f"Successfully scraped data for game ID: {game_id}, PFR: {pfr_value}")
                            time.sleep(2)  # Additional sleep after successful scrape
                            break
                    except Exception as e:
                        print(f"An error occurred while scraping {url}. Error: {e}")
                        if attempt < max_retries - 1:
                            time.sleep(2 ** attempt)
                        else:
                            break
                time.sleep(2.5)
    print(f"Scraping completed for {year_to_scrape}. Data saved to {output_filename}.")


##### Cleaning weird rows in passing/rushing/receiving #####
directory = 'data/SR-passing-rushing-receiving-game-logs/'
for filename in os.listdir(directory):
    if filename.endswith('.csv'):
        file_path = os.path.join(directory, filename)
        df = pd.read_csv(file_path)
        df_cleaned = df[(df['player'] != 'Player') & (df['player'].notna())]
        df_cleaned.to_csv(file_path, index=False)
        print(f"Processed {filename}")


##### Merge all passing/rushing/receiving #####
directory = 'data/SR-passing-rushing-receiving-game-logs/'
merged_file_path = 'data/all_passing_rushing_receiving.csv'  
dataframes = []
for filename in os.listdir(directory):
    if filename.endswith('.csv'):
        file_path = os.path.join(directory, filename)
        df = pd.read_csv(file_path)
        dataframes.append(df)
        print(f"Added {filename} to the merge list")
merged_df = pd.concat(dataframes, ignore_index=True)
merged_df.to_csv(merged_file_path, index=False)
print(f"All files have been merged into {merged_file_path}")


##### Add opponent_team column to all_passing_rushing_receiving.csv #####
file_path = 'data/all_passing_rushing_receiving.csv'  
df = pd.read_csv(file_path)
team_corrections = {
    'NWE': 'NE',
    'GNB': 'GB',
    'KAN': 'KC',
    'STL': 'LAR',
    'NOR': 'NO',
    'SDG': 'LAC',
    'OAK': 'LVR',
    'TAM': 'TB',
    'SFO': 'SF'
}
df['team'] = df['team'].replace(team_corrections)
def get_opponent_team(row):
    game_id = row['game_id']
    team = row['team']
    _, _, away_team, home_team = game_id.split('_')
    if team == home_team:
        return away_team
    elif team == away_team:
        return home_team
    else:
        return None  
def is_player_home(row):
    game_id = row['game_id']
    team = row['team']
    _, _, away_team, home_team = game_id.split('_')
    return 'y' if team == home_team else 'n'
df['opponent_team'] = df.apply(get_opponent_team, axis=1)
df['home'] = df.apply(is_player_home, axis=1)
df.to_csv('data/all_passing_rushing_receiving.csv', index=False)  
print(df.head())


##### Add position column to all_passing_rushing_receiving.csv #####
all_passing_file = 'data/all_passing_rushing_receiving.csv'
rosters_file = 'data/rosters.csv'
all_passing_df = pd.read_csv(all_passing_file)
rosters_df = pd.read_csv(rosters_file)
merged_df = pd.merge(all_passing_df, rosters_df[['full_name', 'position']], 
                     left_on='player', right_on='full_name', how='left')
if 'position' not in merged_df.columns:
    merged_df['position'] = None
relevant_positions = ['QB', 'WR', 'TE', 'RB']
merged_df['position'] = merged_df['position'].where(merged_df['position'].isin(relevant_positions), None)
merged_df.drop(columns=['full_name'], inplace=True)
merged_df['position'] = merged_df.groupby('player')['position'].transform(lambda x: x.ffill().bfill())
merged_df.to_csv('data/all_passing_rushing_receiving.csv', index=False)
print(merged_df[['player', 'position']].head())

##### Create clean PFR-only version without NFLverse position data #####
print("\nCreating clean PFR-only version of passing/rushing/receiving data...")
# Recreate the clean PFR data by merging all years without position data
directory = 'data/SR-passing-rushing-receiving-game-logs/'
clean_pfr_file_path = 'data/all_passing_rushing_receiving_pfr_clean.csv'  
clean_dataframes = []
for filename in os.listdir(directory):
    if filename.endswith('.csv'):
        file_path = os.path.join(directory, filename)
        df = pd.read_csv(file_path)
        clean_dataframes.append(df)
        print(f"Added {filename} to clean PFR merge list")
clean_merged_df = pd.concat(clean_dataframes, ignore_index=True)
# Add opponent_team and home columns (these are derived from PFR game_id, not NFLverse)
clean_merged_df['opponent_team'] = clean_merged_df.apply(get_opponent_team, axis=1)
clean_merged_df['home'] = clean_merged_df.apply(is_player_home, axis=1)
# Save clean PFR version without position data
clean_merged_df.to_csv(clean_pfr_file_path, index=False)
print(f"✅ Clean PFR-only version saved to: {clean_pfr_file_path}")


##### Defense #####
print("\n" + "*"*80 + "\n")
os.makedirs('data/SR-defense-game-logs', exist_ok=True)
headers = [
    'player', 'team', 'def_int', 'def_int_yds', 'def_int_td', 'def_int_long', 'pass_defended', 'sacks',
    'tackles_combined', 'tackles_solo', 'tackles_assists', 'tackles_loss', 'qb_hits', 'fumbles_rec',
    'fumbles_rec_yds', 'fumbles_rec_td', 'fumbles_forced', 'game_id'
]
for year_to_scrape in range(2025, 2026):
    output_filename = f'./data/SR-defense-game-logs/all_defense_{year_to_scrape}.csv'
    existing_game_ids = set()
    if os.path.exists(output_filename):
        df_existing = pd.read_csv(output_filename)
        if 'game_id' in df_existing.columns:
            existing_game_ids = set(df_existing['game_id'].unique())
    mode = 'a' if os.path.exists(output_filename) else 'w'
    with open(output_filename, mode, newline='') as output_csvfile:
        csvwriter = csv.writer(output_csvfile)
        if mode == 'w':
            csvwriter.writerow(headers)
        with open('./data/games.csv', 'r') as csvfile:
            reader = csv.DictReader(csvfile)
            rows = []
            now_dt = datetime.now()
            for row in reader:
                try:
                    game_dt = datetime.fromisoformat(row['date'])
                except Exception:
                    continue
                if int(row['game_id'].split('_')[0]) == year_to_scrape and game_dt <= now_dt:
                    rows.append(row)
            for row in rows:
                if not row['away_score'] or not row['home_score']:
                    print(f"Skipping game {row['game_id']} due to missing scores.")
                    continue  
                pfr_value = row['pfr']
                game_id = row['game_id']
                if game_id in existing_game_ids:
                    print(f"Skipping already scraped game ID: {game_id}")
                    continue
                url = f"https://www.pro-football-reference.com/boxscores/{pfr_value}.htm"
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        response = requests.get(url, timeout=10)
                        response.raise_for_status()
                        soup = BeautifulSoup(response.text, 'html.parser')
                        comments = soup.find_all(string=lambda text: isinstance(text, Comment))
                        table_found = False
                        for comment in comments:
                            soup_comment = BeautifulSoup(comment, 'html.parser')
                            table = soup_comment.find('table', id='player_defense')
                            if table:
                                table_found = True
                                for i, tr in enumerate(table.find_all('tr')):
                                    if i == 0:
                                        continue
                                    player_name = tr.find('th').get_text() if tr.find('th') else ''
                                    stats = [td.get_text() for td in tr.find_all('td')]
                                    row_data = [player_name] + stats + [game_id]
                                    csvwriter.writerow(row_data)
                                print(f"Successfully scraped data for game ID: {game_id}, PFR: {pfr_value}")
                                break
                        if not table_found:
                            print(f"No defense table found for {url}")
                        break
                    except Exception as e:
                        print(f"An error occurred while scraping {url}. Error: {e}")
                        if attempt < max_retries - 1:
                            time.sleep(2 ** attempt)
                        else:
                            break
                time.sleep(2.5)
    print(f"Scraping completed for {year_to_scrape}. Data saved to {output_filename}.")

# df = pd.read_csv('./data/defense-game-logs/all_defense_2025.csv')
# df.dropna(inplace=True)
# df.to_csv('./data/defense-game-logs/all_defense_2025.csv', index=False)
for year in range(2025, 2026):
    file_path = f'./data/SR-defense-game-logs/all_defense_{year}.csv'
    try:
        df = pd.read_csv(file_path)
        df.dropna(inplace=True)
        df.to_csv(file_path, index=False)
        print(f"Cleaned defense data for {year}")
    except FileNotFoundError:
        print(f"No defense data file found for {year}")

##### Merge all defense-game-logs.csv files into one #####
input_dir = 'data/SR-defense-game-logs/'
csv_files = [f for f in os.listdir(input_dir) if f.endswith('.csv')]
dataframes = [pd.read_csv(os.path.join(input_dir, file)) for file in csv_files]
merged_dataframe = pd.concat(dataframes, ignore_index=True)
output_file = 'data/all_defense-game-logs.csv'
merged_dataframe.to_csv(output_file, index=False)
print(f"Merged dataset saved as {output_file}")


##### Red Zone Statistics #####
print("\n" + "*"*80 + "\n")
os.makedirs('./data/SR-redzone', exist_ok=True)
categories = {
    'passing': 'redzone-passing.htm',
    'rushing': 'redzone-rushing.htm',
    'receiving': 'redzone-receiving.htm',
}
headers = {
    'User-Agent': (
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/114.0.0.0 Safari/537.36'
    )
}
for year_to_scrape in range(2025, 2026):
    all_redzone_data = []
    for stat_type, suffix in categories.items():
        url = f'https://www.pro-football-reference.com/years/{year_to_scrape}/{suffix}'
        try:
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            df = pd.read_html(response.content)[0]
            # Flatten multi-index columns
            new_cols = []
            for col in df.columns:
                if isinstance(col, tuple):
                    parts = [c for c in col if c and 'Unnamed' not in str(c)]
                    new_name = '_'.join(parts)
                    new_cols.append(new_name)
                else:
                    new_cols.append(col)
            df.columns = new_cols
            # Drop header repeats and link column
            if 'Player' in df.columns:
                df = df[df['Player'] != 'Player']
            if 'Link' in df.columns:
                df = df.drop(columns=['Link'])
            # Add metadata
            df.insert(0, 'Year', year_to_scrape)
            df.insert(1, 'StatType', stat_type)
            # Standardize team abbreviations
            team_standardization = {
                'GNB': 'GB',    # Green Bay Packers
                'KAN': 'KC',    # Kansas City Chiefs  
                'NOR': 'NO',    # New Orleans Saints
                'NWE': 'NE',    # New England Patriots
                'OAK': 'LVR',   # Oakland Raiders → Las Vegas Raiders
                'SFO': 'SF',    # San Francisco 49ers
                'TAM': 'TB'     # Tampa Bay Buccaneers
            }
            df['Tm'] = df['Tm'].replace(team_standardization)
            all_redzone_data.append(df)
            print(f"Successfully scraped {stat_type} data for {year_to_scrape}")
            time.sleep(2.5)
        except Exception as e:
            print(f"Error scraping {stat_type} for {year_to_scrape}: {e}")
            continue
    if all_redzone_data:
        combined_df = pd.concat(all_redzone_data, ignore_index=True)
        output_file = f'./data/SR-redzone/all_redzone_{year_to_scrape}.csv'
        combined_df.to_csv(output_file, index=False)
        print(f"Combined red zone data saved to {output_file}")

##### Merge Red Zone Data #####
input_dir = 'data/SR-redzone/'
csv_files = [f for f in os.listdir(input_dir) if f.endswith('.csv')]
if csv_files:
    dataframes = [pd.read_csv(os.path.join(input_dir, file)) for file in csv_files]
    merged_dataframe = pd.concat(dataframes, ignore_index=True)
    # Apply team standardization to merged data as well
    team_standardization = {
        'GNB': 'GB',    # Green Bay Packers
        'KAN': 'KC',    # Kansas City Chiefs  
        'NOR': 'NO',    # New Orleans Saints
        'NWE': 'NE',    # New England Patriots
        'OAK': 'LVR',   # Oakland Raiders → Las Vegas Raiders
        'SFO': 'SF',    # San Francisco 49ers
        'TAM': 'TB'     # Tampa Bay Buccaneers
    }
    merged_dataframe['Tm'] = merged_dataframe['Tm'].replace(team_standardization)
    output_file = 'data/all_redzone.csv'
    merged_dataframe.to_csv(output_file, index=False)
    print(f"Merged red zone dataset saved as {output_file}")


##### Export all tables from nfl.db to csv files with current date's timestamp in the file names to a final directory #####
##### Regenerate final files with ALL available historical data + new current year data #####
print("\n" + "*"*80 + "\n")
final_dir = 'final_data'
if not os.path.exists(final_dir):
    os.makedirs(final_dir)
current_date = datetime.now().strftime("%b_%d_%Y").upper()
print("Regenerating final files with 2025 season data...")
games_df = pd.read_csv('data/games.csv') # Games: Load from data/games.csv (contains 2025)
games_df.to_csv(f"{final_dir}/Games_{current_date}.csv", index=False)
print(f"Regenerated Games: {len(games_df)} total games")
player_stats_df = pd.read_csv('data/player_stats.csv') # PlayerStats: Load from data/player_stats.csv (contains 2025)
player_stats_df.to_csv(f"{final_dir}/PlayerStats_{current_date}.csv", index=False)
print(f"Regenerated PlayerStats: {len(player_stats_df)} total records")
rosters_df = pd.read_csv('data/rosters.csv') # Rosters: Load from data/rosters.csv (contains 2025)
rosters_df.to_csv(f"{final_dir}/Rosters_{current_date}.csv", index=False)
print(f"Regenerated Rosters: {len(rosters_df)} total records")
db_path = 'nfl.db' # Teams: Static data, load from database
conn = sqlite3.connect(db_path)
teams_df = pd.read_sql_query("SELECT * FROM Teams", conn)
teams_df.to_csv(f"{final_dir}/Teams_{current_date}.csv", index=False)
print(f"Regenerated Teams: {len(teams_df)} total teams")


##### Remove Unplayed Games #####
current_date_str = datetime.now().strftime("%b_%d_%Y").upper()
file_name = f"final_data/Games_{current_date_str}.csv"
games_df = pd.read_csv(file_name)
games_df.rename(columns={'gameday': 'date'}, inplace=True)
games_df['date'] = pd.to_datetime(games_df['date'], errors='coerce')
current_date = datetime.now()
cleaned_games_df = games_df[games_df['date'] <= current_date]
cleaned_games_df.to_csv(file_name, index=False)
print(f"Cleaned data saved to {file_name}")


##### TO DO #####
##### 1. Add Box Scores to nfl.db #####
##### 2. Add Scoring Tables to nfl.db #####
##### 3. Add the rest of the missing files data to nfl.db and final clean #####
##### 4. Uncomment and optimize the QB, RB, WR, TE game tables: #####



# ##### QB Game Tables #####
# headers = [
#     'Player URL', 'Position', 'First Name', 'Last Name', 'Year', 'Age', 'Tm', 'Pos', 'No.', 'G', 'GS', 'QBrec', 'Cmp', 'Att', 'Cmp%', 'Yds', 'TD', 
#     'TD%', 'Int', 'Int%', '1D', 'Succ%', 'Lng', 'Y/A', 'AY/A', 'Y/C', 'Y/G', 'Rate', 'QBR', 
#     'Sk', 'Yds', 'Sk%', 'NY/A', 'ANY/A', '4QC', 'GWD', 'AV', 'Awards'
# ]
# import time
# import csv
# import requests
# from bs4 import BeautifulSoup
# from requests.exceptions import Timeout, RequestException
# import pandas as pd
# df = pd.read_csv('./data/rosters.csv')
# df = df.dropna(subset=['pfr_id'])
# qbs = df[df['position'] == 'QB']
# try:
#     existing_qb_data = pd.read_csv('./data/game_logs_qb.csv')
#     existing_url_years = set(zip(existing_qb_data['Player URL'], existing_qb_data['Year']))
# except FileNotFoundError:
#     existing_qb_data = pd.DataFrame(columns=headers)
#     existing_url_years = set()
# with open('./data/game_logs_qb.csv', 'a', newline='') as file:
#     writer = csv.writer(file)
#     if file.tell() == 0:
#         writer.writerow(headers)
#     total_qbs = len(qbs)
#     qb_counter = 0
#     max_retries = 3  
#     for index, qb in qbs.iterrows():
#         qb_counter += 1
#         url = qb['url']
#         first_name = qb['first_name']
#         last_name = qb['last_name']
#         position = 'QB'
#         print(f"Processing QB {qb_counter}/{total_qbs}: {first_name} {last_name}")
#         retries = 0  
#         success = False  
#         while retries < max_retries and not success:
#             try:
#                 response = requests.get(url, timeout=10)  
#                 if response.status_code == 200:
#                     soup = BeautifulSoup(response.content, 'html.parser')
#                     game_logs_table = soup.find('table', {'id': 'passing'})  
#                     if game_logs_table:  
#                         data_rows = game_logs_table.find('tbody').find_all('tr')
#                         for row in data_rows:
#                             cells = row.find_all(['th', 'td'])
#                             data = [cell.text.strip() for cell in cells]
#                             year = data[0]  
#                             if (url, year) in existing_url_years:
#                                 print(f"Data for {first_name} {last_name} in year {year} already exists. Skipping...")
#                                 continue
#                             data = [url, position, first_name, last_name] + data
#                             writer.writerow(data)
#                             existing_url_years.add((url, year))  
#                         print(f"Data written for {first_name} {last_name}")
#                         success = True  
#                     else:
#                         print(f"No game logs table found for URL: {url}")
#                         success = True  
#                 else:
#                     print(f"Failed to retrieve URL: {url} with status code: {response.status_code}")
#                     retries += 1
#             except (Timeout, RequestException) as e:
#                 retries += 1
#                 print(f"Error processing {url}: {e}. Retrying ({retries}/{max_retries})...")
#                 time.sleep(2 ** retries)  
#         if not success:
#             print(f"Skipping {first_name} {last_name} after {max_retries} failed attempts.")
#         print(f'Processed URL: {url}')
#         time.sleep(2.25)  
# print('Data saved to game_logs_qb.csv')

# ##### RB Game Tables #####
# import pandas as pd
# import requests
# import os
# import csv
# from bs4 import BeautifulSoup
# import time
# df = pd.read_csv('./data/rosters.csv')
# df = df.dropna(subset=['pfr_id'])
# rbs = df[df['position'].str.lower() == 'rb']
# existing_data = []
# if os.path.exists('./data/game_logs_rb.csv'):
#     with open('./data/game_logs_rb.csv', 'r', newline='') as existing_file:
#         reader = csv.reader(existing_file)
#         existing_data = list(reader)
# if existing_data:
#     headers = existing_data[0]
#     existing_player_urls = {row[headers.index('Player URL')] for row in existing_data[1:]}
# else:
#     headers = []
#     existing_player_urls = set()
# with open('./data/game_logs_rb.csv', 'a', newline='') as file:
#     writer = csv.writer(file)
#     if not headers:
#         headers = ['Player URL', 'Position', 'First Name', 'Last Name']  
#         headers_written = False
#     else:
#         headers_written = True
#     total_rbs = len(rbs)
#     rb_counter = 0
#     for index, rb in rbs.iterrows():
#         rb_counter += 1
#         url = rb['url']
#         print(f"Processing RB {rb_counter}/{total_rbs}: {rb['first_name']} {rb['last_name']}")
#         first_name = rb['first_name']  
#         last_name = rb['last_name']    
#         position = 'RB'  
#         if url in existing_player_urls:
#             print(f"Skipping {rb['first_name']} {rb['last_name']}, data already exists.")
#             continue
#         response = requests.get(url)
#         if response.status_code == 200:
#             soup = BeautifulSoup(response.content, 'html.parser')
#             game_logs_table = soup.find('table', {'id': 'rushing_and_receiving'})
#             if game_logs_table:  
#                 header_row = game_logs_table.find('thead').find_all('tr')[-1]
#                 data_rows = game_logs_table.find('tbody').find_all('tr')
#                 if not headers_written:  
#                     headers.extend(header.text.strip() for header in header_row.find_all('th'))  
#                     writer.writerow(headers)
#                     headers_written = True
#                 for row in data_rows:
#                     cells = row.find_all(['th', 'td'])
#                     data = [url, position, first_name, last_name]  
#                     data.extend(cell.text.strip() for cell in cells)  
#                     writer.writerow(data)
#                     existing_player_urls.add(url)  
#                 print(f"Data written for {first_name} {last_name}")
#             else:
#                 print(f"No game logs table found for URL: {url}")
#         else:
#             print(f"Failed to retrieve URL: {url} with status code: {response.status_code}")
#         time.sleep(2)  
# print('Data saved to game_logs_rb.csv')


# ##### WR Game Tables #####
# df = pd.read_csv('./data/rosters.csv')
# df = df.dropna(subset=['pfr_id'])
# wrs = df[df['position'].str.lower() == 'wr']
# existing_data = pd.DataFrame()
# try:
#     existing_data = pd.read_csv('./data/game_logs_wr.csv')
#     existing_urls = existing_data['Player URL'].unique()
#     wrs = wrs[~wrs['url'].isin(existing_urls)]
# except FileNotFoundError:
#     print('No existing game logs found, starting fresh.')
# with open('./data/game_logs_wr.csv', 'a', newline='') as file:
#     writer = csv.writer(file)
#     headers_written = False  
#     total_wrs = len(wrs)
#     wr_counter = 0
#     for index, wr in wrs.iterrows():
#         wr_counter += 1
#         url = wr['url']
#         print(f"Processing WR {wr_counter}/{total_wrs}: {wr['first_name']} {wr['last_name']}")
#         first_name = wr['first_name']  
#         last_name = wr['last_name']    
#         position = 'WR'  
#         response = requests.get(url)
#         if response.status_code == 200:
#             soup = BeautifulSoup(response.content, 'html.parser')
#             game_logs_table = soup.find('table', {'id': 'receiving_and_rushing'})
#             if game_logs_table:  
#                 header_row = game_logs_table.find('thead').find_all('tr')[-1]
#                 data_rows = game_logs_table.find('tbody').find_all('tr')
#                 if not headers_written:  
#                     headers = ['Player URL', 'Position', 'First Name', 'Last Name']  
#                     headers.extend(header.text.strip() for header in header_row.find_all('th'))  
#                     writer.writerow(headers)
#                     headers_written = True
#                 for row in data_rows:
#                     cells = row.find_all(['th', 'td'])
#                     data = [url, position, first_name, last_name]  
#                     data.extend(cell.text.strip() for cell in cells)  
#                     writer.writerow(data)
#                 print(f"Data written for {first_name} {last_name}")
#             else:
#                 print(f"No game logs table found for URL: {url}")
#         else:
#             print(f"Failed to retrieve URL: {url} with status code: {response.status_code}")
#         time.sleep(2)
# print('Data saved to game_logs_wr.csv')

# ##### TE Game Tables #####
# import pandas as pd
# import csv
# import requests
# from bs4 import BeautifulSoup
# import time
# import os
# df = pd.read_csv('./data/rosters.csv')
# df = df.dropna(subset=['pfr_id'])
# tes = df[df['position'].str.lower() == 'te']
# processed_urls = set()
# if os.path.exists('./data/game_logs_te.csv'):
#     with open('./data/game_logs_te.csv', 'r', newline='') as file:
#         reader = csv.reader(file)
#         next(reader)  
#         for row in reader:
#             processed_urls.add(row[0])  
# with open('./data/game_logs_te.csv', 'a', newline='') as file:
#     writer = csv.writer(file)
#     headers_written = os.path.getsize('./data/game_logs_te.csv') > 0  
#     total_tes = len(tes)
#     te_counter = 0
#     for index, te in tes.iterrows():
#         url = te['url']
#         if url in processed_urls:
#             print(f"Skipping already processed TE: {te['first_name']} {te['last_name']}")
#             continue
#         te_counter += 1
#         print(f"Processing TE {te_counter}/{total_tes}: {te['first_name']} {te['last_name']}")
#         first_name = te['first_name']  
#         last_name = te['last_name']    
#         position = 'TE'  
#         response = requests.get(url)
#         if response.status_code == 200:
#             soup = BeautifulSoup(response.content, 'html.parser')
#             game_logs_table = soup.find('table', {'id': 'receiving_and_rushing'})
#             if game_logs_table:  
#                 header_row = game_logs_table.find('thead').find_all('tr')[-1]
#                 data_rows = game_logs_table.find('tbody').find_all('tr')
#                 if not headers_written:  
#                     headers = ['Player URL', 'Position', 'First Name', 'Last Name']  
#                     headers.extend(header.text.strip() for header in header_row.find_all('th'))  
#                     writer.writerow(headers)
#                     headers_written = True
#                 for row in data_rows:
#                     cells = row.find_all(['th', 'td'])
#                     data = [url, position, first_name, last_name]  
#                     data.extend(cell.text.strip() for cell in cells)  
#                     writer.writerow(data)
#                 print(f"Data written for {first_name} {last_name}")
#             else:
#                 print(f"No game logs table found for URL: {url}")
#         else:
#             print(f"Failed to retrieve URL: {url} with status code: {response.status_code}")
#         processed_urls.add(url)
#         time.sleep(2)  
# print('Data saved to game_logs_te.csv')

# ##### Clean 'em #####
# file_paths = [
#     './data/game_logs_qb.csv',
#     './data/game_logs_wr.csv',
#     './data/game_logs_rb.csv',
#     './data/game_logs_te.csv'
# ]
# for file_path in file_paths:
#     data = pd.read_csv(file_path)
#     data['Year'] = data['Year'].astype(str)
#     data['Pro Bowl'] = data['Year'].str.contains('*', regex=False)
#     data['First-Team AP All-Pro'] = data['Year'].str.contains('+', regex=False)
#     data['Year'] = data['Year'].str.replace('*', '', regex=False)
#     data['Year'] = data['Year'].str.replace('+', '', regex=False)
#     data.to_csv(file_path, index=False)
#     print(f"File updated: {file_path}")






# Print end time and total elapsed time
end_time = datetime.now()
elapsed_time = end_time - start_time
print("\n" + "*"*80 + "\n")
print(f"Process ended at: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
print(f"Total time elapsed: {elapsed_time}")



# ### Delete files if they exist
# if os.path.exists('data/games.csv'):
#     os.remove('data/games.csv')
# if os.path.exists('data/player_stats.csv'):
#     os.remove('data/player_stats.csv')
# if os.path.exists('data/rosters.csv'):
#     os.remove('data/rosters.csv')


# ### Export all tables from SQLite to CSV ###
# conn = sqlite3.connect('data/nfl.db')
# cursor = conn.cursor()
# cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
# tables = cursor.fetchall()
# for table_name_tuple in tables:
#     table_name = table_name_tuple[0]
#     df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
#     output_file = f'data/{table_name.lower()}.csv'
#     df.to_csv(output_file, index=False)
#     print(f"Exported {table_name} to {output_file}")
# conn.close()
# player_stats_path = 'data/playerstats.csv'
# if os.path.exists('data/playerstats.csv'):
#     os.rename('data/playerstats.csv', 'data/player_stats.csv')
#     print(f"Renamed PlayerStats to {player_stats_path}")
