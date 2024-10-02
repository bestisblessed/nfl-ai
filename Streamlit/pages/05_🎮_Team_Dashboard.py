import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os
from Home import df_teams, df_games, df_playerstats, df_team_game_logs, df_schedule_and_game_results
import plotly
import plotly.graph_objects as go
import numpy as np
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
import requests
from io import BytesIO

# Set up the page
st.title('Team Dashboard')
df_teams = st.session_state['df_teams']
df_games = st.session_state['df_games']
df_playerstats = st.session_state['df_playerstats']
df_team_game_logs = st.session_state['df_team_game_logs']
df_schedule_and_game_results = st.session_state['df_schedule_and_game_results']
st.divider()

import pandas as pd
import matplotlib.pyplot as plt

# Load the dataset
file_path = "data/all_team_game_logs.csv"
data = pd.read_csv(file_path)

# Filter dataset for the 2024 season
season_2024_data = data[data['season'] == 2024]

# Group by team and calculate the average pass_yds and rush_yds per game
team_averages = season_2024_data.groupby('Team_Name').agg({'pass_yds': 'mean', 'rush_yds': 'mean'}).reset_index()

# Sort the data by team name for consistent plotting
team_averages = team_averages.sort_values('Team_Name')

# Plotting the double bar graph
fig, ax = plt.subplots(figsize=(14, 7))

# Define the x locations for the groups
x = range(len(team_averages))

# Bar positions for each metric
bar_width = 0.35
bar1 = plt.bar(x, team_averages['pass_yds'], width=bar_width, label='Average Pass Yards per Game')
bar2 = plt.bar([i + bar_width for i in x], team_averages['rush_yds'], width=bar_width, label='Average Rush Yards per Game')

# Set labels and title
plt.xlabel('Teams')
plt.ylabel('Yards per Game')
plt.title('Average Pass Yards and Rush Yards per Game for NFL Teams (2024 Season)')
plt.xticks([i + bar_width / 2 for i in x], team_averages['Team_Name'], rotation=90)
plt.legend()

# Display the plot
plt.tight_layout()
# plt.show()
st.pyplot(plt)

# Find top 5 teams for average pass yards and rush yards per game
top_5_pass_yds = team_averages[['Team_Name', 'pass_yds']].sort_values(by='pass_yds', ascending=False).head(5)
top_5_rush_yds = team_averages[['Team_Name', 'rush_yds']].sort_values(by='rush_yds', ascending=False).head(5)

# # Display the top 5 teams for passing and rushing yards per game
# st.write("Top 5 Teams for Passing Yards per Game (2024 Season):")
# st.write(top_5_pass_yds)

# st.write("\nTop 5 Teams for Rushing Yards per Game (2024 Season):")
# st.write(top_5_rush_yds)
# Create two columns for passing and rushing yards
col1, col2 = st.columns(2)

# Display top 5 passing yards in the first column
with col1:
    st.write("Top 5 Teams for Passing Yards per Game (2024 Season):")
    st.write(top_5_pass_yds)

# Display top 5 rushing yards in the second column
with col2:
    st.write("Top 5 Teams for Rushing Yards per Game (2024 Season):")
    st.write(top_5_rush_yds)


st.divider()


import pandas as pd
import matplotlib.pyplot as plt

# Load the dataset
file_path = "data/all_team_game_logs.csv"
data = pd.read_csv(file_path)

# Filter dataset for the 2024 season
season_2024_data = data[data['season'] == 2024]

# Group by team and calculate the average pass and rush yards allowed per game based on the opponent's performance
defense_averages = season_2024_data.groupby('opp').agg({'pass_yds': 'mean', 'rush_yds': 'mean'}).reset_index()
defense_averages.columns = ['Team_Name', 'pass_yards_allowed', 'rush_yards_allowed']

# Sort the data by team name for consistent plotting
defense_averages = defense_averages.sort_values('Team_Name')

