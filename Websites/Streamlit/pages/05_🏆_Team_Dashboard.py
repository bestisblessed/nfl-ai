import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os
import plotly
import plotly.graph_objects as go
import numpy as np
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
import requests
from io import BytesIO

# Page configuration
st.set_page_config(
    page_title="🏆 Team Dashboard",
    page_icon="🏆",
    layout="wide"
)

### Data ###
st.title('Team Dashboard')

# Season selector
selected_season = st.selectbox("Select Season:", [2025, 2024], index=0)

df_teams = st.session_state['df_teams']
df_games = st.session_state['df_games']
df_playerstats = st.session_state['df_playerstats']
df_team_game_logs = st.session_state['df_all_team_game_logs']
df_schedule_and_game_results = st.session_state['df_schedule_and_game_results']
df_all_passing_rushing_receiving = st.session_state['df_all_passing_rushing_receiving']
df_team_game_logs_2024 = st.session_state['df_all_team_game_logs_2024']
df_team_game_logs_2025 = st.session_state['df_all_team_game_logs_2025']

# Select the appropriate dataset based on season
if selected_season == 2025:
    df_team_game_logs_selected = df_team_game_logs_2025
else:
    df_team_game_logs_selected = df_team_game_logs_2024

# Both datasets use the same column names
team_name_col = 'team_name'
week_col = 'week'
st.divider()

### Average Pass Yards and Rush Yards per Game for NFL Teams ###
df_team_game_logs_selected['season'] = selected_season
season_data = df_team_game_logs_selected[df_team_game_logs_selected['season'] == selected_season]
team_averages = season_data.groupby(team_name_col).agg({'pass_yds': 'mean', 'rush_yds': 'mean'}).reset_index()
team_averages = team_averages.sort_values(team_name_col)
fig, ax = plt.subplots(figsize=(14, 7))
x = range(len(team_averages))
bar_width = 0.35
bar1 = plt.bar(x, team_averages['pass_yds'], width=bar_width, label='Average Pass Yards per Game')
bar2 = plt.bar([i + bar_width for i in x], team_averages['rush_yds'], width=bar_width, label='Average Rush Yards per Game')
plt.xlabel('Teams')
plt.ylabel('Yards per Game')
plt.title(f'Average Pass Yards and Rush Yards per Game for NFL Teams ({selected_season} Season)')
plt.xticks([i + bar_width / 2 for i in x], team_averages[team_name_col], rotation=90)
plt.legend()
plt.tight_layout()
st.pyplot(plt)
top_5_pass_yds = team_averages[[team_name_col, 'pass_yds']].sort_values(by='pass_yds', ascending=False).head(5)
top_5_rush_yds = team_averages[[team_name_col, 'rush_yds']].sort_values(by='rush_yds', ascending=False).head(5)
col1, col2 = st.columns(2)
with col1:
    st.write(f"Top 5 Teams for Passing Yards per Game ({selected_season} Season):")
    st.write(top_5_pass_yds)
with col2:
    st.write(f"Top 5 Teams for Rushing Yards per Game ({selected_season} Season):")
    st.write(top_5_rush_yds)
st.divider()

### Average Pass Yards and Rush Yards Allowed per Game for NFL Teams ###
df_team_game_logs_selected['season'] = selected_season
season_data = df_team_game_logs_selected[df_team_game_logs_selected['season'] == selected_season]
defense_averages = season_data.groupby('opp').agg({'pass_yds': 'mean', 'rush_yds': 'mean'}).reset_index()
defense_averages.columns = ['Team_Name', 'pass_yards_allowed', 'rush_yards_allowed']
defense_averages = defense_averages.sort_values('Team_Name')
fig, ax = plt.subplots(figsize=(14, 7))
x_def = range(len(defense_averages))
bar_width_def = 0.35
bar1_def = plt.bar(x_def, defense_averages['pass_yards_allowed'], width=bar_width_def, label='Average Pass Yards Allowed per Game')
bar2_def = plt.bar([i + bar_width_def for i in x_def], defense_averages['rush_yards_allowed'], width=bar_width_def, label='Average Rush Yards Allowed per Game')
plt.xlabel('Teams')
plt.ylabel('Yards Allowed per Game')
plt.title(f'Average Pass Yards and Rush Yards Allowed per Game for NFL Teams ({selected_season} Season)')
plt.xticks([i + bar_width_def / 2 for i in x_def], defense_averages['Team_Name'], rotation=90)
plt.legend()
plt.tight_layout()
st.pyplot(plt)
top_5_pass_yards_allowed = defense_averages[['Team_Name', 'pass_yards_allowed']].sort_values(by='pass_yards_allowed', ascending=True).head(5)
bottom_5_pass_yards_allowed = defense_averages[['Team_Name', 'pass_yards_allowed']].sort_values(by='pass_yards_allowed', ascending=False).head(5)
top_5_rush_yards_allowed = defense_averages[['Team_Name', 'rush_yards_allowed']].sort_values(by='rush_yards_allowed', ascending=True).head(5)
bottom_5_rush_yards_allowed = defense_averages[['Team_Name', 'rush_yards_allowed']].sort_values(by='rush_yards_allowed', ascending=False).head(5)
col1, col2 = st.columns(2)
with col1:
    st.write(f"Top 5 Teams Allowing the Fewest Passing Yards per Game ({selected_season} Season):")
    st.write(top_5_pass_yards_allowed)
