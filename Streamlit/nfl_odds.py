import os
import re
from datetime import datetime
import subprocess, shutil, os
import json
import csv  # Importing the csv module

shutil.rmtree("data/odds/", ignore_errors=True)
os.makedirs("data/odds/", exist_ok=True)
subprocess.run(["ssh", "Neo", "cd /Users/neo/odds-monitoring/ && zip -r data_backup.zip data"])
subprocess.run(["scp", "-r", "Neo:~/odds-monitoring/data_backup.zip", "."])
subprocess.run(["unzip", "data_backup.zip", "-d", "data/odds/"])

# Step 2: Move the contents of 'data/odds/data' to 'data/odds/'
src_dir = "data/odds/data"
dst_dir = "data/odds"

for filename in os.listdir(src_dir):
    src_file = os.path.join(src_dir, filename)
    dst_file = os.path.join(dst_dir, filename)
    if os.path.exists(dst_file):
        shutil.rmtree(dst_file) if os.path.isdir(dst_file) else os.remove(dst_file)
    shutil.move(src_file, dst_file)

# Remove the empty 'data/odds/data' folder after moving the files
shutil.rmtree(src_dir)


# Function to get the timestamp from the filename
def extract_timestamp(filename):
    match = re.search(r'nfl_odds_vsin_(\d{8}_\d{4})\.json', filename)
    if match:
        return datetime.strptime(match.group(1), '%Y%m%d_%H%M')
    return None

# Function to filter files based on the end time
def filter_files_by_time(directory, end_time):
    files = os.listdir(directory)
    
    # Convert end_time to a datetime object
    end_time_dt = datetime.strptime(end_time, '%Y%m%d_%H%M')
    
    for file in files:
        file_path = os.path.join(directory, file)
        if os.path.isfile(file_path):
            # Extract the timestamp from the filename
            file_timestamp = extract_timestamp(file)
            
            # If the file's timestamp is after the end time, delete it
            if file_timestamp and file_timestamp > end_time_dt:
                print(f"Deleting file: {file}")
                os.remove(file_path)

# Set the directory and end time
directory = 'data/odds/'  # Directory where your files are stored
# end_time = '20240929_1259'  # End time: Sep 29th at 12:59 PM (YYYYMMDD_HHMM)
end_time = input('Input end date like "20240929_1259": ')  # End time: Sep 29th at 12:59 PM (YYYYMMDD_HHMM)

# Call the function to filter files
filter_files_by_time(directory, end_time)

print("File filtering completed.")

# Delete empty files right at the beginning
files = os.listdir('data/odds/')
for file in files:
    file_path = os.path.join('data/odds/', file)
    if os.path.isfile(file_path) and os.stat(file_path).st_size == 0:
        print(f"Deleting empty file: {file}")
        os.remove(file_path)

# Function to dynamically load JSON files based on timestamps
def load_files(directory):
    files = [f for f in os.listdir(directory) if re.match(r'nfl_odds_vsin_\d{8}_\d{4}\.json', f)]
    files.sort(key=lambda x: re.findall(r'(\d{8}_\d{4})', x)[0])
    return files

# Function to format odds
def format_odds(odds):
    return odds.replace("\n", " | ")

# Function to compare odds between two datasets
def detect_odds_movement(odds_before, odds_after):
    movements = []
    
    for game_before, game_after in zip(odds_before, odds_after):
        if game_before['Time'] == game_after['Time']:
            game_date_column_name = list(game_before.keys())[1]  # Assuming the second key is the date
            
            for key in game_before:
                if key not in ["Time", game_date_column_name] and key in game_after:
                    if game_before[key] != game_after[key]:
                        movements.append({
                            'game_time': game_before['Time'],  # Game time is stored
                            'game_date_column_name': game_date_column_name,
                            'game_date_value': game_before[game_date_column_name],
                            'sportsbook': key,
                            'odds_before': format_odds(game_before[key]),
                            'odds_after': format_odds(game_after[key])
                        })
    return movements

# Directory containing the odds files
directory = 'data/odds/'
# Load and sort files
files = load_files(directory)

# List to hold all detected movements for CSV
all_movements = []

# Loop through consecutive files and compare odds
for i in range(len(files) - 1):
    file1 = files[i]
    file2 = files[i + 1]
    
    with open(os.path.join(directory, file1)) as f1, open(os.path.join(directory, file2)) as f2:
        odds_before = json.load(f1)
        odds_after = json.load(f2)
# # Loop through consecutive files and compare odds
# for i in range(len(files) - 1):
#     file1 = files[i]
#     file2 = files[i + 1]
    
#     with open(os.path.join(directory, file1)) as f1, open(os.path.join(directory, file2)) as f2:
#         # Check if the files are empty before loading them
#         if os.stat(f1.name).st_size == 0:
#             print(f"File {f1.name} is empty.")
#             continue

#         if os.stat(f2.name).st_size == 0:
#             print(f"File {f2.name} is empty.")
#             continue
        
#         odds_before = json.load(f1)
#         odds_after = json.load(f2)
  
    # Detect movements between consecutive files
    odds_movements = detect_odds_movement(odds_before, odds_after)
    
    if odds_movements:
        for movement in odds_movements:
            all_movements.append({
                'file1': file1,
                'file2': file2,
                'game_date': movement['game_date_column_name'],  # Save the matchup column name
                'game_time': movement['game_time'],  # Use game_time directly
                'matchup': f"{movement['game_date_value'].replace('\n', ' vs').strip()}",
                'sportsbook': movement['sportsbook'],
                'odds_before': movement['odds_before'],
                'odds_after': movement['odds_after']
            })
    else:
        # print(f"No odds movement detected between {file1} and {file2}.")
        pass

# Save movements to a CSV file
csv_file_path = 'data/odds/nfl_odds_movements.csv'
with open(csv_file_path, mode='w', newline='') as csv_file:
    fieldnames = ['file1', 'file2', 'game_date', 'game_time', 'matchup', 'sportsbook', 'odds_before', 'odds_after']
    writer = csv.DictWriter(csv_file, fieldnames=fieldnames)

    writer.writeheader()  # Write the header
    for movement in all_movements:
        writer.writerow(movement)  # Write each movement

print(f"Odds movements saved to {csv_file_path}")
