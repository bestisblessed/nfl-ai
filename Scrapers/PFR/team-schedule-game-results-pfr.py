import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import os

os.makedirs('./data', exist_ok=True)
os.makedirs('./data/schedule-game-results', exist_ok=True)

years = [2020, 2021, 2022, 2023, 2024, 2025]

teams = ['crd', 'atl', 'rav', 'buf', 'car', 'chi', 'cin', 'cle', 'dal', 'den', 
         'det', 'gnb', 'htx', 'clt', 'jax', 'kan', 'sdg', 'ram', 'rai', 'mia', 
         'min', 'nwe', 'nor', 'nyg', 'nyj', 'phi', 'pit', 'sea', 'sfo', 'tam', 
         'oti', 'was']

all_schedule_results = []
for year in years:
    year_file = f'./data/schedule-game-results/schedule_game_results_{year}.csv'
    if os.path.exists(year_file):
        os.remove(year_file)
    print(f"Scraping schedule and game results for {year}...")
    year_schedule_results = []
    for team in teams:
        print(f"   Scraping {team.upper()} schedule for {year}...")
        url = f'https://www.pro-football-reference.com/teams/{team}/{year}.htm'
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        try:
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            schedule_table = soup.find('table', {'id': 'games'})
            if not schedule_table:
                print(f"   -> No games table found for {team} {year}")
                continue
            column_names = []
            header_row = schedule_table.find('thead').find_all('tr')[-1]
            if header_row:
                for th in header_row.find_all('th'):
                    data_stat = th.get('data-stat')
                    if data_stat:
                        column_names.append(data_stat)
            tbody = schedule_table.find('tbody')
            if tbody:
                for tr in tbody.find_all('tr'):
                    if tr.get('class') and 'thead' in tr.get('class'):
                        continue
                    cells = tr.find_all(['th', 'td'])
                    if len(cells) > 0:
                        row_data = {'team': team, 'season': year}
                        
                        for i, cell in enumerate(cells):
                            if i < len(column_names):
                                col_name = column_names[i]
                                cell_text = cell.get_text(strip=True)
                                row_data[col_name] = cell_text
                        year_schedule_results.append(row_data)
            time.sleep(4.1)
        except requests.exceptions.RequestException as e:
            print(f"   -> Request failed for {team} {year}: {e}")
            time.sleep(4.1)
            continue
        except Exception as e:
            print(f"   -> Error scraping {team} {year}: {e}")
            time.sleep(4.1)
            continue
    print(f"-> Found {len(year_schedule_results)} schedule entries for {year}")
    if year_schedule_results:
        year_df = pd.DataFrame(year_schedule_results)
        year_df.to_csv(year_file, index=False)
        print(f"-> Saved schedule results to {year_file}")
        all_schedule_results.extend(year_schedule_results)
    time.sleep(10)
    
if all_schedule_results:
    df = pd.DataFrame(all_schedule_results)
    df = df.drop_duplicates()
    df['week_num'] = pd.to_numeric(df['week_num'], errors='coerce')
    df = df.sort_values(['season', 'team', 'week_num'])
    df.to_csv('./data/schedule_game_results.csv', index=False)
    print(f"\nSaved {len(df)} total schedule entries to schedule_game_results.csv")
else:
    print("\nNo schedule data scraped.")