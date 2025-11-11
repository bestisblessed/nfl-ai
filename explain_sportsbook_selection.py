"""
Explanation of how sportsbooks are selected when scraping props from the-odds-api.com

The selection is determined by:
1. API regions parameter: 'us,us2,us_dfs,eu'
2. Markets parameter: 'player_pass_yds,player_reception_yds,player_rush_yds'
3. All bookmakers returned by the API for these regions are included (no filtering)

The regions parameter controls which sportsbooks are available:
- 'us': US-regulated sportsbooks
- 'us2': Additional US sportsbooks
- 'us_dfs': Daily Fantasy Sports providers (like DraftKings Pick6, PrizePicks, Underdog)
- 'eu': European sportsbooks (like Pinnacle)

The API automatically returns all available bookmakers for the specified regions
that offer the requested markets (player props).
"""

print("=" * 80)
print("HOW SPORTSBOOKS ARE SELECTED")
print("=" * 80)
print(__doc__)

print("\n\nKey Code Location:")
print("  File: Models/10-ARBITRAGE/fetch_upcoming_games_and_props.py")
print("  Line 34: regions = 'us,us2,us_dfs,eu'")
print("  Line 35: markets = 'player_pass_yds,player_reception_yds,player_rush_yds'")
print("\n  The code extracts ALL bookmakers from the API response:")
print("  Line 140-141: for bookmaker in data['bookmakers']:")
print("                  bookmaker_name = bookmaker['title']")
print("\n  No filtering is applied - all sportsbooks returned by the API are included.")
