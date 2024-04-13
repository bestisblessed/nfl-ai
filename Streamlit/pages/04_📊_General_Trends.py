import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import sqlite3

### --- Title and Data --- ###
st.title('General Trends')
df_teams = pd.read_csv('./data/Teams.csv')
df_games = pd.read_csv('./data/Games.csv')
df_playerstats = pd.read_csv('./data/PlayerStats.csv')

### --- Avg PPG Home vs Away 2023 --- ###
st.divider()
st.header("Avg PPG Home vs Away 2023")
st.write("##")

# Calculation
games_2023 = df_games[df_games['season'] == 2023]
avg_points_scored_home = games_2023.groupby('home_team')['home_score'].mean()
avg_points_scored_away = games_2023.groupby('away_team')['away_score'].mean()
avg_points = pd.concat([avg_points_scored_home, avg_points_scored_away], axis=1) # Combine to get overall averages
avg_points.columns = ['Avg Home Points', 'Avg Away Points']

# Display
col1, col2 = st.columns((2, 1))
with col1:
    fig, ax = plt.subplots(figsize=(10, 6))
    avg_points.plot(kind='bar', ax=ax)
    plt.xlabel('Teams')
    plt.ylabel('Average Points')
    plt.title('Average Points per Game (Home vs Away) - 2023 Season')
    plt.xticks(rotation=45)
    plt.legend()
    plt.tight_layout()
    st.pyplot(fig)
with col2:      
    st.dataframe(avg_points, use_container_width=True)



### --- Avg Points Allowed Home vs Away 2023--- ###
st.divider()
st.header("Avg Points Allowed Home vs Away 2023")
st.write("##")

# Calculation
games_2023 = df_games[df_games['season'] == 2023]
avg_points_allowed_home = games_2023.groupby('home_team')['away_score'].mean()
avg_points_allowed_away = games_2023.groupby('away_team')['home_score'].mean()
avg_points_allowed = pd.concat([avg_points_allowed_home, avg_points_allowed_away], axis=1) # Combining the two series to get overall averages for each team
avg_points_allowed.columns = ['Avg Points Allowed Home', 'Avg Points Allowed Away']

# Display
col1, col2 = st.columns((1, 2))
with col1:      
    st.dataframe(avg_points_allowed, use_container_width=True)
with col2:
    fig, ax = plt.subplots(figsize=(10, 6))
    avg_points_allowed.plot(kind='bar', ax=ax)
    plt.xlabel('Teams')
    plt.ylabel('Average Points Allowed')
    plt.title('Average Points Allowed per Game (Home vs Away) - 2023 Season')
    plt.xticks(rotation=45)
    plt.legend()
    plt.tight_layout()
    st.pyplot(fig)



### --- Avg Passing+Rushing Yards Per Game 2023 --- ###
st.divider()
st.header("Avg Passing/Rushing Yards Per Game 2023")
st.write("##")

# Calculation

# Display



### --- Avg Passing+Rushing Yards Allowed Per Game 2023 --- ###
st.divider()
st.header("Avg Passing+Rushing Yards Allowed Per Game 2023")
st.write("##")

# Calculation

# Display




### --- Home vs Away Record 2023 --- ###
st.divider()
st.header("Home vs Away Record 2023")
st.write("##")

db_path = './data/nfl.db'  # Adjust the path if your database has a different name
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute("SELECT MAX(season) FROM Games;")
latest_season = cursor.fetchone()[0]
def get_wl_records(cursor, season, home_or_away):
    column = 'home_team' if home_or_away == 'home' else 'away_team'
    score_comparison = 'home_score > away_score' if home_or_away == 'home' else 'away_score > home_score'
    wl_query = f"""
    SELECT 
        {column} AS team, 
        COUNT(*) AS total_games, 
        SUM(CASE WHEN {score_comparison} THEN 1 ELSE 0 END) AS wins, 
        SUM(CASE WHEN NOT ({score_comparison}) THEN 1 ELSE 0 END) AS losses 
    FROM 
        Games 
    WHERE 
        season = {season}
    GROUP BY 
        {column}
    ORDER BY 
        wins DESC, losses;
    """
    cursor.execute(wl_query)
    return cursor.fetchall()
home_wl_records = get_wl_records(cursor, latest_season, 'home')
away_wl_records = get_wl_records(cursor, latest_season, 'away')
st.write("Home Win/Loss Records:")
for record in home_wl_records:
    st.write(f"Team: {record[0]}, Wins: {record[2]}, Losses: {record[3]}")
st.write("\nAway Win/Loss Records:")
for record in away_wl_records:
    st.write(f"Team: {record[0]}, Wins: {record[2]}, Losses: {record[3]}")
conn.close()
