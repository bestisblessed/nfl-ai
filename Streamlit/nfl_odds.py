import os
import re
from datetime import datetime
import subprocess, shutil, os
import json
import csv  
import pandas as pd
shutil.rmtree("data/odds/", ignore_errors=True)
os.makedirs("data/odds/", exist_ok=True)
subprocess.run(["ssh", "Neo", "cd /Users/neo/odds-monitoring/ && zip -r data_backup.zip data"])
subprocess.run(["scp", "-r", "Neo:~/odds-monitoring/data_backup.zip", "."])
subprocess.run(["unzip", "data_backup.zip", "-d", "data/odds/"])
src_dir = "data/odds/data"
dst_dir = "data/odds"
for filename in os.listdir(src_dir):
    src_file = os.path.join(src_dir, filename)
    dst_file = os.path.join(dst_dir, filename)
    if os.path.exists(dst_file):
        shutil.rmtree(dst_file) if os.path.isdir(dst_file) else os.remove(dst_file)
    shutil.move(src_file, dst_file)
shutil.rmtree(src_dir)
def extract_timestamp(filename):
    match = re.search(r'nfl_odds_vsin_(\d{8}_\d{4})\.json', filename)
    if match:
        return datetime.strptime(match.group(1), '%Y%m%d_%H%M')
    return None
def filter_files_by_time(directory, end_time):
    files = os.listdir(directory)
    end_time_dt = datetime.strptime(end_time, '%Y%m%d_%H%M')
    for file in files:
        file_path = os.path.join(directory, file)
        if os.path.isfile(file_path):
            file_timestamp = extract_timestamp(file)
            if file_timestamp and file_timestamp > end_time_dt:
                print(f"Deleting file: {file}")
                os.remove(file_path)
directory = 'data/odds/'  
end_time = input('Input end date like "20240929_1259" (leave empty for current time): ')
if not end_time:
    current_time = datetime.now()
    end_time = current_time.strftime('%Y%m%d_%H%M')
    print(f"Using current time: {end_time}")
filter_files_by_time(directory, end_time)
print("File filtering completed.")
files = os.listdir('data/odds/')
for file in files:
    file_path = os.path.join('data/odds/', file)
    if os.path.isfile(file_path) and os.stat(file_path).st_size == 0:
        print(f"Deleting empty file: {file}")
        os.remove(file_path)
def load_files(directory):
    files = [f for f in os.listdir(directory) if re.match(r'nfl_odds_vsin_\d{8}_\d{4}\.json', f)]
    files.sort(key=lambda x: re.findall(r'(\d{8}_\d{4})', x)[0])
    return files
def format_odds(odds):
    return odds.replace("\n", " | ")
def detect_odds_movement(odds_before, odds_after):
    movements = []
    for game_before, game_after in zip(odds_before, odds_after):
        if game_before['Time'] == game_after['Time']:
            game_date_column_name = list(game_before.keys())[1]  
            for key in game_before:
                if key not in ["Time", game_date_column_name] and key in game_after:
                    if game_before[key] != game_after[key]:
                        movements.append({
                            'game_time': game_before['Time'],  
                            'game_date_column_name': game_date_column_name,
                            'game_date_value': game_before[game_date_column_name],
                            'sportsbook': key,
                            'odds_before': format_odds(game_before[key]),
                            'odds_after': format_odds(game_after[key])
                        })
    return movements
directory = 'data/odds/'
files = load_files(directory)
all_movements = []
for i in range(len(files) - 1):
    file1 = files[i]
    file2 = files[i + 1]
    with open(os.path.join(directory, file1)) as f1, open(os.path.join(directory, file2)) as f2:
        odds_before = json.load(f1)
        odds_after = json.load(f2)
    odds_movements = detect_odds_movement(odds_before, odds_after)
    if odds_movements:
        for movement in odds_movements:
            all_movements.append({
                'file1': file1,
                'file2': file2,
                'game_date': movement['game_date_column_name'],  
                'game_time': movement['game_time'],  
                'matchup': f"{movement['game_date_value'].replace('\n', ' vs').strip()}",
                'sportsbook': movement['sportsbook'],
                'odds_before': movement['odds_before'],
                'odds_after': movement['odds_after']
            })
    else:
        pass
all_movements.sort(key=lambda x: x['game_date'])
csv_file_path = 'data/odds/nfl_odds_movements.csv'
with open(csv_file_path, mode='w', newline='') as csv_file:
    fieldnames = ['file1', 'file2', 'game_date', 'game_time', 'matchup', 'sportsbook', 'odds_before', 'odds_after']
    writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
    writer.writeheader()  
    for movement in all_movements:
        writer.writerow(movement)  
print(f"Odds movements saved to {csv_file_path}")
os.remove('data_backup.zip')
file_path = 'data/odds/nfl_odds_movements.csv'  
nfl_odds_data = pd.read_csv(file_path)
nfl_odds_data[['team_1', 'team_2']] = nfl_odds_data['matchup'].str.split(' vs ', expand=True)
nfl_odds_data[['team1_odds_before', 'team2_odds_before']] = nfl_odds_data['odds_before'].str.split(r'\s+\|\s+', expand=True)
nfl_odds_data[['team1_odds_after', 'team2_odds_after']] = nfl_odds_data['odds_after'].str.split(r'\s+\|\s+', expand=True)
nfl_odds_data['team1_odds_before'] = nfl_odds_data['team1_odds_before'].str.split().str[0]
nfl_odds_data['team2_odds_before'] = nfl_odds_data['team2_odds_before'].str.split().str[0]
nfl_odds_data['team1_odds_after'] = nfl_odds_data['team1_odds_after'].str.split().str[0]
nfl_odds_data['team2_odds_after'] = nfl_odds_data['team2_odds_after'].str.split().str[0]
def extract_timestamp(filename):
    try:
        timestamp_str = filename.split('_')[-1].replace('.json', '')
        return datetime.strptime(filename.split('_')[-2] + "_" + timestamp_str, '%Y%m%d_%H%M')
    except:
        return None
nfl_odds_data['time_before'] = nfl_odds_data['file1'].apply(extract_timestamp)
nfl_odds_data['time_after'] = nfl_odds_data['file2'].apply(extract_timestamp)
nfl_odds_data['time_before'] = nfl_odds_data['time_before'].apply(lambda dt: dt.strftime('%b %d %-I:%M%p') if pd.notnull(dt) else None)
nfl_odds_data['time_after'] = nfl_odds_data['time_after'].apply(lambda dt: dt.strftime('%b %d %-I:%M%p') if pd.notnull(dt) else None)
nfl_odds_data = nfl_odds_data.drop(columns=['odds_before', 'odds_after', 'file1', 'file2'])
print(nfl_odds_data[['team_1', 'team_2', 'team1_odds_before', 'team2_odds_before', 'team1_odds_after', 'team2_odds_after']].head())
nfl_odds_data.to_csv(file_path, index=False)  
nfl_odds_data = pd.read_csv('data/odds/nfl_odds_movements.csv')
circa_odds_data = nfl_odds_data[nfl_odds_data['sportsbook'] == 'Circa']
circa_odds_data.to_csv('data/nfl_odds_movements_circa.csv', index=False)
nfl_odds_data = pd.read_csv('data/odds/nfl_odds_movements.csv')
circa_odds_data = nfl_odds_data[nfl_odds_data['sportsbook'] == 'DK']
circa_odds_data.to_csv('data/nfl_odds_movements_dk.csv', index=False)