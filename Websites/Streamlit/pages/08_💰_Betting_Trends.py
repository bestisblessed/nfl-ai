import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import sqlite3
import os
from utils.footer import render_footer

# Page configuration
st.set_page_config(
    page_title="💰 Betting Trends",
    page_icon="🏈",
    layout="wide"
)

st.markdown(f"""
    <div style='text-align: center;'>
        <div style='font-size: 3.1rem; font-weight: 800; padding-bottom: 0.5rem;'>
            Betting Trends
        </div>
        <div style='color: #7f8c8d; font-size: 1rem; margin-top: 0; line-height: 1.2;'>
            Advanced betting analytics and spread performance tracking
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

# Season selector
selected_season = st.selectbox("Select Season:", [2025, 2024], index=0)

# Load data files directly if not in session state
if 'df_teams' not in st.session_state:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    df_teams = pd.read_csv(os.path.join(current_dir, '../data', 'Teams.csv'))
    df_games = pd.read_csv(os.path.join(current_dir, '../data', 'Games.csv'))
    df_playerstats = pd.read_csv(os.path.join(current_dir, '../data', 'PlayerStats.csv'))
    
    # Store in session state for future use
    st.session_state['df_teams'] = df_teams
    st.session_state['df_games'] = df_games
    st.session_state['df_playerstats'] = df_playerstats
else:
    df_teams = st.session_state['df_teams']
    df_games = st.session_state['df_games'] 
    df_playerstats = st.session_state['df_playerstats']

tab1, tab2 = st.tabs(["ATS", "Over/Under"])

### --- ATS Record (Overall, Home, Away) --- ###
with tab1:
    st.header("ATS Stats (Reg Reason)")
        
    teams = df_teams['TeamID'].tolist()

    # Function to determine the ATS result for a game using actual scores and spread
    def ats_result(row, team):
        # Check if scores are available (not empty strings or NaN)
        if pd.isna(row['home_score']) or pd.isna(row['away_score']) or row['home_score'] == '' or row['away_score'] == '':
            return None  # Game not played yet
        
        spread = float(row['home_spread']) if row['home_team'] == team else float(row['away_spread'])
        score_diff = row['home_score'] - row['away_score'] if row['home_team'] == team else row['away_score'] - row['home_score']
        if score_diff > spread:
            return 'Win'
        elif score_diff < spread:
            return 'Loss'
        else:
            return 'Push'

    # Dropdown button for single team stats
    selected_team = st.selectbox('Team:', (df_teams), key="ATS_selectbox", index=df_teams['TeamID'].tolist().index('DAL') if 'DAL' in df_teams['TeamID'].tolist() else 0)
    if selected_team:
        # Filter the games for the selected team
        relevant_columns = ['home_team', 'away_team', 'home_score', 'away_score', 'home_spread', 'away_spread']
        team_games = df_games[
            ((df_games['home_team'] == selected_team) | (df_games['away_team'] == selected_team)) & (df_games['season'] == selected_season) & (df_games['week'].between(1, 18))
        ][relevant_columns]    
        team_games['ATS_Result'] = team_games.apply(lambda row: ats_result(row, selected_team), axis=1)
        # Filter out unplayed games (None values)
        played_games = team_games.dropna(subset=['ATS_Result'])
        overall_ats_record = played_games['ATS_Result'].value_counts().reindex(['Win', 'Loss', 'Push'], fill_value=0)
        home_ats_record = played_games[played_games['home_team'] == selected_team]['ATS_Result'].value_counts().reindex(['Win', 'Loss', 'Push'], fill_value=0)
        away_ats_record = played_games[played_games['away_team'] == selected_team]['ATS_Result'].value_counts().reindex(['Win', 'Loss', 'Push'], fill_value=0)
        st.write(f"ATS Record for {selected_team} in {selected_season} Season")
        ats_data = pd.DataFrame({
            'Overall': overall_ats_record,
            'Home': home_ats_record,
            'Away': away_ats_record
        })
        st.table(ats_data)

    st.divider()

    # DataFrames to store ATS results
    overall_ats_records = pd.DataFrame(index=teams, columns=['Win', 'Loss', 'Push'], dtype='int64').fillna(0)
    home_ats_records = pd.DataFrame(index=teams, columns=['Win', 'Loss', 'Push'], dtype='int64').fillna(0)
    away_ats_records = pd.DataFrame(index=teams, columns=['Win', 'Loss', 'Push'], dtype='int64').fillna(0)

    for team in teams:
        relevant_columns = ['home_team', 'away_team', 'home_score', 'away_score', 'home_spread', 'away_spread']
        team_games = df_games[
        ((df_games['home_team'] == team) | (df_games['away_team'] == team)) & (df_games['season'] == selected_season) & (df_games['week'].between(1, 18))
        ][relevant_columns]
        team_games['ATS_Result'] = team_games.apply(lambda row: ats_result(row, team), axis=1)
        # Filter out unplayed games (None values)
        played_games = team_games.dropna(subset=['ATS_Result'])
        # overall_ats_record = team_games['ATS_Result'].value_counts()
        # home_ats_record = team_games[team_games['home_team'] == team]['ATS_Result'].value_counts()
        # away_ats_record = team_games[team_games['away_team'] == team]['ATS_Result'].value_counts()
        # st.write(f"{team} ATS Record for 2023 Season:")
        # st.write("Overall:", overall_ats_record)
        # st.write("Home:", home_ats_record)
        # st.write("Away:", away_ats_record)
        # st.divider()
        overall_ats_records.loc[team] = played_games['ATS_Result'].value_counts()
        home_ats_records.loc[team] = played_games[played_games['home_team'] == team]['ATS_Result'].value_counts()
        away_ats_records.loc[team] = played_games[played_games['away_team'] == team]['ATS_Result'].value_counts()

    # Plotting Overall ATS Record
    st.subheader("Overall ATS Record")
    st.bar_chart(overall_ats_records, 
                x_label='Teams', 
                y_label='Games', 
                color=['#ff0000', '#0000ff', '#00ff00'],  # Red, Blue, Green
                #  stack=False,
                horizontal=True)

    # Plotting Home ATS Record
    st.subheader("Home ATS Record")
    st.bar_chart(home_ats_records, 
                x_label='Teams', 
                y_label='Games', 
                color=['#ff0000', '#0000ff', '#00ff00'],  # Red, Blue, Green
                horizontal=True)

    # Plotting Away ATS Record
    st.subheader("Away ATS Record")
    st.bar_chart(away_ats_records, 
                x_label='Teams', 
                y_label='Games', 
                color=['#ff0000', '#0000ff', '#00ff00'],  # Red, Blue, Green
                horizontal=True)





### --- Over/Under Stats (Reg Reason) --- ###
with tab2:
    st.header("O/U Stats (Reg Reason)")

    teams = df_teams['TeamID'].tolist()
    games_selected = df_games[(df_games['season'] == selected_season) & (df_games['week'].between(1, 18))].copy()
    
    # Filter out unplayed games (games with empty or NaN scores)
    games_selected = games_selected[
        (games_selected['home_score'].notna()) & 
        (games_selected['away_score'].notna()) & 
        (games_selected['home_score'] != '') & 
        (games_selected['away_score'] != '')
    ].copy()
    
    games_selected['total_score'] = games_selected['home_score'] + games_selected['away_score']
    games_selected['over_under_result'] = games_selected.apply(lambda row: 'over' if row['total_score'] > row['total_line'] else 'under' if row['total_score'] < row['total_line'] else 'push', axis=1)

    # Dropdown button for single team stats
    selected_team = st.selectbox('Team:', (df_teams), key="O/U_selectbox", index=df_teams['TeamID'].tolist().index('DAL') if 'DAL' in df_teams['TeamID'].tolist() else 0)
    if selected_team:
        selected_team_games = games_selected[(games_selected['home_team'] == selected_team) | (games_selected['away_team'] == selected_team)]
        over_count = selected_team_games['over_under_result'].value_counts().get('over', 0)
        under_count = selected_team_games['over_under_result'].value_counts().get('under', 0)
        push_count = selected_team_games['over_under_result'].value_counts().get('push', 0)
        home_games = games_selected[games_selected['home_team'] == selected_team]
        home_over_count = home_games['over_under_result'].value_counts().get('over', 0)
        home_under_count = home_games['over_under_result'].value_counts().get('under', 0)
        home_push_count = home_games['over_under_result'].value_counts().get('push', 0)
        away_games = games_selected[games_selected['away_team'] == selected_team]
        away_over_count = away_games['over_under_result'].value_counts().get('over', 0)
        away_under_count = away_games['over_under_result'].value_counts().get('under', 0)
        away_push_count = away_games['over_under_result'].value_counts().get('push', 0)
        combined_record = pd.DataFrame({
            'Type': ['Overall', 'Home', 'Away'],
            'Over': [over_count, home_over_count, away_over_count],
            'Under': [under_count, home_under_count, away_under_count],
            'Push': [push_count, home_push_count, away_push_count]
        })
        st.write(f"O/U Record for {selected_team} in {selected_season} Season")
        st.table(combined_record)

    st.divider()

    over_under_stats = {}
    home_over_under_stats = {}
    away_over_under_stats = {}

    for team in teams:
        # Overall record
        team_games = games_selected[(games_selected['home_team'] == team) | (games_selected['away_team'] == team)]
        over_count = team_games['over_under_result'].value_counts().get('over', 0)
        under_count = team_games['over_under_result'].value_counts().get('under', 0)
        push_count = team_games['over_under_result'].value_counts().get('push', 0)
        over_under_stats[team] = {'over': over_count, 'under': under_count, 'push': push_count}

        # Home record
        home_games = games_selected[games_selected['home_team'] == team]
        home_over_count = home_games['over_under_result'].value_counts().get('over', 0)
        home_under_count = home_games['over_under_result'].value_counts().get('under', 0)
        home_push_count = home_games['over_under_result'].value_counts().get('push', 0)
        home_over_under_stats[team] = {'over': home_over_count, 'under': home_under_count, 'push': home_push_count}

        # Away record
        away_games = games_selected[games_selected['away_team'] == team]
        away_over_count = away_games['over_under_result'].value_counts().get('over', 0)
        away_under_count = away_games['over_under_result'].value_counts().get('under', 0)
        away_push_count = away_games['over_under_result'].value_counts().get('push', 0)
        away_over_under_stats[team] = {'over': away_over_count, 'under': away_under_count, 'push': away_push_count}

    over_under_df = pd.DataFrame.from_dict(over_under_stats, orient='index').reset_index() # Convert the dictionary to a DataFrame for easy plotting
    over_under_df.columns = ['team', 'over', 'under', 'push']
    home_over_under_df = pd.DataFrame.from_dict(home_over_under_stats, orient='index').reset_index()
    home_over_under_df.columns = ['team', 'over', 'under', 'push']
    away_over_under_df = pd.DataFrame.from_dict(away_over_under_stats, orient='index').reset_index()
    away_over_under_df.columns = ['team', 'over', 'under', 'push']

    # Display overall bar chart
    st.subheader("Overall")
    st.bar_chart(over_under_df.set_index('team'), color=[ '#00ff00', '#0000ff', '#ff0000'], horizontal=True)
    if st.button("Show Details", key="overall_details"):
        sorted_over_under_df = over_under_df.sort_values(by='over', ascending=False, ignore_index=True)
        st.dataframe(sorted_over_under_df, use_container_width=True)
    else:
        st.write("")

    # Display home bar chart
    st.subheader("Home")
    st.bar_chart(home_over_under_df.set_index('team'), color=['#00ff00', '#0000ff', '#ff0000'], horizontal=True)
    if st.button("Show Details", key="home_details"):
        sorted_home_over_under_df = home_over_under_df.sort_values(by='over', ascending=False, ignore_index=True)
        st.dataframe(sorted_home_over_under_df, use_container_width=True)
    else:
        st.write("")

    # Display away bar chart
    st.subheader("Away")
    st.bar_chart(away_over_under_df.set_index('team'), color=['#00ff00', '#0000ff', '#ff0000'], horizontal=True)
    if st.button("Show Details", key="away_details"):
        sorted_away_over_under_df = away_over_under_df.sort_values(by='over', ascending=False, ignore_index=True)
        st.dataframe(sorted_away_over_under_df, use_container_width=True)
    else:
        st.write("")







# 4. Radar Charts:
# Team Performance Radar Chart:
# A radar chart (spider chart) comparing each team’s ATS performance across multiple dimensions (Overall, Home, Away, Performance as Favorite, Performance as Underdog, etc.). This can give a holistic view of team strengths and weaknesses against the spread.

# 5. Scatter Plots with Regression Lines:
# ATS Win Percentage vs. Point Spread:
# Scatter plots showing the relationship between the average point spread and the ATS win percentage for each team. Adding regression lines can help identify if teams tend to perform better with larger or smaller spreads.
# ATS Win Percentage vs. Team Statistics:
# Scatter plots showing the relationship between ATS win percentage and various team statistics (e.g., offensive or defensive rankings). This can help identify correlations between team performance metrics and success against the spread.

# 7. Correlation Matrix:
# Team Performance Metrics vs. ATS Performance:
# A correlation matrix showing the relationships between various team performance metrics (like offensive/defensive efficiency, turnovers, etc.) and their ATS performance. This can help in identifying which metrics most strongly correlate with ATS success.

# 8. Sankey Diagrams:
# Flow of ATS Outcomes:
# A Sankey diagram to show the flow of ATS outcomes (Win, Loss, Push) based on factors like home/away games, the spread, and other variables. This can visualize how different factors contribute to ATS results.

# 10. 3D Bar Charts:
# 3D Bar Chart for Multi-Dimensional Data:
# A 3D bar chart showing the relationship between three dimensions, such as the ATS record (Win/Loss/Push), the spread size, and the week of the season. This can add depth to understanding how different factors interact.

# Footer
render_footer()