# Plotting the double bar graph for defensive metrics
fig, ax = plt.subplots(figsize=(14, 7))

# Define the x locations for the groups
x_def = range(len(defense_averages))

# Bar positions for each metric
bar_width_def = 0.35
bar1_def = plt.bar(x_def, defense_averages['pass_yards_allowed'], width=bar_width_def, label='Average Pass Yards Allowed per Game')
bar2_def = plt.bar([i + bar_width_def for i in x_def], defense_averages['rush_yards_allowed'], width=bar_width_def, label='Average Rush Yards Allowed per Game')

# Set labels and title
plt.xlabel('Teams')
plt.ylabel('Yards Allowed per Game')
plt.title('Average Pass Yards and Rush Yards Allowed per Game for NFL Teams (2024 Season)')
plt.xticks([i + bar_width_def / 2 for i in x_def], defense_averages['Team_Name'], rotation=90)
plt.legend()

# Display the plot
plt.tight_layout()
# plt.show()
st.pyplot(plt)

# Find top 5 and bottom 5 teams for pass yards and rush yards allowed per game
top_5_pass_yards_allowed = defense_averages[['Team_Name', 'pass_yards_allowed']].sort_values(by='pass_yards_allowed', ascending=True).head(5)
bottom_5_pass_yards_allowed = defense_averages[['Team_Name', 'pass_yards_allowed']].sort_values(by='pass_yards_allowed', ascending=False).head(5)

top_5_rush_yards_allowed = defense_averages[['Team_Name', 'rush_yards_allowed']].sort_values(by='rush_yards_allowed', ascending=True).head(5)
bottom_5_rush_yards_allowed = defense_averages[['Team_Name', 'rush_yards_allowed']].sort_values(by='rush_yards_allowed', ascending=False).head(5)

# # Display the top 5 and bottom 5 teams
# st.write("Top 5 Teams Allowing the Fewest Passing Yards per Game (2024 Season):")
# st.write(top_5_pass_yards_allowed)

# # st.write("\nBottom 5 Teams Allowing the Most Passing Yards per Game (2024 Season):")
# # st.write(bottom_5_pass_yards_allowed)

# st.write("\nTop 5 Teams Allowing the Fewest Rushing Yards per Game (2024 Season):")
# st.write(top_5_rush_yards_allowed)

# # st.write("\nBottom 5 Teams Allowing the Most Rushing Yards per Game (2024 Season):")
# # st.write(bottom_5_rush_yards_allowed)
# Create two columns for passing yards
col1, col2 = st.columns(2)

# Display top 5 and bottom 5 for passing yards in two columns
with col1:
    st.write("Top 5 Teams Allowing the Fewest Passing Yards per Game (2024 Season):")
    st.write(top_5_pass_yards_allowed)

with col2:
    st.write("Top 5 Teams Allowing the Fewest Rushing Yards per Game (2024 Season):")
    st.write(top_5_rush_yards_allowed)

st.divider()

# Sacks Given & Taken
# years = [2021, 2022, 2023, 2024]
years = [2024]

unplayed_games = df_team_game_logs[
    df_team_game_logs['game_id'].str.contains('2024') &  # Check if 'game_id' contains "2024"
    ((df_team_game_logs['home_pts_off'].isnull() | (df_team_game_logs['home_pts_off'] == 0)) &
     (df_team_game_logs['away_pts_off'].isnull() | (df_team_game_logs['away_pts_off'] == 0)))
]
unplayed_game_ids = unplayed_games['game_id'].tolist()
df_team_game_logs = df_team_game_logs[~df_team_game_logs['game_id'].isin(unplayed_game_ids)]
# df_team_game_logs.to_csv('data/all_team_game_logs.csv', index=False)
st.write("Unplayed games removed and updated CSV saved.")

