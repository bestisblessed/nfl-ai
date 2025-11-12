"""
Script to fetch NFL betting props from the-odds-api.com for all games in week10_all_props_summary.csv

Fetches the following 7 prop types:
- QB Passing Yards (player_pass_yds)
- WR Receiving Yards (player_reception_yds)
- TE Receiving Yards (player_reception_yds)
- RB Receiving Yards (player_reception_yds)
- RB Rushing Yards (player_rush_yds)
- QB Rushing Yards (player_rush_yds)
- Anytime Touchdown Scorer (player_touchdowns)

Output CSV columns:
- bookmaker: Sportsbook name
- market: Prop type (player_pass_yds, player_reception_yds, player_rush_yds, player_touchdowns)
- player: Player name
- outcome: Over/Under (for yards props) or Yes/No (for TD props)
- point: Line/total (N/A for TD props)
- price: American odds
- event_id: API event ID
- home_team: Home team name
- away_team: Away team name
"""

import requests
import csv
import os
import pandas as pd
import time
from datetime import datetime

api_key = '8aabcc029890b3fd7f740a705758c2d8'
sport_key = 'americanfootball_nfl'
base_url = 'https://api.the-odds-api.com/v4/sports/'
regions = 'us,us2,us_dfs,eu'
markets = 'player_pass_yds,player_reception_yds,player_rush_yds,player_touchdowns'
odds_format = 'american'

team_abbrev_to_full = {
    'ARI': 'Arizona Cardinals', 'ATL': 'Atlanta Falcons', 'BAL': 'Baltimore Ravens',
    'BUF': 'Buffalo Bills', 'CAR': 'Carolina Panthers', 'CHI': 'Chicago Bears',
    'CIN': 'Cincinnati Bengals', 'CLE': 'Cleveland Browns', 'DAL': 'Dallas Cowboys',
    'DEN': 'Denver Broncos', 'DET': 'Detroit Lions', 'GB': 'Green Bay Packers',
    'HOU': 'Houston Texans', 'IND': 'Indianapolis Colts', 'JAX': 'Jacksonville Jaguars',
    'KC': 'Kansas City Chiefs', 'LVR': 'Las Vegas Raiders', 'LAC': 'Los Angeles Chargers',
    'LAR': 'Los Angeles Rams', 'MIA': 'Miami Dolphins', 'MIN': 'Minnesota Vikings',
    'NE': 'New England Patriots', 'NO': 'New Orleans Saints', 'NYG': 'New York Giants',
    'NYJ': 'New York Jets', 'PHI': 'Philadelphia Eagles', 'PIT': 'Pittsburgh Steelers',
    'SF': 'San Francisco 49ers', 'SEA': 'Seattle Seahawks', 'TB': 'Tampa Bay Buccaneers',
    'TEN': 'Tennessee Titans', 'WAS': 'Washington Commanders'
}

def normalize_team_name(name):
    name = name.strip()
    if 'Las Vegas' in name or 'Raiders' in name:
        return 'Las Vegas Raiders'
    if 'Los Angeles' in name:
        if 'Chargers' in name:
            return 'Los Angeles Chargers'
        if 'Rams' in name:
            return 'Los Angeles Rams'
    return name

def get_team_keywords(team_abbrev):
    full_name = team_abbrev_to_full.get(team_abbrev, team_abbrev)
    words = full_name.split()
    if len(words) >= 2:
        return words[-1]
    return full_name

def print_api_usage(response):
    remaining = response.headers.get('x-requests-remaining', 'N/A')
    used = response.headers.get('x-requests-used', 'N/A')
    print(f"  API Usage: {used} used, {remaining} remaining")

def get_unique_games_from_csv(week):
    csv_path = f'0-FINAL-REPORTS/week{week}_all_props_summary.csv'
    if not os.path.exists(csv_path):
        csv_path = f'../0-FINAL-REPORTS/week{week}_all_props_summary.csv'
    df = pd.read_csv(csv_path)
    games = []
    for _, row in df.iterrows():
        team = row['team']
        opp = row['opp']
        games.append((team, opp))
    return list(set(games))

def fetch_all_events():
    events_url = f"{base_url}{sport_key}/events?apiKey={api_key}"
    response = requests.get(events_url)
    print_api_usage(response)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching events: {response.status_code}")
        return []

def match_game_to_event(game_team, game_opp, events):
    game_team_full = team_abbrev_to_full.get(game_team, game_team)
    game_opp_full = team_abbrev_to_full.get(game_opp, game_opp)
    game_team_keyword = get_team_keywords(game_team)
    game_opp_keyword = get_team_keywords(game_opp)
    
    for event in events:
        home_team = event['home_team'].strip()
        away_team = event['away_team'].strip()
        
        home_match = (game_team_keyword in home_team or game_team_full in home_team or 
                     game_team in home_team)
        away_match = (game_opp_keyword in away_team or game_opp_full in away_team or 
                     game_opp in away_team)
        
        if home_match and away_match:
            return event['id']
        
        home_match_opp = (game_opp_keyword in home_team or game_opp_full in home_team or 
                          game_opp in home_team)
        away_match_team = (game_team_keyword in away_team or game_team_full in away_team or 
                          game_team in away_team)
        
        if home_match_opp and away_match_team:
            return event['id']
    return None

