import sqlite3
import pandas as pd
import os
import shutil
import requests
import re
# os.remove('nfl.db')
shutil.rmtree('data', ignore_errors=True)
shutil.copytree('/Users/td/Code/nfl-ai/Scrapers/data', 'data')
shutil.copy('/Users/td/Code/nfl-ai/Scrapers/nfl.db', 'data')
# shutil.copy('/Users/td/Code/nfl-ai/Scrapers/data/SR-schedule-and-game-results/all_teams_schedule_and_game_results_merged.csv', 'data')

### Remove all files except for 2023 and 2024 and merged files
# data_directory = 'data'
# for root, dirs, files in os.walk(data_directory):
#     for filename in files:
#         if filename.endswith('.csv'):
#             if '2023' not in filename and '2024' not in filename:
#                 file_path = os.path.join(root, filename)
#                 os.remove(file_path)
#                 print(f"Removed: {file_path}")

# data_directory = 'data'
# years_to_keep = [str(year) for year in range(2020, 2025)]  # Creates a list of years from 2015 to 2024
# for root, dirs, files in os.walk(data_directory):
#     for filename in files:
#         if filename.endswith('.csv'):
#             # if not any(year in filename for year in years_to_keep) and 'merged' not in filename:
#             if not any(year in filename for year in years_to_keep) or 'merged' in filename:
#                 file_path = os.path.join(root, filename)
#                 os.remove(file_path)
#                 print(f"Removed: {file_path}")

data_directory = 'data'
years_to_keep = [str(year) for year in range(2020, 2026)]  # Creates a list of years from 2020 to 2025
for root, dirs, files in os.walk(data_directory):
    if root == data_directory:
        continue
    for filename in files:
        if filename.endswith('.csv'):
            # Check if the filename does not contain any of the years to keep
            if not any(year in filename for year in years_to_keep):
                file_path = os.path.join(root, filename)
                os.remove(file_path)
                print(f"Removed: {file_path}")                


### Retrieve Next Week's Games ###
db_path = 'data/nfl.db'
conn = sqlite3.connect(db_path)
current_week_query = """
    SELECT MAX(CAST(week AS INTEGER)) as current_week
    FROM Games
    WHERE season = 2024 AND home_score IS NOT NULL AND away_score IS NOT NULL
"""
current_week_df = pd.read_sql(current_week_query, conn)
current_week = current_week_df.iloc[0]['current_week']
if pd.isnull(current_week):
    current_week = 0
next_week_query = f"""
    SELECT *
    FROM Games
    WHERE season = 2024 AND CAST(week AS INTEGER) = {current_week + 1} AND home_score IS NULL AND away_score IS NULL
"""
next_week_games_df = pd.read_sql(next_week_query, conn)
output_dir = 'data/'
os.makedirs(output_dir, exist_ok=True)
if next_week_games_df.empty:
    print(f"No games found for Week {current_week + 1}.")
else:
    upcoming_games_path = os.path.join(output_dir, 'UpcomingGames.csv')
    next_week_games_df.to_csv(upcoming_games_path, index=False)
    print(f"Next week's games (Week {current_week + 1}) saved to {upcoming_games_path}.")
conn.close()

### Team Logos Download ###
shutil.rmtree('images/team-logos', ignore_errors=True)
save_dir = "images/team-logos"
os.makedirs(save_dir, exist_ok=True)
teams = {
    'crd': 'ARI', 'atl': 'ATL', 'rav': 'BAL', 'buf': 'BUF', 'car': 'CAR',
    'chi': 'CHI', 'cin': 'CIN', 'cle': 'CLE', 'dal': 'DAL', 'den': 'DEN',
    'det': 'DET', 'gnb': 'GB', 'htx': 'HOU', 'clt': 'IND', 'jax': 'JAX',
    'kan': 'KC', 'sdg': 'LAC', 'ram': 'LAR', 'rai': 'LVR', 'mia': 'MIA',
    'min': 'MIN', 'nwe': 'NE', 'nor': 'NO', 'nyg': 'NYG', 'nyj': 'NYJ',
    'phi': 'PHI', 'pit': 'PIT', 'sea': 'SEA', 'sfo': 'SF', 'tam': 'TB',
    'oti': 'TEN', 'was': 'WAS'
}
base_url = "https://cdn.ssref.net/req/202409272/tlogo/pfr/"
def download_image(team_code, team_name):
    url = f"{base_url}{team_code}.png"
    response = requests.get(url)
    if response.status_code == 200:
        with open(os.path.join(save_dir, f"{team_name}.png"), 'wb') as f:
            f.write(response.content)
        print(f"Downloaded: {team_name}.png")
    else:
        print(f"Failed to download: {team_name}.png")
