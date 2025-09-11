import streamlit as st
import pandas as pd
import os
import json
import re
from streamlit_modal import Modal
import matplotlib.pyplot as plt

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Load data files directly
csv_file_path_odds = os.path.join(BASE_DIR, 'data/odds/nfl_odds_movements.csv')
csv_file_path_circa = os.path.join(BASE_DIR, 'data/odds/nfl_odds_movements_circa.csv')

try:
    df_nfl_odds_movements = pd.read_csv(csv_file_path_odds)
except FileNotFoundError:
    st.error(f"File not found: {csv_file_path_odds}. Please ensure the file exists.")
    df_nfl_odds_movements = pd.DataFrame()

try:
    df_nfl_odds_movements_circa = pd.read_csv(csv_file_path_circa)
except FileNotFoundError:
    st.error(f"File not found: {csv_file_path_circa}. Please ensure the file exists.")
    df_nfl_odds_movements_circa = pd.DataFrame()

st.title('Odds Dashboard')
st.divider()
# BLACKLIST_TEAMS = ["Minnesota Vikings", "Los Angeles Rams"]
# st.write(f"*Blacklisted Teams:* {', '.join(BLACKLIST_TEAMS)}")
def load_odds_movements():
    if df_nfl_odds_movements.empty:
        st.error("Data not loaded. Please ensure the data is loaded in Home.py.")
        return pd.DataFrame()  
    df_nfl_odds_movements['game_date'] = df_nfl_odds_movements['game_date'].str.replace(' ', '').str.strip().str.lower()
    df_nfl_odds_movements['game_time'] = df_nfl_odds_movements['game_time'].str.replace('\n', ' ').str.replace(r'\s+', ' ', regex=True).str.strip().str.lower()
    df_nfl_odds_movements['matchup'] = df_nfl_odds_movements['matchup'].str.replace(r'\s+', ' ', regex=True).str.strip().str.lower()
    sportsbooks_to_include = [
        'Circa', 'Westgate', 'South Point', 'Wynn', 'Caesars', 'BetMGM', 'DK'
    ]
    filtered_odds = df_nfl_odds_movements[df_nfl_odds_movements['sportsbook'].isin(sportsbooks_to_include)].copy()
    return filtered_odds
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
                if '  ' in teams:
                    teams_list = [team.strip() for team in teams.split('  ') if team.strip()]
                else:
                    teams_list = [team.strip() for team in re.split(r'\s+|,', teams) if team.strip()]
                # if len(teams_list) != 2 or any(team in teams_list for team in BLACKLIST_TEAMS):
                if len(teams_list) != 2:  # or any(team in teams_list for team in BLACKLIST_TEAMS):
                    continue  
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
df_nfl_odds_movements = load_odds_movements()
games_data = load_games_data()
games_df = pd.DataFrame(games_data)

# Load upcoming games and filter to only show those matchups
upcoming_matchups = []  # Initialize empty list
try:
    df_upcoming_games = pd.read_csv(os.path.join(BASE_DIR, 'upcoming_games.csv'))
    
    # Team abbreviation to full name mapping
    team_mapping = {
        'GB': 'Green Bay Packers', 'WAS': 'Washington Commanders',
        'DAL': 'Dallas Cowboys', 'NYG': 'New York Giants',
        'PIT': 'Pittsburgh Steelers', 'SEA': 'Seattle Seahawks',
        'TEN': 'Tennessee Titans', 'LAR': 'Los Angeles Rams',
        'NYJ': 'New York Jets', 'BUF': 'Buffalo Bills',
        'MIA': 'Miami Dolphins', 'NE': 'New England Patriots',
        'CIN': 'Cincinnati Bengals', 'JAX': 'Jacksonville Jaguars',
        'NO': 'New Orleans Saints', 'SF': 'San Francisco 49ers',
        'BAL': 'Baltimore Ravens', 'CLE': 'Cleveland Browns',
        'DET': 'Detroit Lions', 'CHI': 'Chicago Bears',
        'IND': 'Indianapolis Colts', 'DEN': 'Denver Broncos',
        'ARI': 'Arizona Cardinals', 'CAR': 'Carolina Panthers',
        'KC': 'Kansas City Chiefs', 'PHI': 'Philadelphia Eagles',
        'MIN': 'Minnesota Vikings', 'ATL': 'Atlanta Falcons',
        'HOU': 'Houston Texans', 'TB': 'Tampa Bay Buccaneers',
        'LVR': 'Las Vegas Raiders', 'LAC': 'Los Angeles Chargers'
    }
    
    # Create matchup strings from upcoming games (format: "Team1 vs Team2")
    for _, row in df_upcoming_games.iterrows():
        away_team = team_mapping.get(row['away_team'], row['away_team'])
        home_team = team_mapping.get(row['home_team'], row['home_team'])
        matchup = f"{away_team} vs {home_team}".lower()
        upcoming_matchups.append(matchup)
    
    # Filter games_df to only include upcoming games
    if not games_df.empty:
        games_df = games_df[games_df['matchup'].isin(upcoming_matchups)]
    
