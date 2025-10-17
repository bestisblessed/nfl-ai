import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import sqlite3
import os

# Page configuration
st.set_page_config(
    page_title="📉 Team Trends",
    page_icon="📉",
    layout="wide"
)

st.markdown(f"""
    <div style='text-align: center;'>
        <div style='font-size: 3.1rem; font-weight: 800; padding-bottom: 0.5rem;'>
            Team Trends
        </div>
        <div style='color: #7f8c8d; font-size: 1rem; margin-top: 0; line-height: 1.2;'>
            Historical team performance analysis and statistical insights
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

# Load data using cached function
@st.cache_data(show_spinner=False)
def load_data():
    """Load all required CSV files for Team Trends"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    try:
        df_teams = pd.read_csv(os.path.join(current_dir, '../data', 'Teams.csv'))
        df_games = pd.read_csv(os.path.join(current_dir, '../data', 'Games.csv'))
        df_playerstats = pd.read_csv(os.path.join(current_dir, '../data', 'PlayerStats.csv'))
        df_team_game_logs = pd.read_csv(os.path.join(current_dir, '../data', 'all_team_game_logs.csv'))
        df_schedule_and_game_results = pd.read_csv(os.path.join(current_dir, '../data', 'all_teams_schedule_and_game_results_merged.csv'))
        
        # Load year-specific team game logs
        df_team_game_logs_2024 = pd.read_csv(os.path.join(current_dir, '../data', 'SR-game-logs/all_teams_game_logs_2024.csv'))
        df_team_game_logs_2025 = pd.read_csv(os.path.join(current_dir, '../data', 'SR-game-logs/all_teams_game_logs_2025.csv'))
        
        return (df_teams, df_games, df_playerstats, df_team_game_logs, 
                df_schedule_and_game_results, df_team_game_logs_2024, df_team_game_logs_2025)
    except FileNotFoundError as e:
        st.error(f"Error loading data files: {e}")
        st.stop()

# Load all data
(df_teams, df_games, df_playerstats, df_team_game_logs, 
 df_schedule_and_game_results, df_team_game_logs_2024, df_team_game_logs_2025) = load_data()

# Season selector
selected_season = st.selectbox("Select Season:", [2025, 2024], index=0)

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
    team_passing_yards = merged_data.groupby('TeamID')['pass_yds'].mean().reset_index()
    team_passing_yards_ranked = team_passing_yards.sort_values(by='pass_yds', ascending=False).reset_index(drop=True)
    st.dataframe(team_passing_yards_ranked, use_container_width=True)

# Rushing Yards
with col2:
    df_team_game_logs_filtered = df_team_game_logs_selected[(df_team_game_logs_selected[week_col] >= 1) & (df_team_game_logs_selected[week_col] <= 18)]
    merged_data = pd.merge(df_team_game_logs_filtered, df_teams, left_on=team_name_col, right_on='Team', how='left')
    team_rushing_yards = merged_data.groupby('TeamID')['rush_yds'].mean().reset_index()
    team_rushing_yards_ranked = team_rushing_yards.sort_values(by='rush_yds', ascending=False).reset_index(drop=True)
    st.dataframe(team_rushing_yards_ranked, use_container_width=True)



### --- Avg Passing/Rushing Yards Allowed Per Game --- ###
st.divider()
st.header(f"Avg Passing+Rushing Yards Allowed Per Game {selected_season}")
st.write("##")

col1, col2 = st.columns(2)

filtered_df_teams = df_teams.copy()
filtered_df_teams.loc[:, 'TeamID'] = filtered_df_teams['TeamID'].str.lower()

# Create a copy of df_schedule_and_game_results to avoid SettingWithCopyWarning
df_schedule_results = df_schedule_and_game_results.copy()
df_schedule_results.loc[:, 'Week'] = pd.to_numeric(df_schedule_results['Week'], errors='coerce')
df_schedule_results = df_schedule_results.dropna(subset=['Day'])

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
df_schedule_results.loc[:, 'Team'] = df_schedule_results['Team'].map(team_abbreviation_mapping).fillna(df_schedule_results['Team'])
df_schedule_and_game_results_filtered = df_schedule_results[(df_schedule_results['Season'] == selected_season) & (df_schedule_results['Week'] >= 1) & (df_schedule_results['Week'] <= 18)]

# Passing Yards Allowed
with col1:
    results_passing_yards_allowed = []
    for team in filtered_df_teams['TeamID']:
        team_filtered_data = df_schedule_and_game_results_filtered[df_schedule_and_game_results_filtered['Team'] == team]
        avg_passing_yards_allowed = team_filtered_data['OppPassY'].mean()
        results_passing_yards_allowed.append({'Team': team, 'Avg Passing Yards Allowed': avg_passing_yards_allowed})
    st.dataframe(results_passing_yards_allowed, use_container_width=True)

# Rushing Yards Allowed
with col2:
    results_rushing_yards_allowed = []
    for team in filtered_df_teams['TeamID']:
        team_filtered_data = df_schedule_and_game_results_filtered[df_schedule_and_game_results_filtered['Team'] == team]
        avg_rushing_yards_allowed = team_filtered_data['OppRushY'].mean()
        results_rushing_yards_allowed.append({'Team': team, 'Avg Rushing Yards Allowed': avg_rushing_yards_allowed})
    st.dataframe(results_rushing_yards_allowed, use_container_width=True)


### --- 1H vs 2H Scoring Trends --- ###
st.divider()
st.header(f"1H vs 2H Scoring Trends {selected_season}")
st.write(" ")

# Load quarter scoring box scores and compute halves
current_dir = os.path.dirname(os.path.abspath(__file__))
boxscores_path = os.path.join(current_dir, '../data', 'all_box_scores.csv')
try:
    df_box = pd.read_csv(boxscores_path)
except FileNotFoundError:
    st.error("all_box_scores.csv not found.")
    st.stop()

# Extract PFR game id to join to Games for season/week filtering
df_box['pfr'] = df_box['URL'].str.extract(r'/boxscores/([0-9a-z]+)\.htm')
for c in ['1', '2', '3', '4']:
    df_box[c] = pd.to_numeric(df_box[c], errors='coerce').fillna(0)
df_box['first_half'] = df_box['1'] + df_box['2']
df_box['second_half'] = df_box['3'] + df_box['4']

# Restrict to regular season games for the selected season (weeks 1-18)
games_sel = df_games[(df_games['season'] == selected_season) & (df_games['game_type'] == 'REG') & (df_games['week'].between(1, 18))]
df_box = df_box.merge(games_sel[['pfr', 'season']], on='pfr', how='inner')

# Map full team names to TeamID
df_box = df_box.merge(df_teams[['TeamID', 'Team']], left_on='Team', right_on='Team', how='left')

# Aggregate per team
team_halves = (
    df_box.groupby('TeamID')[['first_half', 'second_half']]
    .mean()
    .round(2)
    .reset_index()
)
team_halves['diff_2H_minus_1H'] = (team_halves['second_half'] - team_halves['first_half']).round(2)

# Display table
st.markdown("<h5 style='text-align: center; color: grey;'>Average Points by Half (Reg Season)</h5>", unsafe_allow_html=True)
st.dataframe(
    team_halves.sort_values('diff_2H_minus_1H', ascending=False).set_index('TeamID'),
    use_container_width=True,
)

# Create images directory
images_dir = os.path.normpath(os.path.join(current_dir, '../images'))
os.makedirs(images_dir, exist_ok=True)

# Figure 1: 2H - 1H difference (horizontal bar)
fig1, ax1 = plt.subplots(figsize=(10, 12))
ordered = team_halves.sort_values('diff_2H_minus_1H', ascending=True)
ax1.barh(ordered['TeamID'], ordered['diff_2H_minus_1H'], color=['#2ecc71' if v > 0 else '#e74c3c' for v in ordered['diff_2H_minus_1H']])
ax1.axvline(0, color='#7f8c8d', linewidth=1)
ax1.set_xlabel('2H - 1H (points)')
ax1.set_ylabel('Team')
ax1.set_title(f'Average 2H minus 1H Points by Team ({selected_season})')
fig1.tight_layout()
diff_path = os.path.join(images_dir, f'1h_vs_2h_diff_{selected_season}.png')
fig1.savefig(diff_path, dpi=150, bbox_inches='tight')
st.image(diff_path, caption='2H - 1H Average Points by Team', use_container_width=True)
with open(diff_path, 'rb') as f:
    st.download_button('Download Diff Chart (PNG)', f.read(), file_name=f'1h_vs_2h_diff_{selected_season}.png')

# Figure 2: 1H vs 2H scatter
fig2, ax2 = plt.subplots(figsize=(8, 8))
ax2.scatter(team_halves['first_half'], team_halves['second_half'], color='#3498db')
mn = float(min(team_halves['first_half'].min(), team_halves['second_half'].min()))
mx = float(max(team_halves['first_half'].max(), team_halves['second_half'].max()))
ax2.plot([mn, mx], [mn, mx], linestyle='--', color='#e74c3c', linewidth=1)
ax2.set_xlabel('Avg 1H Points')
ax2.set_ylabel('Avg 2H Points')
ax2.set_title(f'Avg 1H vs 2H Points by Team ({selected_season})')
ax2.grid(True, axis='both', linestyle='--', alpha=0.3)
fig2.tight_layout()
scatter_path = os.path.join(images_dir, f'1h_vs_2h_scatter_{selected_season}.png')
fig2.savefig(scatter_path, dpi=150, bbox_inches='tight')
st.image(scatter_path, caption='Avg 1H vs 2H Points by Team', use_container_width=True)
with open(scatter_path, 'rb') as f:
    st.download_button('Download Scatter (PNG)', f.read(), file_name=f'1h_vs_2h_scatter_{selected_season}.png')