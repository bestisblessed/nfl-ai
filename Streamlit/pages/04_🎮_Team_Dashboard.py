import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os
from Home import df_teams, df_games, df_playerstats, df_team_game_logs, df_schedule_and_game_results
import plotly
import plotly.graph_objects as go
import numpy as np


# Set up the page
st.title('Team Dashboard')
df_teams = st.session_state['df_teams']
df_games = st.session_state['df_games']
df_playerstats = st.session_state['df_playerstats']
df_team_game_logs = st.session_state['df_team_game_logs']
df_schedule_and_game_results = st.session_state['df_schedule_and_game_results']
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
        'LV', 'LAC', 'LAR', 'MIA', 'MIN', 'NE', 'NO', 'NYG',
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



# # Get the list of teams from the unique team values in your dataset
# teams = sacks_made_2024_filtered['team'].tolist()

# # Ensure we match the correct sacks made and sacks taken for each team
# sacks_made = [sacks_made_2024_filtered[sacks_made_2024_filtered['team'] == team]['sacks_made'].values[0] for team in teams]
# sacks_taken = [sacks_taken_2024_filtered[sacks_taken_2024_filtered['team'] == team]['sacks_taken'].values[0] for team in teams]

# # Create the x locations for the teams
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

# # Bar chart for sacks taken
# rects2 = ax2.bar(x, sacks_taken, color='red')
# ax2.set_xlabel('Teams')
# ax2.set_ylabel('Sacks Taken')
# ax2.set_title('Sacks Taken for All NFL Teams')
# ax2.set_xticks(x)
# ax2.set_xticklabels(teams, rotation=90)

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
# autolabel(rects2, ax2)

# # Ensure layout fits well with rotated labels
# plt.tight_layout()
# plt.show()

# Code for plotting Sacks Made and Sacks Taken
# Get the list of teams from the unique team values in your dataset
# teams = sack_stats_df['team'].tolist()

# # Ensure we match the correct sacks made and sacks taken for each team
# sacks_made = [sack_stats_df[sack_stats_df['team'] == team]['sacks_made'].values[0] for team in teams]
# sacks_taken = [sack_stats_df[sack_stats_df['team'] == team]['sacks_taken'].values[0] for team in teams]

# # Create the x locations for the teams
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

# # Bar chart for sacks taken
# rects2 = ax2.bar(x, sacks_taken, color='red')
# ax2.set_xlabel('Teams')
# ax2.set_ylabel('Sacks Taken')
# ax2.set_title('Sacks Taken for All NFL Teams')
# ax2.set_xticks(x)
# ax2.set_xticklabels(teams, rotation=90)

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
# autolabel(rects2, ax2)

# # Ensure layout fits well with rotated labels
# plt.tight_layout()

# # Display the plots in Streamlit
# st.pyplot(fig)  # Use Streamlit to display the Matplotlib figure


# Add this chart code at the end of your existing code

# Get the list of teams from the unique team values in your dataset
teams = sack_stats_df['team'].tolist()

# Ensure we match the correct sacks made and sacks taken for each team
sacks_made = [sack_stats_df[sack_stats_df['team'] == team]['sacks_made'].values[0] for team in teams]
sacks_taken = [sack_stats_df[sack_stats_df['team'] == team]['sacks_taken'].values[0] for team in teams]

# Create the x locations for the teams
x = np.arange(len(teams))  # Label locations

# Create a single subplot for sacks made and sacks taken
fig, ax = plt.subplots(figsize=(14, 8))

# Bar chart for sacks made and taken side by side
bar_width = 0.35
rects1 = ax.bar(x - bar_width/2, sacks_made, bar_width, label='Sacks Made', color='green')
rects2 = ax.bar(x + bar_width/2, sacks_taken, bar_width, label='Sacks Taken', color='red')

# Add labels and title
ax.set_xlabel('Teams')
ax.set_ylabel('Sacks')
ax.set_title('Sacks Made and Taken for All NFL Teams')
ax.set_xticks(x)
ax.set_xticklabels(teams, rotation=90)  # Rotate team labels for better visibility
ax.legend()

# Add value labels on top of the bars
def autolabel(rects):
    """Attach a text label above each bar displaying its height."""
    for rect in rects:
        height = rect.get_height()
        ax.annotate(f'{height:.1f}',
                    xy=(rect.get_x() + rect.get_width() / 2, height),
                    xytext=(0, 3),  # 3 points vertical offset
                    textcoords="offset points",
                    ha='center', va='bottom')

# Add value labels to both sets of bars
autolabel(rects1)
autolabel(rects2)

# Ensure layout fits well with rotated labels
plt.tight_layout()

# Display the plot in Streamlit
st.pyplot(fig)  # Use Streamlit to display the Matplotlib figure