with col2:
    st.write(f"Top 5 Teams Allowing the Fewest Rushing Yards per Game ({selected_season} Season):")
    st.write(top_5_rush_yards_allowed)
st.divider()

### Average Passing and Running Plays per Game for NFL Teams ###
df_team_game_logs_selected['season'] = selected_season
season_data = df_team_game_logs_selected[df_team_game_logs_selected['season'] == selected_season]
team_averages = season_data.groupby(team_name_col).agg({'pass_att': 'mean', 'rush_att': 'mean'}).reset_index()
team_averages = team_averages.sort_values(team_name_col)
fig, ax = plt.subplots(figsize=(14, 7))
x = range(len(team_averages))
bar_width = 0.35
bar1 = plt.bar(x, team_averages['pass_att'], width=bar_width, label='Average Passing Plays per Game')
bar2 = plt.bar([i + bar_width for i in x], team_averages['rush_att'], width=bar_width, label='Average Running Plays per Game')
plt.xlabel('Teams')
plt.ylabel('Plays per Game')
plt.title(f'Average Passing and Running Plays per Game for NFL Teams ({selected_season} Season)')
plt.xticks([i + bar_width / 2 for i in x], team_averages[team_name_col], rotation=90)
plt.legend()
plt.tight_layout()
st.pyplot(plt)

### Average Passing and Running Plays per Game for NFL Teams continued ###
season_data = df_team_game_logs_selected[df_team_game_logs_selected['season'] == selected_season]
team_averages_pass_sorted = team_averages.sort_values('pass_att', ascending=False)
team_averages_rush_sorted = team_averages.sort_values('rush_att', ascending=False)
team_averages['combined_att'] = team_averages['pass_att'] + team_averages['rush_att']
team_averages_combined_sorted = team_averages.sort_values('combined_att', ascending=False)
fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(14, 15))
x_pass = range(len(team_averages_pass_sorted))
x_rush = range(len(team_averages_rush_sorted))
x_combined = range(len(team_averages_combined_sorted))
colors_pass = plt.cm.get_cmap('magma', len(team_averages_pass_sorted))
colors_rush = plt.cm.get_cmap('magma', len(team_averages_rush_sorted))
colors_combined = plt.cm.get_cmap('magma', len(team_averages_combined_sorted))
bars1 = ax1.bar(x_pass, team_averages_pass_sorted['pass_att'], color=colors_pass(range(len(team_averages_pass_sorted))))
for bar in bars1:
    ax1.text(bar.get_x() + bar.get_width() / 2, bar.get_height(), f'{bar.get_height():.1f}', ha='center', va='bottom', fontsize=10)
ax1.set_xlabel('Teams')
ax1.set_ylabel('Passing Plays per Game')
ax1.set_title(f'Average Passing Plays per Game for NFL Teams ({selected_season} Season)')
ax1.set_xticks([i for i in x_pass])
ax1.set_xticklabels(team_averages_pass_sorted[team_name_col], rotation=90)
ax1.grid(True, which='both', axis='y', linestyle='--', linewidth=0.7)
bars2 = ax2.bar(x_rush, team_averages_rush_sorted['rush_att'], color=colors_rush(range(len(team_averages_rush_sorted))))
for bar in bars2:
    ax2.text(bar.get_x() + bar.get_width() / 2, bar.get_height(), f'{bar.get_height():.1f}', ha='center', va='bottom', fontsize=10)
