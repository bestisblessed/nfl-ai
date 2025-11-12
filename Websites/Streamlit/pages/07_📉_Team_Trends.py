import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import sqlite3
import os
import altair as alt
import plotly.express as px

# Page configuration
st.set_page_config(
    page_title="📉 Team Trends",
    page_icon="🏈",
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

# Season selector in sidebar
with st.sidebar:
    st.header("Filters")
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
# st.subheader(f"Home vs Away Record ({selected_season})")
# st.subheader(f"Home vs Away W/L Record")
st.subheader(f"Home vs Away Record (W/L)")
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

### --- 1H vs 2H Scoring Trends --- ###
st.divider()
st.subheader(f"1H vs 2H Performance Trends")
st.write(" ")
# st.write(" ")


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
st.markdown(f"<h5 style='text-align: center; color: grey;'>Average Points Per Game - 1H vs 2H ({selected_season})</h5>", unsafe_allow_html=True)
team_half_scores_df = team_half_scores.reset_index()
# Create Plotly Express chart with purple theme
fig = px.bar(
    team_half_scores_df,
    x='TeamID',
    y=['1H', '2H'],
    color_discrete_map={'1H': '#8A2BE2', '2H': '#9370DB'},  # Blue Violet and Medium Purple
    barmode='group'
)
fig.update_layout(
    xaxis_title='Teams',
    yaxis_title='Average Points',
    showlegend=True,
    font=dict(size=12),
    xaxis=dict(tickangle=45),
    height=500
)
st.plotly_chart(fig, use_container_width=True)

# Add expandable table below the chart
with st.expander("View Table", expanded=False):
    st.dataframe(team_half_scores, use_container_width=True)

st.write("#####")
# st.write(" ")

# Calculate and display 1H vs 2H differential
st.markdown(f"<h5 style='text-align: center; color: grey;'>2H vs 1H Scoring Differential by Team ({selected_season})</h5>", unsafe_allow_html=True)
st.write("Teams with positive values score more in the 2nd half. Teams with negative values score more in the 1st half.")

team_half_scores_diff = team_half_scores.copy()
team_half_scores_diff['Differential'] = team_half_scores_diff['2H'] - team_half_scores_diff['1H']
team_half_scores_diff_sorted = team_half_scores_diff.sort_values(by='Differential', ascending=False)

# Create Altair chart with blue and red theme
team_half_scores_diff_sorted_reset = team_half_scores_diff_sorted.reset_index()
team_half_scores_diff_sorted_reset['color'] = team_half_scores_diff_sorted_reset['Differential'].apply(lambda x: '#1E90FF' if x > 0 else '#DC143C')

chart = alt.Chart(team_half_scores_diff_sorted_reset).mark_bar(
    size=20
).encode(
    x=alt.X('Differential:Q', title='Point Differential (2H - 1H)'),
    y=alt.Y('TeamID:N', title='Teams', sort='-x'),
    color=alt.Color('color:N', scale=None, legend=None),
    tooltip=['TeamID', 'Differential']
).properties(
    width=800,
    # height=max(600, len(team_half_scores_diff_sorted_reset) * 35),
    height=1000,
).configure_axisX(
    grid=True,
    labelColor='#333333'
).configure_axisY(
    grid=False,
    labelColor='#333333'
).add_params(
    alt.selection_interval()
)

st.altair_chart(chart, use_container_width=True)

# Add expandable table below the chart
with st.expander("View Table", expanded=False):
    st.dataframe(team_half_scores_diff_sorted[['Differential']], use_container_width=True)

### --- Quarter Performance Trends --- ###
st.divider()
st.subheader(f"Quarter Performance Trends")
st.write(" ")

# Placeholder for future quarter performance analysis
st.info("**Coming Soon**")

### --- Avg PPG and PA Home vs Away --- ###
st.divider()
st.subheader(f"PPG & Opp PPG - Home vs Away")
st.write(" ")

# PPG
st.markdown(f"<h5 style='text-align: center; color: grey;'>Average Points Per Game - Home vs. Away ({selected_season})</h5>", unsafe_allow_html=True)
games_selected = df_games[(df_games['season'] == selected_season) & (df_games['week'].between(1, 18))]
avg_points_scored_home = games_selected.groupby('home_team')['home_score'].mean()
avg_points_scored_away = games_selected.groupby('away_team')['away_score'].mean()
avg_points = pd.concat([avg_points_scored_home, avg_points_scored_away], axis=1) # Combine to get overall averages
avg_points.columns = ['Home', 'Away']
avg_points = avg_points.reset_index()
avg_points.rename(columns={'index': 'Team'}, inplace=True)

# Create Plotly Express chart with green theme and fade effect
fig = px.bar(
    avg_points,
    x='Team',
    y=['Home', 'Away'],
    color_discrete_map={'Home': '#2E8B57', 'Away': '#123829'},  # Sea Green and Dark Green
    barmode='group'
)
fig.update_layout(
    xaxis_title='Teams',
    yaxis_title='Average PPG',
    showlegend=True,
    font=dict(size=12),
    xaxis=dict(tickangle=45),
    height=500
)
st.plotly_chart(fig, use_container_width=True)

# Add expandable table below the chart
with st.expander("View Table", expanded=False):
    st.dataframe(avg_points.set_index('Team'), use_container_width=True)

# st.write("#####")
st.write(" ")

# PA
st.markdown(f"<h5 style='text-align: center; color: grey;'>Average Opponent Points Per Game - Home vs. Away ({selected_season})</h5>", unsafe_allow_html=True)
games_selected = df_games[(df_games['season'] == selected_season) & (df_games['week'].between(1, 18))]
avg_points_allowed_home = games_selected.groupby('home_team')['away_score'].mean()
avg_points_allowed_away = games_selected.groupby('away_team')['home_score'].mean()
avg_points_allowed = pd.concat([avg_points_allowed_home, avg_points_allowed_away], axis=1) # Combining the two series to get overall averages for each team
avg_points_allowed.columns = ['Home', 'Away']
avg_points_allowed = avg_points_allowed.reset_index()
avg_points_allowed.rename(columns={'index': 'Team'}, inplace=True)

# Create Plotly Express chart with green theme and fade effect
fig = px.bar(
    avg_points_allowed,
    x='Team',
    y=['Home', 'Away'],
    color_discrete_map={'Home': '#2E8B57', 'Away': '#123829'},  # Sea Green and Dark Forest Green
    barmode='group'
)
fig.update_layout(
    xaxis_title='Teams',
    yaxis_title='Average Opp PPG',
    showlegend=True,
    font=dict(size=12),
    xaxis=dict(tickangle=45),
    height=500
)
st.plotly_chart(fig, use_container_width=True)

# Add expandable table below the chart
with st.expander("View Table", expanded=False):
    st.dataframe(avg_points_allowed.set_index('Team'), use_container_width=True)

# st.write("#####")
st.write(" ")

### --- Avg Passing/Rushing Yards Per Game --- ###
st.divider()
st.subheader(f"Avg Passing & Rushing Yards Per Game")
st.write(" ")
# st.write(" ")

col1, col2 = st.columns(2)

# Passing Yards
with col1:
    st.write(f"Passing Yards ({selected_season})")
    df_team_game_logs_filtered = df_team_game_logs_selected[(df_team_game_logs_selected[week_col] >= 1) & (df_team_game_logs_selected[week_col] <= 18)]
    merged_data = pd.merge(df_team_game_logs_filtered, df_teams, left_on=team_name_col, right_on='Team', how='left')
    team_passing_yards = merged_data.groupby('TeamID')['pass_yds'].mean().reset_index()
    team_passing_yards_ranked = team_passing_yards.sort_values(by='pass_yds', ascending=False).reset_index(drop=True)
    
    # Create horizontal bar chart
    fig = px.bar(
        team_passing_yards_ranked,
        x='pass_yds',
        y='TeamID',
        orientation='h',
        color='pass_yds',
        color_continuous_scale='Blues',
        title=""
    )
    fig.update_layout(
        height=800,
        xaxis_title="Passing Yards per Game",
        yaxis_title="Teams",
        yaxis={'categoryorder':'total ascending'},
        showlegend=False,
        coloraxis_showscale=False
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Top 5 Teams for Passing Yards per Game
    st.write(f"**Top 5 Passing Offenses ({selected_season}):**")
    top_5_pass_yds = team_passing_yards_ranked.head(5)
    st.dataframe(top_5_pass_yds, use_container_width=True, hide_index=True)

# Rushing Yards
with col2:
    st.write(f"Rushing Yards ({selected_season})")
    df_team_game_logs_filtered = df_team_game_logs_selected[(df_team_game_logs_selected[week_col] >= 1) & (df_team_game_logs_selected[week_col] <= 18)]
    merged_data = pd.merge(df_team_game_logs_filtered, df_teams, left_on=team_name_col, right_on='Team', how='left')
    team_rushing_yards = merged_data.groupby('TeamID')['rush_yds'].mean().reset_index()
    team_rushing_yards_ranked = team_rushing_yards.sort_values(by='rush_yds', ascending=False).reset_index(drop=True)
    
    # Create horizontal bar chart
    fig = px.bar(
        team_rushing_yards_ranked,
        x='rush_yds',
        y='TeamID',
        orientation='h',
        color='rush_yds',
        color_continuous_scale='Blues',
        title=""
    )
    fig.update_layout(
        height=800,
        xaxis_title="Rushing Yards per Game",
        yaxis_title="Teams",
        yaxis={'categoryorder':'total ascending'},
        showlegend=False,
        coloraxis_showscale=False
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Top 5 Teams for Rushing Yards per Game
    st.write(f"**Top 5 Rushing Offenses ({selected_season}):**")
    top_5_rush_yds = team_rushing_yards_ranked.head(5)
    st.dataframe(top_5_rush_yds, use_container_width=True, hide_index=True)

### --- Avg Passing/Rushing Yards Allowed Per Game --- ###
st.divider()
st.subheader(f"Avg Opponent Passing & Rushing Yards Per Game")
st.write(" ")

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
    st.write(f"Passing Yards Allowed ({selected_season})")
    results_passing_yards_allowed = []
    for team in filtered_df_teams['TeamID']:
        team_filtered_data = df_schedule_and_game_results_filtered[df_schedule_and_game_results_filtered['Team'] == team]
        avg_passing_yards_allowed = team_filtered_data['OppPassY'].mean()
        results_passing_yards_allowed.append({'Team': team.upper(), 'Avg Passing Yards Allowed': avg_passing_yards_allowed})
    
    # Create DataFrame and sort for chart
    df_passing_allowed_chart = pd.DataFrame(results_passing_yards_allowed)
    df_passing_allowed_chart_sorted = df_passing_allowed_chart.sort_values(by='Avg Passing Yards Allowed', ascending=True)
    
    # Create horizontal bar chart
    fig = px.bar(
        df_passing_allowed_chart_sorted,
        x='Avg Passing Yards Allowed',
        y='Team',
        orientation='h',
        color='Avg Passing Yards Allowed',
        color_continuous_scale='Blues',
        title=""
    )
    fig.update_layout(
        height=800,
        xaxis_title="Passing Yards Allowed per Game",
        yaxis_title="Teams",
        yaxis={'categoryorder':'total ascending'},
        showlegend=False,
        coloraxis_showscale=False
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Top 5 Teams Allowing the Fewest Passing Yards per Game
    st.write(f"**Top 5 Passing Defenses ({selected_season}):**")
    df_passing_allowed = pd.DataFrame(results_passing_yards_allowed)
    top_5_pass_allowed = df_passing_allowed.sort_values(by='Avg Passing Yards Allowed', ascending=True).head(5)
    st.dataframe(top_5_pass_allowed, use_container_width=True, hide_index=True)

# Rushing Yards Allowed
with col2:
    st.write(f"Rushing Yards Allowed ({selected_season})")
    results_rushing_yards_allowed = []
    for team in filtered_df_teams['TeamID']:
        team_filtered_data = df_schedule_and_game_results_filtered[df_schedule_and_game_results_filtered['Team'] == team]
        avg_rushing_yards_allowed = team_filtered_data['OppRushY'].mean()
        results_rushing_yards_allowed.append({'Team': team.upper(), 'Avg Rushing Yards Allowed': avg_rushing_yards_allowed})
    
    # Create DataFrame and sort for chart
    df_rushing_allowed_chart = pd.DataFrame(results_rushing_yards_allowed)
    df_rushing_allowed_chart_sorted = df_rushing_allowed_chart.sort_values(by='Avg Rushing Yards Allowed', ascending=True)
    
    # Create horizontal bar chart
    fig = px.bar(
        df_rushing_allowed_chart_sorted,
        x='Avg Rushing Yards Allowed',
        y='Team',
        orientation='h',
        color='Avg Rushing Yards Allowed',
        color_continuous_scale='Blues',
        title=""
    )
    fig.update_layout(
        height=800,
        xaxis_title="Rushing Yards Allowed per Game",
        yaxis_title="Teams",
        yaxis={'categoryorder':'total ascending'},
        showlegend=False,
        coloraxis_showscale=False
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Top 5 Teams Allowing the Fewest Rushing Yards per Game
    st.write(f"**Top 5 Rushing Defenses ({selected_season}):**")
    df_rushing_allowed = pd.DataFrame(results_rushing_yards_allowed)
    top_5_rush_allowed = df_rushing_allowed.sort_values(by='Avg Rushing Yards Allowed', ascending=True).head(5)
    st.dataframe(top_5_rush_allowed, use_container_width=True, hide_index=True)

### --- Passing vs Rushing Plays Called --- ###
st.divider()
st.subheader(f"Avg Passing vs Rushing Plays Called")
st.write(" ")

# Average Passing and Running Plays per Game for NFL Teams
df_team_game_logs_selected['season'] = selected_season
season_data = df_team_game_logs_selected[df_team_game_logs_selected['season'] == selected_season]
team_averages = season_data.groupby(team_name_col).agg({'pass_att': 'mean', 'rush_att': 'mean'}).reset_index()

# Convert team names to abbreviations
team_abbreviation_mapping = {
    'Arizona Cardinals': 'ARI', 'Atlanta Falcons': 'ATL', 'Baltimore Ravens': 'BAL', 'Buffalo Bills': 'BUF',
    'Carolina Panthers': 'CAR', 'Chicago Bears': 'CHI', 'Cincinnati Bengals': 'CIN', 'Cleveland Browns': 'CLE',
    'Dallas Cowboys': 'DAL', 'Denver Broncos': 'DEN', 'Detroit Lions': 'DET', 'Green Bay Packers': 'GB',
    'Houston Texans': 'HOU', 'Indianapolis Colts': 'IND', 'Jacksonville Jaguars': 'JAX', 'Kansas City Chiefs': 'KC',
    'Las Vegas Raiders': 'LVR', 'Los Angeles Chargers': 'LAC', 'Los Angeles Rams': 'LAR', 'Miami Dolphins': 'MIA',
    'Minnesota Vikings': 'MIN', 'New England Patriots': 'NE', 'New Orleans Saints': 'NO', 'New York Giants': 'NYG',
    'New York Jets': 'NYJ', 'Philadelphia Eagles': 'PHI', 'Pittsburgh Steelers': 'PIT', 'San Francisco 49ers': 'SF',
    'Seattle Seahawks': 'SEA', 'Tampa Bay Buccaneers': 'TB', 'Tennessee Titans': 'TEN', 'Washington Commanders': 'WAS'
}
team_averages['team_abbrev'] = team_averages[team_name_col].map(team_abbreviation_mapping)
team_averages = team_averages.dropna().reset_index(drop=True)

# Create vertical bar charts for passing and rushing plays
team_averages_pass_sorted = team_averages.sort_values('pass_att', ascending=False)
team_averages_rush_sorted = team_averages.sort_values('rush_att', ascending=False)

# Passing Plays Chart
st.markdown(f"<h5 style='text-align: center; color: grey;'>Passing Plays per Game ({selected_season})</h5>", unsafe_allow_html=True)
fig_pass = px.bar(
    team_averages_pass_sorted,
    x='team_abbrev',
    y='pass_att',
    color='pass_att',
    color_continuous_scale='Oranges',
    title=""
)
fig_pass.update_layout(
    height=700,
    xaxis_title="Teams",
    yaxis_title="Passing Plays per Game",
    xaxis={'categoryorder':'total descending'},
    showlegend=False,
    coloraxis_showscale=False
)
fig_pass.update_xaxes(tickangle=-45, tickfont_size=14)
fig_pass.update_yaxes(tickfont_size=14)
fig_pass.update_traces(texttemplate='%{y:.1f}', textposition='outside', textfont_color='#FF6B35')
st.plotly_chart(fig_pass, use_container_width=True)

st.write("#####")

# Rushing Plays Chart
st.markdown(f"<h5 style='text-align: center; color: grey;'>Running Plays per Game ({selected_season})</h5>", unsafe_allow_html=True)
fig_rush = px.bar(
    team_averages_rush_sorted,
    x='team_abbrev',
    y='rush_att',
    color='rush_att',
    color_continuous_scale='Oranges',
    title=""
)
fig_rush.update_layout(
    height=700,
    xaxis_title="Teams",
    yaxis_title="Running Plays per Game",
    xaxis={'categoryorder':'total descending'},
    showlegend=False,
    coloraxis_showscale=False
)
fig_rush.update_xaxes(tickangle=-45, tickfont_size=14)
fig_rush.update_yaxes(tickfont_size=14)
fig_rush.update_traces(texttemplate='%{y:.1f}', textposition='outside', textfont_color='#FF6B35')
st.plotly_chart(fig_rush, use_container_width=True)

### --- Sacks --- ###
st.divider()
st.subheader(f"Sacks")
st.write(" ")

# Sacks Analysis
years = [selected_season]
unplayed_games = df_team_game_logs[
    df_team_game_logs['game_id'].str.contains(str(selected_season)) &  
    ((df_team_game_logs['home_pts_off'].isnull() | (df_team_game_logs['home_pts_off'] == 0)) &
     (df_team_game_logs['away_pts_off'].isnull() | (df_team_game_logs['away_pts_off'] == 0)))
]
unplayed_game_ids = unplayed_games['game_id'].tolist()
df_team_game_logs_filtered = df_team_game_logs[~df_team_game_logs['game_id'].isin(unplayed_game_ids)].copy()
df_team_game_logs_filtered[['year', 'week', 'away_team', 'home_team']] = df_team_game_logs_filtered['game_id'].str.split('_', expand=True).iloc[:, :4]
df_team_game_logs_filtered.loc[:, 'year'] = df_team_game_logs_filtered['year'].astype(int)
df_team_game_logs_filtered.loc[:, 'week'] = df_team_game_logs_filtered['week'].astype(int)

for year in years:
    df_selected = df_team_game_logs_filtered[(df_team_game_logs_filtered['year'] == year) & (df_team_game_logs_filtered['week'] <= 18)]
    sack_stats = {
        'team': [],
        'sacks_made': [],
        'sacks_taken': []
    }
    teams = [
        'ARI', 'ATL', 'BAL', 'BUF', 'CAR', 'CHI', 'CIN', 'CLE',
        'DAL', 'DEN', 'DET', 'GB', 'HOU', 'IND', 'JAX', 'KC',
        'LVR', 'LAC', 'LAR', 'MIA', 'MIN', 'NE', 'NO', 'NYG',
        'NYJ', 'PHI', 'PIT', 'SF', 'SEA', 'TB', 'TEN', 'WAS'
    ]
    for team in teams:
        sacks_made = df_selected.loc[(df_selected['home_team'] == team), 'away_pass_sacked'].sum() + \
                     df_selected.loc[(df_selected['away_team'] == team), 'home_pass_sacked'].sum()
        sacks_taken = df_selected.loc[(df_selected['home_team'] == team), 'home_pass_sacked'].sum() + \
                      df_selected.loc[(df_selected['away_team'] == team), 'away_pass_sacked'].sum()
        sack_stats['team'].append(team)
        sack_stats['sacks_made'].append(sacks_made)
        sack_stats['sacks_taken'].append(sacks_taken)
    sack_stats_df = pd.DataFrame(sack_stats)
    sack_stats_df['average_sacks_made'] = sack_stats_df['sacks_made'] / len(df_selected['week'].unique())
    sack_stats_df['average_sacks_taken'] = sack_stats_df['sacks_taken'] / len(df_selected['week'].unique())

# Sacks Made Chart
st.markdown(f"<h5 style='text-align: center; color: grey;'>Total Sacks ({selected_season})</h5>", unsafe_allow_html=True)
sacks_made_sorted = sack_stats_df.sort_values('sacks_made', ascending=False)

chart_sacks = alt.Chart(sacks_made_sorted).mark_bar().encode(
    x=alt.X('team:N', title='Teams', sort='-y'),
    y=alt.Y('sacks_made:Q', title='Sacks Made'),
    # color=alt.Color('sacks_made:Q', scale=alt.Scale(range=['#2D1B69', '#7F3C8D']), legend=None),
    color=alt.Color('sacks_made:Q', scale=alt.Scale(scheme='magma', domain=[0, 120]), legend=None),
    tooltip=['team', alt.Tooltip('sacks_made:Q', format='.0f')]
).properties(
    title="",
    width=800,
    height=500
).configure_axisX(
    grid=False,
    labelColor='#333333',
    labelAngle=-45
).configure_axisY(
    grid=True,
    labelColor='#333333'
)
st.altair_chart(chart_sacks, use_container_width=True)

st.write("#####")

# Sacks Taken Chart
st.markdown(f"<h5 style='text-align: center; color: grey;'>Total Sacks Taken ({selected_season})</h5>", unsafe_allow_html=True)
sacks_taken_sorted = sack_stats_df.sort_values('sacks_taken', ascending=False)

chart_sacks_taken = alt.Chart(sacks_taken_sorted).mark_bar().encode(
    x=alt.X('team:N', title='Teams', sort='-y'),
    y=alt.Y('sacks_taken:Q', title='Sacks Taken'),
    # color=alt.Color('sacks_taken:Q', scale=alt.Scale(range=['#2D1B69', '#7F3C8D']), legend=None),
    color=alt.Color('sacks_taken:Q', scale=alt.Scale(scheme='magma', domain=[0, 120]), legend=None),
    tooltip=['team', alt.Tooltip('sacks_taken:Q', format='.0f')]
).properties(
    title="",
    width=800,
    height=500
).configure_axisX(
    grid=False,
    labelColor='#333333',
    labelAngle=-45
).configure_axisY(
    grid=True,
    labelColor='#333333'
)

st.altair_chart(chart_sacks_taken, use_container_width=True)

# Footer
from utils.footer import render_footer
render_footer()