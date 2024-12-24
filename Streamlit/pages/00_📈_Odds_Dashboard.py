import streamlit as st
import pandas as pd
import os
import json
import re
from streamlit_modal import Modal
import matplotlib.pyplot as plt

st.title('Odds Dashboard')
# df_nfl_odds_movements = st.session_state['df_nfl_odds_movements']
# df_nfl_odds_movements = df_nfl_odds_movements
df_nfl_odds_movements = st.session_state.get('df_nfl_odds_movements', pd.DataFrame())
df_nfl_odds_movements_circa = st.session_state.get('df_nfl_odds_movements_circa', pd.DataFrame())
st.divider()

### Load NFL odds movements ###
def load_odds_movements():
    # Access the data from session state
    # df_nfl_odds_movements = st.session_state.get('df_nfl_odds_movements', pd.DataFrame())

    # Check if the DataFrame is empty, which means the data wasn't loaded
    if df_nfl_odds_movements.empty:
        st.error("Data not loaded. Please ensure the data is loaded in Home.py.")
        return pd.DataFrame()  # Return an empty DataFrame if data is not available

    # Process the data as before
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

### Display game information and odds ###
df_nfl_odds_movements = load_odds_movements()
games_data = load_games_data()
for game in games_data:
    # st.subheader(game['day_and_matchup_column_name'])
    # st.markdown(game['day_and_matchup_column_name'])
    # st.markdown(f"<h2 style='color: purple; font-size: 24px; font-weight: bold;'>{game['day_and_matchup_column_name']}</h2>", unsafe_allow_html=True)
    st.markdown(f"<h3 style='font-weight: bold; color: #512D6D; text-shadow: -1px -1px 0 #C5B783, 1px -1px 0 #C5B783, -1px 1px 0 #C5B783, 1px 1px 0 #C5B783;'> {game['day_and_matchup_column_name']} </h3>", unsafe_allow_html=True)
    st.text(f"Game Time: {game['time'].replace('splits', '').strip()}")
    # st.markdown(f"<h5 style='font-weight: bold; color: #512D6D; text-shadow: -1px -1px 0 #C5B783, 1px -1px 0 #C5B783, -1px 1px 0 #C5B783, 1px 1px 0 #C5B783;'>Game Time: {game['time'].replace('splits', '').strip()}</h5>", unsafe_allow_html=True)
    df = pd.DataFrame({
        "Team": [game['teams'][0], game['teams'][1]],
        "Spread": [game['spread'][0], game['spread'][1]],
        "Moneyline": [game['moneyline'][0], game['moneyline'][1]],
        "Total": [game['total'][0], game['total'][1]]
    })
    st.table(df)
    # st.dataframe(df, use_container_width=True)

    ### Buttons and modal for odds movement ###
    for team in game['teams']:
        modal = Modal(f"Odds Movement for {team}", key=f"modal_{team}_{game['game_date']}")
        # Adding a unique key to each button using team name and game date as part of the key
        if st.button(f"See odds movement for {team}", key=f"button_{team}_{game['day_and_matchup_column_name']}"):
            modal.open()

        if modal.is_open():
            with modal.container():
                # st.subheader(f"Odds Movement for {team}")
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
                    st.dataframe(filtered_data[['timestamp', 'sportsbook', 'odds_before', 'odds_after']], use_container_width=True)
                else:
                    st.write("No odds movement data available for this game.")

            
                    
    st.divider()