for team_code, team_name in teams.items():
    download_image(team_code, team_name)
print("All team logos downloaded successfully.")

### Player Headshots Download ###
df_player_stats = pd.read_csv('data/player_stats.csv')
unique_qbs_with_urls = df_player_stats[df_player_stats['headshot_url'].notna()] \
                        .drop_duplicates(subset=['player_display_name'])
image_folder = 'images/player-headshots'
os.makedirs(image_folder, exist_ok=True)

downloaded_count = 0
skipped_count = 0
total_qbs = len(unique_qbs_with_urls)

for index, row in unique_qbs_with_urls.iterrows():
    player_name = row['player_display_name'].lower().replace(' ', '_')
    headshot_url = row['headshot_url']
    image_path = os.path.join(image_folder, f"{player_name}.png")
    
    # Skip if image already exists
    if os.path.exists(image_path):
        skipped_count += 1
        continue
        
    try:
        response = requests.get(headshot_url)
        if response.status_code == 200:
            with open(image_path, 'wb') as file:
                file.write(response.content)
            downloaded_count += 1
            print(f"Downloaded {player_name}'s headshot ({downloaded_count} new, {skipped_count} existing).")
        else:
            print(f"Failed to download {player_name}'s headshot (Status code: {response.status_code}).")
    except Exception as e:
        print(f"Error downloading {player_name}'s headshot: {e}")

print(f"Download complete: {downloaded_count} new images downloaded, {skipped_count} already existed.")


### Connect to the copied SQLite database and export tables to CSV ###
if os.path.exists('data/games.csv'): os.remove('data/games.csv')
if os.path.exists('data/player_stats.csv'): os.remove('data/player_stats.csv')
if os.path.exists('data/teams.csv'): os.remove('data/teams.csv')
if os.path.exists('data/rosters.csv'): os.remove('data/rosters.csv')
conn = sqlite3.connect('data/nfl.db')
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
for table_name_tuple in tables:
    table_name = table_name_tuple[0]
    df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
    output_file = os.path.join('data/', f"{table_name}.csv")
    df.to_csv(output_file, index=False)
    print(f"Table '{table_name}' saved to {output_file}")
conn.close()
print("All tables have been saved to CSV files.")

# os.rename('data/games.csv', 'data/Games.csv'); print("Renamed 'data/games.csv' to 'data/Games.csv'.")
# os.rename('data/teams.csv', 'data/Teams.csv'); print("Renamed 'data/teams.csv' to 'data/Teams.csv'.")
# os.rename('data/rosters.csv', 'data/Rosters.csv'); print("Renamed 'data/rosters.csv' to 'data/Rosters.csv'.")
# shutil.copy('data/player_stats.csv', 'data/PlayerStats.csv')
# shutil.copy('data/games.csv', 'data/Games.csv')
# shutil.copy('data/teams.csv', 'data/Teams.csv')
# shutil.copy('data/rosters.csv', 'data/Rosters.csv')

### Copy Odds Data ###
os.makedirs('data/odds/', exist_ok=True)
shutil.copy('/Users/td/Code/odds-monitoring/NFL/Analysis/data/nfl_odds_movements.csv', 'data/odds/')
shutil.copy('/Users/td/Code/odds-monitoring/NFL/Analysis/data/nfl_odds_movements_circa.csv', 'data/odds/')
shutil.copytree('/Users/td/Code/odds-monitoring/NFL/Analysis/data/odds/', 'data/odds/', dirs_exist_ok=True)
# for file in os.listdir('../../odds-monitoring/NFL/Analysis/data/odds/'):
#     shutil.copy(os.path.join('../../odds-monitoring/NFL/Analysis/data/odds/', file), 'data/odds/')



