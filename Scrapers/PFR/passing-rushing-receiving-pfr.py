import requests
from bs4 import BeautifulSoup, Comment
import pandas as pd
import time
import os

os.makedirs('./data', exist_ok=True)
os.makedirs('./data/passing-rushing-receiving', exist_ok=True)

# years = [2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025]
# years = [2021]
years = [2020, 2021, 2022, 2023, 2024, 2025]

games_df = pd.read_csv('./data/games.csv')
all_player_stats = []
for year in years:
    year_file = f'./data/passing-rushing-receiving/passing_rushing_receiving_{year}.csv'
    
    # Delete existing year file to start fresh
    if os.path.exists(year_file):
        os.remove(year_file)
    
    print(f"Scraping passing/rushing/receiving for {year}...")
    year_games = games_df[games_df['season'] == year]
    print(f"-> Found {len(year_games)} games to scrape")
    year_stats = []
    for idx, game in year_games.iterrows():
        game_id = game['game_id']
        pfr_id = game['pfr_boxscore_id']
        home_team = game['home_team']
        away_team = game['away_team']
        print(f"   Scraping game {pfr_id} ({game_id})...")
        url = f'https://www.pro-football-reference.com/boxscores/{pfr_id}.htm'
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        try:
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code != 200:
                print(f"   -> Error: Status {response.status_code}")
                time.sleep(5)
                continue
            soup = BeautifulSoup(response.content, 'html.parser')
            div_offense = soup.find('div', id='div_player_offense')
            if not div_offense:
                print(f"   -> No div_player_offense found")
                time.sleep(5)
                continue
            offense_table = div_offense.find('table')
            if not offense_table:
                print(f"   -> No table found inside div_player_offense")
                time.sleep(5)
                continue
            tbody = offense_table.find('tbody')
            if not tbody:
                time.sleep(5)
                continue
            first_row = None
            for tr in tbody.find_all('tr'):
                if tr.get('class') and 'thead' in tr.get('class'):
                    continue
                cells = tr.find_all(['th', 'td'])
                if cells:
                    first_row = cells
                    break
            if not first_row:
                time.sleep(5)
                continue
            column_names = []
            for cell in first_row:
                data_stat = cell.get('data-stat', '')
                if data_stat:
                    column_names.append(data_stat)
            for tr in tbody.find_all('tr'):
                if tr.get('class') and 'thead' in tr.get('class'):
                    continue
                cells = tr.find_all(['th', 'td'])
                if not cells or len(cells) != len(column_names):
                    continue
                player_data = {}
                for i, cell in enumerate(cells):
                    if i < len(column_names):
                        col_name = column_names[i]
                        cell_text = cell.get_text(strip=True)
                        if col_name == 'player':
                            player_link = cell.find('a')
                            if player_link:
                                player_data['player'] = cell_text
                                href = player_link.get('href', '')
                                if href:
                                    player_data['player_id'] = href.split('/')[-1]
                                else:
                                    player_data['player_id'] = ''
                            else:
                                player_data['player'] = cell_text
                                player_data['player_id'] = ''
                        else:
                            player_data[col_name] = cell_text
                player_data['game_id'] = game_id
                player_team = player_data.get('team', '')
                if player_team == home_team:
                    player_data['opponent_team'] = away_team
                    player_data['home'] = 'y'
                elif player_team == away_team:
                    player_data['opponent_team'] = home_team
                    player_data['home'] = 'n'
                else:
                    player_data['opponent_team'] = ''
                    player_data['home'] = ''
                year_stats.append(player_data)
            
            # Save after each game
            if year_stats:
                if os.path.exists(year_file):
                    existing_df = pd.read_csv(year_file)
                    combined_df = pd.concat([existing_df, pd.DataFrame(year_stats)], ignore_index=True)
                else:
                    combined_df = pd.DataFrame(year_stats)
                combined_df.to_csv(year_file, index=False)
                year_stats = []
            
            time.sleep(4.2)
        except Exception as e:
            print(f"   -> Error scraping {pfr_id}: {e}")
            time.sleep(4.2)
            continue
    if os.path.exists(year_file):
        year_df = pd.read_csv(year_file)
        print(f"-> Completed scraping for {year}")
        print(f"-> Found {len(year_df)} player game stats for {year}")
        all_player_stats.extend(year_df.to_dict('records'))
    time.sleep(10)

if all_player_stats:
    df = pd.DataFrame(all_player_stats)
    df = df.sort_values(['game_id', 'player'])
    df.to_csv('./data/passing_rushing_receiving.csv', index=False)
    print(f"\nSaved {len(df)} total player game stats to passing_rushing_receiving.csv")
