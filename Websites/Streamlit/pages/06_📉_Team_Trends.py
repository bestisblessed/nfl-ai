import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import sqlite3

# Page configuration
st.set_page_config(
    page_title="📊 Team Trends",
    page_icon="📊",
    layout="wide"
)

### --- Title and Data --- ###
st.title('General Trends')

# Season selector
selected_season = st.selectbox("Select Season:", [2025, 2024], index=0)

# df_teams = pd.read_csv('./data/Teams.csv')
# df_games = pd.read_csv('./data/Games.csv')
# df_playerstats = pd.read_csv('./data/PlayerStats.csv')
df_teams = st.session_state['df_teams']
df_games = st.session_state['df_games'] 
df_playerstats = st.session_state['df_playerstats']
df_team_game_logs = st.session_state['df_all_team_game_logs']
df_team_game_logs_2024 = st.session_state['df_all_team_game_logs_2024']
df_team_game_logs_2025 = st.session_state['df_all_team_game_logs_2025']
df_schedule_and_game_results = st.session_state['df_schedule_and_game_results']

# Select the appropriate dataset based on season
if selected_season == 2025:
    df_team_game_logs_selected = df_team_game_logs_2025
else:
    df_team_game_logs_selected = df_team_game_logs_2024

# Both datasets use the same column names
team_name_col = 'team_name'
week_col = 'week'

dataframes = [df_teams, df_games, df_playerstats, df_team_game_logs, df_schedule_and_game_results]

### --- Home vs Away Record --- ###
st.divider()
st.header(f"Home vs Away Record {selected_season} (Reg Season)")
st.write(" ")

games_selected = df_games[(df_games['season'] == selected_season) & (df_games['week'].between(1, 18))]
win_loss_records = {}
for team in df_teams['TeamID']:
    # Calculate home win/loss record
    home_games = games_selected[games_selected['home_team'] == team]
    home_wins = home_games[home_games['home_score'] > home_games['away_score']].shape[0]
    home_losses = home_games[home_games['home_score'] < home_games['away_score']].shape[0]

    # Calculate away win/loss record
    away_games = games_selected[games_selected['away_team'] == team]
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
        with st.expander(f"Home Games for {selected_home_team} in {selected_season}", expanded=False):
            home_games = games_selected[(games_selected['home_team'] == selected_home_team) & (games_selected['season'] == selected_season) & (games_selected['week'].between(1, 18))]
            home_games_sorted = home_games.sort_values(by='week')
            st.dataframe(home_games_sorted, use_container_width=True)
with col2:
    st.markdown("<h5 style='text-align: center; color: grey;'>Away</h5>", unsafe_allow_html=True)
    st.dataframe(away_records_df, use_container_width=True)
    selected_away_team = st.selectbox("Select a team to see their away games", away_records_df.index)
    if selected_away_team:
        with st.expander(f"Away Games for {selected_away_team} in {selected_season}", expanded=False):
            away_games = games_selected[(games_selected['away_team'] == selected_away_team) & (games_selected['season'] == selected_season) & (games_selected['week'].between(1, 18))]
            away_games_sorted = away_games.sort_values(by='week')
            st.dataframe(away_games_sorted, use_container_width=True)




### --- Avg PPG and PA Home vs Away --- ###
st.divider()
st.header(f"PPG and Points Allowed Home vs Away {selected_season}")
st.markdown("###")

# PPG
st.markdown("<h5 style='text-align: center; color: grey;'>Average Points Per Game (PPG) - Home vs. Away</h5>", unsafe_allow_html=True)
games_selected = df_games[(df_games['season'] == selected_season) & (df_games['week'].between(1, 18))]
avg_points_scored_home = games_selected.groupby('home_team')['home_score'].mean()
avg_points_scored_away = games_selected.groupby('away_team')['away_score'].mean()
avg_points = pd.concat([avg_points_scored_home, avg_points_scored_away], axis=1) # Combine to get overall averages
col1, col2 = st.columns((3, 1))
with col1:
    st.bar_chart(avg_points, color=["#FFA500", "#0000FF"], x_label="Teams", y_label="Average PPG", use_container_width=True, stack=False)
with col2:      
    st.dataframe(avg_points, use_container_width=True)

# PA
st.write(" ")
st.markdown("<h5 style='text-align: center; color: grey;'>Average Points Allowed (PA) - Home vs. Away</h5>", unsafe_allow_html=True)
games_selected = df_games[(df_games['season'] == selected_season) & (df_games['week'].between(1, 18))]
avg_points_allowed_home = games_selected.groupby('home_team')['away_score'].mean()
avg_points_allowed_away = games_selected.groupby('away_team')['home_score'].mean()
avg_points_allowed = pd.concat([avg_points_allowed_home, avg_points_allowed_away], axis=1) # Combining the two series to get overall averages for each team
col1, col2 = st.columns((1, 3))
with col1:      
    st.dataframe(avg_points_allowed, use_container_width=True)
