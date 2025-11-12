# **Master PFR-Only NFL Data Scraper**
# Standalone script that scrapes ONLY from Pro Football Reference sources
# Creates comprehensive CSV files in FINAL/ directory (no database files)
# Combines all PFR scraping functionality into one script

import pandas as pd
import requests
import os
import csv
from bs4 import BeautifulSoup, Comment
import time
from time import sleep
import numpy as np
from datetime import datetime, timedelta
from requests.exceptions import Timeout, RequestException

print("="*80)
print("MASTER PFR-ONLY NFL DATA SCRAPER")
print("="*80)
print("Scraping ONLY from Pro Football Reference sources")
print("Creating CSV files in FINAL/ directory (no database files)")
print("="*80)

# Create output directory
final_dir = 'FINAL'
if not os.path.exists(final_dir):
    os.makedirs(final_dir)

# Print start time
start_time = datetime.now()
print(f"\nProcess started at: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")

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

##### Create Teams CSV #####
print("\n1. Creating Teams data...")
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
df_teams.to_csv(f'{final_dir}/teams.csv', index=False)
print(f"✅ Teams CSV created: {len(df_teams)} teams")

##### Scrape Team Game Logs (2023-2025) #####
print("\n2. Scraping Team Game Logs from PFR...")
data_dir = f'{final_dir}/SR-game-logs'
os.makedirs(data_dir, exist_ok=True)
opponent_data_dir = f'{final_dir}/SR-opponent-game-logs'
os.makedirs(opponent_data_dir, exist_ok=True)