# Extract year and week from 'game_id'
df_team_game_logs[['year', 'week', 'away_team', 'home_team']] = df_team_game_logs['game_id'].str.split('_', expand=True).iloc[:, :4]
df_team_game_logs['year'] = df_team_game_logs['year'].astype(int)
df_team_game_logs['week'] = df_team_game_logs['week'].astype(int)

for year in years:
    df_2023 = df_team_game_logs[(df_team_game_logs['year'] == year) & (df_team_game_logs['week'] <= 18)]
    
    # Initialize a dictionary to track sacks made and sacks taken
    sack_stats = {
        'team': [],
        'sacks_made': [],
        'sacks_taken': []
    }
    
    # List of all 32 NFL teams
    teams = [
        'ARI', 'ATL', 'BAL', 'BUF', 'CAR', 'CHI', 'CIN', 'CLE',
        'DAL', 'DEN', 'DET', 'GB', 'HOU', 'IND', 'JAX', 'KC',
        'LVR', 'LAC', 'LAR', 'MIA', 'MIN', 'NE', 'NO', 'NYG',
        'NYJ', 'PHI', 'PIT', 'SF', 'SEA', 'TB', 'TEN', 'WAS'
    ]
    
    # Calculate the sacks made and sacks taken for each team
    for team in teams:
        # Sacks made by the team's defense (home and away games)
        sacks_made = df_2023.loc[(df_2023['home_team'] == team), 'away_pass_sacked'].sum() + \
                     df_2023.loc[(df_2023['away_team'] == team), 'home_pass_sacked'].sum()
        
        # Sacks taken (against the team) - includes home and away games
        sacks_taken = df_2023.loc[(df_2023['home_team'] == team), 'home_pass_sacked'].sum() + \
                      df_2023.loc[(df_2023['away_team'] == team), 'away_pass_sacked'].sum()
        
        # Store results
        sack_stats['team'].append(team)
        sack_stats['sacks_made'].append(sacks_made)
        sack_stats['sacks_taken'].append(sacks_taken)
    
    # Convert the dictionary to a DataFrame
    sack_stats_df = pd.DataFrame(sack_stats)
    
    # # Calculate average sacks made and taken (if needed by game or for total analysis)
    sack_stats_df['average_sacks_made'] = sack_stats_df['sacks_made'] / len(df_2023['week'].unique())
    sack_stats_df['average_sacks_taken'] = sack_stats_df['sacks_taken'] / len(df_2023['week'].unique())
    
    sacks_made_sorted = sack_stats_df[['team', 'sacks_made', 'average_sacks_made']].sort_values(by='sacks_made', ascending=False)
    sacks_taken_sorted = sack_stats_df[['team', 'sacks_taken', 'average_sacks_taken']].sort_values(by='sacks_taken', ascending=False)

    
    # st.write("\nTeams Sorted by Sacks Taken:")
    # st.write(tabulate(sacks_taken_sorted, headers='keys', tablefmt='grid'))
    st.write(sacks_taken_sorted)
    # sacks_taken_sorted.to_csv(f'data/sacks_taken_sorted_{year}.csv', index=False)
    st.write()
    st.write()

# # Code for plotting Sacks Made and Sacks Taken
# # Get the list of teams from the unique team values in your dataset
# teams = sack_stats_df['team'].tolist()

# # Ensure we match the correct sacks made and sacks taken for each team
# sacks_made = [sack_stats_df[sack_stats_df['team'] == team]['sacks_made'].values[0] for team in teams]
# sacks_taken = [sack_stats_df[sack_stats_df['team'] == team]['sacks_taken'].values[0] for team in teams]
# Sort sack_stats_df by sacks made and taken
sack_stats_df_sorted = sack_stats_df.sort_values(by=['sacks_made', 'sacks_taken'], ascending=False)

# Get the list of teams from the sorted DataFrame
teams = sack_stats_df_sorted['team'].tolist()

# Ensure we match the correct sacks made and sacks taken for each team
sacks_made = sack_stats_df_sorted['sacks_made'].tolist()
sacks_taken = sack_stats_df_sorted['sacks_taken'].tolist()

