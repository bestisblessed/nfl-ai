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
        df_box_scores = pd.read_csv(os.path.join(current_dir, '../data', 'all_box_scores.csv'))
        
        # Load year-specific team game logs
        df_team_game_logs_2024 = pd.read_csv(os.path.join(current_dir, '../data', 'SR-game-logs/all_teams_game_logs_2024.csv'))
        df_team_game_logs_2025 = pd.read_csv(os.path.join(current_dir, '../data', 'SR-game-logs/all_teams_game_logs_2025.csv'))
        
        return (df_teams, df_games, df_playerstats, df_team_game_logs, 
                df_schedule_and_game_results, df_team_game_logs_2024, df_team_game_logs_2025, df_box_scores)
    except FileNotFoundError as e:
        st.error(f"Error loading data files: {e}")
        st.stop()

# Load all data
(df_teams, df_games, df_playerstats, df_team_game_logs, 
 df_schedule_and_game_results, df_team_game_logs_2024, df_team_game_logs_2025, df_box_scores) = load_data()

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
st.write("##")

# Process box scores data
df_box_scores_proc = df_box_scores.copy()
df_box_scores_proc['date_str'] = df_box_scores_proc['URL'].str.extract(r'/boxscores/(\d{8})')
df_box_scores_proc['date'] = pd.to_datetime(df_box_scores_proc['date_str'], format='%Y%m%d')
df_box_scores_proc['season'] = df_box_scores_proc['date'].dt.year

# Fill NaN values with 0 for overtime quarters
for col in ['OT1', 'OT2', 'OT3', 'OT4']:
    if col in df_box_scores_proc.columns:
        df_box_scores_proc[col] = df_box_scores_proc[col].fillna(0)

# Calculate 1H and 2H scores
df_box_scores_proc['1H'] = df_box_scores_proc['1'] + df_box_scores_proc['2']
df_box_scores_proc['2H'] = df_box_scores_proc['3'] + df_box_scores_proc['4']
if 'OT1' in df_box_scores_proc.columns:
    df_box_scores_proc['2H'] += df_box_scores_proc['OT1'] + df_box_scores_proc['OT2'] + df_box_scores_proc['OT3'] + df_box_scores_proc['OT4']

# Merge with games to get week info
df_games_date = df_games.copy()
df_games_date['date'] = pd.to_datetime(df_games_date['date'])
df_merged_box = df_box_scores_proc.merge(df_games_date[['date', 'week', 'season']], on=['date', 'season'], how='left')

# Map team names to TeamIDs
def map_team_name(name):
    name_mapping = {
        'Kansas City Chiefs': 'KC',
        'New England Patriots': 'NE',
        'New York Jets': 'NYJ',
        'Buffalo Bills': 'BUF',
        'Atlanta Falcons': 'ATL',
        'Chicago Bears': 'CHI',
        'Baltimore Ravens': 'BAL',
        'Cincinnati Bengals': 'CIN',
        'Pittsburgh Steelers': 'PIT',
        'Cleveland Browns': 'CLE',
        'Arizona Cardinals': 'ARI',
        'Detroit Lions': 'DET',
        'Jacksonville Jaguars': 'JAX',
        'Houston Texans': 'HOU',
        'Oakland Raiders': 'LVR',
        'Las Vegas Raiders': 'LVR',
        'Tennessee Titans': 'TEN',
        'Philadelphia Eagles': 'PHI',
        'Washington Redskins': 'WAS',
        'Washington Football Team': 'WAS',
        'Washington Commanders': 'WAS',
        'Indianapolis Colts': 'IND',
        'Los Angeles Rams': 'LAR',
        'St. Louis Rams': 'LAR',
        'Seattle Seahawks': 'SEA',
        'Minnesota Vikings': 'MIN',
        'Green Bay Packers': 'GB',
        'Tampa Bay Buccaneers': 'TB',
        'New Orleans Saints': 'NO',
        'San Francisco 49ers': 'SF',
        'Los Angeles Chargers': 'LAC',
        'San Diego Chargers': 'LAC',
        'Denver Broncos': 'DEN',
        'Miami Dolphins': 'MIA',
        'Carolina Panthers': 'CAR',
        'New York Giants': 'NYG',
        'Dallas Cowboys': 'DAL'
    }
    return name_mapping.get(name, name)