import pandas as pd
from datetime import datetime, timedelta
import os
import glob

print("\nExample format: 20241223 (for Dec 23, 2024)")
starter_date_default = '20241223'
current_date = datetime.now().strftime('%Y%m%d')
start_date = input(f"Enter start date (YYYYMMDD) [press Enter for {starter_date_default}]: ").strip()
if not start_date:
    start_date = starter_date_default
start_dt = datetime.strptime(start_date, '%Y%m%d')
default_end = (start_dt + timedelta(days=7)).strftime('%Y%m%d')
end_date = input(f"Enter end date (YYYYMMDD) [press Enter for {default_end}]: ").strip()
if not end_date:
    end_date = default_end
datetime.strptime(start_date, '%Y%m%d')
datetime.strptime(end_date, '%Y%m%d')
input_files = {
    'all': 'data/odds/nfl_odds_movements.csv',
    'circa': 'data/odds/nfl_odds_movements_circa.csv',
    # 'dk': 'data/odds/nfl_odds_movements_dk.csv'
}
for name, file_path in input_files.items():
    df = pd.read_csv(file_path)
    df['date'] = df['file1'].str.extract(r'(\d{8})')
    df = df[(df['date'] >= start_date) & (df['date'] <= end_date)]
    df = df.drop('date', axis=1)
    df.to_csv(file_path, index=False)
    print(f"Filtered {name} odds data saved to {file_path} ({len(df)} rows)")
cleanup = input("\nRemove raw odds files from data/odds/? (y/n) [press Enter for n]: ").lower().strip()
if cleanup == 'y':
    odds_files = glob.glob('data/odds/nfl_odds_vsin_*.json')
    odds_files = glob.glob('data/odds/nfl_odds_vsin_*.json')
    removed = 0
    for file in odds_files:
        file_date = file.split('_')[-2]  # Gets YYYYMMDD from filename
        if file_date < start_date or file_date > end_date:
            os.remove(file)
            removed += 1
    print(f"\nRemoved {removed} raw odds files outside the date range {start_date} to {end_date}") 



# # # import streamlit as st
# # # import pandas as pd
# # # import numpy as np
# # # import sqlite3
# # # import os

# # # # Use os.system to run a shell command to copy the file
# # # os.system('cp "../Scrapers/nfl.db" "."')

# # # ### Download data from nfl.db to csv files
# # # conn = sqlite3.connect('nfl.db')  # Replace 'your_database.db' with your database file path
# # # cursor = conn.cursor()

# # # for table_info in cursor.execute("SELECT name FROM sqlite_master WHERE type='table';"):
# # #     table_name = table_info[0]
# # #     df = pd.read_sql_query(f"SELECT * FROM {table_name};", conn)
    
# # #     # Save to the first directory
# # #     df.to_csv(f'data/{table_name}.csv', index=False)
    
# # #     # Save to the second directory
# # #     df.to_csv(f'Streamlit/data/{table_name}.csv', index=False)

# # # conn.close()

# # # os.remove("nfl.db")
# # import sqlite3
# # import os
# # import shutil
# # import pandas as pd

# # # Step 1: Save upcoming week's games to CSV

# # # Database path (you can modify this to point to your actual database)
# # db_path = '../Scrapers/nfl.db'

# # # Connect to the SQLite database
# # conn = sqlite3.connect(db_path)

# # # Query to get the current week (latest week where games have been played)
# # current_week_query = """
# #     SELECT MAX(CAST(week AS INTEGER)) as current_week
# #     FROM Games
# #     WHERE season = 2024 AND home_score IS NOT NULL AND away_score IS NOT NULL
# # """

