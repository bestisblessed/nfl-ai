### Libraries ###
import streamlit as st
import pandas as pd
import os
import json
import re
from streamlit_modal import Modal

st.title('Odds Dashboard')
# df_nfl_odds_movements = st.session_state['df_nfl_odds_movements']
# df_nfl_odds_movements = df_nfl_odds_movements

### Load NFL odds movements ###
def load_odds_movements():
    df_nfl_odds_movements = pd.read_csv('data/odds/nfl_odds_movements.csv')
    df_nfl_odds_movements['game_date'] = df_nfl_odds_movements['game_date'].str.replace(' ', '').str.strip().str.lower()
    df_nfl_odds_movements['game_time'] = df_nfl_odds_movements['game_time'].str.replace('\n', ' ').str.replace(r'\s+', ' ', regex=True).str.strip().str.lower()
    df_nfl_odds_movements['matchup'] = df_nfl_odds_movements['matchup'].str.replace(r'\s+', ' ', regex=True).str.strip().str.lower()
    sportsbooks_to_include = [
        'Circa', 'Westgate', 'South Point', 'Wynn', 'Caesars', 'BetMGM', 'DK'
    ]
    filtered_odds = df_nfl_odds_movements[df_nfl_odds_movements['sportsbook'].isin(sportsbooks_to_include)].copy()
    return filtered_odds

### Load NFL games data from JSON files ###
def load_games_data():
    games_data = []
    data_dir = os.path.join(os.path.dirname(__file__), '../data/odds/')
    json_files = sorted([f for f in os.listdir(data_dir) if f.endswith(".json") and f.startswith('nfl')], reverse=True)
    most_recent_file = json_files[0] if json_files else None

    if most_recent_file:
        filepath = os.path.join(data_dir, most_recent_file)
        with open(filepath) as f:
            data = json.load(f)
            for game in data:
                game_time = game['Time']
                day_and_matchup_key = list(game.keys())[1]
                day_and_matchup_value = game[day_and_matchup_key]
                day_and_matchup_column_name = list(game.keys())[1].replace(',', ', ')
                game_date = day_and_matchup_key.strip()
                teams = day_and_matchup_value.replace('\n', ' ').strip()
                teams_list = [team.strip() for team in teams.split('  ')]
                game_date = game_date.replace(' ', '').strip().lower()
                game_time = re.sub(r'\s+', ' ', game_time.replace('\n', ' ')).strip().lower()
                matchup = re.sub(r'\s+', ' ', ' vs '.join(teams_list)).strip().lower()
                circa_spread = game.get("Circa", "").replace('\n', ' ').strip().split(' ')
                spread_favorite, spread_underdog = ("N/A", "N/A") if len(circa_spread) != 4 else (f"{circa_spread[0]} {circa_spread[1]}", f"{circa_spread[2]} {circa_spread[3]}")
                games_data.append({
                    'time': game_time,
                    'day_and_matchup_column_name': day_and_matchup_column_name,
                    'game_date': game_date,
                    'matchup': matchup,
                    'teams': teams_list,
                    'spread': [spread_favorite, spread_underdog],
                    'moneyline': ['N/A', 'N/A'],
                    'total': ['N/A', 'N/A']
                })
    else:
        st.warning("No JSON files found in the data directory.")
    return games_data

### Load the data ###
df_nfl_odds_movements = load_odds_movements()
games_data = load_games_data()

### Streamlit layout ###
st.title("NFL Odds Dashboard")

### Display game information and odds ###
for game in games_data:
    st.subheader(game['day_and_matchup_column_name'])
    st.text(f"Game Time: {game['time'].replace('splits', '').strip()}")
    df = pd.DataFrame({
        "Team": [game['teams'][0], game['teams'][1]],
        "Spread": [game['spread'][0], game['spread'][1]],
        "Moneyline": [game['moneyline'][0], game['moneyline'][1]],
        "Total": [game['total'][0], game['total'][1]]
    })
    st.table(df)

    ### Buttons and modal for odds movement ###
    for team in game['teams']:
        modal = Modal(f"Odds Movement for {team}", key=f"modal_{team}")
        if st.button(f"See odds movement for {team}"):
            modal.open()

        if modal.is_open():
            with modal.container():
                st.subheader(f"Odds Movement for {team}")
                game_date_clean = game['game_date'].replace(' ', '').strip().lower()
                game_time_clean = game['time'].strip().lower()
                matchup_clean = game['matchup'].strip().lower()
                relevant_odds_movements = df_nfl_odds_movements.loc[
                    (df_nfl_odds_movements['game_date'] == game_date_clean) &
                    (df_nfl_odds_movements['game_time'] == game_time_clean) &
                    (df_nfl_odds_movements['matchup'] == matchup_clean)
                ].copy()

                if not relevant_odds_movements.empty:
                    if 'file2' in relevant_odds_movements.columns:
                        relevant_odds_movements['timestamp'] = relevant_odds_movements['file2'].apply(
                            lambda x: '_'.join(x.split('_')[3:5]).replace('.json', '')
                        )
                        relevant_odds_movements['timestamp'] = pd.to_datetime(
                            relevant_odds_movements['timestamp'], format='%Y%m%d_%H%M'
                        ).dt.strftime('%-m/%d %-I:%M%p').str.lower()
                    
                    ### Select sportsbook to view odds ###
                    sportsbooks = relevant_odds_movements['sportsbook'].unique().tolist()
                    default_index = sportsbooks.index('Circa') if 'Circa' in sportsbooks else 0
                    selected_sportsbook = st.selectbox("Select Sportsbook", sportsbooks, index=default_index, key=f"sb_{team}")
                    filtered_data = relevant_odds_movements[relevant_odds_movements['sportsbook'] == selected_sportsbook]
                    st.table(filtered_data[['timestamp', 'sportsbook', 'odds_before', 'odds_after']])
                else:
                    st.write("No odds movement data available for this game.")