def fetch_props_for_event(event_id):
    props_url = f"{base_url}{sport_key}/events/{event_id}/odds"
    url = f"{props_url}?apiKey={api_key}&regions={regions}&markets={markets}&oddsFormat={odds_format}"
    response = requests.get(url)
    print_api_usage(response)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching props for event {event_id}: {response.status_code} - {response.text}")
        return None

def extract_props_from_response(data, target_props):
    if not data or 'bookmakers' not in data:
        return []
    
    props_list = []
    for bookmaker in data['bookmakers']:
        bookmaker_name = bookmaker['title']
        for market in bookmaker['markets']:
            market_key = market['key']
            if market_key not in target_props:
                continue
            
            for outcome in market['outcomes']:
                player_name = outcome.get('description', '')
                point = outcome.get('point', 'N/A')
                price = outcome['price']
                outcome_type = outcome['name']
                
                # For anytime TD props, outcome is typically "Yes" or "No" instead of Over/Under
                # Point is typically N/A for anytime TD props
                
                props_list.append({
                    'bookmaker': bookmaker_name,
                    'market': market_key,
                    'player': player_name,
                    'outcome': outcome_type,
                    'point': point,
                    'price': price,
                    'event_id': data.get('id', ''),
                    'home_team': data.get('home_team', ''),
                    'away_team': data.get('away_team', '')
                })
    return props_list

def main():
    import sys
    if len(sys.argv) < 2:
        print("Usage: python fetch_upcoming_games_and_props.py <week_number>")
        sys.exit(1)
    week = sys.argv[1]
    
    print(f"Step 1: Reading unique games from week{week}_all_props_summary.csv")
    unique_games = get_unique_games_from_csv(week)
    print(f"Found {len(unique_games)} unique games")
    
    print("\nStep 2: Fetching all NFL events from API")
    all_events = fetch_all_events()
    print(f"Found {len(all_events)} total events")
    
    print("\nStep 3: Matching games to event IDs")
    event_mapping = {}
    for game_team, game_opp in unique_games:
        event_id = match_game_to_event(game_team, game_opp, all_events)
        if event_id:
            event_mapping[event_id] = (game_team, game_opp)
            print(f"Matched {game_team} vs {game_opp} -> Event ID: {event_id}")
        else:
            print(f"WARNING: Could not match {game_team} vs {game_opp}")
    
    print(f"\nStep 4: Fetching props for {len(event_mapping)} matched events")
    all_props = []
    target_props = ['player_pass_yds', 'player_reception_yds', 'player_rush_yds', 'player_touchdowns']
    
    for idx, (event_id, (team, opp)) in enumerate(event_mapping.items(), 1):
        print(f"[{idx}/{len(event_mapping)}] Fetching props for {team} vs {opp} (Event ID: {event_id})")
        event_data = fetch_props_for_event(event_id)
        if event_data:
            props = extract_props_from_response(event_data, target_props)
            all_props.extend(props)
            print(f"  Found {len(props)} props")
        if idx < len(event_mapping):
            time.sleep(1)
    
    print(f"\nStep 5: Saving events data to CSV")
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(script_dir, 'data')
    os.makedirs(data_dir, exist_ok=True)
    events_data = []
    for event_id, (team, opp) in event_mapping.items():
        # Find the event in all_events
        event = next((e for e in all_events if e['id'] == event_id), None)
        if event:
            events_data.append({
                'home_team': event.get('home_team', ''),
                'away_team': event.get('away_team', ''),
                'commence_time': event.get('commence_time', '')
            })
    
    if events_data:
        events_df = pd.DataFrame(events_data)
        events_filename = os.path.join(data_dir, f'week{week}_events.csv')
        events_df.to_csv(events_filename, index=False)
        print(f"Saved events to {events_filename}")
    
    print(f"\nStep 6: Saving {len(all_props)} total props to CSV")
    current_date = datetime.now().strftime("%Y-%m-%d")
    filename = os.path.join(data_dir, f'week{week}_props_{current_date}.csv')
    
    if all_props:
        df = pd.DataFrame(all_props)
        df.to_csv(filename, index=False)
        print(f"Saved to {filename}")
        print(f"\nSummary:")
        print(f"  Total props: {len(df)}")
        print(f"  Markets: {df['market'].value_counts().to_dict()}")
        print(f"  Bookmakers: {df['bookmaker'].nunique()}")
        print(f"  Unique players: {df['player'].nunique()}")
    else:
        print("No props found to save")

if __name__ == "__main__":
    main()

