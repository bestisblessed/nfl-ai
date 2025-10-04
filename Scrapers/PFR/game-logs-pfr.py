import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import os

os.makedirs('./data', exist_ok=True)
os.makedirs('./data/game-logs', exist_ok=True)

# years = [2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025]
# years = [2020]
years = [2020, 2021, 2022, 2023, 2024, 2025]

teams = [
    ['crd', 'Arizona Cardinals'],
    ['atl', 'Atlanta Falcons'],
    ['rav', 'Baltimore Ravens'],
    ['buf', 'Buffalo Bills'],
    ['car', 'Carolina Panthers'],
    ['chi', 'Chicago Bears'],
    ['cin', 'Cincinnati Bengals'],
    ['cle', 'Cleveland Browns'],
    ['dal', 'Dallas Cowboys'],
    ['den', 'Denver Broncos'],
    ['det', 'Detroit Lions'],
    ['gnb', 'Green Bay Packers'],
    ['htx', 'Houston Texans'],
    ['clt', 'Indianapolis Colts'],
    ['jax', 'Jacksonville Jaguars'],
    ['kan', 'Kansas City Chiefs'],
    ['sdg', 'Los Angeles Chargers'],
    ['ram', 'Los Angeles Rams'],
    ['rai', 'Las Vegas Raiders'],
    ['mia', 'Miami Dolphins'],
    ['min', 'Minnesota Vikings'],
    ['nwe', 'New England Patriots'],
    ['nor', 'New Orleans Saints'],
    ['nyg', 'New York Giants'],
    ['nyj', 'New York Jets'],
    ['phi', 'Philadelphia Eagles'],
    ['pit', 'Pittsburgh Steelers'],
    ['sea', 'Seattle Seahawks'],
    ['sfo', 'San Francisco 49ers'],
    ['tam', 'Tampa Bay Buccaneers'],
    ['oti', 'Tennessee Titans'],
    ['was', 'Washington Commanders']
]
for year in years:
    print(f"\nScraping game logs for {year}...")
    output_file = f'./data/game-logs/all_teams_game_logs_{year}.csv'
    if os.path.exists(output_file):
        os.remove(output_file)
        print(f"-> Deleted existing file: {output_file}")
    all_game_logs = []
    headers_extracted = False
    column_names = []
    for i, (abbr, name) in enumerate(teams, 1):
        print(f"  [{i:2d}/32] Processing {name}...")
        url = f'https://www.pro-football-reference.com/teams/{abbr}/{year}/gamelog/'
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        # headers = {
            # 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',  # CRITICAL: Only header that matters
            # 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',  # USELESS: Server sends HTML anyway
            # 'Accept-Language': 'en-US,en;q=0.9',  # USELESS: PFR doesn't check language
            # 'Accept-Encoding': 'gzip, deflate, br',  # USELESS: requests library handles this automatically
            # 'DNT': '1',  # USELESS: No one respects Do Not Track
            # 'Connection': 'keep-alive',  # USELESS: requests handles connections automatically
            # 'Upgrade-Insecure-Requests': '1',  # USELESS: Not needed for scraping
            # 'Sec-Fetch-Dest': 'document',  # USELESS: Only modern Chrome sends these
            # 'Sec-Fetch-Mode': 'navigate',  # USELESS: Can look suspicious if wrong
            # 'Sec-Fetch-Site': 'none',  # DANGEROUS: Contradicts Referer header!
            # 'Cache-Control': 'max-age=0',  # USELESS: Not checked by server
            # 'Referer': 'https://www.pro-football-reference.com/'  # OPTIONAL: Might help look natural but not needed
        # }
        try:
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code == 429:
                print(f"     Rate limited (429) - waiting 30 seconds...")
                time.sleep(30)
                response = requests.get(url, headers=headers, timeout=15)
            if response.status_code != 200:
                print(f"     Error: Got status code {response.status_code}")
                time.sleep(5)
                continue
        except Exception as e:
            print(f"     Error: {e}")
            time.sleep(5)
            continue
        soup = BeautifulSoup(response.content, 'html.parser')
        reg_table = soup.find('table', {'id': lambda x: x and 'team-year-regular-season-game-log' in x})
        if reg_table:
            if not headers_extracted:
                tbody = reg_table.find('tbody')
                if tbody:
                    first_data_row = None
                    for tr in tbody.find_all('tr'):
                        if tr.get('class') and 'thead' in tr.get('class'):
                            continue
                        cells = tr.find_all(['th', 'td'])
                        if cells:
                            first_data_row = cells
                            break
                    if first_data_row:
                        for cell in first_data_row:
                            data_stat = cell.get('data-stat', '')
                            if data_stat:
                                column_names.append(data_stat)
                            else:
                                column_names.append('unknown')
                        column_names.append('team_name')
                        headers_extracted = True
                        print(f"     -> Extracted {len(column_names)} columns")
            tbody = reg_table.find('tbody')
            if tbody:
                for tr in tbody.find_all('tr'):
                    if tr.get('class') and 'thead' in tr.get('class'):
                        continue
                    cells = tr.find_all(['th', 'td'])
                    row_data = []
                    for cell in cells:
                        text = cell.get_text(strip=True)
                        row_data.append(text if text else '')
                    if len(row_data) > 0 and row_data[0]:
                        row_data.append(name)
                        all_game_logs.append(row_data)
        playoff_table = soup.find('table', {'id': lambda x: x and 'team-year-playoffs-game-log' in x})
        if playoff_table:
            playoff_tbody = playoff_table.find('tbody')
            if playoff_tbody:
                for tr in playoff_tbody.find_all('tr'):
                    if tr.get('class') and 'thead' in tr.get('class'):
                        continue
                    cells = tr.find_all(['th', 'td'])
                    row_data = []
                    for cell in cells:
                        text = cell.get_text(strip=True)
                        row_data.append(text if text else '')
                    if len(row_data) > 0 and row_data[0]:
                        row_data.append(name)
                        all_game_logs.append(row_data)
        if all_game_logs and headers_extracted:
            df = pd.DataFrame(all_game_logs, columns=column_names)
            if i == 1:
                df.to_csv(output_file, index=False)
            else:
                df.to_csv(output_file, mode='a', header=False, index=False)
            print(f"     -> Saved {len(all_game_logs)} games for {name}")
            all_game_logs = []
        time.sleep(4.1)
    if headers_extracted:
        try:
            final_df = pd.read_csv(output_file)
            print(f"-> Completed {year}: {len(final_df)} total game logs saved to {output_file}")
        except:
            print(f"-> Error reading final file for {year}")
    else:
        print(f"-> No game logs found for {year}")
    time.sleep(10)
print("\n" + "="*80)
print("All game logs scraped successfully!")
print("="*80)
