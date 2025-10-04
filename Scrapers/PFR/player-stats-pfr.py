import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import os

os.makedirs('./data', exist_ok=True)
os.makedirs('./data/player-stats', exist_ok=True)

# years = [2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025]
years = [2023]

all_player_stats = []
for year in years:
    print(f"Scraping player stats for {year}...")
    url = f'https://www.pro-football-reference.com/years/{year}/fantasy.htm'
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    response = requests.get(url, headers=headers, timeout=15)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Find the fantasy rankings table
    fantasy_table = soup.find('table', {'id': 'fantasy'})
    if not fantasy_table:
        print(f"No fantasy table found for {year}")
        continue
    
    # Get column headers from thead
    thead = fantasy_table.find('thead')
    if not thead:
        print(f"No table header found for {year}")
        continue
    
    # Get the first data row to determine column structure
    tbody = fantasy_table.find('tbody')
    if not tbody:
        print(f"No tbody found for {year}")
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
        print(f"No data rows found for {year}")
        continue
    
    # Create column names based on data-stat attributes or position
    column_names = []
    for i, cell in enumerate(first_data_row):
        data_stat = cell.get('data-stat', '')
        if data_stat:
            column_names.append(data_stat)
        else:
            # Use generic names for columns without data-stat
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
    
    print(f"Found table with {len(column_names)} columns")
    print(f"Found tbody with {len(tbody.find_all('tr'))} rows")
    
    year_stats = []
    
    for tr in tbody.find_all('tr'):
        if tr.get('class') and 'thead' in tr.get('class'):
            continue
        
        cells = tr.find_all(['th', 'td'])
        if not cells or len(cells) != len(column_names):
            continue
        
        # Extract player data using proper column names
        player_data = {}
        for i, cell in enumerate(cells):
            if i < len(column_names):
                col_name = column_names[i]
                cell_text = cell.get_text(strip=True)
                
                # Handle special cases for player and team links
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
                    # Use the data-stat name as column name
                    player_data[col_name] = cell_text
        
        player_data['season'] = year
        year_stats.append(player_data)
    
    print(f"-> Found {len(year_stats)} players")
    
    # Save individual year file
    if year_stats:
        year_df = pd.DataFrame(year_stats)
        year_df.to_csv(f'./data/player-stats/player_stats_{year}.csv', index=False)
        print(f"-> Saved player stats to ./data/player-stats/player_stats_{year}.csv")
        all_player_stats.extend(year_stats)
    
    time.sleep(10)

# Combine all years
if all_player_stats:
    df = pd.DataFrame(all_player_stats)
    df = df.drop_duplicates(subset=['player_name', 'season'])
    df = df.sort_values(['season', 'player_name'])
    df.to_csv('./data/player_stats.csv', index=False)
    print(f"Saved {len(df)} total player stats to player_stats.csv")
else:
    print("No player stats found")
