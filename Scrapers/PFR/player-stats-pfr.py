import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import os

os.makedirs('./data', exist_ok=True)
os.makedirs('./data/player-stats', exist_ok=True)

years = [2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025]
# years = [2023]

all_player_stats = []
for year in years:
    print(f"Scraping player stats for {year}...")
    url = f'https://www.pro-football-reference.com/years/{year}/fantasy.htm'
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    response = requests.get(url, headers=headers, timeout=15)
    soup = BeautifulSoup(response.content, 'html.parser')
    fantasy_table = soup.find('table', {'id': 'fantasy'})
    if not fantasy_table:
        print(f"No fantasy table found for {year}")
        continue
    tbody = fantasy_table.find('tbody')
    if not tbody:
        continue
    first_data_row = None
    for tr in tbody.find_all('tr'):
        if tr.get('class') and 'thead' in tr.get('class'):
            continue
        cells = tr.find_all(['th', 'td'])
        if cells:
            first_data_row = cells
            break
    if not first_data_row:
        continue
    column_names = []
    for i, cell in enumerate(first_data_row):
        data_stat = cell.get('data-stat', '')
        if data_stat:
            column_names.append(data_stat)
        else:
            if i == 0:
                column_names.append('ranker')
            elif i == 1:
                column_names.append('player')
            elif i == 2:
                column_names.append('team')
            elif i == 3:
                column_names.append('fantasy_pos')
            elif i == 4:
                column_names.append('age')
            else:
                column_names.append(f'stat_{i}')
    year_stats = []
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
                        player_data['player_name'] = cell_text
                        player_data['player_url'] = player_link.get('href', '')
                    else:
                        player_data['player_name'] = cell_text
                        player_data['player_url'] = ''
                elif col_name == 'team':
                    team_link = cell.find('a')
                    if team_link:
                        player_data['team'] = cell_text
                        player_data['team_url'] = team_link.get('href', '')
                    else:
                        player_data['team'] = cell_text
                        player_data['team_url'] = ''
                else:
                    player_data[col_name] = cell_text
        player_data['season'] = year
        year_stats.append(player_data)
    print(f"-> Found {len(year_stats)} players")
    if year_stats:
        year_df = pd.DataFrame(year_stats)
        year_df.to_csv(f'./data/player-stats/player_stats_{year}.csv', index=False)
        print(f"-> Saved player stats to ./data/player-stats/player_stats_{year}.csv")
        all_player_stats.extend(year_stats)
    time.sleep(10)

# Combine all years
df = pd.DataFrame(all_player_stats)
df = df.drop_duplicates(subset=['player_name', 'season'])
df = df.sort_values(['season', 'player_name'])
df.to_csv('./data/player_stats.csv', index=False)
print(f"Saved {len(df)} total player stats to player_stats.csv")