# Create the x locations for the teams
# x = np.arange(len(teams))  # Label locations

# # Create two subplots: one for sacks made and one for sacks taken
# fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 12))

# # Bar chart for sacks made
# rects1 = ax1.bar(x, sacks_made, color='green')
# ax1.set_xlabel('Teams')
# ax1.set_ylabel('Sacks Made')
# ax1.set_title('Sacks Made for All NFL Teams')
# ax1.set_xticks(x)
# ax1.set_xticklabels(teams, rotation=90)  # Rotate team labels for better visibility

# # Add value labels on top of the bars
# def autolabel(rects, ax):
#     """Attach a text label above each bar displaying its height."""
#     for rect in rects:
#         height = rect.get_height()
#         ax.annotate(f'{height:.1f}',
#                     xy=(rect.get_x() + rect.get_width() / 2, height),
#                     xytext=(0, 3),  # 3 points vertical offset
#                     textcoords="offset points",
#                     ha='center', va='bottom')

# # Add value labels to both bar charts
# autolabel(rects1, ax1)

# # Ensure layout fits well with rotated labels
# plt.tight_layout()

# # Display the plots in Streamlit
# st.pyplot(fig)  # Use Streamlit to display the Matplotlib figure
# Create the x locations for the teams
x = np.arange(len(teams))  # Label locations

# Create a single plot for sacks made
fig, ax1 = plt.subplots(figsize=(14, 6))

# Bar chart for sacks made
rects1 = ax1.bar(x, sacks_made, color='green')
ax1.set_xlabel('Teams')
ax1.set_ylabel('Sacks Made')
ax1.set_title('Sacks Made for All NFL Teams')
ax1.set_xticks(x)
ax1.set_xticklabels(teams, rotation=90)  # Rotate team labels for better visibility

# Add value labels on top of the bars
def autolabel(rects, ax):
    """Attach a text label above each bar displaying its height."""
    for rect in rects:
        height = rect.get_height()
        ax.annotate(f'{height:.1f}',
                    xy=(rect.get_x() + rect.get_width() / 2, height),
                    xytext=(0, 3),  # 3 points vertical offset
                    textcoords="offset points",
                    ha='center', va='bottom')

# Add value labels to the bar chart
autolabel(rects1, ax1)

# Ensure layout fits well with rotated labels
plt.tight_layout()

# Display the plot in Streamlit
st.pyplot(fig)  # Use Streamlit to display the Matplotlib figure

st.divider()

import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import matplotlib.image as mpimg
from matplotlib.offsetbox import OffsetImage, AnnotationBbox

# Streamlit title
st.title("Explosive Play Rates After Week 3 - 2024 NFL Season")

# List of teams and their explosive play rates
teams = [
    'crd', 'atl', 'rav', 'buf', 'car', 'chi', 'cin', 'cle', 'dal', 'den',
    'det', 'gnb', 'htx', 'clt', 'jax', 'kan', 'sdg', 'ram', 'rai', 'mia',
    'min', 'nwe', 'nor', 'nyg', 'nyj', 'phi', 'pit', 'sea', 'sfo', 'tam',
    'oti', 'was'
]

explosive_play_rates = [
    14.1, 13.2, 10.9, 10.9, 10.4, 10.4, 10.4, 10.3, 
    10.2, 10.0, 9.3, 9.3, 9.1, 8.0, 7.9, 7.8, 7.7, 
    7.5, 7.4, 7.3, 7.2, 7.0, 6.9, 6.1, 5.4, 6.0, 
    6.5, 5.9, 6.3, 6.2, 5.8, 5.3
]

# Create a DataFrame
df = pd.DataFrame({
    'Team': teams,
    'Explosive Play Rate (%)': explosive_play_rates
})

# Set the plot size
plt.figure(figsize=(14, 8))

