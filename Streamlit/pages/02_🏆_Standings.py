import streamlit as st
import pandas as pd
import numpy as np
#import matplotlib.pyplot as plt

st.title('2023 NFL Season Division Standings')

# Load data
df_teams = st.session_state['df_teams']
df_games = st.session_state['df_games'] 
df_playerstats = st.session_state['df_playerstats']

# Filter the games to the 2023 season
games_2023 = df_games[df_games['season'] == 2023]

# Initialize dictionaries to store wins, losses, and ties for each team
team_wins = {team: 0 for team in df_teams['TeamID']}
team_losses = {team: 0 for team in df_teams['TeamID']}
team_ties = {team: 0 for team in df_teams['TeamID']}

# Iterate through each game to determine wins, losses, and ties
for _, game in games_2023.iterrows():
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
teams_performance_2023 = pd.DataFrame({
    'TeamID': team_wins.keys(),
    'Wins': team_wins.values(),
    'Losses': team_losses.values(),
    'Ties': team_ties.values()
})

# Merge with division information
teams_division = df_teams[['TeamID', 'Division']]
standings = pd.merge(teams_performance_2023, teams_division, on='TeamID')

# Group by division and sort
division_standings = standings.groupby('Division').apply(
    lambda x: x.sort_values(['Wins', 'Losses', 'Ties'], ascending=[False, True, True])
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