except FileNotFoundError:
    st.error("upcoming_games.csv not found. Showing all games.")
except Exception as e:
    st.error(f"Error loading upcoming games: {str(e)}")

if not games_df.empty:
    games_with_sufficient_data = (
        games_df.groupby('matchup')
        .filter(lambda x: len(df_nfl_odds_movements[df_nfl_odds_movements['matchup'] == x.name]) >= 3)
    )
else:
    games_with_sufficient_data = []
for _, game in games_with_sufficient_data.iterrows():
    st.markdown(f"<h2 style='font-weight: bold; color: #512D6D; text-shadow: -1px -1px 0 #C5B783, 1px -1px 0 #C5B783, -1px 1px 0 #C5B783, 1px 1px 0 #C5B783;'>{game['teams'][0]} vs {game['teams'][1]}</h2>", unsafe_allow_html=True)
    
    # Format date properly - "Sun, September 14th"
    formatted_date = game['game_date'].replace(',', ', ').replace('september', 'September ').replace('sun', 'Sun').replace('mon', 'Mon').replace('tue', 'Tue').replace('wed', 'Wed').replace('thu', 'Thu').replace('fri', 'Fri').replace('sat', 'Sat')
    
    # Format time properly
    formatted_time = game['time'].replace('splits', '').strip().replace('pm', 'PM').replace('am', 'AM')
    
    # Game Date - half size of title
    st.markdown(f"<p style='font-size: 18px; margin: 5px 0;'>📅 <strong>{formatted_date}</strong></p>", unsafe_allow_html=True)
    
    # Game Time - bigger size
    st.markdown(f"<p style='font-size: 16px; margin: 5px 0;'>🕐 <strong>{formatted_time}</strong></p>", unsafe_allow_html=True)
    st.write("")
    df = pd.DataFrame({
        "Team": [game['teams'][0], game['teams'][1]],
        "Spread": [game['spread'][0], game['spread'][1]],
        "Moneyline": [game['moneyline'][0], game['moneyline'][1]],
        "Total": [game['total'][0], game['total'][1]]
    })
    st.table(df.set_index('Team'))
    st.divider()
    for team in game['teams']:
        modal = Modal(f"Odds Movement for {team}", key=f"modal_{team}_{game['game_date']}_{game['time']}")
        if st.button(f"See odds movement for {team}", key=f"button_{team}_{game['day_and_matchup_column_name']}_{game['time']}"):
            modal.open()
        if modal.is_open():
            with modal.container():
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
                    sportsbooks = relevant_odds_movements['sportsbook'].unique().tolist()
                    default_index = sportsbooks.index('Circa') if 'Circa' in sportsbooks else 0
                    selected_sportsbook = st.selectbox("Select Sportsbook", sportsbooks, index=default_index, key=f"sb_{team}")
                    filtered_data = relevant_odds_movements[relevant_odds_movements['sportsbook'] == selected_sportsbook]
                    st.dataframe(filtered_data[['timestamp', 'sportsbook', 'odds_before', 'odds_after']], use_container_width=True)
                else:
                    st.write("No odds movement data available for this game.")
    st.divider()
