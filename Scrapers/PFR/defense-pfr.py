import os
import csv
import time
import requests
import pandas as pd
from bs4 import BeautifulSoup, Comment

os.makedirs('data', exist_ok=True)
os.makedirs('data/defense', exist_ok=True)

# session = requests.Session()
# session.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
# session.headers.update({
#     'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
#     'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
#     'Accept-Language': 'en-US,en;q=0.5',
#     'Accept-Encoding': 'gzip, deflate',
#     'Connection': 'keep-alive',
#     'Upgrade-Insecure-Requests': '1'
# })

games = pd.read_csv('data/games.csv')
for year in range(2020, 2026):
    print(f"Scraping defense game logs for {year}")
    yearly_path = f'./data/defense/all_defense_{year}.csv'
    
    # Delete existing year file to start fresh
    if os.path.exists(yearly_path):
        os.remove(yearly_path)
    with open(yearly_path, 'w', newline='') as f:
        w = csv.writer(f)
        headers_written = False
        dfy = games[games['season'] == year]
        for _, row in dfy.iterrows():
            url = f"https://www.pro-football-reference.com/boxscores/{row['pfr_boxscore_id']}.htm"
            print(f"-> scraping {row['game_id']}...")
            # Retry logic for rate limiting
            max_retries = 3
            retry_delay = 30
            for attempt in range(max_retries):
                try:
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                        'Accept-Language': 'en-US,en;q=0.9',
                        'Accept-Encoding': 'gzip',
                        'Cache-Control': 'no-cache',
                        'Pragma': 'no-cache'
                    }
                    r = requests.get(url, headers=headers, timeout=15)
                    r.raise_for_status()
                    soup = BeautifulSoup(r.text, 'html.parser')
                    comments = soup.find_all(string=lambda text: isinstance(text, Comment))
                    for c in comments:
                        if c.strip() and '<table' in c:
                            t = BeautifulSoup(c, 'html.parser').find('table', id='player_defense')
                            if t:
                                if not headers_written:
                                    body = t.find('tbody')
                                    rows_iter = body.find_all('tr') if body else t.find_all('tr')
                                    first_data_row = None
                                    for tr in rows_iter:
                                        classes = tr.get('class') or []
                                        if any(cls in ('thead', 'spacer', 'over_header') for cls in classes):
                                            continue
                                        cells = tr.find_all(['th', 'td'])
                                        if cells and any(c.get_text(strip=True) for c in cells):
                                            first_data_row = cells
                                            break
                                    if first_data_row:
                                        num_cols = len(first_data_row)
                                        thead = t.find('thead')
                                        header_names = []
                                        if thead:
                                            all_header_cells = []
                                            for tr in thead.find_all('tr'):
                                                cells = tr.find_all(['th', 'td'])
                                                all_header_cells.extend(cells)
                                            if len(all_header_cells) == num_cols:
                                                header_names = [hc.get_text(strip=True) for hc in all_header_cells]
                                                header_names = [h for h in header_names if h != '']
                                        if len(header_names) != num_cols:
                                            header_names = [f'col_{i+1}' for i in range(num_cols)]
                                        header_names.append('game_id')
                                        w.writerow(header_names)
                                        headers_written = True
                                body = t.find('tbody')
                                rows_iter = body.find_all('tr') if body else t.find_all('tr')
                                for tr in rows_iter:
                                    classes = tr.get('class') or []
                                    if any(cls in ('thead', 'spacer', 'over_header') for cls in classes):
                                        continue
                                    cells = tr.find_all(['th', 'td'])
                                    if not cells:
                                        continue
                                    row_vals = [c.get_text(strip=True) for c in cells]
                                    if all(v == '' for v in row_vals):
                                        continue
                                    row_vals.append(row['game_id'])
                                    w.writerow(row_vals)
                                break
                    break 
                except requests.exceptions.HTTPError as e:
                    if e.response.status_code == 429 and attempt < max_retries - 1:
                        print(f"Rate limited, waiting {retry_delay} seconds before retry {attempt + 1}/{max_retries}")
                        time.sleep(retry_delay)
                        retry_delay *= 2 
                        continue
                    else:
                        raise e
                except Exception as e:
                    print(f"Error scraping {url}: {e}")
                    break
            time.sleep(5)
            
    if os.path.exists(yearly_path):
        dfc = pd.read_csv(yearly_path)
        dfc.dropna(inplace=True)
        dfc.to_csv(yearly_path, index=False)
        print(f"Cleaned defense data for {year}")
csv_files = [f for f in os.listdir('data/defense/') if f.endswith('.csv')]
if csv_files:
    merged = pd.concat([pd.read_csv(f'data/defense/{f}') for f in csv_files], ignore_index=True)
    if 'game_id' in merged.columns and ('player' in merged.columns or 'Player' in merged.columns):
        key_col = 'player' if 'player' in merged.columns else 'Player'
        merged = merged.drop_duplicates(subset=['game_id', key_col])
    elif 'game_id' in merged.columns:
        merged = merged.drop_duplicates(subset=['game_id'])
    merged.to_csv('data/defense.csv', index=False)
    print("Merged dataset saved as data/defense.csv")
else:
    print("No defense files found to merge")