### Line Graph ###
# file_path_circa = 'data/nfl_odds_movements_circa.csv'  # Update with your file path
# nfl_odds_data_circa = pd.read_csv(file_path_circa)
# browns_raiders_data = nfl_odds_data_circa[nfl_odds_data_circa['matchup'] == 'Cleveland Browns vs  Las Vegas Raiders'] # Filter data for the two matchups
# saints_falcons_data = nfl_odds_data_circa[nfl_odds_data_circa['matchup'] == 'New Orleans Saints vs  Atlanta Falcons']
# browns_raiders_data['team1_odds_before'] = browns_raiders_data['team1_odds_before'].replace('PK', 0).astype(float) # Replace 'PK' with 0 for plotting purposes and convert odds to float
# browns_raiders_data['team2_odds_before'] = browns_raiders_data['team2_odds_before'].replace('PK', 0).astype(float)
# saints_falcons_data['team1_odds_before'] = saints_falcons_data['team1_odds_before'].replace('PK', 0).astype(float)
# saints_falcons_data['team2_odds_before'] = saints_falcons_data['team2_odds_before'].replace('PK', 0).astype(float)
# browns_raiders_data['time_before'] = pd.to_datetime(browns_raiders_data['time_before'], format='%b %d %I:%M%p') # Convert time_before column to datetime for proper plotting
# saints_falcons_data['time_before'] = pd.to_datetime(saints_falcons_data['time_before'], format='%b %d %I:%M%p')
# plt.figure(figsize=(10, 6)) # Create the line graph for Cleveland Browns vs Las Vegas Raiders
# plt.plot(browns_raiders_data['time_before'], browns_raiders_data['team1_odds_before'], label='Cleveland Browns', marker='o')
# plt.plot(browns_raiders_data['time_before'], browns_raiders_data['team2_odds_before'], label='Las Vegas Raiders', marker='o')
# plt.title('Odds Movement: Cleveland Browns vs Las Vegas Raiders')
# plt.xlabel('Time of Odds Change')
# plt.ylabel('Odds')
# plt.xticks(rotation=45)
# plt.legend()
# plt.grid(True)
# st.pyplot(plt)
# plt.figure(figsize=(10, 6)) # Create the line graph for New Orleans Saints vs Atlanta Falcons
# plt.plot(saints_falcons_data['time_before'], saints_falcons_data['team1_odds_before'], label='New Orleans Saints', marker='o')
# plt.plot(saints_falcons_data['time_before'], saints_falcons_data['team2_odds_before'], label='Atlanta Falcons', marker='o')
# plt.title('Odds Movement: New Orleans Saints vs Atlanta Falcons')
# plt.xlabel('Time of Odds Change')
# plt.ylabel('Odds')
# plt.xticks(rotation=45)
# plt.legend()
# plt.grid(True)
# st.pyplot(plt)
# file_path_circa = 'data/odds/nfl_odds_movements_circa.csv'
# nfl_odds_data_circa = pd.read_csv(file_path_circa)
# df_nfl_odds_movements_circa = st.session_state.get('df_nfl_odds_movements_circa', pd.DataFrame())
unique_matchups = df_nfl_odds_movements_circa['matchup'].unique()
selected_matchup = st.selectbox("Select Matchup", unique_matchups)
selected_data = df_nfl_odds_movements_circa[df_nfl_odds_movements_circa['matchup'] == selected_matchup].copy()
selected_data.loc[:, 'team1_odds_before'] = selected_data['team1_odds_before'].replace('PK', 0).astype(float)
selected_data.loc[:, 'team2_odds_before'] = selected_data['team2_odds_before'].replace('PK', 0).astype(float)
selected_data.loc[:, 'time_before'] = pd.to_datetime(selected_data['time_before'], format='%b %d %I:%M%p')
plt.figure(figsize=(10, 6))
# plt.plot(selected_data['time_before'], selected_data['team1_odds_before'], label=selected_matchup.split(' vs ')[0], marker='o')
# plt.plot(selected_data['time_before'], selected_data['team2_odds_before'], label=selected_matchup.split(' vs ')[1], marker='o')
plt.plot(selected_data['time_before'], selected_data['team1_odds_before'], label=selected_matchup.split(' vs ')[0])
plt.plot(selected_data['time_before'], selected_data['team2_odds_before'], label=selected_matchup.split(' vs ')[1])
plt.title(f'Odds Movement: {selected_matchup}')
plt.xlabel('Time of Odds Change')
plt.ylabel('Odds')
plt.xticks(rotation=45)
plt.legend()
plt.grid(True)
st.pyplot(plt)



### Archive (Past Games) ###
st.divider()
st.subheader("Archive")
archive_options = ["2022 Season", "2021 Season", "2020 Season", "Older Seasons"]
selected_archive = st.selectbox("Select Archive", options=archive_options)
