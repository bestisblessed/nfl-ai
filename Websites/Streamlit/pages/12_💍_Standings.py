import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# Page configuration
st.set_page_config(
    page_title="💍 NFL Standings",
    page_icon="💍",
    layout="centered"
)

# - add dropdowns for each division
# - add team logo pictures

st.markdown(f"""
    <div style='text-align: center;'>
        <div style='font-size: 3.1rem; font-weight: 800; padding-bottom: 0.5rem;'>
            NFL Standings
        </div>
        <div style='color: #7f8c8d; font-size: 1rem; margin-top: 0; line-height: 1.2;'>
            Division rankings and team performance statistics
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

# Load data using cached function
@st.cache_data(show_spinner=False)
def load_data():
    """Load all required CSV files for Standings"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    try:
        df_teams = pd.read_csv(os.path.join(current_dir, '../data', 'Teams.csv'))
        df_games = pd.read_csv(os.path.join(current_dir, '../data', 'Games.csv'))
        df_playerstats = pd.read_csv(os.path.join(current_dir, '../data', 'PlayerStats.csv'))
        
        return df_teams, df_games, df_playerstats
    except FileNotFoundError as e:
        st.error(f"Error loading data files: {e}")
        st.stop()

# Load all data
df_teams, df_games, df_playerstats = load_data()

# Season selector
selected_season = st.selectbox("Select Season:", [2025, 2024], index=0)

# Filter the games to the selected season
# games_2023 = df_games[df_games['season'] == 2023]
games_selected = df_games[(df_games['season'] == selected_season) & (df_games['week'].between(1, 18))]

# Filter out games that haven't been played yet (where scores are null or 0)
games_selected = games_selected[
    (games_selected['home_score'].notna()) & 
    (games_selected['away_score'].notna()) &
    (games_selected['home_score'] > 0) & 
    (games_selected['away_score'] > 0)
]

# Initialize dictionaries to store wins, losses, and ties for each team
team_wins = {team: 0 for team in df_teams['TeamID']}
team_losses = {team: 0 for team in df_teams['TeamID']}
team_ties = {team: 0 for team in df_teams['TeamID']}

# Iterate through each game to determine wins, losses, and ties
for _, game in games_selected.iterrows():
    away_team = game['away_team']
    home_team = game['home_team']
    away_score = game['away_score']
    home_score = game['home_score']

    # Determine the winner, loser, or if it's a tie
    if away_score > home_score:
        team_wins[away_team] += 1
        team_losses[home_team] += 1
    elif home_score > away_score:
        team_wins[home_team] += 1
        team_losses[away_team] += 1
    else:  # This is a tie
        team_ties[away_team] += 1
        team_ties[home_team] += 1

# Combine wins, losses, and ties into a single DataFrame
teams_performance_selected = pd.DataFrame({
    'TeamID': team_wins.keys(),
    'Wins': team_wins.values(),
    'Losses': team_losses.values(),
    'Ties': team_ties.values()
})

# Merge with division information
teams_division = df_teams[['TeamID', 'Division']]
standings = pd.merge(teams_performance_selected, teams_division, on='TeamID')

# Group by division and sort - using sort_values instead of apply to avoid deprecation warning
division_standings = standings.sort_values(
    by=['Division', 'Wins', 'Losses', 'Ties'], 
    ascending=[True, False, True, True]
).reset_index(drop=True)

# Display each division's standings with styling, two per row
divisions = division_standings['Division'].unique()
for i, division in enumerate(divisions):
    if i % 2 == 0:
        cols = st.columns(2)  # Create two columns at the start of each row

    group = division_standings[division_standings['Division'] == division]
    with cols[i % 2]:
        st.subheader(division)
        styled_group = group.style.highlight_max(subset=['Wins'], color='lightgreen', axis=0)
        st.table(styled_group)