df_merged_box['TeamID'] = df_merged_box['Team'].apply(map_team_name)

# Filter for selected season, regular season only
df_season_half = df_merged_box[(df_merged_box['season'] == selected_season) & (df_merged_box['week'] >= 1) & (df_merged_box['week'] <= 18)]

# Calculate average 1H and 2H scores by team
team_half_scores = df_season_half.groupby('TeamID')[['1H', '2H']].mean().sort_values(by='1H', ascending=False)

# Display 1H vs 2H averages
st.markdown("<h5 style='text-align: center; color: grey;'>Average Points Per Game - 1H vs 2H</h5>", unsafe_allow_html=True)
col1, col2 = st.columns((3, 1))
with col1:
    st.bar_chart(team_half_scores, color=["#FFA500", "#0000FF"], x_label="Teams", y_label="Average Points", use_container_width=True, stack=False)
with col2:
    st.dataframe(team_half_scores, use_container_width=True)

# Calculate and display 1H vs 2H differential
st.write(" ")
st.markdown("<h5 style='text-align: center; color: grey;'>2H vs 1H Scoring Differential by Team</h5>", unsafe_allow_html=True)
st.write("Teams with positive values score more in the 2nd half. Teams with negative values score more in the 1st half.")

team_half_scores_diff = team_half_scores.copy()
team_half_scores_diff['Differential'] = team_half_scores_diff['2H'] - team_half_scores_diff['1H']
team_half_scores_diff_sorted = team_half_scores_diff.sort_values(by='Differential', ascending=False)

col1, col2 = st.columns((1, 3))
with col1:
    st.dataframe(team_half_scores_diff_sorted[['Differential']], use_container_width=True)
with col2:
    fig, ax = plt.subplots(figsize=(10, 8))
    colors = ['green' if x > 0 else 'red' for x in team_half_scores_diff_sorted['Differential']]
    ax.barh(range(len(team_half_scores_diff_sorted)), team_half_scores_diff_sorted['Differential'], color=colors, alpha=0.7)
    ax.set_yticks(range(len(team_half_scores_diff_sorted)))
    ax.set_yticklabels(team_half_scores_diff_sorted.index)
    ax.set_xlabel('Point Differential (2H - 1H)', fontsize=10)
    ax.set_title(f'{selected_season} Season - 2H vs 1H Scoring Differential', fontsize=12, fontweight='bold')
    ax.axvline(x=0, color='black', linestyle='-', linewidth=0.8)
    ax.grid(axis='x', alpha=0.3)
    st.pyplot(fig)


### --- Quarter-by-Quarter Scoring Trends --- ###
st.divider()
st.header(f"Quarter-by-Quarter Scoring Trends {selected_season}")
st.write("##")

# Calculate quarter averages
team_quarter_scores = df_season_half.groupby('TeamID')[['1', '2', '3', '4']].mean()
team_quarter_scores.columns = ['Q1', 'Q2', 'Q3', 'Q4']

# 1Q Specific Analysis
st.markdown("<h5 style='text-align: center; color: grey;'>1st Quarter (Q1) Scoring Leaders</h5>", unsafe_allow_html=True)
st.write("Teams that come out strong and score early in games")
q1_sorted = team_quarter_scores.sort_values(by='Q1', ascending=False)

col1, col2 = st.columns((1, 3))
with col1:
    st.dataframe(q1_sorted[['Q1']], use_container_width=True)
with col2:
    fig, ax = plt.subplots(figsize=(10, 8))
    ax.barh(range(len(q1_sorted)), q1_sorted['Q1'], color='#FF6B6B', alpha=0.8)
    ax.set_yticks(range(len(q1_sorted)))
    ax.set_yticklabels(q1_sorted.index)
    ax.set_xlabel('Average Points in Q1', fontsize=10)
    ax.set_title(f'{selected_season} Season - 1st Quarter Scoring', fontsize=12, fontweight='bold')
    ax.grid(axis='x', alpha=0.3)
    st.pyplot(fig)

