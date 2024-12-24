import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from datetime import datetime

def load_data():
    file_path = 'data/odds/nfl_odds_movements_circa.csv'
    df = pd.read_csv(file_path)
    
    # Get date input in YYYYMMDD format
    filter_date = input("Enter the date to filter (format: YYYYMMDD, e.g., '20241223'): ")
    
    # Convert YYYYMMDD to datetime and then to the format in the CSV
    try:
        date_obj = datetime.strptime(filter_date, '%Y%m%d')
        formatted_date = date_obj.strftime('%A,%B %dst').replace('1st', '1st').replace('2st', '2nd').replace('3st', '3rd').replace('4st', '4th').replace('5st', '5th').replace('6st', '6th').replace('7st', '7th').replace('8st', '8th').replace('9st', '9th').replace('0st', '0th')
        df = df[df['game_date'] == formatted_date]
    except ValueError:
        print(f"Invalid date format. Please use YYYYMMDD format.")
        return None
        
    if df.empty:
        print(f"No data found for the date: {formatted_date}")
        return None
        
    df['game_time_clean'] = df['game_time'].str.extract(r'(\d{1,2}:\d{2} [APM]{2})')
    df['game_date_clean'] = df['game_date'].str.replace(r'^\w+,\s*', '', regex=True)
    df['game_date_clean'] = df['game_date_clean'].str.replace(r'(st|nd|rd|th)', '', regex=True)
    df['game_date_with_year'] = df['game_date_clean'] + ', 2024'
    df['datetime'] = pd.to_datetime(df['game_date_with_year'] + ' ' + df['game_time_clean'], errors='coerce')
    
    problematic_rows = df[df['datetime'].isna()]
    if not problematic_rows.empty:
        print("Rows with NaT values in datetime column:")
        print(problematic_rows[['game_date', 'game_time', 'matchup']])
    
    df = df.dropna(subset=['datetime'])
    return df

def get_unique_matchups(df):
    return df['matchup'].unique()

def plot_odds_movement(df, matchup, pdf):
    matchup_data = df[df['matchup'] == matchup]
    if matchup_data.empty:
        print(f"No data found for matchup: {matchup}")
        return
    game_date = matchup_data['datetime'].iloc[0].strftime('%b %d %Y')
    time_increment = pd.to_timedelta(np.arange(0, len(matchup_data)) * 10, unit='m')
    matchup_data['datetime_simulated'] = matchup_data['datetime'] + time_increment
    for col in ['team1_odds_before', 'team1_odds_after', 'team2_odds_before', 'team2_odds_after']:
        matchup_data[col] = pd.to_numeric(matchup_data[col], errors='coerce')
    for col in ['team1_odds_before', 'team1_odds_after', 'team2_odds_before', 'team2_odds_after']:
        matchup_data[col].interpolate(inplace=True)
    min_spread = min(matchup_data['team1_odds_after'].min(), matchup_data['team2_odds_after'].min())
    max_spread = max(matchup_data['team1_odds_after'].max(), matchup_data['team2_odds_after'].max())
    plt.figure(figsize=(10, 6))
    plt.plot([matchup_data.iloc[0]['datetime_simulated']] + list(matchup_data['datetime_simulated'][1:]), 
             [matchup_data.iloc[0]['team1_odds_before']] + list(matchup_data['team1_odds_after'][1:]), 
             label=matchup_data.iloc[0]['team_1'], marker='o')
    plt.plot([matchup_data.iloc[0]['datetime_simulated']] + list(matchup_data['datetime_simulated'][1:]), 
             [matchup_data.iloc[0]['team2_odds_before']] + list(matchup_data['team2_odds_after'][1:]), 
             label=matchup_data.iloc[0]['team_2'], marker='x')
    plt.axhline(0, color='black', linewidth=0.8, linestyle='--', label='PK')
    plt.ylim(min_spread - 1, max_spread + 1)
    plt.title(f'{matchup} {game_date} - Team Odds Movement')
    plt.xlabel('Time')
    plt.ylabel('Spread')
    plt.xticks(rotation=45)
    plt.gcf().autofmt_xdate()  
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    pdf.savefig()
    plt.close()

def main():
    df = load_data()
    if df is None:
        print("No data available for the specified date. Exiting...")
        return
    
    matchups = get_unique_matchups(df)
    if not len(matchups):
        print("No matchups found for the specified date.")
        return
        
    with PdfPages('nfl_odds_movements.pdf') as pdf:
        for matchup in matchups:
            print(f"Generating plot for: {matchup}")
            plot_odds_movement(df, matchup, pdf)
    print("All plots have been generated and saved to 'nfl_odds_movements.pdf'")

if __name__ == "__main__":
    main()