# # # Execute the query to get the current week
# # current_week_df = pd.read_sql(current_week_query, conn)
# # current_week = current_week_df.iloc[0]['current_week']

# # # If no games have been played, default to week 1
# # if pd.isnull(current_week):
# #     current_week = 0

# # # Query to get the next week's games (where scores are NULL)
# # next_week_query = f"""
# #     SELECT *
# #     FROM Games
# #     WHERE season = 2024 AND CAST(week AS INTEGER) = {current_week + 1} AND home_score IS NULL AND away_score IS NULL
# # """

# # # Execute the query to load the next week's games into a DataFrame
# # next_week_games_df = pd.read_sql(next_week_query, conn)

# # # Step 2: Check if any games exist for the next week and save them to CSV
# # output_dir = './data'
# # os.makedirs(output_dir, exist_ok=True)  # Ensure the output directory exists

# # if next_week_games_df.empty:
# #     print(f"No games found for Week {current_week + 1}.")
# # else:
# #     # Export the DataFrame to a CSV file
# #     upcoming_games_path = os.path.join(output_dir, 'UpcomingGames.csv')
# #     next_week_games_df.to_csv(upcoming_games_path, index=False)
# #     print(f"Next week's games (Week {current_week + 1}) saved to {upcoming_games_path}.")

# #     # Query to delete all unplayed games (games where both home_score and away_score are NULL)
# #     delete_unplayed_games_query = """
# #         DELETE FROM Games
# #         WHERE season = 2024 AND home_score IS NULL AND away_score IS NULL
# #     """

# #     # Execute the deletion of unplayed games
# #     conn.execute(delete_unplayed_games_query)
# #     conn.commit()
# #     print(f"Unplayed games from season 2024 have been removed from the database.")

# # # Close the connection
# # conn.close()

# # # Step 3: Copy the database file to the current directory
# # source_db_path = db_path
# # destination_db_path = './nfl.db'

# # # Check if the source file exists
# # if os.path.exists(source_db_path):
# #     shutil.copy(source_db_path, destination_db_path)
# #     print(f"Database copied from {source_db_path} to {destination_db_path}")
# # else:
# #     print(f"Source database not found at {source_db_path}")
# #     exit(1)

# # # Step 4: Delete the 'data/' directory if it exists, then create a fresh one
# # if os.path.exists(output_dir):
# #     shutil.rmtree(output_dir)  # Deletes the directory and all its contents
# #     print(f"Deleted existing directory: {output_dir}")

# # os.makedirs(output_dir, exist_ok=True)  # Create the directory

# # # Step 5: Connect to the copied SQLite database and export tables to CSV
# # conn = sqlite3.connect(destination_db_path)
# # cursor = conn.cursor()

# # # Get all table names from the database
# # cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
# # tables = cursor.fetchall()

# # # Save all tables to CSV files in the data/ directory
# # for table_name_tuple in tables:
# #     table_name = table_name_tuple[0]
    
# #     # Load the table into a DataFrame
# #     df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
    
# #     # Save the DataFrame to a CSV file
# #     output_file = os.path.join(output_dir, f"{table_name}.csv")
# #     df.to_csv(output_file, index=False)
    
# #     print(f"Table '{table_name}' saved to {output_file}")

# # # Close the database connection
# # conn.close()
# # print("All tables have been saved to CSV files.")

# # os.system('cp "../Scrapers/nfl.db" "data/"')
# # os.system('cp "../Scrapers/nfl.db" "Streamlit/data/"')
# # os.system('cp "../Scrapers/data/SR-game-logs/all_teams_game_logs_2023.csv" "data/"')
# # os.system('cp "../Scrapers/data/SR-game-logs/all_teams_game_logs_2023.csv" "Streamlit/data/"')
# # os.system('cp "../Scrapers/data/SR-schedule-and-game-results/all_teams_schedule_and_game_results_merged.csv" "data/"')
# # os.system('cp "../Scrapers/data/SR-schedule-and-game-results/all_teams_schedule_and_game_results_merged.csv" "Streamlit/data/"')
# import sqlite3
# import os
# import shutil
# import pandas as pd

