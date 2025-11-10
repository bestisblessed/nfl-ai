"""
Filter props data to use only Pinnacle lines for 1pm games (already started).

When running at 3pm, the 1pm games had already started. Most books switched to live 
in-game lines, but Pinnacle retained pre-game lines. This script:
- For 1pm games: Keep ONLY Pinnacle lines (pre-game)
- For later games: Keep ALL bookmaker lines

This gives us accurate pre-game lines for all games.
"""

import csv
import sys
import os
from datetime import datetime, timedelta

# Week 10 1pm ET games
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

def is_1pm_game(home_team, away_team):
    """Check if game was 1pm ET kickoff."""
    for key in normalize_game_key(home_team, away_team):
        if key in WEEK_10_1PM_GAMES:
            return True
    return False

def main():
    if len(sys.argv) < 2:
        print("Usage: python filter_by_game_time.py <week_number>")
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
    output_file = f"data/week{week}_props_{input_date}_pregame.csv"
    
    print(f"Filtering to pre-game lines from {input_file}")
    print(f"Strategy: 1pm games = Pinnacle only, Later games = All books")
    print()
    
    rows_in = 0
    rows_out = 0
    filtered_early = 0
    early_games = set()
    late_games = set()
    
    with open(input_file, 'r') as fin, open(output_file, 'w', newline='') as fout:
        reader = csv.DictReader(fin)
        writer = csv.DictWriter(fout, fieldnames=reader.fieldnames)
        writer.writeheader()
        
        for row in reader:
            rows_in += 1
            home = row['home_team']
            away = row['away_team']
            bookmaker = row['bookmaker']
            game_key = f"{home} vs {away}"
            
            # Check if this is a 1pm game
            if is_1pm_game(home, away):
                early_games.add(game_key)
                # For 1pm games: ONLY keep Pinnacle (pre-game lines)
                if bookmaker != 'Pinnacle':
                    filtered_early += 1
                    continue
            else:
                late_games.add(game_key)
            
            writer.writerow(row)
            rows_out += 1
    
    print(f"Input rows: {rows_in}")
    print(f"Output rows: {rows_out}")
    print(f"Filtered (non-Pinnacle from 1pm games): {filtered_early}")
    print()
    print(f"1pm games (Pinnacle only):")
    for game in sorted(early_games):
        print(f"  - {game}")
    print()
    print(f"Later games (all books):")
    for game in sorted(late_games):
        print(f"  - {game}")
    print()
    print(f"Saved to {output_file}")

if __name__ == "__main__":
    main()