ax2.set_xlabel('Teams')
ax2.set_ylabel('Running Plays per Game')
ax2.set_title(f'Average Running Plays per Game for NFL Teams ({selected_season} Season)')
ax2.set_xticks([i for i in x_rush])
ax2.set_xticklabels(team_averages_rush_sorted[team_name_col], rotation=90)
ax2.grid(True, which='both', axis='y', linestyle='--', linewidth=0.7)
bars3 = ax3.bar(x_combined, team_averages_combined_sorted['combined_att'], color=colors_combined(range(len(team_averages_combined_sorted))))
for bar in bars3:
    ax3.text(bar.get_x() + bar.get_width() / 2, bar.get_height(), f'{bar.get_height():.1f}', ha='center', va='bottom', fontsize=10)
ax3.set_xlabel('Teams')
ax3.set_ylabel('Combined Plays per Game')
ax3.set_title(f'Average Combined Plays (Passing + Running) per Game for NFL Teams ({selected_season} Season)')
ax3.set_xticks([i for i in x_combined])
ax3.set_xticklabels(team_averages_combined_sorted[team_name_col], rotation=90)
ax3.grid(True, which='both', axis='y', linestyle='--', linewidth=0.7)
plt.tight_layout()
st.pyplot(plt)
st.divider()

### Sacks ###
years = [selected_season]
unplayed_games = df_team_game_logs[
    df_team_game_logs['game_id'].str.contains(str(selected_season)) &  
    ((df_team_game_logs['home_pts_off'].isnull() | (df_team_game_logs['home_pts_off'] == 0)) &
     (df_team_game_logs['away_pts_off'].isnull() | (df_team_game_logs['away_pts_off'] == 0)))
]
unplayed_game_ids = unplayed_games['game_id'].tolist()
df_team_game_logs = df_team_game_logs[~df_team_game_logs['game_id'].isin(unplayed_game_ids)]
st.write("Unplayed games removed and updated CSV saved.")
df_team_game_logs[['year', 'week', 'away_team', 'home_team']] = df_team_game_logs['game_id'].str.split('_', expand=True).iloc[:, :4]
df_team_game_logs['year'] = df_team_game_logs['year'].astype(int)
df_team_game_logs['week'] = df_team_game_logs['week'].astype(int)
for year in years:
    df_selected = df_team_game_logs[(df_team_game_logs['year'] == year) & (df_team_game_logs['week'] <= 18)]
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
    sacks_made_sorted = sack_stats_df[['team', 'sacks_made', 'average_sacks_made']].sort_values(by='sacks_made', ascending=False)
    sacks_taken_sorted = sack_stats_df[['team', 'sacks_taken', 'average_sacks_taken']].sort_values(by='sacks_taken', ascending=False)
    st.write(sacks_taken_sorted)
    st.write()
    st.write()
sack_stats_df_sorted = sack_stats_df.sort_values(by=['sacks_made', 'sacks_taken'], ascending=False)
teams = sack_stats_df_sorted['team'].tolist()
sacks_made = sack_stats_df_sorted['sacks_made'].tolist()
sacks_taken = sack_stats_df_sorted['sacks_taken'].tolist()
x = np.arange(len(teams))  
fig, ax1 = plt.subplots(figsize=(14, 6))
rects1 = ax1.bar(x, sacks_made, color='green')
ax1.set_xlabel('Teams')
ax1.set_ylabel('Sacks Made')
ax1.set_title('Sacks Made for All NFL Teams')
ax1.set_xticks(x)
ax1.set_xticklabels(teams, rotation=90)  
def autolabel(rects, ax):
    """Attach a text label above each bar displaying its height."""
    for rect in rects:
        height = rect.get_height()
        ax.annotate(f'{height:.1f}',
                    xy=(rect.get_x() + rect.get_width() / 2, height),
                    xytext=(0, 3),  
                    textcoords="offset points",
                    ha='center', va='bottom')
autolabel(rects1, ax1)
plt.tight_layout()
st.pyplot(fig)  
st.divider()



