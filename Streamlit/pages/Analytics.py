# import pandas as pd
# import matplotlib.pyplot as plt
# import streamlit as st

# # Function to calculate average points per game
# def calculate_avg_points(games_df):
#     # Filter to include only the 2023 season
#     games_2023 = games_df[games_df['season'] == 2023]

#     # Calculate average points scored for each team at home and away
#     avg_points_scored_home = games_2023.groupby('home_team')['home_score'].mean()
#     avg_points_scored_away = games_2023.groupby('away_team')['away_score'].mean()

#     # Combine to get overall averages
#     avg_points = pd.concat([avg_points_scored_home, avg_points_scored_away], axis=1)
#     avg_points.columns = ['Avg Home Points', 'Avg Away Points']

#     return avg_points

# # Function to load data
# def load_data():
#     if 'df_games' not in st.session_state:
#         # Load your data here and store it in st.session_state
#         st.session_state['df_games'] = pd.read_csv('path_to_your_games.csv')  # Replace with your data file path
#         # Similarly load df_teams and df_playerstats if needed

# # Streamlit app
# def main():
#     st.title('NFL Team Average Points per Game - 2023 Season')

#     # Load data
#     load_data()
#     df_games = st.session_state['df_games']

#     # Calculate average points
#     average_points = calculate_avg_points(df_games)

#     # Display the data as a table
#     st.dataframe(average_points)

#     # Visualization
#     fig, ax = plt.subplots(figsize=(10, 6))
#     average_points.plot(kind='bar', ax=ax)
#     plt.xlabel('Teams')
#     plt.ylabel('Average Points')
#     plt.title('Average Points per Game (Home vs Away) - 2023 Season')
#     plt.xticks(rotation=45)
#     plt.legend()
#     plt.tight_layout()

#     st.pyplot(fig)

# if __name__ == "__main__":
#     main()


import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

st.set_page_config(layout="wide")

# Check if data is already loaded in st.session_state, if not, load it
if 'df_games' not in st.session_state:
    st.session_state['df_games'] = pd.read_csv('./data/games.csv')  # Replace with your data file path
    # Similarly, load df_teams and df_playerstats if needed

# Assign the data to variables
df_games = st.session_state['df_games']

# Filter to include only the 2023 season
games_2023 = df_games[df_games['season'] == 2023]

# Calculate average points scored for each team at home and away
avg_points_scored_home = games_2023.groupby('home_team')['home_score'].mean()
avg_points_scored_away = games_2023.groupby('away_team')['away_score'].mean()

# Combine to get overall averages
avg_points = pd.concat([avg_points_scored_home, avg_points_scored_away], axis=1)
avg_points.columns = ['Avg Home Points', 'Avg Away Points']

# Streamlit app display
st.title('NFL Team Average Points per Game - 2023 Season')

# Display the data as a table
st.dataframe(avg_points, width=1200)
#use_column_width=True

# Visualization
fig, ax = plt.subplots(figsize=(10, 6))
avg_points.plot(kind='bar', ax=ax)
plt.xlabel('Teams')
plt.ylabel('Average Points')
plt.title('Average Points per Game (Home vs Away) - 2023 Season')
plt.xticks(rotation=45)
plt.legend()
plt.tight_layout()

st.pyplot(fig)


from mpl_toolkits.mplot3d import Axes3D
import numpy as np

# Assuming 'avg_points' DataFrame is already calculated

# 3D Visualization
fig = plt.figure(figsize=(12, 8))
ax = fig.add_subplot(111, projection='3d')

# Data for 3D bar graph
teams = np.arange(len(avg_points))
bar_width = 0.4

# Plotting home points
ax.bar(teams, avg_points['Avg Home Points'], zdir='y', width=bar_width, align='center', color='b', label='Home Points')

# Plotting away points
ax.bar(teams + bar_width, avg_points['Avg Away Points'], zdir='y', width=bar_width, align='center', color='r', label='Away Points')

# Labels and Titles
ax.set_xlabel('Teams')
ax.set_ylabel('Average Points')
ax.set_zlabel('Points Scored')
ax.set_xticks(teams + bar_width / 2)
ax.set_xticklabels(avg_points.index, rotation=90)
ax.set_title('Average Points per Game (Home vs Away) - 2023 Season')
ax.legend()

st.pyplot(fig)


import plotly.graph_objects as go
import streamlit as st

# Assuming 'avg_points' DataFrame is already calculated

# Plotly 3D Visualization
fig = go.Figure()

# Adding Home Points bar
fig.add_trace(go.Bar(
    x=avg_points.index,
    y=avg_points['Avg Home Points'],
    name='Home Points',
    marker=dict(color='blue'),
    orientation='v'
))

# Adding Away Points bar
fig.add_trace(go.Bar(
    x=avg_points.index,
    y=avg_points['Avg Away Points'],
    name='Away Points',
    marker=dict(color='red'),
    orientation='v'
))

# Updating layout for a 3D-like effect
fig.update_layout(
    title='Average Points per Game (Home vs Away) - 2023 Season',
    xaxis=dict(title='Teams'),
    yaxis=dict(title='Average Points'),
    barmode='group'
)

# Show the plot in Streamlit
st.plotly_chart(fig)





### Heatmap 


import seaborn as sns

# Heatmap Display
st.header("Heatmap of Average Points Allowed")
plt.figure(figsize=(12, 8))
sns.heatmap(avg_points_allowed, annot=True, cmap='coolwarm', linewidths=.5)
plt.title('Heatmap of Average Points Allowed (Home vs Away) - 2023 Season')
st.pyplot(plt)
