import requests
from bs4 import BeautifulSoup, Comment
import pandas as pd
import time
import os

os.makedirs('./data', exist_ok=True)
os.makedirs('./data/rosters', exist_ok=True)

# years = [2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025]
years = [2020, 2021, 2022, 2023, 2024, 2025]

teams = ['crd', 'atl', 'rav', 'buf', 'car', 'chi', 'cin', 'cle', 'dal', 'den', 
         'det', 'gnb', 'htx', 'clt', 'jax', 'kan', 'sdg', 'ram', 'rai', 'mia', 
         'min', 'nwe', 'nor', 'nyg', 'nyj', 'phi', 'pit', 'sea', 'sfo', 'tam', 
         'oti', 'was']

all_rosters = []
for year in years:
    year_file = f'./data/rosters/rosters_{year}.csv'
    
    # Delete existing year file to start fresh
    if os.path.exists(year_file):
        os.remove(year_file)
    
    for team in teams:
        print(f"Scraping {team.upper()} roster for {year}...")
        url = f'https://www.pro-football-reference.com/teams/{team}/{year}_roster.htm'
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        try:
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code != 200:
                print(f"-> Failed to retrieve {team} {year}: Status {response.status_code}")
                continue
        except Exception as e:
            print(f"-> Error retrieving {team} {year}: {e}")
            continue
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Check for roster table in HTML comments (common for PFR)
        roster_table = None
        comments = soup.find_all(string=lambda text: isinstance(text, Comment))
        for comment in comments:
            if 'id="roster"' in comment:
                comment_soup = BeautifulSoup(comment, 'html.parser')
                roster_table = comment_soup.find('table', {'id': 'roster'})
                if roster_table:
                    break
        
        # If not in comments, try to find it normally
        if not roster_table:
            roster_table = soup.find('table', {'id': 'roster'})
        if not roster_table:
            print(f"-> No roster table found for {team} {year}")
            continue
        tbody = roster_table.find('tbody')
        if not tbody:
            continue
        # Get column names from first data row
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
                column_names.append(f'col_{i}')
        # Extract roster data
        year_team_roster = []
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
                    # Extract player name and URL
                    if col_name == 'player':
                        player_link = cell.find('a')
                        if player_link:
                            player_data['player_name'] = cell_text
                            player_data['player_url'] = player_link.get('href', '')
                        else:
                            player_data['player_name'] = cell_text
                            player_data['player_url'] = ''
                    # Extract college URLs (data-stat is 'college_id')
                    elif col_name == 'college_id':
                        college_links = cell.find_all('a')
                        if college_links:
                            player_data['college'] = cell_text
                            player_data['college_url'] = ','.join([link.get('href', '') for link in college_links])
                        else:
                            player_data['college'] = cell_text
                            player_data['college_url'] = ''
                    # Extract draft info
                    elif col_name == 'draft_info':
                        draft_link = cell.find('a')
                        if draft_link:
                            player_data['draft_info'] = cell_text
                            player_data['draft_url'] = draft_link.get('href', '')
                        else:
                            player_data['draft_info'] = cell_text
                            player_data['draft_url'] = ''
                    else:
                        player_data[col_name] = cell_text
            player_data['team'] = team
            player_data['season'] = year
            year_team_roster.append(player_data)
        print(f"-> Found {len(year_team_roster)} players")
        all_rosters.extend(year_team_roster)
        time.sleep(10)  # Be respectful to PFR servers - increased to avoid rate limiting
    # Save individual year file after completing all teams
    year_df = pd.DataFrame([r for r in all_rosters if r['season'] == year])
    if not year_df.empty:
        year_df.to_csv(f'./data/rosters/rosters_{year}.csv', index=False)
        print(f"=> Saved {year} rosters to ./data/rosters/rosters_{year}.csv")
# Combine all years
df = pd.DataFrame(all_rosters)
df = df.drop_duplicates(subset=['player_name', 'team', 'season'])
df = df.sort_values(['season', 'team', 'player_name'])
df.to_csv('./data/rosters.csv', index=False)
print(f"\nSaved {len(df)} total roster entries to rosters.csv")