# # Step 1: Save upcoming week's games to CSV

# # Database path (you can modify this to point to your actual database)
# db_path = '../Scrapers/nfl.db'

# # Connect to the SQLite database
# conn = sqlite3.connect(db_path)

# # Query to get the current week (latest week where games have been played)
# current_week_query = """
#     SELECT MAX(CAST(week AS INTEGER)) as current_week
#     FROM Games
#     WHERE season = 2024 AND home_score IS NOT NULL AND away_score IS NOT NULL
# """

# # Execute the query to get the current week
# current_week_df = pd.read_sql(current_week_query, conn)
# current_week = current_week_df.iloc[0]['current_week']

# # If no games have been played, default to week 1
# if pd.isnull(current_week):
#     current_week = 0

# # Query to get the next week's games (where scores are NULL)
# next_week_query = f"""
#     SELECT *
#     FROM Games
#     WHERE season = 2024 AND CAST(week AS INTEGER) = {current_week + 1} AND home_score IS NULL AND away_score IS NULL
# """

# # Execute the query to load the next week's games into a DataFrame
# next_week_games_df = pd.read_sql(next_week_query, conn)

# # Step 2: Check if any games exist for the next week and save them to CSV
# output_dir = './data'
# os.makedirs(output_dir, exist_ok=True)  # Ensure the output directory exists

# if next_week_games_df.empty:
#     print(f"No games found for Week {current_week + 1}.")
# else:
#     # Export the DataFrame to a CSV file
#     upcoming_games_path = os.path.join(output_dir, 'UpcomingGames.csv')
#     next_week_games_df.to_csv(upcoming_games_path, index=False)
#     print(f"Next week's games (Week {current_week + 1}) saved to {upcoming_games_path}.")

#     # Query to delete all unplayed games (games where both home_score and away_score are NULL)
#     delete_unplayed_games_query = """
#         DELETE FROM Games
#         WHERE season = 2024 AND home_score IS NULL AND away_score IS NULL
#     """

#     # Execute the deletion of unplayed games
#     conn.execute(delete_unplayed_games_query)
#     conn.commit()
#     print(f"Unplayed games from season 2024 have been removed from the database.")

# # Close the connection
# conn.close()

# # Step 3: Copy the database file to the current directory
# source_db_path = db_path
# destination_db_path = './nfl.db'

# # Check if the source file exists
# if os.path.exists(source_db_path):
#     shutil.copy(source_db_path, destination_db_path)
#     print(f"Database copied from {source_db_path} to {destination_db_path}")
# else:
#     print(f"Source database not found at {source_db_path}")
#     exit(1)

# # Step 4: Delete the 'data/' and 'Streamlit/data/' directories if they exist, then create fresh ones
# if os.path.exists('./data'):
#     shutil.rmtree('./data')  # Deletes the directory and all its contents
#     print("Deleted existing directory: ./data")

# if os.path.exists('./Streamlit/data'):
#     shutil.rmtree('./Streamlit/data')  # Deletes the directory and all its contents
#     print("Deleted existing directory: ./Streamlit/data")

# # Copy the full directory
# shutil.copytree('../Scrapers/data', './data')
# shutil.copytree('../Scrapers/data', './Streamlit/data')

# print("Data directories have been successfully copied.")

# # Step 5: Connect to the copied SQLite database and export tables to CSV
# conn = sqlite3.connect(destination_db_path)
# cursor = conn.cursor()

# # Get all table names from the database
# cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
# tables = cursor.fetchall()

# # Save all tables to CSV files in the data/ directory
# for table_name_tuple in tables:
#     table_name = table_name_tuple[0]
    
#     # Load the table into a DataFrame
#     df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
    
#     # Save the DataFrame to a CSV file
#     output_file = os.path.join(output_dir, f"{table_name}.csv")
#     df.to_csv(output_file, index=False)
    
#     print(f"Table '{table_name}' saved to {output_file}")

# # Close the database connection
# conn.close()
# print("All tables have been saved to CSV files.")
