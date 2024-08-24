import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import sqlite3

### --- Title and Data --- ###
st.title('General Trends')
# df_teams = pd.read_csv('./data/Teams.csv')
# df_games = pd.read_csv('./data/Games.csv')
# df_playerstats = pd.read_csv('./data/PlayerStats.csv')
df_teams = st.session_state['df_teams']
df_games = st.session_state['df_games'] 
df_playerstats = st.session_state['df_playerstats']
df_team_game_logs = st.session_state['df_team_game_logs']
dataframes = [df_teams, df_games, df_playerstats, df_team_game_logs]

### --- Home vs Away Record 2023 --- ###
st.divider()
st.header("Home vs Away Record 2023 (Reg Season)")
st.write(" ")

games_2023 = df_games[(df_games['season'] == 2023) & (df_games['week'].between(1, 18))]
win_loss_records = {}
for team in df_teams['TeamID']:
    # Calculate home win/loss record
    home_games = games_2023[games_2023['home_team'] == team]
    home_wins = home_games[home_games['home_score'] > home_games['away_score']].shape[0]
    home_losses = home_games[home_games['home_score'] < home_games['away_score']].shape[0]

    # Calculate away win/loss record
    away_games = games_2023[games_2023['away_team'] == team]
    away_wins = away_games[away_games['away_score'] > away_games['home_score']].shape[0]
    away_losses = away_games[away_games['away_score'] < away_games['home_score']].shape[0]
    win_loss_records[team] = {
        'home_wins': home_wins,
        'home_losses': home_losses,
        'away_wins': away_wins,
        'away_losses': away_losses
    }

win_loss_df = pd.DataFrame.from_dict(win_loss_records, orient='index') # Convert the results to a DataFrame for easier viewing
home_records_df = win_loss_df[['home_wins', 'home_losses']].sort_values(by='home_wins', ascending=False)
away_records_df = win_loss_df[['away_wins', 'away_losses']].sort_values(by='away_wins', ascending=False)
col1, col2 = st.columns(2)
with col1:
    st.markdown("<h5 style='text-align: center; color: grey;'>Home</h5>", unsafe_allow_html=True)
    st.dataframe(home_records_df, use_container_width=True)
    selected_home_team = st.selectbox("Select a team to see their home games", home_records_df.index)
    if selected_home_team:
        with st.expander(f"Home Games for {selected_home_team} in 2023", expanded=False):
            home_games = games_2023[(games_2023['home_team'] == selected_home_team) & (games_2023['season'] == 2023) & (games_2023['week'].between(1, 18))]
            home_games_sorted = home_games.sort_values(by='week')
            st.dataframe(home_games_sorted, use_container_width=True)
with col2:
    st.markdown("<h5 style='text-align: center; color: grey;'>Away</h5>", unsafe_allow_html=True)
    st.dataframe(away_records_df, use_container_width=True)
    selected_away_team = st.selectbox("Select a team to see their away games", away_records_df.index)
    if selected_away_team:
        with st.expander(f"Away Games for {selected_away_team} in 2023", expanded=False):
            away_games = games_2023[(games_2023['away_team'] == selected_away_team) & (games_2023['season'] == 2023) & (games_2023['week'].between(1, 18))]
            away_games_sorted = away_games.sort_values(by='week')
            st.dataframe(away_games_sorted, use_container_width=True)




### --- Avg PPG and PA Home vs Away 2023 --- ###
st.divider()
st.header("PPG and Points Allowed Home vs Away 2023")
st.markdown("###")

# PPG
st.markdown("<h5 style='text-align: center; color: grey;'>Average Points Per Game (PPG) - Home vs. Away</h5>", unsafe_allow_html=True)
games_2023 = df_games[(df_games['season'] == 2023) & (df_games['week'].between(1, 18))]
avg_points_scored_home = games_2023.groupby('home_team')['home_score'].mean()
avg_points_scored_away = games_2023.groupby('away_team')['away_score'].mean()
avg_points = pd.concat([avg_points_scored_home, avg_points_scored_away], axis=1) # Combine to get overall averages
col1, col2 = st.columns((3, 1))
with col1:
    st.bar_chart(avg_points, color=["#FFA500", "#0000FF"], x_label="Teams", y_label="Average PPG", use_container_width=True, stack=False)
with col2:      
    st.dataframe(avg_points, use_container_width=True)

# PA
st.write(" ")
st.markdown("<h5 style='text-align: center; color: grey;'>Average Points Allowed (PA) - Home vs. Away</h5>", unsafe_allow_html=True)
games_2023 = df_games[(df_games['season'] == 2023) & (df_games['week'].between(1, 18))]
avg_points_allowed_home = games_2023.groupby('home_team')['away_score'].mean()
avg_points_allowed_away = games_2023.groupby('away_team')['home_score'].mean()
avg_points_allowed = pd.concat([avg_points_allowed_home, avg_points_allowed_away], axis=1) # Combining the two series to get overall averages for each team
col1, col2 = st.columns((1, 3))
with col1:      
    st.dataframe(avg_points_allowed, use_container_width=True)
with col2:
    st.bar_chart(avg_points_allowed, color=["#FFA500", "#0000FF"], x_label="Teams", y_label="Average Points Allowed", use_container_width=True, stack=False)


### --- Avg Passing/Rushing Yards Per Game 2023 --- ###
st.divider()
st.header("Avg Passing/Rushing Yards Per Game 2023")
st.write("##")

# Passing Yards
df_team_game_logs_filtered = df_team_game_logs[(df_team_game_logs['week_num'] >= 1) & (df_team_game_logs['week_num'] <= 18)]
merged_data = pd.merge(df_team_game_logs_filtered, df_teams, left_on='team_name', right_on='Team', how='left')
team_passing_yards = merged_data.groupby('TeamID')['pass_yds'].sum().reset_index()
team_passing_yards_ranked = team_passing_yards.sort_values(by='pass_yds', ascending=False).reset_index(drop=True)
st.dataframe(team_passing_yards_ranked)

# Rushing Yards
df_team_game_logs_filtered = df_team_game_logs[(df_team_game_logs['week_num'] >= 1) & (df_team_game_logs['week_num'] <= 18)]
merged_data = pd.merge(df_team_game_logs_filtered, df_teams, left_on='team_name', right_on='Team', how='left')
team_rushing_yards = merged_data.groupby('TeamID')['rush_yds'].sum().reset_index()
team_rushing_yards_ranked = team_rushing_yards.sort_values(by='rush_yds', ascending=False).reset_index(drop=True)
st.dataframe(team_rushing_yards_ranked)



### --- Avg Passing/Rushing Yards Allowed Per Game 2023 --- ###
st.divider()
st.header("Avg Passing+Rushing Yards Allowed Per Game 2023")
st.write("##")
