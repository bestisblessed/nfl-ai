import sqlite3
from IPython.display import display
import pandas as pd
from tabulate import tabulate
import os
import matplotlib.pyplot as plt
import seaborn as sns
import requests
import warnings


# Analyzing Seasonal Trends in Average Points Scored and Allowed by NFL Teams (2019-2023)

team = 'DAL'  # Example team

# Load the dataset
df = pd.read_csv('data/Games.csv')

# Filter for recent seasons if needed (e.g., 2019-2023)
df_recent = df[df['season'].isin([2019, 2020, 2021, 2022, 2023])]

# Group by team and week to calculate average points scored and allowed per week
team_weekly_performance = df_recent.groupby(['home_team', 'week']).agg(
    avg_points_scored=('home_score', 'mean'),
    avg_points_allowed=('away_score', 'mean')
).reset_index()

# Plotting seasonal trends for a selected team (e.g., DAL)
team_data = team_weekly_performance[team_weekly_performance['home_team'] == team]

plt.figure(figsize=(12, 6))
plt.plot(team_data['week'], team_data['avg_points_scored'], label='Avg Points Scored', marker='o')
plt.plot(team_data['week'], team_data['avg_points_allowed'], label='Avg Points Allowed', marker='o')
plt.title(f'Seasonal Trends for {team} (2019-2023)')
plt.xlabel('Week')
plt.ylabel('Average Points')
plt.xticks(team_data['week'])
plt.grid(True)
plt.legend()
plt.show()