# Filter odds data to only include upcoming games (using the same logic as above)
if upcoming_matchups:
    # Create a more flexible matching approach for Circa data
    def normalize_matchup(matchup):
        """Normalize matchup string for comparison"""
        return matchup.lower().replace('  ', ' ').strip()
    
    # Normalize both the upcoming matchups and the Circa data
    upcoming_matchups_normalized = [normalize_matchup(m) for m in upcoming_matchups]
    circa_matchups_normalized = df_nfl_odds_movements_circa['matchup'].apply(normalize_matchup)
    
    # Filter Circa data based on normalized matchups
    upcoming_week_games = df_nfl_odds_movements_circa[
        circa_matchups_normalized.isin(upcoming_matchups_normalized)
    ]
    
else:
    upcoming_week_games = df_nfl_odds_movements_circa

# Get matchups with sufficient data from upcoming week games
filtered_matchups = (
    upcoming_week_games.groupby('matchup')
    .filter(lambda x: len(x) >= 3)['matchup']
    .unique()
)
if len(filtered_matchups) > 0:
    selected_matchup = st.selectbox("Select Matchup", filtered_matchups)
else:
    st.warning("No games with sufficient odds movement data found.")
    selected_matchup = None
if selected_matchup:
    selected_data = upcoming_week_games[upcoming_week_games['matchup'] == selected_matchup].copy()
    # Clean and convert odds data, filtering out invalid entries
    # Replace 'PK' with 0 (Pick'em is valid)
    selected_data.loc[:, 'team1_odds_before'] = selected_data['team1_odds_before'].replace('PK', 0)
    selected_data.loc[:, 'team2_odds_before'] = selected_data['team2_odds_before'].replace('PK', 0)

    # Convert to numeric, coercing errors to NaN
    selected_data.loc[:, 'team1_odds_before'] = pd.to_numeric(selected_data['team1_odds_before'], errors='coerce')
    selected_data.loc[:, 'team2_odds_before'] = pd.to_numeric(selected_data['team2_odds_before'], errors='coerce')

    # Filter out rows where either team's odds are invalid (NaN)
    selected_data = selected_data.dropna(subset=['team1_odds_before', 'team2_odds_before'])
    # Convert time column with error handling
    try:
        selected_data.loc[:, 'time_before'] = pd.to_datetime(selected_data['time_before'], format='%b %d %I:%M%p')
    except:
        # Fallback: try different datetime formats or use index as time
        try:
            selected_data.loc[:, 'time_before'] = pd.to_datetime(selected_data['time_before'], errors='coerce')
        except:
            selected_data.loc[:, 'time_before'] = pd.date_range(start='2024-01-01', periods=len(selected_data), freq='H')
    # Create the plot with error handling
    try:
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(8, 4))
        
        # Check if we have valid data to plot after filtering
        if len(selected_data) > 0 and not selected_data['time_before'].isna().all():
            ax.plot(selected_data['time_before'], selected_data['team1_odds_before'], label=selected_matchup.split(' vs ')[0])
            ax.plot(selected_data['time_before'], selected_data['team2_odds_before'], label=selected_matchup.split(' vs ')[1])
            ax.set_title(f'Odds Movement: {selected_matchup}')
            ax.set_xlabel('Time of Odds Change')
            ax.set_ylabel('Odds')
            plt.xticks(rotation=45)
            plt.legend()
            plt.grid(True)
            st.pyplot(fig, use_container_width=False)
        else:
            st.warning("No valid odds data available for plotting this matchup. Some data points may have been filtered out due to invalid odds values (like '-').")
    except Exception as e:
        st.error(f"Error creating plot: {str(e)}")
        st.write("Raw data for debugging:")
        st.dataframe(selected_data)
st.divider()
st.subheader("Archive")
archive_options = ["2022 Season", "2021 Season", "2020 Season", "Older Seasons"]
selected_archive = st.selectbox("Select Archive", options=archive_options)