# COMMENTED OUT - Explosive Play Rates section
# import streamlit as st
# import matplotlib.pyplot as plt
# import seaborn as sns
# import pandas as pd
# import matplotlib.image as mpimg
# from matplotlib.offsetbox import OffsetImage, AnnotationBbox
# st.title(f"Explosive Play Rates After Week 3 - {selected_season} NFL Season")
# teams = [
#     'crd', 'atl', 'rav', 'buf', 'car', 'chi', 'cin', 'cle', 'dal', 'den',
#     'det', 'gnb', 'htx', 'clt', 'jax', 'kan', 'sdg', 'ram', 'rai', 'mia',
#     'min', 'nwe', 'nor', 'nyg', 'nyj', 'phi', 'pit', 'sea', 'sfo', 'tam',
#     'oti', 'was'
# ]
# explosive_play_rates = [
#     14.1, 13.2, 10.9, 10.9, 10.4, 10.4, 10.4, 10.3, 
#     10.2, 10.0, 9.3, 9.3, 9.1, 8.0, 7.9, 7.8, 7.7, 
#     7.5, 7.4, 7.3, 7.2, 7.0, 6.9, 6.1, 5.4, 6.0, 
#     6.5, 5.9, 6.3, 6.2, 5.8, 5.3
# ]
# df = pd.DataFrame({
#     'Team': teams,
#     'Explosive Play Rate (%)': explosive_play_rates
# })
# plt.figure(figsize=(14, 8))
# ax = sns.barplot(
#     x='Team', 
#     y='Explosive Play Rate (%)', 
#     data=df,
#     palette="coolwarm"
# )
# for index, value in enumerate(df['Explosive Play Rate (%)']):
#     ax.text(index, value + 0.2, f'{value}%', ha='center', va='bottom', fontsize=10, fontweight='bold')

# # Add this mapping dictionary after the teams list
# team_abbrev_mapping = {
#     'crd': 'ARI', 'atl': 'ATL', 'rav': 'BAL', 'buf': 'BUF', 
#     'car': 'CAR', 'chi': 'CHI', 'cin': 'CIN', 'cle': 'CLE',
#     'dal': 'DAL', 'den': 'DEN', 'det': 'DET', 'gnb': 'GB',
#     'htx': 'HOU', 'clt': 'IND', 'jax': 'JAX', 'kan': 'KC',
#     'sdg': 'LAC', 'ram': 'LAR', 'rai': 'LVR', 'mia': 'MIA',
#     'min': 'MIN', 'nwe': 'NE', 'nor': 'NO', 'nyg': 'NYG',
#     'nyj': 'NYJ', 'phi': 'PHI', 'pit': 'PIT', 'sea': 'SEA',
#     'sfo': 'SF', 'tam': 'TB', 'oti': 'TEN', 'was': 'WAS'
# }

# # Update the add_team_logo function to use the mapping
# def add_team_logo(axes, team_abbreviation, xpos, ypos):
#     mapped_team = team_abbrev_mapping[team_abbreviation]
#     img_path = f'images/team-logos/{mapped_team}.png'  
#     logo = mpimg.imread(img_path)
#     imagebox = OffsetImage(logo, zoom=0.15)
#     ab = AnnotationBbox(imagebox, (xpos, ypos), frameon=False, box_alignment=(0.5, -0.15))
#     axes.add_artist(ab)

# for i, team in enumerate(df['Team']):
#     add_team_logo(ax, team, i, 0)
# plt.title(f'Explosive Play Rates After Week 3 {selected_season} NFL Season\n(10+ yard run or 20+ yard pass)', fontsize=14, weight='bold')
# plt.xlabel('')
# plt.ylabel('Explosive Play Rate (%)')
# ax.set_xticklabels([''] * len(teams))
# plt.grid(True, axis='y', linestyle='--', alpha=0.7)
# st.pyplot(plt)
# st.divider()


import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
years = [selected_season]
unplayed_games = df_team_game_logs[
    df_team_game_logs['game_id'].str.contains(str(selected_season)) &  
    ((df_team_game_logs['home_pts_off'].isnull() | (df_team_game_logs['home_pts_off'] == 0)) &
     (df_team_game_logs['away_pts_off'].isnull() | (df_team_game_logs['away_pts_off'] == 0)))
]
unplayed_game_ids = unplayed_games['game_id'].tolist()
df_team_game_logs = df_team_game_logs[~df_team_game_logs['game_id'].isin(unplayed_game_ids)]
st.write("Unplayed games removed and updated CSV saved.")
df_team_game_logs[['year', 'week', 'away_team', 'home_team']] = df_team_game_logs['game_id'].str.split('_', expand=True).iloc[:, :4]
df_team_game_logs['year'] = df_team_game_logs['year'].astype(int)
df_team_game_logs['week'] = df_team_game_logs['week'].astype(int)
for year in years:
    df_selected = df_team_game_logs[(df_team_game_logs['year'] == year) & (df_team_game_logs['week'] <= 18)]
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