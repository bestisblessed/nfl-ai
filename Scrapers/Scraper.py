import pandas as pd
import sqlite3
import requests
import os
import csv
from bs4 import BeautifulSoup, Comment
import time
from time import sleep
os.remove('nfl.db')

### Create 'Teams' in nfl.db

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


# Create 'Games' in nfl.db

url = 'https://raw.githubusercontent.com/nflverse/nfldata/master/data/games.csv'
response = requests.get(url)
if response.ok:
    with open('./data/games.csv', 'wb') as file:
        file.write(response.content)
else:
    raise Exception(f"Failed to download the file. Status code: {response.status_code}")

df = pd.read_csv('./data/games.csv')

# Standardize team names
standardize_mapping = {
    'OAK': 'LVR',  # Oakland Raiders to Las Vegas Raiders
    'SD': 'LAC',   # San Diego Chargers to Los Angeles Chargers
    'STL': 'LAR',  # St. Louis Rams to Los Angeles Rams
    'LA': 'LAR',   # Los Angeles Rams
    'LV': 'LVR'    # Las Vegas Raiders
}
df['away_team'] = df['away_team'].replace(standardize_mapping)
df['home_team'] = df['home_team'].replace(standardize_mapping)
df.rename(columns={'gameday': 'date'}, inplace=True)
df = df[df['season'] != 1999]

# Standardize the 'game_id' column
df['game_id'] = df['game_id'].apply(lambda x: f"{x.split('_')[0]}_{x.split('_')[1]}_{standardize_mapping.get(x.split('_')[2], x.split('_')[2])}_{standardize_mapping.get(x.split('_')[3], x.split('_')[3])}")

# Convert datetime and create new columns
df['date'] = pd.to_datetime(df['date'])
df['week'] = df['week'].apply(lambda x: f'{x:02d}')
df['game_id_simple'] = df['season'].astype(str) + "_" + df['week']
df['game_id_team1'] = df['game_id_simple'] + "_" + df['home_team']
df['game_id_team2'] = df['game_id_simple'] + "_" + df['away_team']

# Select columns 
selected_columns = [
    'game_id', 'season', 'week', 'game_type', 'date', 'weekday', 'gametime', 
    'away_team', 'away_score', 'home_team', 'home_score', 'location', 'result',	'total', 'overtime', 
    'spread_line', 'total_line', 'away_rest', 'home_rest', 'roof', 'surface', 'temp', 'wind', 
    'away_qb_id', 'home_qb_id', 'away_qb_name', 'home_qb_name', 'away_coach', 'home_coach', 'referee',
    'stadium_id', 'stadium', 'game_id_simple', 'game_id_team1', 'game_id_team2', 'pfr'
]
df_selected = df[selected_columns]

# Save
db_path = 'nfl.db'
conn = sqlite3.connect(db_path)
df_selected.to_sql('Games', conn, if_exists='replace', index=False)
conn.close()
df_selected.to_csv('./data/games_modified.csv', index=False)



# Create 'Players' in nfl.db

dataframes = []

# for year in range(2015, 2025):
for year in range(2000, 2025):
    url = f"https://github.com/nflverse/nflverse-data/releases/download/player_stats/player_stats_{year}.csv"
    response = requests.get(url)
    if response.ok:
        file_path = os.path.join('./data/player-stats/', f"player_stats_{year}.csv")
        with open(file_path, 'wb') as file:
            file.write(response.content)
        print(f"Downloaded and saved player_stats_{year}.csv")
        
        # Load and append the downloaded file to the list of DataFrames
        df = pd.read_csv(file_path)
        if 'opponent_team' in df.columns:
            df = df.drop(columns=['opponent_team'])
        dataframes.append(df)
    else:
        print(f"Failed to download data for the year {year}")

# Merge all player stats DataFrames
merged_df = pd.concat(dataframes, ignore_index=True, sort=False)

# Standardize team abbreviations and format weeks
# standardize_mapping = {'LA': 'LAR', 'LV': 'LVR'}
standardize_mapping = {
    'OAK': 'LVR',  # Oakland Raiders to Las Vegas Raiders
    'SD': 'LAC',   # San Diego Chargers to Los Angeles Chargers
    'STL': 'LAR',  # St. Louis Rams to Los Angeles Rams
    'LA': 'LAR',   # Los Angeles Rams
    'LV': 'LVR'    # Las Vegas Raiders
}
merged_df['recent_team'] = merged_df['recent_team'].replace(standardize_mapping)
merged_df['week'] = merged_df['week'].apply(lambda x: f'{x:02d}')

# Create game IDs
merged_df['game_id_team'] = merged_df['season'].astype(str) + '_' + merged_df['week'].astype(str) + '_' + merged_df['recent_team']
merged_df['game_id_simple'] = merged_df['season'].astype(str) + '_' + merged_df['week'].astype(str)

# Save
merged_df.to_csv('./data/player_stats.csv', index=False)
print("Merged and cleaned player stats saved to './data/player_stats.csv'")

# Merge with game data from games.csv
# games_df = pd.read_csv('./data/games.csv')
# game_id_map = pd.concat([
#     games_df[['game_id_team1', 'game_id', 'home_team', 'away_team']].rename(columns={'game_id_team1': 'game_id_team'}),
#     games_df[['game_id_team2', 'game_id', 'home_team', 'away_team']].rename(columns={'game_id_team2': 'game_id_team'})
# ]).drop_duplicates(subset=['game_id_team'])
# merged_df = merged_df.merge(game_id_map, on='game_id_team', how='left')
games_df = pd.read_csv('./data/games_modified.csv')
game_id_map = pd.concat([
    games_df[['game_id_team1', 'game_id', 'home_team', 'away_team']].rename(columns={'game_id_team1': 'game_id_team'}),
    games_df[['game_id_team2', 'game_id', 'home_team', 'away_team']].rename(columns={'game_id_team2': 'game_id_team'})
]).drop_duplicates(subset=['game_id_team'])
merged_df = merged_df.merge(game_id_map, on='game_id_team', how='left')


# Clean the DataFrame
position_groups_to_remove = ['SPEC', 'LB', 'DB', 'OL', 'DL']
df_cleaned = merged_df[~merged_df['position_group'].isin(position_groups_to_remove)].dropna(subset=['position_group'])

df_cleaned.to_csv('./data/player_stats.csv', index=False)
print("Final cleaned player stats saved to './data/player_stats.csv'")

# Save the cleaned player stats to SQLite database
conn = sqlite3.connect('nfl.db')
cursor = conn.cursor()

# SQL command to create the 'PlayerStats' table
# player_current_team TEXT,  -- Renamed column
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

# Execute the SQL command
cursor.execute(create_table_sql)

# Load the cleaned data into a DataFrame
df = pd.read_csv('./data/player_stats.csv')

