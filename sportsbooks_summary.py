import csv
import os
from collections import Counter

props_file = 'Models/10-ARBITRAGE/data/week10_props_2025-11-09.csv'

if not os.path.exists(props_file):
    print(f"File not found: {props_file}")
    exit(1)

sportsbooks = []
with open(props_file, 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        sportsbooks.append(row['bookmaker'])

unique_sportsbooks = sorted(set(sportsbooks))
counts = Counter(sportsbooks)

print("=" * 80)
print("UNIQUE SPORTSBOOKS SCRAPED FROM THE-ODDS-API.COM")
print("=" * 80)
print(f"\nTotal unique sportsbooks: {len(unique_sportsbooks)}\n")
print("List of all unique sportsbooks:")
for i, book in enumerate(unique_sportsbooks, 1):
    print(f"  {i:2d}. {book}")

print(f"\n\nCount per sportsbook:")
for book, count in sorted(counts.items()):
    print(f"  {book:30s}: {count:5d} props")

print("\n" + "=" * 80)
print("HOW THESE SPORTSBOOKS WERE SELECTED")
print("=" * 80)
print("""
The sportsbooks are selected automatically by the-odds-api.com based on the 
regions parameter specified in the API request.

SELECTION METHOD:
-----------------
1. API Regions Parameter: 'us,us2,us_dfs,eu'
   - This parameter tells the API which geographic regions to include
   - The API returns ALL available bookmakers from these regions that offer
     the requested markets

2. Markets Parameter: 'player_pass_yds,player_reception_yds,player_rush_yds'
   - Only bookmakers offering these specific player prop markets are included

3. No Manual Filtering:
   - The code does NOT filter or exclude any sportsbooks
   - ALL bookmakers returned by the API are included in the dataset

REGION BREAKDOWN:
-----------------
- 'us': US-regulated sportsbooks (e.g., DraftKings, FanDuel, BetMGM, ESPN BET)
- 'us2': Additional US sportsbooks (e.g., BetRivers, Hard Rock Bet, betPARX)
- 'us_dfs': Daily Fantasy Sports providers (e.g., DraftKings Pick6, PrizePicks, Underdog)
- 'eu': European sportsbooks (e.g., Pinnacle, Bovada)

CODE LOCATION:
--------------
File: Models/10-ARBITRAGE/fetch_upcoming_games_and_props.py
- Line 34: regions = 'us,us2,us_dfs,eu'
- Line 35: markets = 'player_pass_yds,player_reception_yds,player_rush_yds'
- Lines 140-141: Extracts all bookmakers from API response without filtering

NOTE:
-----
The specific list of sportsbooks may vary slightly depending on:
- Which bookmakers are currently active/available in the API
- Which bookmakers offer the specific player prop markets requested
- Regional availability and licensing status
""")