# Create the barplot
ax = sns.barplot(
    x='Team', 
    y='Explosive Play Rate (%)', 
    data=df, 
    palette="coolwarm"
)

# Add data labels above the bars
for index, value in enumerate(df['Explosive Play Rate (%)']):
    ax.text(index, value + 0.2, f'{value}%', ha='center', va='bottom', fontsize=10, fontweight='bold')

# Function to add team logos
def add_team_logo(axes, team_abbreviation, xpos, ypos):
    img_path = f'images/team-logos/{team_abbreviation}.png'  # Adjust the path based on your setup
    logo = mpimg.imread(img_path)
    imagebox = OffsetImage(logo, zoom=0.15)
    ab = AnnotationBbox(imagebox, (xpos, ypos), frameon=False, box_alignment=(0.5, -0.15))
    axes.add_artist(ab)

# Add logos below each bar
for i, team in enumerate(df['Team']):
    add_team_logo(ax, team, i, 0)

# Set chart title and labels
plt.title('Explosive Play Rates After Week 3 2024 NFL Season\n(10+ yard run or 20+ yard pass)', fontsize=14, weight='bold')
plt.xlabel('')
plt.ylabel('Explosive Play Rate (%)')

# Hide x-axis labels (since we're using logos)
ax.set_xticklabels([''] * len(teams))

# Show the grid for better readability
plt.grid(True, axis='y', linestyle='--', alpha=0.7)

# Display the chart in Streamlit
st.pyplot(plt)

st.divider()


# %matplotlib inline
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Load CSV (adjust the path as needed)
# df_team_game_logs = pd.read_csv('./data/all_team_game_logs.csv')

# Sacks Given & Taken
years = [2024]

unplayed_games = df_team_game_logs[
    df_team_game_logs['game_id'].str.contains('2024') &  # Check if 'game_id' contains "2024"
    ((df_team_game_logs['home_pts_off'].isnull() | (df_team_game_logs['home_pts_off'] == 0)) &
     (df_team_game_logs['away_pts_off'].isnull() | (df_team_game_logs['away_pts_off'] == 0)))
]
unplayed_game_ids = unplayed_games['game_id'].tolist()
df_team_game_logs = df_team_game_logs[~df_team_game_logs['game_id'].isin(unplayed_game_ids)]
st.write("Unplayed games removed and updated CSV saved.")

# Extract year and week from 'game_id'
df_team_game_logs[['year', 'week', 'away_team', 'home_team']] = df_team_game_logs['game_id'].str.split('_', expand=True).iloc[:, :4]
df_team_game_logs['year'] = df_team_game_logs['year'].astype(int)
df_team_game_logs['week'] = df_team_game_logs['week'].astype(int)
for year in years:
    df_2023 = df_team_game_logs[(df_team_game_logs['year'] == year) & (df_team_game_logs['week'] <= 18)]
    
    # Initialize a dictionary to track sacks made and sacks taken
    sack_stats = {
        'team': [],
        'sacks_made': [],
        'sacks_taken': []
    }
    
    # List of all 32 NFL teams
    teams = [
        'ARI', 'ATL', 'BAL', 'BUF', 'CAR', 'CHI', 'CIN', 'CLE',
        'DAL', 'DEN', 'DET', 'GB', 'HOU', 'IND', 'JAX', 'KC',
        'LVR', 'LAC', 'LAR', 'MIA', 'MIN', 'NE', 'NO', 'NYG',
        'NYJ', 'PHI', 'PIT', 'SF', 'SEA', 'TB', 'TEN', 'WAS'
    ]
    
    # Calculate the sacks made and sacks taken for each team
    for team in teams:
        sacks_made = df_2023.loc[(df_2023['home_team'] == team), 'away_pass_sacked'].sum() + \
                     df_2023.loc[(df_2023['away_team'] == team), 'home_pass_sacked'].sum()
        
        sacks_taken = df_2023.loc[(df_2023['home_team'] == team), 'home_pass_sacked'].sum() + \
                      df_2023.loc[(df_2023['away_team'] == team), 'away_pass_sacked'].sum()
        
        sack_stats['team'].append(team)
        sack_stats['sacks_made'].append(sacks_made)
        sack_stats['sacks_taken'].append(sacks_taken)
    
