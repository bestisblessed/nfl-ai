import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import os

os.makedirs('./data', exist_ok=True)
os.makedirs('./data/games', exist_ok=True)

years = [2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025]
# years = list(range(2015, 2026))

all_games = []
for year in years:
    print(f"Scraping {year}...")
    url = f'https://www.pro-football-reference.com/years/{year}/games.htm'
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    response = requests.get(url, headers=headers, timeout=15)
    soup = BeautifulSoup(response.content, 'html.parser')
    games_table = soup.find('table', {'id': 'games'})
    tbody = games_table.find('tbody')
    year_games = []
    for tr in tbody.find_all('tr'):
        if tr.get('class') and 'thead' in tr.get('class'):
            continue
        week_th = tr.find('th', {'data-stat': 'week_num'})
        if not week_th:
            continue
        week_text = week_th.text.strip()
        if not week_text or week_text == 'Week':
            continue
        winner_td = tr.find('td', {'data-stat': 'winner'})
        loser_td = tr.find('td', {'data-stat': 'loser'})
        winner_link = winner_td.find('a')
        loser_link = loser_td.find('a')
        if winner_link and winner_link.get('href') and loser_link and loser_link.get('href'):
            winner_href = winner_link.get('href', '')
            loser_href = loser_link.get('href', '')
            if '/teams/' in winner_href and '/teams/' in loser_href:
                winner_abbr = winner_href.split('/teams/')[1].split('/')[0]
                loser_abbr = loser_href.split('/teams/')[1].split('/')[0]
                boxscore_td = tr.find('td', {'data-stat': 'boxscore_word'})
                boxscore_link = boxscore_td.find('a')
                if boxscore_link and boxscore_link.get('href'):
                    pfr_id = boxscore_link['href'].split('/')[-1].replace('.htm', '')
                    home_team_abbr = pfr_id[-3:]
                    if winner_abbr == home_team_abbr:
                        away_team, home_team = loser_abbr, winner_abbr
                    else:
                        away_team, home_team = winner_abbr, loser_abbr
                    postseason_map = {'WildCard': '19', 'Division': '20', 'ConfChamp': '21', 'SuperBowl': '22'}
                    if week_text in postseason_map:
                        week_formatted = postseason_map[week_text]
                    else:
                        week_formatted = f"{int(week_text):02d}"
                    game_id = f"{year}_{week_formatted}_{away_team}_{home_team}"
                    pts_win_td = tr.find('td', {'data-stat': 'pts_win'})
                    pts_lose_td = tr.find('td', {'data-stat': 'pts_lose'})
                    yards_win_td = tr.find('td', {'data-stat': 'yards_win'})
                    to_win_td = tr.find('td', {'data-stat': 'to_win'})
                    yards_lose_td = tr.find('td', {'data-stat': 'yards_lose'})
                    to_lose_td = tr.find('td', {'data-stat': 'to_lose'})
                    year_games.append({
                        'game_id': game_id,
                        'pfr_boxscore_id': pfr_id,
                        'season': year,
                        'week': week_formatted,
                        'away_team': away_team,
                        'home_team': home_team,
                        'winning_team': winner_abbr,
                        'PtsW': pts_win_td.text.strip() if pts_win_td else '',
                        'PtsL': pts_lose_td.text.strip() if pts_lose_td else '',
                        'YdsW': yards_win_td.text.strip() if yards_win_td else '',
                        'TOW': to_win_td.text.strip() if to_win_td else '',
                        'YdsL': yards_lose_td.text.strip() if yards_lose_td else '',
                        'TOL': to_lose_td.text.strip() if to_lose_td else ''
                    })
    
    print(f"-> Found {len(year_games)} games")
    
    # Save individual year file
    if year_games:
        year_df = pd.DataFrame(year_games)
        year_df.to_csv(f'./data/games/games_{year}.csv', index=False)
        print(f"-> Saved games to ./data/games/games_{year}.csv")
        all_games.extend(year_games)
    
    time.sleep(10)
    
df = pd.DataFrame(all_games)
df = df.drop_duplicates(subset=['pfr_boxscore_id'])
df = df.sort_values(['season', 'week', 'game_id'])
df.to_csv('./data/games.csv', index=False)
print(f"Saved {len(df)} total games to games.csv")