# All Quarters Comparison
st.write(" ")
st.write(" ")
st.markdown("<h5 style='text-align: center; color: grey;'>All Quarters Scoring Comparison</h5>", unsafe_allow_html=True)
team_quarter_sorted = team_quarter_scores.sort_values(by='Q1', ascending=False)

col1, col2 = st.columns((3, 1))
with col1:
    fig, ax = plt.subplots(figsize=(12, 6))
    x = range(len(team_quarter_sorted))
    width = 0.2
    
    ax.bar([i - 1.5*width for i in x], team_quarter_sorted['Q1'], 
           width, label='Q1', alpha=0.8, color='#FF6B6B')
    ax.bar([i - 0.5*width for i in x], team_quarter_sorted['Q2'], 
           width, label='Q2', alpha=0.8, color='#4ECDC4')
    ax.bar([i + 0.5*width for i in x], team_quarter_sorted['Q3'], 
           width, label='Q3', alpha=0.8, color='#45B7D1')
    ax.bar([i + 1.5*width for i in x], team_quarter_sorted['Q4'], 
           width, label='Q4', alpha=0.8, color='#96CEB4')
    
    ax.set_xlabel('Team', fontsize=10)
    ax.set_ylabel('Average Points', fontsize=10)
    ax.set_title(f'{selected_season} Season - Scoring by Quarter', fontsize=11, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(team_quarter_sorted.index, rotation=45, ha='right', fontsize=8)
    ax.legend()
    ax.grid(axis='y', alpha=0.3)
    st.pyplot(fig)
with col2:
    st.dataframe(team_quarter_sorted, use_container_width=True)

# Quarter Performance Heatmap
st.write(" ")
st.write(" ")
st.markdown("<h5 style='text-align: center; color: grey;'>Quarter Scoring Heatmap</h5>", unsafe_allow_html=True)
st.write("Visual representation of each team's performance across all quarters")

fig, ax = plt.subplots(figsize=(8, 12))
data_for_heatmap = team_quarter_scores.sort_values(by='Q1', ascending=False)
im = ax.imshow(data_for_heatmap.values, cmap='YlOrRd', aspect='auto')

ax.set_xticks(range(4))
ax.set_xticklabels(['Q1', 'Q2', 'Q3', 'Q4'], fontsize=10)
ax.set_yticks(range(len(data_for_heatmap)))
ax.set_yticklabels(data_for_heatmap.index, fontsize=9)
ax.set_title(f'{selected_season} Season - Quarter Scoring Heatmap', fontsize=12, fontweight='bold')

for i in range(len(data_for_heatmap)):
    for j in range(4):
        text = ax.text(j, i, f'{data_for_heatmap.values[i, j]:.1f}',
                      ha="center", va="center", color="black", fontsize=7)

plt.colorbar(im, ax=ax, label='Average Points')
st.pyplot(fig)

# Strongest/Weakest Quarter Analysis
st.write(" ")
st.write(" ")
st.markdown("<h5 style='text-align: center; color: grey;'>Strongest & Weakest Quarters by Team</h5>", unsafe_allow_html=True)
team_quarter_analysis = team_quarter_scores.copy()
team_quarter_analysis['Strongest_Quarter'] = team_quarter_scores.idxmax(axis=1)
team_quarter_analysis['Weakest_Quarter'] = team_quarter_scores.idxmin(axis=1)
team_quarter_analysis['Quarter_Differential'] = team_quarter_scores.max(axis=1) - team_quarter_scores.min(axis=1)

col1, col2 = st.columns(2)
with col1:
    st.markdown("**Strongest Quarters**")
    strongest_summary = team_quarter_analysis['Strongest_Quarter'].value_counts().sort_index()
    st.dataframe(team_quarter_analysis[['Strongest_Quarter', 'Quarter_Differential']].sort_values(by='Quarter_Differential', ascending=False), use_container_width=True)
with col2:
    st.markdown("**Weakest Quarters**")
    weakest_summary = team_quarter_analysis['Weakest_Quarter'].value_counts().sort_index()
    st.dataframe(team_quarter_analysis[['Weakest_Quarter']].sort_index(), use_container_width=True)