pfr_teams = [
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

team_game_logs_headers = [
    'rk', 'gtm', 'week', 'date', 'day', 'game_location', 'opp', 'result', 'pts', 'pts_opp', 'ot', 
    'pass_cmp', 'pass_att', 'pass_cmp_pct', 'pass_yds', 'pass_td', 'pass_ya', 'pass_aya', 'pass_rate', 
    'pass_sk', 'pass_sk_yds', 'rush_att', 'rush_yds', 'rush_td', 'rush_ya', 'plays', 'total_yds', 'ypp',
    'fga', 'fgm', 'xpa', 'xpm', 'punt', 'punt_yds', 'first_downs_pass', 'first_downs_rush', 'first_downs_pen',
    'first_downs_total', 'third_down_conv', 'third_down_att', 'fourth_down_conv', 'fourth_down_att', 
    'pen', 'pen_yds', 'fumbles_lost', 'turnovers_int', 'turnovers_total', 'time_of_poss'
]

opponent_game_logs_headers = [
    'rk', 'gtm', 'week', 'date', 'day', 'game_location', 'opp', 'result', 'pts', 'pts_opp', 'ot', 
    'pass_cmp', 'pass_att', 'pass_cmp_pct', 'pass_yds', 'pass_td', 'pass_ya', 'pass_aya', 'pass_rate', 
    'pass_sk', 'pass_sk_yds', 'rush_att', 'rush_yds', 'rush_td', 'rush_ya', 'plays', 'total_yds', 'ypp',
    'fga', 'fgm', 'xpa', 'xpm', 'punt', 'punt_yds', 'first_downs_pass', 'first_downs_rush', 'first_downs_pen',
    'first_downs_total', 'third_down_conv', 'third_down_att', 'fourth_down_conv', 'fourth_down_att', 
    'pen', 'pen_yds', 'fumbles_lost', 'turnovers_int', 'turnovers_total', 'time_of_poss'
]

for year in range(2023, 2026):
    team_file = f'{data_dir}/all_teams_game_logs_{year}.csv'
    opponent_file = f'{opponent_data_dir}/all_teams_opponent_game_logs_{year}.csv'
    
    all_team_game_logs = []  
    all_opponent_game_logs = []
    
    for team in pfr_teams:
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
        sleep(2.5)  # Rate limiting delay
    
    # Save yearly files
    with open(team_file, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(team_game_logs_headers + ['team_name'])
        writer.writerows(all_team_game_logs)
    
    with open(opponent_file, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(opponent_game_logs_headers + ['team_name'])
        writer.writerows(all_opponent_game_logs)

print(f"✅ Team Game Logs scraped and saved to {data_dir}/")

##### Create Game IDs and Basic Games Data #####
print("\n3. Creating basic games data from team game logs...")
directory = data_dir
df_list = []
for filename in os.listdir(directory):
    if filename.endswith(".csv"):  
        file_path = os.path.join(directory, filename)
        season = filename.split('_')[-1].replace('.csv', '')
        df = pd.read_csv(file_path)
        df['season'] = season
        df_list.append(df)

if df_list:
    df = pd.concat(df_list, ignore_index=True)
    
    # Team abbreviation mapping
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

    # PFR to standard abbreviation mapping
    pfr_to_standard_abbr = {
        'ARI': 'ARI', 'ATL': 'ATL', 'BAL': 'BAL', 'BUF': 'BUF', 'CAR': 'CAR',
        'CHI': 'CHI', 'CIN': 'CIN', 'CLE': 'CLE', 'DAL': 'DAL', 'DEN': 'DEN',
        'DET': 'DET', 'GNB': 'GB', 'HOU': 'HOU', 'IND': 'IND', 'JAX': 'JAX',
        'KAN': 'KC', 'LA': 'LAR', 'LAC': 'LAC', 'LAR': 'LAR', 'LV': 'LVR',
        'LVR': 'LVR', 'MIA': 'MIA', 'MIN': 'MIN', 'NWE': 'NE', 'NOR': 'NO',
        'NYG': 'NYG', 'NYJ': 'NYJ', 'OAK': 'LVR', 'PHI': 'PHI', 'PIT': 'PIT',
        'SD': 'LAC', 'SDG': 'LAC', 'SEA': 'SEA', 'SF': 'SF', 'SFO': 'SF',
        'STL': 'LAR', 'TAM': 'TB', 'TEN': 'TEN', 'WAS': 'WAS'
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
    
    # Save basic team game logs with game IDs
    df.to_csv(f'{final_dir}/all_team_game_logs.csv', index=False)
    print(f"✅ Basic team game logs saved with game IDs")

    # Create basic games data
    games_dataframes = []
    for year in range(2023, 2026):
        year_df = df[df['season'] == str(year)].copy()
        if not year_df.empty:
            year_df['season'] = year
            year_df['week'] = year_df['week']
            year_df['date'] = pd.to_datetime(year_df['date'])
            
            # Extract team abbreviation from team name
            year_df['home_team'] = year_df['team_name'].str.extract(r'(\w+)')[0]
            year_df['away_team'] = year_df['opp']
            year_df['home_score'] = year_df['pts']
            year_df['away_score'] = year_df['pts_opp']
            year_df['game_location'] = year_df['game_location']
            year_df['result'] = year_df['result']
            year_df['overtime'] = year_df['ot'].fillna(0)
            
            # Create game_id
            year_df['game_id'] = year_df.apply(lambda row: f"{year}_{row['week']:02d}_{row['away_team']}_{row['home_team']}", axis=1)
            
            games_dataframes.append(year_df[['game_id', 'season', 'week', 'date', 'home_team', 'away_team', 'home_score', 'away_score', 'game_location', 'result', 'overtime']])

    if games_dataframes:
        df_games = pd.concat(games_dataframes, ignore_index=True)
        # Remove duplicates (each game appears twice - once for each team)
        df_games = df_games.drop_duplicates(subset=['game_id'], keep='first')
        df_games = df_games.sort_values(['season', 'week', 'date'])
        
        # Apply team name standardization
        df_games['away_team'] = df_games['away_team'].replace(standardize_mapping)
        df_games['home_team'] = df_games['home_team'].replace(standardize_mapping)
        
        # Save basic games data
        df_games.to_csv(f'{final_dir}/games.csv', index=False)
        print(f"✅ Basic games data created: {len(df_games)} games")

##### Create Aggregated Team Game Logs #####
print("\n4. Creating aggregated team game logs...")
df = pd.read_csv(f'{final_dir}/all_team_game_logs.csv')
grouped_df = df.groupby('game_id', group_keys=False).apply(lambda x: pd.Series({
    'season': x['season'].iloc[0],
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

grouped_df.to_csv(f'{final_dir}/team_game_logs.csv', index=True)
print(f"✅ Aggregated team game logs created: {len(grouped_df)} games")

##### Create Comprehensive Game Logs (Games + Team Stats) #####
print("\n5. Creating comprehensive game logs...")
games_df = pd.read_csv(f'{final_dir}/games.csv')
team_logs_df = pd.read_csv(f'{final_dir}/team_game_logs.csv')

# Merge games and team game logs on game_id and season
comprehensive_games_df = games_df.merge(
    team_logs_df, 
    on=['game_id', 'season'], 
    how='inner'
)

# Save comprehensive merged file
comprehensive_games_df.to_csv(f'{final_dir}/game_logs.csv', index=False)
print(f"✅ Comprehensive game logs created: {len(comprehensive_games_df)} games with {len(comprehensive_games_df.columns)} columns")

##### Scrape Box Scores (2023-2025) #####
print("\n6. Scraping Box Scores from PFR...")
os.makedirs(f'{final_dir}/SR-box-scores/', exist_ok=True)

# Create PFR URLs from games data
games_df_temp = pd.read_csv(f'{final_dir}/games.csv')
games_df_temp['pfr'] = games_df_temp['game_id'].str.replace('_', '').str.lower()
games_df_temp['pfr_url'] = 'https://www.pro-football-reference.com/boxscores/' + games_df_temp['pfr'] + '.htm'
games_df_temp.to_csv(f'{final_dir}/games.csv', index=False)

headers = ['URL', 'Team', '1', '2', '3', '4', 'OT1', 'OT2', 'OT3', 'OT4', 'Final']

for year_to_scrape in range(2023, 2026):
    csv_file_path = f'{final_dir}/SR-box-scores/all_box_scores_{year_to_scrape}.csv'
    games_csv_path = f'{final_dir}/games.csv'
    
    existing_urls = set()
    if os.path.exists(csv_file_path):
        with open(csv_file_path, 'r') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                existing_urls.add(row['URL'])
    
    with open(csv_file_path, 'a', newline='') as csvfile:
        score_writer = csv.writer(csvfile)
        if os.path.getsize(csv_file_path) == 0:
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
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    print(f"Scraping game: {url}")
                    response = requests.get(url, timeout=10)
                    response.raise_for_status()
                    
                    # Save raw HTML
                    raw_file_name = url.split('/')[-1].replace('.htm', '') + '.html'
                    raw_file_path = f'{final_dir}/SR-box-scores/{raw_file_name}'
                    with open(raw_file_path, 'wb') as raw_file:
                        raw_file.write(response.content)
                    
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
                    print(f"Successfully scraped box score for {url}")
                    break
                except Exception as e:
                    print(f"Error scraping {url}: {e}")
                    if attempt < max_retries - 1:
                        time.sleep(2 ** attempt)
                    else:
                        pass
            time.sleep(2.5)
    
    print(f"Box scores scraping completed for {year_to_scrape}. Data saved to {csv_file_path}.")

# Merge Box Scores
input_dir = f'{final_dir}/SR-box-scores/'
csv_files = [f for f in os.listdir(input_dir) if f.endswith('.csv')]
if csv_files:
    dataframes = [pd.read_csv(os.path.join(input_dir, file)) for file in csv_files]
    merged_dataframe = pd.concat(dataframes, ignore_index=True)
    output_file = f'{final_dir}/box_scores.csv'
    merged_dataframe.to_csv(output_file, index=False)
    print(f"✅ Box Scores created: {len(merged_dataframe)} records")
else:
    box_scores_df = pd.DataFrame(columns=headers)
    box_scores_df.to_csv(f'{final_dir}/box_scores.csv', index=False)
    print(f"✅ Box Scores structure created")

##### Create Player Stats (PFR-only, no NFLverse) #####
print("\n7. Creating Player Stats structure...")
# For a full implementation, you would scrape PFR player offense tables
# Here we create the structure that would be populated

player_stats_headers = [
    'player', 'player_id', 'team', 'game_id', 'season', 'week',
    'pass_cmp', 'pass_att', 'pass_yds', 'pass_td', 'pass_int', 
    'pass_sacked', 'pass_sacked_yds', 'pass_long', 'pass_rating', 
    'rush_att', 'rush_yds', 'rush_td', 'rush_long', 
    'targets', 'rec', 'rec_yds', 'rec_td', 'rec_long', 
    'fumbles', 'fumbles_lost'
]

# Create empty player stats structure (you would populate this with actual PFR scraping)
player_stats_df = pd.DataFrame(columns=player_stats_headers)
player_stats_df.to_csv(f'{final_dir}/player_stats.csv', index=False)
print(f"✅ Player Stats structure created")

##### Scrape Scoring Tables/Touchdown Logs (2023-2025) #####
print("\n8. Scraping Scoring Tables from PFR...")
os.makedirs(f'{final_dir}/SR-scoring-tables/', exist_ok=True)

for year_to_scrape in range(2023, 2026):
    output_filename = f'{final_dir}/SR-scoring-tables/all_nfl_scoring_tables_{year_to_scrape}.csv'
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
        
        # Use comprehensive games data to get PFR URLs
        games_df_temp = pd.read_csv(f'{final_dir}/games.csv')
        # Add dummy PFR values for demo (in real implementation, these would come from original games data)
        games_df_temp['pfr'] = games_df_temp['game_id'].str.replace('_', '').str.lower()
        
        rows = []
        now_dt = datetime.now()
        for _, row in games_df_temp.iterrows():
            try:
                game_dt = datetime.fromisoformat(row['date'])
            except Exception:
                continue
            if int(row['game_id'].split('_')[0]) == year_to_scrape and game_dt <= now_dt:
                rows.append(row.to_dict())
        
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
                    print(f"Successfully scraped scoring data for game ID: {game_id}")
                    break
                except (requests.exceptions.RequestException, Exception) as e:
                    print(f"An error occurred while scraping {url}. Error: {e}")
                    if attempt < max_retries - 1:
                        time.sleep(2 ** attempt)
                    else:
                        break
            time.sleep(2.5)
    
    print(f"Scoring tables scraping completed for {year_to_scrape}")

# Merge Scoring Tables
input_dir = f'{final_dir}/SR-scoring-tables/'
csv_files = [f for f in os.listdir(input_dir) if f.endswith('.csv')]
if csv_files:
    dataframes = [pd.read_csv(os.path.join(input_dir, file)) for file in csv_files]
    merged_dataframe = pd.concat(dataframes, ignore_index=True)
    output_file = f'{final_dir}/scoring_tables.csv'
    merged_dataframe.to_csv(output_file, index=False)
    print(f"✅ Scoring Tables created: {len(merged_dataframe)} records")
else:
    scoring_tables_df = pd.DataFrame(columns=['Quarter', 'Time', 'Team', 'Detail', 'Team_1', 'Team_2', 'Game_ID'])
    scoring_tables_df.to_csv(f'{final_dir}/scoring_tables.csv', index=False)
    print(f"✅ Scoring Tables structure created")

##### Team Stats and Rankings (2023-2025) #####
print("\n9. Scraping Team Stats from PFR...")
os.makedirs(f'{final_dir}/SR-team-stats/', exist_ok=True)

team_stats_headers = [
    'Player', 'PF', 'Yds', 'Ply', 'Y/P', 'TO', 'FL', '1stD', 'Cmp', 'Att', 'Yds', 'TD', 'Int', 'NY/A',
    '1stD', 'Att', 'Yds', 'TD', 'Y/A', '1stD', 'Pen', 'Yds', '1stPy', '#Dr', 'Sc%', 'TO%', 'Start', 'Time', 'Plays', 'Yds', 'Pts', 'Team'
]

for year in range(2023, 2026):
    output_file = f'{final_dir}/SR-team-stats/all_teams_stats_{year}.csv'
    if os.path.exists(output_file):
        print(f"Skipping year {year}, file already exists.")
        continue
    
    all_team_stats = []
    for team in pfr_teams:
        abbreviation, name = team
        print(f'Processing {name} for the year {year}')
        url = f'https://www.pro-football-reference.com/teams/{abbreviation}/{year}.htm'
        
        # Add retry logic for rate limiting
        max_retries = 3
        retry_delay = 10
        response = None
        
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
        
        if response is None or response.status_code != 200:
            continue
            
        soup = BeautifulSoup(response.content, 'html.parser')
        table = soup.find('table', {'id': 'team_stats'})
        if table is None:
            print(f'Team stats table not found on page {url} for {name} in {year}')
            continue
        
        tbody = table.find('tbody')
        if tbody:
            for tr in tbody.find_all('tr'):
                row_data = [tr.find('th').text.strip()]
                row_data.extend([td.text.strip() for td in tr.find_all('td')])
                row_data.append(abbreviation)
                all_team_stats.append(row_data)
        
        sleep(2.5)
    
    with open(output_file, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(team_stats_headers)
        writer.writerows(all_team_stats)
    
    print(f'Saved team stats data for all teams for the year {year}')

# Merge Team Stats
input_dir = f'{final_dir}/SR-team-stats/'
csv_files = [f for f in os.listdir(input_dir) if f.endswith('.csv')]
if csv_files:
    dataframes = []
    for file in csv_files:
        df = pd.read_csv(os.path.join(input_dir, file))
        df['Year'] = file.split('_')[-1].split('.')[0]
        dataframes.append(df)
    merged_dataframe = pd.concat(dataframes, ignore_index=True)
    output_file = f'{final_dir}/team_stats.csv'
    merged_dataframe.to_csv(output_file, index=False)
    print(f"✅ Team Stats created: {len(merged_dataframe)} records")
else:
    team_stats_df = pd.DataFrame(columns=team_stats_headers + ['Year'])
    team_stats_df.to_csv(f'{final_dir}/team_stats.csv', index=False)
    print(f"✅ Team Stats structure created")

##### Schedule & Game Results (2023-2025) #####
print("\n10. Scraping Schedule & Game Results from PFR...")
os.makedirs(f'{final_dir}/SR-schedule-and-game-results/', exist_ok=True)

schedule_headers = [
    'Week', 'Day', 'Date', 'Time', 'Boxscore', 'Outcome', 'OT', 'Rec', 'Home/Away', 'Opp', 
    'Tm', 'OppPts', '1stD', 'TotYd', 'PassY', 'RushY', 'TO_lost', 
    'Opp1stD', 'OppTotYd', 'OppPassY', 'OppRushY', 'TO_won',
    'Offense', 'Defense', 'Sp. Tms'
]

for year in range(2023, 2026):
    all_games = []
    for team in pfr_teams:
        abbreviation, name = team
        print(f'Processing {name} for the year {year}')
        url = f'https://www.pro-football-reference.com/teams/{abbreviation}/{year}.htm'
        
        # Add retry logic for rate limiting
        max_retries = 3
        retry_delay = 10
        response = None
        
        for attempt in range(max_retries):
            try:
                response = requests.get(url, timeout=10)
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
            
            if len(row_data) != len(schedule_headers):
                row_data += [''] * (len(schedule_headers) - len(row_data))
            
            team_games.append(row_data)
            all_games.append(row_data)
        
        # Save individual team file
        team_file_path = f'{final_dir}/SR-schedule-and-game-results/{abbreviation}_{year}_schedule_and_game_results.csv'
        with open(team_file_path, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(schedule_headers)
            writer.writerows(team_games)
        
        print(f'Saved schedule data for {name} for the year {year}')
        sleep(2.5)

# Merge all team files
print(f"\nMerging all team files...")
all_games = []
for filename in os.listdir(f'{final_dir}/SR-schedule-and-game-results/'):
    if filename.endswith("_schedule_and_game_results.csv"):
        team_abbr = filename.split('_')[0]
        season_year = filename.split('_')[1]
        file_path = os.path.join(f'{final_dir}/SR-schedule-and-game-results/', filename)
        df = pd.read_csv(file_path)
        df['Team'] = team_abbr
        df['Season'] = season_year
        all_games.append(df)

if all_games:
    merged_df = pd.concat(all_games, ignore_index=True)
    merged_output_path = os.path.join(f'{final_dir}/SR-schedule-and-game-results/', 'all_teams_schedule_and_game_results_merged.csv')
    merged_df.to_csv(merged_output_path, index=False)
    main_data_path = f'{final_dir}/schedule_game_results.csv'
    merged_df.to_csv(main_data_path, index=False)
    print(f"✅ Schedule & Game Results created: {len(merged_df)} records")
else:
    schedule_df = pd.DataFrame(columns=schedule_headers + ['Team', 'Season'])
    schedule_df.to_csv(f'{final_dir}/schedule_game_results.csv', index=False)
    print(f"✅ Schedule & Game Results structure created")

##### Team Conversions (2023-2025) #####
print("\n11. Scraping Team Conversions from PFR...")
os.makedirs(f'{final_dir}/SR-team-conversions/', exist_ok=True)

team_conversions_headers = [
    'Player', '3DAtt', '3DConv', '4DAtt', '4DConv', '4D%', 'RZAtt', 'RZTD', 'RZPct', 'Team'
]

for year in range(2023, 2026):
    for team in pfr_teams:
        abbreviation, name = team
        team_file = f'{final_dir}/SR-team-conversions/{abbreviation}_{year}_team_conversions.csv'
        
        if os.path.exists(team_file):
            print(f"Skipping {name} for {year}, file already exists.")
            continue
        
        print(f'Processing {name} for the year {year}')
        url = f'https://www.pro-football-reference.com/teams/{abbreviation}/{year}.htm'
        
        # Add retry logic for rate limiting
        max_retries = 3
        retry_delay = 10
        response = None
        
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
        
        if response is None or response.status_code != 200:
            continue
            
        soup = BeautifulSoup(response.content, 'html.parser')
        table = soup.find('table', {'id': 'team_conversions'})
        if table is None:
            print(f'Team Conversions table not found on page {url} for {name} in {year}')
            sleep(2.5)
            continue
        
        all_conversions = []
        tbody = table.find('tbody')
        if tbody:
            for tr in tbody.find_all('tr'):
                row_data = [td.text.strip() for td in tr.find_all(['th', 'td'])]
                row_data.append(abbreviation)
                all_conversions.append(row_data)
        
        with open(team_file, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(team_conversions_headers)
            writer.writerows(all_conversions)
        
        print(f'Saved team conversions data for {name} for the year {year}')
        sleep(3)

# Merge Team Conversions
input_dir = f'{final_dir}/SR-team-conversions/'
csv_files = [f for f in os.listdir(input_dir) if f.endswith('.csv')]
if csv_files:
    dataframes = []
    for file in csv_files:
        df = pd.read_csv(os.path.join(input_dir, file))
        df['Year'] = file.split('_')[1]
        dataframes.append(df)
    merged_dataframe = pd.concat(dataframes, ignore_index=True)
    output_file = f'{final_dir}/team_conversions.csv'
    merged_dataframe.to_csv(output_file, index=False)
    print(f"✅ Team Conversions created: {len(merged_dataframe)} records")
else:
    team_conversions_df = pd.DataFrame(columns=team_conversions_headers + ['Year'])
    team_conversions_df.to_csv(f'{final_dir}/team_conversions.csv', index=False)
    print(f"✅ Team Conversions structure created")

##### Passing/Rushing/Receiving Game Logs (2023-2025) #####
print("\n12. Scraping Passing/Rushing/Receiving from PFR...")
os.makedirs(f'{final_dir}/SR-passing-rushing-receiving-game-logs/', exist_ok=True)

for year_to_scrape in range(2023, 2026):
    output_filename = f'{final_dir}/SR-passing-rushing-receiving-game-logs/all_passing_rushing_receiving_{year_to_scrape}.csv'
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
        
        # Use comprehensive games data to get PFR URLs
        games_df_temp = pd.read_csv(f'{final_dir}/games.csv')
        games_df_temp['pfr'] = games_df_temp['game_id'].str.replace('_', '').str.lower()
        
        rows = []
        now_dt = datetime.now()
        for _, row in games_df_temp.iterrows():
            try:
                game_dt = datetime.fromisoformat(row['date'])
            except Exception:
                continue
            if int(row['game_id'].split('_')[0]) == year_to_scrape and game_dt <= now_dt:
                rows.append(row.to_dict())
        
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
                        print(f"Successfully scraped passing/rushing/receiving data for game ID: {game_id}")
                        time.sleep(2)
                        break
                except Exception as e:
                    print(f"An error occurred while scraping {url}. Error: {e}")
                    if attempt < max_retries - 1:
                        time.sleep(2 ** attempt)
                    else:
                        break
            time.sleep(2.5)
    
    print(f"Passing/Rushing/Receiving scraping completed for {year_to_scrape}")

# Clean weird rows in passing/rushing/receiving
directory = f'{final_dir}/SR-passing-rushing-receiving-game-logs/'
for filename in os.listdir(directory):
    if filename.endswith('.csv'):
        file_path = os.path.join(directory, filename)
        df = pd.read_csv(file_path)
        df_cleaned = df[(df['player'] != 'Player') & (df['player'].notna())]
        df_cleaned.to_csv(file_path, index=False)
        print(f"Processed {filename}")

# Merge all passing/rushing/receiving
merged_file_path = f'{final_dir}/passing_rushing_receiving.csv'
dataframes = []
for filename in os.listdir(directory):
    if filename.endswith('.csv'):
        file_path = os.path.join(directory, filename)
        df = pd.read_csv(file_path)
        dataframes.append(df)
        print(f"Added {filename} to the merge list")

if dataframes:
    merged_df = pd.concat(dataframes, ignore_index=True)
    merged_df.to_csv(merged_file_path, index=False)
    print(f"✅ Passing/Rushing/Receiving created: {len(merged_df)} records")
else:
    passing_rushing_receiving_df = pd.DataFrame(columns=[
        'player', 'player_id', 'team', 'pass_cmp', 'pass_att', 'pass_yds', 'pass_td', 'pass_int', 
        'pass_sacked', 'pass_sacked_yds', 'pass_long', 'pass_rating', 'rush_att', 'rush_yds', 'rush_td', 
        'rush_long', 'targets', 'rec', 'rec_yds', 'rec_td', 'rec_long', 'fumbles', 'fumbles_lost', 'game_id'
    ])
    passing_rushing_receiving_df.to_csv(merged_file_path, index=False)
    print(f"✅ Passing/Rushing/Receiving structure created")

##### Defense Game Logs (2023-2025) #####
print("\n13. Scraping Defense Game Logs from PFR...")
os.makedirs(f'{final_dir}/SR-defense-game-logs/', exist_ok=True)

headers = [
    'player', 'team', 'def_int', 'def_int_yds', 'def_int_td', 'def_int_long', 'pass_defended', 'sacks',
    'tackles_combined', 'tackles_solo', 'tackles_assists', 'tackles_loss', 'qb_hits', 'fumbles_rec',
    'fumbles_rec_yds', 'fumbles_rec_td', 'fumbles_forced', 'game_id'
]

for year_to_scrape in range(2023, 2026):
    output_filename = f'{final_dir}/SR-defense-game-logs/all_defense_{year_to_scrape}.csv'
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
        
        # Use comprehensive games data to get PFR URLs
        games_df_temp = pd.read_csv(f'{final_dir}/games.csv')
        games_df_temp['pfr'] = games_df_temp['game_id'].str.replace('_', '').str.lower()
        
        rows = []
        now_dt = datetime.now()
        for _, row in games_df_temp.iterrows():
            try:
                game_dt = datetime.fromisoformat(row['date'])
            except Exception:
                continue
            if int(row['game_id'].split('_')[0]) == year_to_scrape and game_dt <= now_dt:
                rows.append(row.to_dict())
        
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
                            print(f"Successfully scraped defense data for game ID: {game_id}")
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
    
    print(f"Defense scraping completed for {year_to_scrape}")

# Clean defense data
for year in range(2023, 2026):
    file_path = f'{final_dir}/SR-defense-game-logs/all_defense_{year}.csv'
    try:
        if os.path.exists(file_path):
            df = pd.read_csv(file_path)
            df.dropna(inplace=True)
            df.to_csv(file_path, index=False)
            print(f"Cleaned defense data for {year}")
    except FileNotFoundError:
        print(f"No defense data file found for {year}")

# Merge all defense-game-logs.csv files into one
input_dir = f'{final_dir}/SR-defense-game-logs/'
csv_files = [f for f in os.listdir(input_dir) if f.endswith('.csv')]
if csv_files:
    dataframes = [pd.read_csv(os.path.join(input_dir, file)) for file in csv_files]
    merged_dataframe = pd.concat(dataframes, ignore_index=True)
    output_file = f'{final_dir}/defense_game_logs.csv'
    merged_dataframe.to_csv(output_file, index=False)
    print(f"✅ Defense Game Logs created: {len(merged_dataframe)} records")
else:
    defense_df = pd.DataFrame(columns=headers)
    defense_df.to_csv(f'{final_dir}/defense_game_logs.csv', index=False)
    print(f"✅ Defense Game Logs structure created")

##### Create Summary Report #####
print("\n14. Creating summary report...")
summary_data = {
    'Dataset': ['Teams', 'Games', 'Team Game Logs', 'Comprehensive Game Logs', 'Box Scores', 'Player Stats', 
                'Scoring Tables', 'Team Stats', 'Schedule Game Results', 'Team Conversions', 
                'Passing Rushing Receiving', 'Defense Game Logs'],
    'Records': [len(df_teams), len(games_df), len(grouped_df), len(comprehensive_games_df), 
                len(box_scores_df), len(player_stats_df), len(scoring_tables_df), len(team_stats_df),
                len(schedule_df), len(team_conversions_df), len(passing_rushing_receiving_df), len(defense_df)],
    'Source': ['Hardcoded', 'PFR Team Game Logs', 'PFR Team Game Logs (Aggregated)', 'PFR Team Game Logs (Merged)', 
               'PFR Box Scores', 'PFR Player Offense', 'PFR Scoring Tables', 'PFR Team Stats',
               'PFR Schedule Data', 'PFR Team Conversions', 'PFR Player Offense', 'PFR Defense Stats'],
    'Years': ['Static', '2023-2025', '2023-2025', '2023-2025', '2023-2025', 'Structure Only',
              '2023-2025', '2023-2025', '2023-2025', '2023-2025', '2023-2025', '2023-2025']
}

summary_df = pd.DataFrame(summary_data)
summary_df.to_csv(f'{final_dir}/summary_report.csv', index=False)

# Print final summary
end_time = datetime.now()
elapsed_time = end_time - start_time

print("\n" + "="*80)
print("🎉 MASTER PFR-ONLY SCRAPER COMPLETED!")
print("="*80)
print(f"⏱️  Total time elapsed: {elapsed_time}")
print(f"📁 Output directory: {final_dir}/")
print(f"📊 Files created:")
print(f"  • teams.csv - {len(df_teams)} teams")
print(f"  • games.csv - {len(games_df)} games")
print(f"  • team_game_logs.csv - {len(grouped_df)} aggregated games")
print(f"  • game_logs.csv - {len(comprehensive_games_df)} comprehensive games")
print(f"  • box_scores.csv - {len(box_scores_df)} box score records")
print(f"  • player_stats.csv - Player stats structure")
print(f"  • scoring_tables.csv - {len(scoring_tables_df)} scoring records")
print(f"  • team_stats.csv - {len(team_stats_df)} team stats records")
print(f"  • schedule_game_results.csv - {len(schedule_df)} schedule records")
print(f"  • team_conversions.csv - {len(team_conversions_df)} conversion records")
print(f"  • passing_rushing_receiving.csv - {len(passing_rushing_receiving_df)} player records")
print(f"  • defense_game_logs.csv - {len(defense_df)} defense records")
print(f"  • summary_report.csv - Summary of all datasets")
print(f"📂 Raw data directories:")
print(f"  • {final_dir}/SR-game-logs/ - Raw team game logs by year")
print(f"  • {final_dir}/SR-opponent-game-logs/ - Raw opponent game logs by year")
print(f"  • {final_dir}/SR-box-scores/ - Raw box scores by year")
print(f"  • {final_dir}/SR-scoring-tables/ - Raw scoring tables by year")
print(f"  • {final_dir}/SR-team-stats/ - Raw team stats by year")
print(f"  • {final_dir}/SR-schedule-and-game-results/ - Raw schedule data by year")
print(f"  • {final_dir}/SR-team-conversions/ - Raw team conversions by year")
print(f"  • {final_dir}/SR-passing-rushing-receiving-game-logs/ - Raw player offense by year")
print(f"  • {final_dir}/SR-defense-game-logs/ - Raw defense stats by year")
print("\n✅ All data sourced exclusively from Pro Football Reference!")
print("✅ No NFLverse contamination!")
print("✅ CSV files only - no database files!")
print("="*80)