# Rename the 'recent_team' column to 'player_current_team'
df.rename(columns={'recent_team': 'player_current_team'}, inplace=True)

# Select only the relevant columns to import
columns_to_import = ['player_display_name', 'player_current_team', 'game_id', 'season', 'week', 
                     'position', 'headshot_url', 'completions', 'attempts', 'passing_yards', 
                     'passing_tds', 'interceptions', 'sacks', 'carries', 'rushing_yards', 
                     'rushing_tds', 'rushing_fumbles', 'receptions', 'targets', 'receiving_yards', 
                     'receiving_tds', 'receiving_fumbles', 'fantasy_points_ppr', 'home_team', 'away_team']

df_to_import = df[columns_to_import]

# Import data into the 'PlayerStats' table
df_to_import.to_sql('PlayerStats', conn, if_exists='replace', index=False)

# Close the database connection
conn.close()
print("Player stats saved to 'PlayerStats' table in nfl.db")





# Create 'Rosters' in nfl.db (2015-2025)

# Iterate through the years 2015 to 2025
# for year in range(2015, 2025):
for year in range(2000, 2025):
    # Construct the URL for the CSV file of the specific year
    url = f"https://github.com/nflverse/nflverse-data/releases/download/rosters/roster_{year}.csv"
    
    # Send a GET request to the URL
    response = requests.get(url)

    # Check if the request was successful
    if response.status_code == 200:
        # Open the file in write-binary mode and save the CSV
        with open(f"./data/rosters/roster_{year}.csv", 'wb') as file:
            file.write(response.content)
        print(f"Downloaded and saved roster_{year}.csv")
    else:
        print(f"Failed to download data for the year {year}")

        
# Combine roster data years
dataframes = []

for year in range(2015, 2025):
    file_path = f'./data/rosters/roster_{year}.csv'
    if os.path.exists(file_path):
        df = pd.read_csv(file_path)
        dataframes.append(df)

merged_data = pd.concat(dataframes, ignore_index=True)

# Make pfr_id's
base_url = "https://www.pro-football-reference.com/players/"
merged_data['url'] = merged_data['pfr_id'].apply(lambda x: f"{base_url}{x[0]}/{x}.htm" if pd.notna(x) else None)

merged_data.to_csv('./data/rosters.csv', index=False)
print("Final file saved to ./data/rosters.csv")

conn = sqlite3.connect('nfl.db')
cursor = conn.cursor()
cursor.execute("DROP TABLE IF EXISTS rosters")

# SQL command to create the 'Rosters' table without any primary key
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

# Execute the SQL command to create the table
cursor.execute(create_table_sql)

# Load the CSV data into a DataFrame
df = pd.read_csv('data/rosters.csv')

# Insert the DataFrame data into the 'rosters' table
df.to_sql('Rosters', conn, if_exists='replace', index=False)

# Close the database connection
conn.close()

print("Rosters table created and data inserted successfully.")





# Standardize Team Names in Rosters table

standardize_mapping = {
    'ARZ': 'ARI',  # Arizona Cardinals
    'BLT': 'BAL',  # Baltimore Ravens
    'CLV': 'CLE',  # Cleveland Browns
    'HST': 'HOU',  # Houston Texans
    'LA': 'LAR',   # Los Angeles Rams
    'LV': 'LVR',   # Las Vegas Raiders
    'OAK': 'LVR',  # Oakland Raiders to Las Vegas Raiders
    'SD': 'LAC',   # San Diego Chargers to Los Angeles Chargers
    'SL': 'LAR'    # St. Louis Rams to Los Angeles Rams
}

# Connect to the SQLite database
conn = sqlite3.connect('nfl.db')
cursor = conn.cursor()

# Load the Rosters data into a DataFrame
df = pd.read_sql_query("SELECT * FROM Rosters", conn)

# Standardize team abbreviations in the 'team' and 'draft_club' columns
df['team'] = df['team'].replace(standardize_mapping)
df['draft_club'] = df['draft_club'].replace(standardize_mapping)

# Save the updated DataFrame back to the database
df.to_sql('Rosters', conn, if_exists='replace', index=False)

# Close the database connection
conn.close()
print("Rosters table standardized and updated successfully.")




# Standardize Team Names in rosters.csv

file_path = 'data/rosters.csv'
rosters_df = pd.read_csv(file_path)

# Standardize mapping for team names
standardize_mapping = {
    'ARZ': 'ARI',  # Arizona Cardinals
    'BLT': 'BAL',  # Baltimore Ravens
    'CLV': 'CLE',  # Cleveland Browns
    'HST': 'HOU',  # Houston Texans
    'LA': 'LAR',   # Los Angeles Rams
    'LV': 'LVR',   # Las Vegas Raiders
    'OAK': 'LVR',  # Oakland Raiders to Las Vegas Raiders
    'SD': 'LAC',   # San Diego Chargers to Los Angeles Chargers
    'SL': 'LAR'    # St. Louis Rams to Los Angeles Rams
}

# Apply the standardization mapping to the 'team' column
rosters_df['team'] = rosters_df['team'].replace(standardize_mapping)

# Extract and print the unique standardized team names in a numbered list
standardized_teams = rosters_df['team'].unique()
standardized_team_list_sorted = sorted(list(standardized_teams))

# Print the standardized team names
for idx, team in enumerate(standardized_team_list_sorted, 1):
    print(f"{idx}. {team}")

# If you want to save the standardized data back to a CSV file
rosters_df.to_csv('data/rosters.csv', index=False)


# Box Scores 2024-2025
df = pd.read_csv('./data/games.csv')

# Create the 'pfr_url' column
df['pfr_url'] = 'https://www.pro-football-reference.com/boxscores/' + df['pfr'] + '.htm'

df.to_csv('./data/games.csv', index=False)

csv_file_path = 'data/box_scores.csv'
games_csv_path = 'data/games.csv'

# Define the headers (for reference)
headers = ['URL', 'Team', '1', '2', '3', '4', 'OT1', 'OT2', 'OT3', 'OT4', 'Final']

