import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import sqlite3

### --- Title and Data --- ###
st.title('Betting Trends')
df_teams = pd.read_csv('./data/Teams.csv')
df_games = pd.read_csv('./data/Games.csv')
df_playerstats = pd.read_csv('./data/PlayerStats.csv')
db_path = './data/nfl.db'  # Adjust the path to your database file

### --- ATS Record (Overall, Home, Away) --- ###
st.divider()
st.header("ATS Record (Overall, Home, Away)")
st.write("##")

# Should save to csv file and analyze that way ? ****
# Function to determine the ATS result for a game using actual scores and spread
def ats_result(row, team):
    spread = float(row['home_spread']) if row['home_team'] == team else float(row['away_spread'])
    score_diff = row['home_score'] - row['away_score'] if row['home_team'] == team else row['away_score'] - row['home_score']
    if score_diff > spread:
        return 'Win'
    elif score_diff < spread:
        return 'Loss'
    else:
        return 'Push'
conn = sqlite3.connect(db_path)
teams = ['ARI', 'ATL', 'BAL', 'BUF', 'CAR', 'CHI', 'CIN', 'CLE', 'DAL', 'DEN', 'DET', 'GB', 
         'HOU', 'IND', 'JAX', 'KC', 'LA', 'LAC', 'LV', 'MIA', 'MIN', 'NE', 'NO', 'NYG', 
         'NYJ', 'PHI', 'PIT', 'SEA', 'SF', 'TB', 'TEN', 'WAS']
for team in teams:
    relevant_columns = ['home_team', 'away_team', 'home_score', 'away_score', 'home_spread', 'away_spread']
    team_games = pd.read_sql_query(
        f"SELECT * FROM Games WHERE (home_team = '{team}' OR away_team = '{team}') AND season = 2023", 
        conn
    )[relevant_columns]
    team_games['ATS_Result'] = team_games.apply(lambda row: ats_result(row, team), axis=1)
    overall_ats_record = team_games['ATS_Result'].value_counts()
    home_ats_record = team_games[team_games['home_team'] == team]['ATS_Result'].value_counts()
    away_ats_record = team_games[team_games['away_team'] == team]['ATS_Result'].value_counts()
    st.write(f"{team} ATS Record for 2023 Season:")
    st.write("Overall:", overall_ats_record)
    st.write("Home:", home_ats_record)
    st.write("Away:", away_ats_record)
    st.divider()
conn.close()