sack_stats_df = pd.DataFrame(sack_stats)
    
# Map team logos to their respective file paths in the 'images/team-logos/' directory
team_logos = {
    'ARI': 'images/team-logos/crd.png',
    'ATL': 'images/team-logos/atl.png',
    'BAL': 'images/team-logos/rav.png',
    'BUF': 'images/team-logos/buf.png',
    'CAR': 'images/team-logos/car.png',
    'CHI': 'images/team-logos/chi.png',
    'CIN': 'images/team-logos/cin.png',
    'CLE': 'images/team-logos/cle.png',
    'DAL': 'images/team-logos/dal.png',
    'DEN': 'images/team-logos/den.png',
    'DET': 'images/team-logos/det.png',
    'GB': 'images/team-logos/gnb.png',
    'HOU': 'images/team-logos/htx.png',
    'IND': 'images/team-logos/clt.png',
    'JAX': 'images/team-logos/jax.png',
    'KC': 'images/team-logos/kan.png',
    'LAC': 'images/team-logos/sdg.png',
    'LAR': 'images/team-logos/ram.png',
    'LVR': 'images/team-logos/rai.png',
    'MIA': 'images/team-logos/mia.png',
    'MIN': 'images/team-logos/min.png',
    'NE': 'images/team-logos/nwe.png',
    'NO': 'images/team-logos/nor.png',
    'NYG': 'images/team-logos/nyg.png',
    'NYJ': 'images/team-logos/nyj.png',
    'PHI': 'images/team-logos/phi.png',
    'PIT': 'images/team-logos/pit.png',
    'SEA': 'images/team-logos/sea.png',
    'SF': 'images/team-logos/sfo.png',
    'TB': 'images/team-logos/tam.png',
    'TEN': 'images/team-logos/oti.png',
    'WAS': 'images/team-logos/was.png',
}

# Function to add team logos on top of the bars
def autolabel_with_logos(rects, ax, labels):
    """Attach an image above each bar displaying the team logo."""
    for rect, label in zip(rects, labels):
        # Load the logo image
        img = Image.open(team_logos[label])
        
        # Set the position for the image (centered on the bar and above the bar)
        height = rect.get_height()
        imagebox = OffsetImage(img, zoom=0.15)  # Adjust the zoom as needed
        ab = AnnotationBbox(imagebox, (rect.get_x() + rect.get_width() / 2, height + 1),
                            frameon=False, xycoords='data', box_alignment=(0.5, 0))
        
        ax.add_artist(ab)

# Sort sack_stats_df by sacks made and taken
sack_stats_df_sorted = sack_stats_df.sort_values(by=['sacks_made', 'sacks_taken'], ascending=False)

# Get the list of teams from the sorted DataFrame
teams = sack_stats_df_sorted['team'].tolist()
sacks_made = sack_stats_df_sorted['sacks_made'].tolist()

# Create the
# Create the x locations for the teams
x = np.arange(len(teams))  # Label locations

# Create a single plot for sacks made
fig, ax1 = plt.subplots(figsize=(14, 6))

# Bar chart for sacks made
rects1 = ax1.bar(x, sacks_made, color='green')
ax1.set_xlabel('Teams')
ax1.set_ylabel('Sacks Made')
ax1.set_title('Sacks Made for All NFL Teams')
ax1.set_xticks(x)
ax1.set_xticklabels(teams, rotation=90)  # Rotate team labels for better visibility

# Call autolabel with logos
autolabel_with_logos(rects1, ax1, teams)

# Ensure layout fits well with rotated labels
plt.tight_layout()

# Display the plot
# plt.show()
st.pyplot(plt)

st.divider()