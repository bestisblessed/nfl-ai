import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import os

os.makedirs('./data', exist_ok=True)
os.makedirs('./data/box-scores', exist_ok=True)

# First, we need to get the games data to have the PFR IDs
# Look in both current PFR data folder and parent data folder
if os.path.exists('./data/games.csv'):
    games_df = pd.read_csv('./data/games.csv')
elif os.path.exists('../data/games.csv'):
    games_df = pd.read_csv('../data/games.csv')
else:
    games_df = None

if games_df is None:
    print("Error: games.csv not found. Please run games-pfr.py first.")
    exit(1)

years = [2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025]

all_box_scores = []
for year in years:
    print(f"Scraping box scores for {year}...")
    
    # Filter games for this year
    year_games = games_df[games_df['season'] == year]
    year_box_scores = []
    
    for idx, game in year_games.iterrows():
        pfr_id = game['pfr']
        game_id = game['game_id']
        url = f'https://www.pro-football-reference.com/boxscores/{pfr_id}.htm'
        
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            response = requests.get(url, headers=headers, timeout=15)
            
            if response.status_code == 404:
                print(f"  -> Game not found: {game_id}")
                continue
                
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find the linescore table
            linescore_table = soup.find('table', class_='linescore')
            
            if linescore_table:
                rows = linescore_table.find_all('tr')[1:]  # Skip header row
                
                for row in rows:
                    cols = row.find_all('td')
                    if len(cols) > 1:  # Make sure we have data
                        team_name = cols[1].text.strip()
                        
                        # Extract scores for each quarter
                        scores = {}
                        scores['game_id'] = game_id
                        scores['pfr_id'] = pfr_id
                        scores['team'] = team_name
                        scores['season'] = year
                        scores['week'] = game['week']
                        
                        # Quarter scores start from column 2
                        quarter_cols = cols[2:]
                        for i, col in enumerate(quarter_cols):
                            score = col.text.strip()
                            if i < 4:  # Regular quarters
                                scores[f'q{i+1}'] = score if score else '0'
                            elif i == 4:  # OT or Final
                                # Check if this is OT or Final
                                header_row = linescore_table.find_all('tr')[0]
                                header_cols = header_row.find_all(['th', 'td'])
                                if len(header_cols) > i + 2:
                                    header_text = header_cols[i + 2].text.strip()
                                    if header_text.upper() == 'OT':
                                        scores['ot'] = score if score else ''
                                    elif header_text.upper() == 'FINAL':
                                        scores['final'] = score if score else '0'
                                    else:
                                        scores['final'] = score if score else '0'
                            elif i == 5:  # Final (if OT existed)
                                scores['final'] = score if score else '0'
                        
                        # Ensure we have a final score
                        if 'final' not in scores:
                            # Calculate from quarters if not present
                            total = 0
                            for q in ['q1', 'q2', 'q3', 'q4']:
                                if q in scores and scores[q]:
                                    try:
                                        total += int(scores[q])
                                    except:
                                        pass
                            if 'ot' in scores and scores['ot']:
                                try:
                                    total += int(scores['ot'])
                                except:
                                    pass
                            scores['final'] = str(total)
                        
                        year_box_scores.append(scores)
                        
            print(f"  -> Scraped: {game_id}")
            time.sleep(3)  # Be respectful to the server
            
        except Exception as e:
            print(f"  -> Error scraping {game_id}: {e}")
            continue
    
    print(f"-> Found {len(year_box_scores)} box score entries for {year}")
    
    # Save individual year file
    if year_box_scores:
        year_df = pd.DataFrame(year_box_scores)
        # Ensure column order
        column_order = ['game_id', 'pfr_id', 'season', 'week', 'team', 
                       'q1', 'q2', 'q3', 'q4', 'ot', 'final']
        # Only include columns that exist
        columns_to_use = [col for col in column_order if col in year_df.columns]
        year_df = year_df[columns_to_use]
        
        # Fill NaN values appropriately
        for col in ['q1', 'q2', 'q3', 'q4']:
            if col in year_df.columns:
                year_df[col] = year_df[col].fillna('0')
        if 'ot' in year_df.columns:
            year_df['ot'] = year_df['ot'].fillna('')
        
        year_df.to_csv(f'./data/box-scores/box_scores_{year}.csv', index=False)
        print(f"-> Saved box scores to ./data/box-scores/box_scores_{year}.csv")
        all_box_scores.extend(year_box_scores)
    
    time.sleep(10)

# Combine all years
if all_box_scores:
    df = pd.DataFrame(all_box_scores)
    
    # Ensure column order for final output
    column_order = ['game_id', 'pfr_id', 'season', 'week', 'team', 
                   'q1', 'q2', 'q3', 'q4', 'ot', 'final']
    columns_to_use = [col for col in column_order if col in df.columns]
    df = df[columns_to_use]
    
    # Fill NaN values
    for col in ['q1', 'q2', 'q3', 'q4']:
        if col in df.columns:
            df[col] = df[col].fillna('0')
    if 'ot' in df.columns:
        df['ot'] = df['ot'].fillna('')
    
    df = df.drop_duplicates(subset=['game_id', 'team'])
    df = df.sort_values(['season', 'week', 'game_id', 'team'])
    df.to_csv('./data/box_scores.csv', index=False)
    print(f"Saved {len(df)} total box score entries to box_scores.csv")
else:
    print("No box scores found")