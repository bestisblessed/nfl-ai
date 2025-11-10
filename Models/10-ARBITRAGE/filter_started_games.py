"""
Filter out props from games that have already started.

When running the script during Sunday afternoon, early games (1pm ET) may have already
started, causing sportsbooks to pull/modify their lines. This results in inconsistent
data where most books show live in-game props while some (like Pinnacle) retain 
pre-game lines.

Solution: Remove all props from games in the 1pm ET slot if running after 1pm ET.
"""

import csv
import sys
import os
from datetime import datetime, timedelta

# Week 10 game times (Eastern Time)
# These would ideally come from upcoming_games.csv with time data
WEEK_10_1PM_GAMES = {
    'Minnesota Vikings vs Baltimore Ravens',
    'Baltimore Ravens vs Minnesota Vikings',
    'Miami Dolphins vs Buffalo Bills',
    'Buffalo Bills vs Miami Dolphins',
    'New York Jets vs Cleveland Browns',
    'Cleveland Browns vs New York Jets',
    'Houston Texans vs Jacksonville Jaguars',
    'Jacksonville Jaguars vs Houston Texans',
    'Tampa Bay Buccaneers vs New England Patriots',
    'New England Patriots vs Tampa Bay Buccaneers',
    'Carolina Panthers vs New Orleans Saints',
    'New Orleans Saints vs Carolina Panthers',
    'Chicago Bears vs New York Giants',
    'New York Giants vs Chicago Bears',
}

def normalize_game_key(home, away):
    """Create both possible game keys."""
    return [f"{home} vs {away}", f"{away} vs {home}"]

def is_game_started(home_team, away_team, game_times_1pm):
    """Check if game has started based on known 1pm games."""
    for key in normalize_game_key(home_team, away_team):
        if key in game_times_1pm:
            return True
    return False

def main():
    if len(sys.argv) < 2:
        print("Usage: python filter_started_games.py <week_number>")
        sys.exit(1)
    
    week = sys.argv[1]
    current_date = datetime.now().strftime("%Y-%m-%d")
    
    # Try current date and previous date
    input_file = f"data/week{week}_props_{current_date}.csv"
    if not os.path.exists(input_file):
        prev_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        input_file = f"data/week{week}_props_{prev_date}.csv"
    
    if not os.path.exists(input_file):
        print(f"ERROR: Could not find props file for week {week}")
        sys.exit(1)
    
    input_date = input_file.split('_')[-1].replace('.csv', '')
    output_file = f"data/week{week}_props_{input_date}_filtered.csv"
    
    print(f"Filtering started games from {input_file}")
    
    rows_in = 0
    rows_out = 0
    filtered_games = set()
    
    with open(input_file, 'r') as fin, open(output_file, 'w', newline='') as fout:
        reader = csv.DictReader(fin)
        writer = csv.DictWriter(fout, fieldnames=reader.fieldnames)
        writer.writeheader()
        
        for row in reader:
            rows_in += 1
            home = row['home_team']
            away = row['away_team']
            
            # Filter out 1pm games (already started at 3pm)
            if is_game_started(home, away, WEEK_10_1PM_GAMES):
                game_key = f"{home} vs {away}"
                filtered_games.add(game_key)
                continue
            
            writer.writerow(row)
            rows_out += 1
    
    print(f"Input rows: {rows_in}")
    print(f"Output rows: {rows_out}")
    print(f"Rows filtered: {rows_in - rows_out}")
    print(f"\nGames filtered (1pm ET - already started):")
    for game in sorted(filtered_games):
        print(f"  - {game}")
    print(f"\nSaved to {output_file}")

if __name__ == "__main__":
    main()