# Load existing box scores to avoid duplicates
existing_urls = set()
if os.path.exists(csv_file_path):
    with open(csv_file_path, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            existing_urls.add(row['URL'])

# Open the CSV file for writing (append mode if file exists)
with open(csv_file_path, 'a', newline='') as csvfile:
    score_writer = csv.writer(csvfile)

    # Write headers only if the file is newly created
    if os.path.getsize(csv_file_path) == 0:
        score_writer.writerow(headers)  # Write the headers to the CSV file

    # Loop through each year from 2015 to 2025
    # for year_to_scrape in range(2015, 2025):
    for year_to_scrape in range(2024, 2025):
        # Read the URLs for the current season from 'games.csv'
        game_urls = []
        with open(games_csv_path, 'r') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if row['season'] == str(year_to_scrape):  # Filter for the current season
                    game_urls.append(row['pfr_url'])

        # Iterate over each URL and scrape data
        for url in game_urls:
            if url in existing_urls:
                print(f"Skipping already scraped game: {url}")
                continue

            try:    
                # Print the current game being scraped
                print(f"Scraping game: {url}")
                
                # Send a GET request to the URL
                response = requests.get(url)
                response.raise_for_status()

                # Parse the content with BeautifulSoup
                soup = BeautifulSoup(response.content, 'html.parser')

                # Find the linescore table by its class
                linescore_table = soup.find('table', class_='linescore')

                if linescore_table:
                    # Find all rows in the linescore table, skip the header row
                    rows = linescore_table.find_all('tr')[1:]

                    # Extract and write the data from each row
                    for row in rows:
                        cols = row.find_all('td')
                        team_name = cols[1].text.strip()
                        scores = [col.text.strip() for col in cols[2:]]

                        # Pad the scores list to match the headers length
                        scores += [''] * (len(headers) - 2 - len(scores))

                        score_writer.writerow([url, team_name] + scores)

                # Sleep for 3 seconds before the next request
                time.sleep(2)

            except Exception as e:
                print(f"Error scraping {url}: {e}")

            time.sleep(1)

print(f"Scraping complete. The data has been saved to {csv_file_path}.")

# Fix OT columns in box scores
# Not in nfl.db currently

df = pd.read_csv('data/box_scores.csv')

# Function to shift the furthest right value to the 'Final' column
# def shift_to_final(row):
#     for col in reversed(row.index[:-1]):
#         if pd.notna(row[col]):
#             row['Final'] = row[col]
#             row[col] = None
#             break
#     return row
def shift_to_final(row):
    if pd.isna(row['Final']):  # Only shift if the 'Final' column is empty
        for col in reversed(row.index[:-1]):
            if pd.notna(row[col]):
                row['Final'] = row[col]
                row[col] = None
                break
    return row


# Apply the function to each row
df = df.apply(shift_to_final, axis=1)

# Save the modified DataFrame to a new CSV file
df.to_csv('data/box_scores.csv', index=False)

# Scoring Tables (touchdown logs)
# Not in nfl.db currently

# for year_to_scrape in range(2015, 2025):
for year_to_scrape in range(2024, 2025):
    # Initialize output CSV file with the year and "scoring_tables" in its name
    output_filename = f'./data/scoring-tables/all_nfl_scoring_tables_{year_to_scrape}.csv'
    with open(output_filename, 'w', newline='') as output_csvfile:
        csvwriter = csv.writer(output_csvfile)
        csvwriter.writerow(['Quarter', 'Time', 'Team', 'Detail', 'Team_1', 'Team_2', 'Game_ID'])  # Added 'Game_ID'

        # Read the CSV file containing the game data
        with open('./data/games.csv', 'r') as csvfile:
            reader = csv.DictReader(csvfile)
            rows = [row for row in reader if int(row['game_id'].split('_')[0]) == year_to_scrape]  # Filter rows for the year

            for row in rows:
                pfr_value = row['pfr']
                game_id = row['game_id']

                # Form the URL using the 'pfr' value
                url = f"https://www.pro-football-reference.com/boxscores/{pfr_value}.htm"

                try:
                    # Fetch the webpage
                    response = requests.get(url)
                    soup = BeautifulSoup(response.text, 'html.parser')

                    # Find the table containing box score data using its class
                    table = soup.find('table', {'id': 'scoring'})

                    last_quarter = None  # To keep track of the last available quarter value

                    # Loop through the rows to get the scoring data
                    for i, row in enumerate(table.find_all('tr')):
                        if i == 0:  # Skip the first header row
                            continue
                        cells = row.find_all(['td', 'th'])
                        if len(cells) > 0:
                            csv_row = [cell.text for cell in cells]

                            # Fill in missing quarter values
                            if csv_row[0]:
                                last_quarter = csv_row[0]
                            else:
                                csv_row[0] = last_quarter

                            csv_row.append(game_id)  # Append 'game_id' to each row
                            csvwriter.writerow(csv_row)

                    print(f"Successfully scraped scoring data for game ID: {game_id}, PFR: {pfr_value}")

                except Exception as e:
                    print(f"An error occurred while scraping {url}. Error: {e}")

                # Sleep for 3 seconds to avoid overloading the server
                time.sleep(2)

    print(f"Scraping completed for {year_to_scrape}. Scoring data saved to {output_filename}.")










# Team Game Logs
# Not in nfl.db currently

# Create directories if they don't exist
data_dir = './data/SR-game-logs'
os.makedirs(data_dir, exist_ok=True)

# Create directories if they don't exist
opponent_data_dir = './data/SR-opponent-game-logs'
os.makedirs(opponent_data_dir, exist_ok=True)

# List of teams
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

# Custom headers for team game logs and opponent game logs
# team_game_logs_headers = [
#     'Week', 'Day', 'Date', '', 'OT', '', 'Opp', 'Tm', 'Opp', 'Cmp', 'Att', 'Yds', 'TD', 'Int', 'Sk', 'Yds', 'Y/A', 'NY/A',
#     'Cmp%', 'Rate', 'Att', 'Yds', 'Y/A', 'TD', 'FGM', 'FGA', 'XPM', 'XPA', 'Pnt', 'Yds', '3DConv', '3DAtt', '4DConv', '4DAtt', 'ToP', 'Team_Name'
# ]
# team_game_logs_headers = [
#     'Week', 'Day', 'Date', '', '', 'OT', '', 'Opp', 'Tm', 'Opp', 'Cmp', 'Att', 'Yds', 'TD', 'Int', 'Sk', 'Yds', 'Y/A', 'NY/A',
#     'Cmp%', 'Rate', 'Att', 'Yds', 'Y/A', 'TD', 'FGM', 'FGA', 'XPM', 'XPA', 'Pnt', 'Yds', '3DConv', '3DAtt', '4DConv', '4DAtt', 'ToP', 'Team_Name'
# ]
team_game_logs_headers = [
    'week_num', 'game_day_of_week', 'game_date', 'boxscore_word', 'game_outcome', 'overtime', 
    'game_location', 'opp', 'pts_off', 'pts_def', 'pass_cmp', 'pass_att', 'pass_yds', 'pass_td', 
    'pass_int', 'pass_sacked', 'pass_sacked_yds', 'pass_yds_per_att', 'pass_net_yds_per_att', 
    'pass_cmp_perc', 'pass_rating', 'rush_att', 'rush_yds', 'rush_yds_per_att', 'rush_td', 
    'fgm', 'fga', 'xpm', 'xpa', 'punt', 'punt_yds', 'third_down_success', 'third_down_att', 
    'fourth_down_success', 'fourth_down_att', 'time_of_poss', 'Team_Name'
]
# Need to change to:
# week_num
# game_day_of_week
# game_date
# boxscore_word
# game_outcome
# overtime
# game_location
# opp
# pts_off
# pts_def
# pass_cmp
# pass_att
# pass_yds
# pass_td
# pass_int
# pass_sacked
# pass_sacked_yds
# pass_yds_per_att
# pass_net_yds_per_att
# pass_cmp_perc
# pass_rating
# rush_att
# rush_yds
# rush_yds_per_att
# rush_td
# fgm
# fga
# xpm
# xpa
# punt
# punt_yds
# third_down_success
# third_down_att
# fourth_down_success
# fourth_down_att
# time_of_poss
# team_name

# opponent_game_logs_headers = [
#     'Week', 'Day', 'Date', '', 'OT', '', 'Opp', 'Tm', 'Opp', 'Cmp', 'Att', 'Yds', 'TD', 'Int', 'Sk', 'Yds', 'Y/A', 'NY/A',
#     'Cmp%', 'Rate', 'Att', 'Yds', 'Y/A', 'TD', 'FGM', 'FGA', 'XPM', 'XPA', 'Pnt', 'Yds', '3DConv', '3DAtt', '4DConv', '4DAtt', 'ToP', 'Team_Name'
# ]
# opponent_game_logs_headers = [
#     'Week', 'Day', 'Date', '', '', 'OT', '', 'Opp', 'Tm', 'Opp', 'Cmp', 'Att', 'Yds', 'TD', 'Int', 'Sk', 'Yds', 'Y/A', 'NY/A',
#     'Cmp%', 'Rate', 'Att', 'Yds', 'Y/A', 'TD', 'FGM', 'FGA', 'XPM', 'XPA', 'Pnt', 'Yds', '3DConv', '3DAtt', '4DConv', '4DAtt', 'ToP', 'Team_Name'
# ]
opponent_game_logs_headers = [
    'week_num', 'game_day_of_week', 'game_date', 'boxscore_word', 'game_outcome', 'overtime',
    'game_location', 'opp', 'pts_off', 'pts_def', 'pass_cmp', 'pass_att', 'pass_yds', 'pass_td',
    'pass_int', 'pass_sacked', 'pass_sacked_yds', 'pass_yds_per_att', 'pass_net_yds_per_att',
    'pass_cmp_perc', 'pass_rating', 'rush_att', 'rush_yds', 'rush_yds_per_att', 'rush_td',
    'fgm', 'fga', 'xpm', 'xpa', 'punt', 'punt_yds', 'third_down_success', 'third_down_att',
    'fourth_down_success', 'fourth_down_att', 'time_of_poss', 'Team_Name'
]

# Loop through the years
# for year in range(2015, 2025):
for year in range(2024, 2025):
    all_team_game_logs = []  # Create empty lists to accumulate team and opponent data for each year
    all_opponent_game_logs = []

    for team in teams:
        abbreviation, name = team
        print(f'Processing {name} for the year {year}')  # Include the year in the print statement
        url = f'https://www.pro-football-reference.com/teams/{abbreviation}/{year}/gamelog/'
        response = requests.get(url)

        if response.status_code != 200:
            print(f'Failed to retrieve page {url} for {name} in {year}: {response.status_code}')
            continue

        soup = BeautifulSoup(response.content, 'html.parser')

        for table_id in [f'gamelog{year}', f'gamelog_opp{year}']:
            table = soup.find('table', {'id': table_id})

            if table is None:
                print(f'Table with id {table_id} not found on page {url} for {name} in {year}')
                continue

            tbody = table.find('tbody')
            game_logs = []
            for tr in tbody.find_all('tr'):
                row_data = []  # Start with an empty list
                for td in tr.find_all(['th', 'td']):  # Include <th> elements as well
                    row_data.append(td.text)
                if table_id == f'gamelog{year}':
                    row_data.append(name)  # Append team name as the last column for team game logs
                    game_logs.append(row_data)
                elif table_id == f'gamelog_opp{year}':
                    row_data.append(name)  # Append team name as the last column for opponent game logs
                    all_opponent_game_logs.append(row_data)

            if table_id == f'gamelog{year}':
                all_team_game_logs.extend(game_logs)

            # Check if playoff game logs exist for this team and year
            playoff_table_id = f'playoff_gamelog{year}'
            playoff_table = soup.find('table', {'id': playoff_table_id})

            if playoff_table:
                playoff_tbody = playoff_table.find('tbody')
                playoff_game_logs = []
                for tr in playoff_tbody.find_all('tr'):
                    row_data = []  # Start with an empty list
                    for td in tr.find_all(['th', 'td']):  # Include <th> elements as well
                        row_data.append(td.text)
                    row_data.append(name)  # Append team name as the last column for playoff game logs
                    playoff_game_logs.append(row_data)

                all_team_game_logs.extend(playoff_game_logs)

            sleep(2.5)  # Sleep for 3 seconds after processing each team

    # Save the accumulated team and opponent data to CSV files, named based on the year
    with open(f'./data/SR-game-logs/all_teams_game_logs_{year}.csv', mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(team_game_logs_headers)
        writer.writerows(all_team_game_logs)

    with open(f'./data/SR-opponent-game-logs/all_teams_opponent_game_logs_{year}.csv', mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(opponent_game_logs_headers)
        writer.writerows(all_opponent_game_logs)







# Create game_id in game logs

directory = 'data/SR-game-logs/'

# List to store DataFrames
df_list = []

# Iterate over all files in the directory
for filename in os.listdir(directory):
    if filename.endswith(".csv"):  # Ensure we are processing only CSV files
        file_path = os.path.join(directory, filename)
        
        # Extract the season from the filename, assuming the format: all_teams_opponent_game_logs_YYYY.csv
        season = filename.split('_')[-1].replace('.csv', '')
        
        # Load the CSV file
        df = pd.read_csv(file_path)
        
        # Add the season column
        df['season'] = season
        
        # Append the DataFrame to the list
        df_list.append(df)

# Combine all DataFrames into one
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
    'St. Louis Rams': 'STL',
    'San Diego Chargers': 'LAC'
}

# Function to determine home and away teams
def determine_home_away(row):
    if row['game_location'] == '@':
        away_team = team_abbreviation_map[row['Team_Name']]
        home_team = team_abbreviation_map[row['opp']]
    else:
        home_team = team_abbreviation_map[row['Team_Name']]
        away_team = team_abbreviation_map[row['opp']]
    return pd.Series([home_team, away_team])
df[['home_team_id', 'away_team_id']] = df.apply(determine_home_away, axis=1)
# df['home_team'] = df.apply(lambda row: team_abbreviation_map[row['Opp']] if row['Unnamed: 6'] == '@' else team_abbreviation_map[row['Team_Name']], axis=1)
# df['away_team'] = df.apply(lambda row: team_abbreviation_map[row['Team_Name']] if row['Unnamed: 6'] == '@' else team_abbreviation_map[row['Opp']], axis=1)

# Ensure 'week_num' is a string and pad single digits with a leading zero
df['week_num'] = df['week_num'].astype(str).str.zfill(2)

# Create the 'game_id' column by combining 'season', 'week_num', 'away_team', and 'home_team'
df['game_id'] = df['season'] + '_' + df['week_num'] + '_' + df['away_team_id'] + '_' + df['home_team_id']

# Save the updated combined DataFrame to a new CSV file
output_file_path_with_teams = 'data/all_team_game_logs.csv'
df.to_csv(output_file_path_with_teams, index=False)
print(f"Updated file with home and away teams saved to: {output_file_path_with_teams}")




# Aggregate all_game_logs.csv to single row per game

df = pd.read_csv('data/all_team_game_logs.csv')

# Grouping the data by game_id and aggregating the stats separately for home and away teams
grouped_df = df.groupby('game_id', group_keys=False).apply(lambda x: pd.Series({
    'home_pts_off': x.loc[x['game_location'] == 'N', 'pts_off'].sum() or x.loc[x['game_location'] == '', 'pts_off'].sum(),
    'away_pts_off': x.loc[x['game_location'] == '@', 'pts_off'].sum(),
    'home_pass_cmp': x.loc[x['game_location'] == 'N', 'pass_cmp'].sum() or x.loc[x['game_location'] == '', 'pass_cmp'].sum(),
    'away_pass_cmp': x.loc[x['game_location'] == '@', 'pass_cmp'].sum(),
    'home_pass_att': x.loc[x['game_location'] == 'N', 'pass_att'].sum() or x.loc[x['game_location'] == '', 'pass_att'].sum(),
    'away_pass_att': x.loc[x['game_location'] == '@', 'pass_att'].sum(),
    'home_pass_yds': x.loc[x['game_location'] == 'N', 'pass_yds'].sum() or x.loc[x['game_location'] == '', 'pass_yds'].sum(),
    'away_pass_yds': x.loc[x['game_location'] == '@', 'pass_yds'].sum(),
    'home_pass_td': x.loc[x['game_location'] == 'N', 'pass_td'].sum() or x.loc[x['game_location'] == '', 'pass_td'].sum(),
    'away_pass_td': x.loc[x['game_location'] == '@', 'pass_td'].sum(),
    'home_pass_int': x.loc[x['game_location'] == 'N', 'pass_int'].sum() or x.loc[x['game_location'] == '', 'pass_int'].sum(),
    'away_pass_int': x.loc[x['game_location'] == '@', 'pass_int'].sum(),
    'home_pass_sacked': x.loc[x['game_location'] == 'N', 'pass_sacked'].sum() or x.loc[x['game_location'] == '', 'pass_sacked'].sum(),
    'away_pass_sacked': x.loc[x['game_location'] == '@', 'pass_sacked'].sum(),
    'home_pass_yds_per_att': x.loc[x['game_location'] == 'N', 'pass_yds_per_att'].mean() or x.loc[x['game_location'] == '', 'pass_yds_per_att'].mean(),
    'away_pass_yds_per_att': x.loc[x['game_location'] == '@', 'pass_yds_per_att'].mean(),
    'home_pass_net_yds_per_att': x.loc[x['game_location'] == 'N', 'pass_net_yds_per_att'].mean() or x.loc[x['game_location'] == '', 'pass_net_yds_per_att'].mean(),
    'away_pass_net_yds_per_att': x.loc[x['game_location'] == '@', 'pass_net_yds_per_att'].mean(),
    'home_pass_cmp_perc': x.loc[x['game_location'] == 'N', 'pass_cmp_perc'].mean() or x.loc[x['game_location'] == '', 'pass_cmp_perc'].mean(),
    'away_pass_cmp_perc': x.loc[x['game_location'] == '@', 'pass_cmp_perc'].mean(),
    'home_pass_rating': x.loc[x['game_location'] == 'N', 'pass_rating'].mean() or x.loc[x['game_location'] == '', 'pass_rating'].mean(),
    'away_pass_rating': x.loc[x['game_location'] == '@', 'pass_rating'].mean(),
    'home_rush_att': x.loc[x['game_location'] == 'N', 'rush_att'].sum() or x.loc[x['game_location'] == '', 'rush_att'].sum(),
    'away_rush_att': x.loc[x['game_location'] == '@', 'rush_att'].sum(),
    'home_rush_yds': x.loc[x['game_location'] == 'N', 'rush_yds'].sum() or x.loc[x['game_location'] == '', 'rush_yds'].sum(),
    'away_rush_yds': x.loc[x['game_location'] == '@', 'rush_yds'].sum(),
    'home_rush_yds_per_att': x.loc[x['game_location'] == 'N', 'rush_yds_per_att'].mean() or x.loc[x['game_location'] == '', 'rush_yds_per_att'].mean(),
    'away_rush_yds_per_att': x.loc[x['game_location'] == '@', 'rush_yds_per_att'].mean(),
    'home_rush_td': x.loc[x['game_location'] == 'N', 'rush_td'].sum() or x.loc[x['game_location'] == '', 'rush_td'].sum(),
    'away_rush_td': x.loc[x['game_location'] == '@', 'rush_td'].sum(),
}))

# Save the result to a CSV file if needed
grouped_df.to_csv('data/all_team_game_logs.csv', index=True)


# Team Stats and Rankings
# Not in nfl.db currently

import os
import requests
from bs4 import BeautifulSoup
import csv
from time import sleep

# Create directories if they don't exist
data_dir = './data/SR-team-stats'
os.makedirs(data_dir, exist_ok=True)

# List of teams and abbreviations
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

# Define headers for team stats CSV
team_stats_headers = [
    'Player', 'PF', 'Yds', 'Ply', 'Y/P', 'TO', 'FL', '1stD', 'Cmp', 'Att', 'Yds', 'TD', 'Int', 'NY/A',
    '1stD', 'Att', 'Yds', 'TD', 'Y/A', '1stD', 'Pen', 'Yds', '1stPy', '#Dr', 'Sc%', 'TO%', 'Start', 'Time', 'Plays', 'Yds', 'Pts', 'Team'
]

# Loop through the years
# for year in range(2015, 2025):
for year in range(2024, 2025):
    all_team_stats = []  # Create empty list to accumulate team stats data for each year

    for team in teams:
        abbreviation, name = team
        print(f'Processing {name} for the year {year}')  # Include the year in the print statement
        url = f'https://www.pro-football-reference.com/teams/{abbreviation}/{year}.htm'
        response = requests.get(url)

        if response.status_code != 200:
            print(f'Failed to retrieve page {url} for {name} in {year}: {response.status_code}')
            continue

        soup = BeautifulSoup(response.content, 'html.parser')

        # Find the main table for team stats (e.g., "team_stats" table)
        table = soup.find('table', {'id': 'team_stats'})
        
        if table is None:
            print(f'Team stats table not found on page {url} for {name} in {year}')
            continue

        tbody = table.find('tbody')
        for tr in tbody.find_all('tr'):
            row_data = [tr.find('th').text.strip()]  # Start with the 'Player' column data
            row_data.extend([td.text.strip() for td in tr.find_all('td')])  # Add the rest of the row data
            row_data.append(abbreviation)  # Append team abbreviation as the last column
            all_team_stats.append(row_data)

        sleep(2.5)  # Sleep for 2.5 seconds after processing each team

    # Save the accumulated team stats data to a CSV file, named based on the year
    with open(f'{data_dir}/all_teams_stats_{year}.csv', mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(team_stats_headers)
        writer.writerows(all_team_stats)

    print(f'Saved data for all teams for the year {year}')




# Schedule & Game Results 
# Not in nfl.db currently

# Create directories if they don't exist
data_dir = './data/SR-schedule-and-game-results'
os.makedirs(data_dir, exist_ok=True)

# List of teams and abbreviations
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

# Updated headers for the schedule and game results CSV
schedule_headers = [
    'Week', 'Day', 'Date', 'Time', 'Boxscore', 'Outcome', 'OT', 'Rec', 'Home/Away', 'Opp', 
    'Tm', 'OppPts', '1stD', 'TotYd', 'PassY', 'RushY', 'TO_lost', 
    'Opp1stD', 'OppTotYd', 'OppPassY', 'OppRushY', 'TO_won',
    'Offense', 'Defense', 'Sp. Tms'
]

# Loop through the years
# for year in range(2015, 2025):
for year in range(2024, 2025):
    all_games = []  # Create an empty list to accumulate game data for each year

    for team in teams:
        abbreviation, name = team
        print(f'Processing {name} for the year {year}')  # Include the year in the print statement
        url = f'https://www.pro-football-reference.com/teams/{abbreviation}/{year}.htm'
        response = requests.get(url)

        if response.status_code != 200:
            print(f'Failed to retrieve page {url} for {name} in {year}: {response.status_code}')
            continue

        soup = BeautifulSoup(response.content, 'html.parser')

        # Find the "Schedule & Game Results" table
        table = soup.find('table', {'id': 'games'})
        if table is None:
            print(f'Schedule & Game Results table not found on page {url} for {name} in {year}')
            continue

        tbody = table.find('tbody')
        team_games = []  # Store game data for this team

        for tr in tbody.find_all('tr'):
            # Initialize the row with the Week number
            row_data = []
            week_th = tr.find('th', {'data-stat': 'week_num'})
            week_num = week_th.text.strip() if week_th else ''
            row_data.append(week_num)

            # Add the rest of the data from 'td' elements
            for td in tr.find_all('td'):
                row_data.append(td.text.strip())

            # Ensure row_data matches the number of headers
            if len(row_data) != len(schedule_headers):
                row_data += [''] * (len(schedule_headers) - len(row_data))

            team_games.append(row_data)
            all_games.append(row_data)  # Also add to the all_games list

        # Save the team's data to its own CSV file
        team_file_path = f'{data_dir}/{abbreviation}_{year}_schedule_and_game_results.csv'
        with open(team_file_path, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(schedule_headers)
            writer.writerows(team_games)

        print(f'Saved schedule data for {name} for the year {year}')
        sleep(2.5)  # Sleep for 2.5 seconds after processing each team

# Merge all years and teams into all_teams_schedule_and_game_results_merged.csv
data_dir = './data/SR-schedule-and-game-results'

# List to hold all data from the files
all_games = []

# Iterate over all files in the directory
for filename in os.listdir(data_dir):
    if filename.endswith("_schedule_and_game_results.csv"):
        # Extract the team abbreviation and year from the filename
        team_abbr = filename.split('_')[0]
        season_year = filename.split('_')[1]
        
        # Construct the full path to the file
        file_path = os.path.join(data_dir, filename)
        
        # Read the CSV file into a DataFrame
        df = pd.read_csv(file_path)
        
        # Add new columns for the team abbreviation and season year
        df['Team'] = team_abbr
        df['Season'] = season_year
        
        # Append the DataFrame to the list of all games
        all_games.append(df)

# Concatenate all the DataFrames into a single DataFrame
merged_df = pd.concat(all_games, ignore_index=True)

# Save the merged DataFrame to a new CSV file
merged_output_path = os.path.join(data_dir, 'all_teams_schedule_and_game_results_merged.csv')
merged_df.to_csv(merged_output_path, index=False)

print(f"Successfully merged all team files into {merged_output_path}")

# # Standardize the Team column abbreviations
# team_abbreviation_mapping = {
#     'gnb': 'gb',
#     'htx': 'hou',
#     'clt': 'ind',
#     'kan': 'kc',
#     'sdg': 'lac',
#     'ram': 'lar',
#     'rai': 'lvr',
#     'nwe': 'ne',
#     'nor': 'no',
#     'sfo': 'sf',
#     'tam': 'tb',
#     'oti': 'ten',
#     'rav': 'bal',
#     'crd': 'ari'
# }

# Team Conversions 
# Not in nfl.db currently

# Create directories if they don't exist
data_dir = './data/SR-team-conversions'
os.makedirs(data_dir, exist_ok=True)

# List of teams and abbreviations
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

# Define headers for the team conversions CSV
team_conversions_headers = [
    'Player', '3DAtt', '3DConv', '3D%', '4DAtt', '4DConv', '4D%', 'RZAtt', 'RZTD', 'RZPct', 'Team'
]

# Loop through the years
# for year in range(2015, 2025):
for year in range(2024, 2025):
    for team in teams:
        abbreviation, name = team
        print(f'Processing {name} for the year {year}')  # Include the year in the print statement
        url = f'https://www.pro-football-reference.com/teams/{abbreviation}/{year}.htm'
        response = requests.get(url)

        if response.status_code != 200:
            print(f'Failed to retrieve page {url} for {name} in {year}: {response.status_code}')
            continue

        soup = BeautifulSoup(response.content, 'html.parser')

        # Find the "Team Conversions" table (e.g., "team_conversions" table)
        table = soup.find('table', {'id': 'team_conversions'})

        if table is None:
            print(f'Team Conversions table not found on page {url} for {name} in {year}')
            continue

        all_conversions = []
        tbody = table.find('tbody')
        for tr in tbody.find_all('tr'):
            row_data = [td.text.strip() for td in tr.find_all(['th', 'td'])]  # Extract row data including headers
            row_data.append(abbreviation)  # Append team abbreviation at the end
            all_conversions.append(row_data)

        # Save the conversion data for this team to a separate CSV file
        team_file = f'{data_dir}/{abbreviation}_{year}_team_conversions.csv'
        with open(team_file, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(team_conversions_headers)
            writer.writerows(all_conversions)

        print(f'Saved team conversions data for {name} for the year {year} to {team_file}')
        
        sleep(2.5)  # Sleep for 2.5 seconds after processing each team


# --- Creating home_spread and away_spread columns in nfl.db --- #
# Adjusting to also make team_favorite

# Function to calculate home_spread, away_spread, team_favorite, and team_covered
def calculate_spreads_and_favorite(spread_line, home_team, away_team, home_score, away_score):
    if spread_line is None or home_score is None or away_score is None:
        # Handle cases where spread_line or scores are missing
        return "N/A", "N/A", "N/A", "N/A"

    # Ensure spread_line is a float for arithmetic operations
    spread_line = float(spread_line)
    abs_spread = abs(spread_line)  # Use absolute value of the spread for comparisons

    if spread_line > 0:
        # Home team is favored
        home_spread = f"-{spread_line}"  # Home team is the favorite
        away_spread = f"+{spread_line}"  # Away team is the underdog
        team_favorite = home_team
        # Determine which team covered the spread
        if home_score > away_score + abs_spread:
            team_covered = home_team
        elif away_score > home_score - abs_spread:
            team_covered = away_team
        else:
            team_covered = "Push"
    else:
        # Away team is favored
        home_spread = f"+{-spread_line}"  # Home team is the underdog
        away_spread = f"-{-spread_line}"  # Away team is the favorite
        team_favorite = away_team
        # Determine which team covered the spread
        if away_score > home_score + abs_spread:
            team_covered = away_team
        elif home_score > away_score - abs_spread:
            team_covered = home_team
        else:
            team_covered = "Push"

    return home_spread, away_spread, team_favorite, team_covered

# Connect to the SQLite database
db_path = 'nfl.db'  # Update the path if needed
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Add new columns to the 'Games' table (if they don't already exist)
try:
    cursor.execute("ALTER TABLE Games ADD COLUMN home_spread TEXT;")
except sqlite3.OperationalError:
    pass  # Column already exists

try:
    cursor.execute("ALTER TABLE Games ADD COLUMN away_spread TEXT;")
except sqlite3.OperationalError:
    pass  # Column already exists

try:
    cursor.execute("ALTER TABLE Games ADD COLUMN team_favorite TEXT;")
except sqlite3.OperationalError:
    pass  # Column already exists

try:
    cursor.execute("ALTER TABLE Games ADD COLUMN team_covered TEXT;")
except sqlite3.OperationalError:
    pass  # Column already exists

# Update each row in the 'Games' table with home_spread, away_spread, team_favorite, and team_covered
cursor.execute("SELECT game_id, spread_line, home_team, away_team, home_score, away_score FROM Games;")
games = cursor.fetchall()

for game in games:
    game_id, spread_line, home_team, away_team, home_score, away_score = game
    home_spread, away_spread, team_favorite, team_covered = calculate_spreads_and_favorite(spread_line, home_team, away_team, home_score, away_score)
    update_query = "UPDATE Games SET home_spread = ?, away_spread = ?, team_favorite = ?, team_covered = ? WHERE game_id = ?;"
    cursor.execute(update_query, (home_spread, away_spread, team_favorite, team_covered, game_id))

# Commit the changes and close the connection
conn.commit()
conn.close()

print("Columns 'home_spread', 'away_spread', 'team_favorite', and 'team_covered' have been added and updated for all rows in the 'Games' table.")




# Passing/Rushing/Receiving (from boxscore pages)
# For longest reception
# Not in nfl.db currently

import requests
from bs4 import BeautifulSoup
import csv
import os
import time

# !mkdir data/passing-rushing-receiving-game-logs/

# Passing, Rushing, and Receiving Game Logs
# for year_to_scrape in range(2015, 2025):
for year_to_scrape in range(2024, 2025):
    # Initialize output CSV file with the year in its name
    output_filename = f'./data/passing-rushing-receiving-game-logs/all_passing_rushing_receiving_{year_to_scrape}.csv'
    with open(output_filename, 'w', newline='') as output_csvfile:
        csvwriter = csv.writer(output_csvfile)
        csvwriter.writerow([
            'player', 'team', 'pass_cmp', 'pass_att', 'pass_yds', 'pass_td', 'pass_int', 'pass_sacked', 
            'pass_sacked_yds', 'pass_long', 'pass_rating', 'rush_att', 'rush_yds', 'rush_td', 'rush_long', 
            'targets', 'rec', 'rec_yds', 'rec_td', 'rec_long', 'fumbles', 'fumbles_lost', 'game_id'
        ])  # Added 'game_id' to the header row

        # Read the CSV file containing the game data
        with open('./data/games.csv', 'r') as csvfile:
            reader = csv.DictReader(csvfile)
            rows = [row for row in reader if int(row['game_id'].split('_')[0]) == year_to_scrape]  # Filter rows for the year

            for row in rows:
                pfr_value = row['pfr']
                game_id = row['game_id']

                # Form the URL using the 'pfr' value
                url = f"https://www.pro-football-reference.com/boxscores/{pfr_value}.htm"

                try:
                    # Fetch the webpage
                    response = requests.get(url)

                    # Check if we are being rate limited (status code 429)
                    if response.status_code == 429:
                        print(f"Rate limit exceeded for URL {url}. Please try again later.")
                        time.sleep(60)  # Sleep for 60 seconds before retrying
                        continue

                    soup = BeautifulSoup(response.text, 'html.parser')

                    # Find the table containing player stats
                    table = soup.find('div', id='div_player_offense')
                    if table:
                        # Loop through the rows to get the player stats
                        for i, tr in enumerate(table.find_all('tr')):
                            if i == 0:  # Skip the first header row
                                continue
                            player_name = tr.find('th').get_text() if tr.find('th') else ''
                            stats = [td.get_text() for td in tr.find_all('td')]
                            row_data = [player_name] + stats + [game_id]  # Append game_id to the end of the row
                            csvwriter.writerow(row_data)

                    print(f"Successfully scraped data for game ID: {game_id}, PFR: {pfr_value}")

                except Exception as e:
                    print(f"An error occurred while scraping {url}. Error: {e}")

                # Sleep for 2 seconds to avoid overloading the server
                time.sleep(2)

    print(f"Scraping completed for {year_to_scrape}. Data saved to {output_filename}.")



# Clean weird rows ^

import pandas as pd
import os

# Directory path
directory = 'data/passing-rushing-receiving-game-logs/'

# Iterate through all files in the directory
for filename in os.listdir(directory):
    if filename.endswith('.csv'):
        file_path = os.path.join(directory, filename)

        # Load the CSV file into a DataFrame
        df = pd.read_csv(file_path)

        # Remove rows where the 'player' column is "Player" or NaN (missing)
        df_cleaned = df[(df['player'] != 'Player') & (df['player'].notna())]

        # Save the cleaned DataFrame back to the same CSV file
        df_cleaned.to_csv(file_path, index=False)

        print(f"Processed {filename}")



# Merge all ^

import pandas as pd
import os

# Directory path
directory = 'data/passing-rushing-receiving-game-logs/'
merged_file_path = 'data/all_passing_rushing_receiving.csv'  # Path where the merged file will be saved

# List to hold all DataFrames
dataframes = []

# Iterate through all files in the directory
for filename in os.listdir(directory):
    if filename.endswith('.csv'):
        file_path = os.path.join(directory, filename)
        
        # Load the CSV file into a DataFrame
        df = pd.read_csv(file_path)
        
        # Append the DataFrame to the list
        dataframes.append(df)
        
        print(f"Added {filename} to the merge list")

# Concatenate all DataFrames in the list into one large DataFrame
merged_df = pd.concat(dataframes, ignore_index=True)

# Save the merged DataFrame to a new CSV file
merged_df.to_csv(merged_file_path, index=False)

print(f"All files have been merged into {merged_file_path}")



# Add opponent_team column ^

file_path = 'data/all_passing_rushing_receiving.csv'  # Replace with your actual file path
df = pd.read_csv(file_path)

# Dictionary to map incorrect team codes to the correct ones
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

# Apply the corrections to the 'team' column
df['team'] = df['team'].replace(team_corrections)

# Function to extract the opponent team from the game_id column
def get_opponent_team(row):
    game_id = row['game_id']
    team = row['team']
    
    # Split the game_id to extract the away and home teams
    _, _, away_team, home_team = game_id.split('_')
    
    # Determine the opponent based on whether the player's team is the home or away team
    if team == home_team:
        return away_team
    elif team == away_team:
        return home_team
    else:
        return None  # In case the team does not match either home or away (shouldn't happen)

# Function to determine if the player was at home or away
def is_player_home(row):
    game_id = row['game_id']
    team = row['team']
    
    # Split the game_id to extract the away and home teams
    _, _, away_team, home_team = game_id.split('_')
    
    # Check if the player's team is the home team
    return 'y' if team == home_team else 'n'

# Apply the functions to create new columns 'opponent_team' and 'home'
df['opponent_team'] = df.apply(get_opponent_team, axis=1)
df['home'] = df.apply(is_player_home, axis=1)

# Save the updated dataframe to the same CSV file
df.to_csv('data/all_passing_rushing_receiving.csv', index=False)  # Save the result

# Optionally display the first few rows to verify the changes
print(df.head())
# !open data/all_passing_rushing_receiving.csv

# Add position column ^

# Load the CSV files
all_passing_file = 'data/all_passing_rushing_receiving.csv'
rosters_file = 'data/Rosters.csv'

all_passing_df = pd.read_csv(all_passing_file)
rosters_df = pd.read_csv(rosters_file)

# Merge the two dataframes on player names
merged_df = pd.merge(all_passing_df, rosters_df[['full_name', 'position']], 
                     left_on='player', right_on='full_name', how='left')

# Ensure the 'position' column exists even if no matches are found
if 'position' not in merged_df.columns:
    merged_df['position'] = None

# Filter only relevant positions (QB, WR, TE, RB)
relevant_positions = ['QB', 'WR', 'TE', 'RB']
merged_df['position'] = merged_df['position'].where(merged_df['position'].isin(relevant_positions), None)

# Drop the full_name column that was added during the merge
merged_df.drop(columns=['full_name'], inplace=True)

# Ensure all rows for a player have the same position
merged_df['position'] = merged_df.groupby('player')['position'].transform(lambda x: x.ffill().bfill())

# Save the updated dataframe to a new CSV file
merged_df.to_csv('data/all_passing_rushing_receiving.csv', index=False)

# Optionally display the updated dataframe
print(merged_df[['player', 'position']].head())


# # # # Defense (from boxscore pages)
# # # # For sacks/defensive INT
# # # # Not in nfl.db currently
# Create the directory for defense game logs
os.makedirs('data/defense-game-logs', exist_ok=True)

# Headers for the defense stats, including 'game_id'
headers = [
    'player', 'team', 'def_int', 'def_int_yds', 'def_int_td', 'def_int_long', 'pass_defended', 'sacks',
    'tackles_combined', 'tackles_solo', 'tackles_assists', 'tackles_loss', 'qb_hits', 'fumbles_rec',
    'fumbles_rec_yds', 'fumbles_rec_td', 'fumbles_forced', 'game_id'
]

# Defensive Game Logs
for year_to_scrape in range(2024, 2025):
    output_filename = f'./data/defense-game-logs/all_defense_{year_to_scrape}.csv'
    with open(output_filename, 'w', newline='') as output_csvfile:
        csvwriter = csv.writer(output_csvfile)
        csvwriter.writerow(headers)

        with open('./data/games.csv', 'r') as csvfile:
            reader = csv.DictReader(csvfile)
            rows = [row for row in reader if int(row['game_id'].split('_')[0]) == year_to_scrape]

            for row in rows:
                # Check if 'away_score' and 'home_score' are both present
                if not row['away_score'] or not row['home_score']:
                    print(f"Skipping game {row['game_id']} due to missing scores.")
                    continue  # Skip this game if scores are missing
                
                pfr_value = row['pfr']
                game_id = row['game_id']
                url = f"https://www.pro-football-reference.com/boxscores/{pfr_value}.htm"

                try:
                    response = requests.get(url)

                    if response.status_code == 429:
                        print(f"Rate limit exceeded for URL {url}. Please try again later.")
                        time.sleep(3)
                        continue

                    soup = BeautifulSoup(response.text, 'html.parser')

                    comments = soup.find_all(string=lambda text: isinstance(text, Comment))

                    for comment in comments:
                        soup_comment = BeautifulSoup(comment, 'html.parser')
                        table = soup_comment.find('table', id='player_defense')
                        if table:
                            for i, tr in enumerate(table.find_all('tr')):
                                if i == 0:
                                    continue
                                player_name = tr.find('th').get_text() if tr.find('th') else ''
                                stats = [td.get_text() for td in tr.find_all('td')]
                                row_data = [player_name] + stats + [game_id]
                                csvwriter.writerow(row_data)
                            print(f"Successfully scraped data for game ID: {game_id}, PFR: {pfr_value}")
                            break

                except Exception as e:
                    print(f"An error occurred while scraping {url}. Error: {e}")

                time.sleep(2)

    print(f"Scraping completed for {year_to_scrape}. Data saved to {output_filename}.")

import pandas as pd

# Load the CSV file into a DataFrame
df = pd.read_csv('./data/defense-game-logs/all_defense_2024.csv')

# Drop rows with any missing data
df.dropna(inplace=True)

# Write the cleaned DataFrame back to the CSV file
df.to_csv('./data/defense-game-logs/all_defense_2024.csv', index=False)