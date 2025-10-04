import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import os

os.makedirs('./data', exist_ok=True)
os.makedirs('./data/box-scores', exist_ok=True)

games_df = pd.read_csv('./data/games.csv')

years = [2020, 2021, 2022, 2023, 2024, 2025]

all_box_scores = []
for year in years:
    year_file = f'./data/box-scores/box_scores_{year}.csv'
    if os.path.exists(year_file):
        os.remove(year_file)
    print(f"Scraping box scores for {year}...")
    year_games = games_df[games_df['season'] == year]
    year_box_scores = []
    for idx, game in year_games.iterrows():
        pfr_id = game['pfr_boxscore_id']
        game_id = game['game_id']
        url = f'https://www.pro-football-reference.com/boxscores/{pfr_id}.htm'
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code == 404:
                print(f"  -> Game not found: {game_id}")
                continue
            soup = BeautifulSoup(response.content, 'html.parser')
            linescore_table = soup.find('table', class_='linescore')
            if linescore_table:
                rows = linescore_table.find_all('tr')[1:]
                for row in rows:
                    cols = row.find_all('td')
                    if len(cols) > 1:
                        team_name = cols[1].text.strip()
                        scores = {}
                        scores['game_id'] = game_id
                        scores['pfr_id'] = pfr_id
                        scores['team'] = team_name
                        scores['season'] = year
                        scores['week'] = game['week']
                        quarter_cols = cols[2:]
                        ot_score = ''
                        final_score = ''
                        for i, col in enumerate(quarter_cols):
                            score = col.text.strip()
                            if i < 4:
                                scores[f'q{i+1}'] = score if score else '0'
                            else:
                                header_row = linescore_table.find_all('tr')[0]
                                header_cols = header_row.find_all(['th', 'td'])
                                if len(header_cols) > i + 2:
                                    header_text = header_cols[i + 2].text.strip()
                                    if header_text.upper() == 'OT':
                                        ot_score = score if score else ''
                                    elif header_text.upper() == 'FINAL':
                                        final_score = score if score else '0'
                                    else:
                                        final_score = score if score else '0'
                        scores['ot'] = ot_score
                        scores['final'] = final_score
                        if not scores['final']:
                            total = 0
                            for q in ['q1', 'q2', 'q3', 'q4']:
                                if q in scores and scores[q]:
                                    try:
                                        total += int(scores[q])
                                    except:
                                        pass
                            if scores['ot']:
                                try:
                                    total += int(scores['ot'])
                                except:
                                    pass
                            scores['final'] = str(total)
                        year_box_scores.append(scores)
            print(f"  -> Scraped: {game_id}")
            time.sleep(4.1)
        except Exception as e:
            print(f"  -> Error scraping {game_id}: {e}")
            time.sleep(4.1)
            continue
    print(f"-> Found {len(year_box_scores)} box score entries for {year}")
    if year_box_scores:
        year_df = pd.DataFrame(year_box_scores)
        for col in ['q1', 'q2', 'q3', 'q4']:
            if col in year_df.columns:
                year_df[col] = year_df[col].fillna('0')
        if 'ot' not in year_df.columns:
            year_df['ot'] = ''
        else:
            year_df['ot'] = year_df['ot'].fillna('')
        year_df.to_csv(f'./data/box-scores/box_scores_{year}.csv', index=False)
        print(f"-> Saved box scores to ./data/box-scores/box_scores_{year}.csv")
        all_box_scores.extend(year_df.to_dict('records'))
    time.sleep(10)

if all_box_scores:
    df = pd.DataFrame(all_box_scores)
    for col in ['q1', 'q2', 'q3', 'q4']:
        if col in df.columns:
            df[col] = df[col].fillna('0')
    if 'ot' not in df.columns:
        df['ot'] = ''
    else:
        df['ot'] = df['ot'].fillna('')
    df = df.drop_duplicates(subset=['game_id', 'team'])
    df = df.sort_values(['season', 'week', 'game_id', 'team'])
    df.to_csv('./data/box_scores.csv', index=False)
    print(f"Saved {len(df)} total box score entries to box_scores.csv")
else:
    print("No box scores found")