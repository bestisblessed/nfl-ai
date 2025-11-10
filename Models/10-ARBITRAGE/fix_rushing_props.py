"""
Fix rushing yards props by filtering out books that mislabel rush+receiving as rushing.

Analysis shows that most books (except Pinnacle) are returning rush+receiving combined
lines labeled as "player_rush_yds". This script filters the props data to only keep
Pinnacle's rushing lines (or validates that lines are reasonable for rushing only).

For Week 10 examples:
- De'Von Achane: Most books show 95-100 rush yds (actually rush+rec), Pinnacle shows 65.5 (actual)
- D'Andre Swift: Most books show 78-81 rush yds (actually rush+rec), Pinnacle shows 50.5 (actual)

See RUSHING_PROPS_FIX_README.md for full documentation.
"""

import csv
import sys
import os
from datetime import datetime, timedelta

def main():
    if len(sys.argv) < 2:
        print("Usage: python fix_rushing_props.py <week_number>")
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
        print(f"Tried: data/week{week}_props_{current_date}.csv")
        print(f"Tried: data/week{week}_props_{prev_date}.csv")
        sys.exit(1)
    
    # Extract date from input filename
    input_date = input_file.split('_')[-1].replace('.csv', '')
    output_file = f"data/week{week}_props_{input_date}_fixed.csv"
    
    print(f"Fixing rushing props in {input_file}")
    
    # Books that correctly label rushing-only props
    trusted_rush_books = {"Pinnacle"}
    
    rows_in = 0
    rows_out = 0
    rush_filtered = 0
    
    with open(input_file, 'r') as fin, open(output_file, 'w', newline='') as fout:
        reader = csv.DictReader(fin)
        writer = csv.DictWriter(fout, fieldnames=reader.fieldnames)
        writer.writeheader()
        
        for row in reader:
            rows_in += 1
            market = row['market']
            bookmaker = row['bookmaker']
            
            # Filter out rushing props from untrusted books
            if market == 'player_rush_yds' and bookmaker not in trusted_rush_books:
                rush_filtered += 1
                continue
            
            writer.writerow(row)
            rows_out += 1
    
    print(f"Input rows: {rows_in}")
    print(f"Output rows: {rows_out}")
    print(f"Rushing props filtered: {rush_filtered}")
    print(f"Saved to {output_file}")

if __name__ == "__main__":
    main()