with col2:
    st.bar_chart(avg_points_allowed, color=["#FFA500", "#0000FF"], x_label="Teams", y_label="Average Points Allowed", use_container_width=True, stack=False)


### --- Avg Passing/Rushing Yards Per Game --- ###
st.divider()
st.header(f"Avg Passing/Rushing Yards Per Game {selected_season}")
st.write("##")

col1, col2 = st.columns(2)

# Passing Yards
with col1:
    df_team_game_logs_filtered = df_team_game_logs_selected[(df_team_game_logs_selected[week_col] >= 1) & (df_team_game_logs_selected[week_col] <= 18)]
    merged_data = pd.merge(df_team_game_logs_filtered, df_teams, left_on=team_name_col, right_on='Team', how='left')
    team_passing_yards = merged_data.groupby('TeamID')['pass_yds'].sum().reset_index()
    team_passing_yards_ranked = team_passing_yards.sort_values(by='pass_yds', ascending=False).reset_index(drop=True)
    st.dataframe(team_passing_yards_ranked, use_container_width=True)

# Rushing Yards
with col2:
    df_team_game_logs_filtered = df_team_game_logs_selected[(df_team_game_logs_selected[week_col] >= 1) & (df_team_game_logs_selected[week_col] <= 18)]
    merged_data = pd.merge(df_team_game_logs_filtered, df_teams, left_on=team_name_col, right_on='Team', how='left')
    team_rushing_yards = merged_data.groupby('TeamID')['rush_yds'].sum().reset_index()
    team_rushing_yards_ranked = team_rushing_yards.sort_values(by='rush_yds', ascending=False).reset_index(drop=True)
    st.dataframe(team_rushing_yards_ranked, use_container_width=True)



### --- Avg Passing/Rushing Yards Allowed Per Game --- ###
st.divider()
st.header(f"Avg Passing+Rushing Yards Allowed Per Game {selected_season}")
st.write("##")

col1, col2 = st.columns(2)

filtered_df_teams = df_teams.copy()
filtered_df_teams['TeamID'] = filtered_df_teams['TeamID'].str.lower()
df_schedule_and_game_results['Week'] = pd.to_numeric(df_schedule_and_game_results['Week'], errors='coerce')
df_schedule_and_game_results = df_schedule_and_game_results.dropna(subset=['Day'])
team_abbreviation_mapping = {
    'gnb': 'gb',
    'htx': 'hou',
    'clt': 'ind',
    'kan': 'kc',
    'sdg': 'lac',
    'ram': 'lar',
    'rai': 'lvr',
    'nwe': 'ne',
    'nor': 'no',
    'sfo': 'sf',
    'tam': 'tb',
    'oti': 'ten',
    'rav': 'bal',
    'crd': 'ari'
}
df_schedule_and_game_results['Team'] = df_schedule_and_game_results['Team'].map(team_abbreviation_mapping).fillna(df_schedule_and_game_results['Team'])
df_schedule_and_game_results_filtered = df_schedule_and_game_results[(df_schedule_and_game_results['Season'] == selected_season) & (df_schedule_and_game_results['Week'] >= 1) & (df_schedule_and_game_results['Week'] <= 18)]

# Passing Yards Allowed
with col1:
    results_passing_yards_allowed = []
    for team in filtered_df_teams['TeamID']:
        team_filtered_data = df_schedule_and_game_results_filtered[df_schedule_and_game_results_filtered['Team'] == team]
        total_passing_yards_allowed = team_filtered_data['OppPassY'].sum()
        results_passing_yards_allowed.append({'Team': team, 'Total Passing Yards Allowed': total_passing_yards_allowed})
    st.dataframe(results_passing_yards_allowed, use_container_width=True)

# Rushing Yards Allowed
with col2:
    results_rushing_yards_allowed = []
    for team in filtered_df_teams['TeamID']:
        team_filtered_data = df_schedule_and_game_results_filtered[df_schedule_and_game_results_filtered['Team'] == team]
        total_rushing_yards_allowed = team_filtered_data['OppRushY'].sum()
        results_rushing_yards_allowed.append({'Team': team, 'Total Rushing Yards Allowed': total_rushing_yards_allowed})
    st.dataframe(results_rushing_yards_allowed, use_container_width=True)