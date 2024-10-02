import streamlit as st
import pandas as pd

st.title('Report Generator')
st.write('Select two teams to generate a detailed matchup report, including team trends and player stats.')

# teams_df = st.session_state['df_teams']
games_df = st.session_state['df_games'] 
player_stats_df = st.session_state['df_playerstats']

# Team selection using selectbox with unique teams
unique_teams = sorted(games_df['home_team'].unique())
team1 = st.selectbox('Select Team 1:', options=unique_teams, index=unique_teams.index('BUF'))
team2 = st.selectbox('Select Team 2:', options=unique_teams, index=unique_teams.index('MIA'))

# When the button is clicked, the report is generated
if st.button('Generate Report'):
    
    # Filter for recent matchups between the two teams
    team_matchups = games_df[((games_df['home_team'] == team1) & (games_df['away_team'] == team2)) |
                             ((games_df['home_team'] == team2) & (games_df['away_team'] == team1))]
    last_10_games = team_matchups.sort_values(by='date', ascending=False).head(10)

    if last_10_games.empty:
        st.write(f"No recent games found between {team1} and {team2}.")
    else:
        # Team-level statistics
        total_points = last_10_games['home_score'] + last_10_games['away_score']
        average_total_points = total_points.mean()
        team1_wins = sum((last_10_games['home_team'] == team1) & (last_10_games['home_score'] > last_10_games['away_score'])) + \
                     sum((last_10_games['away_team'] == team1) & (last_10_games['away_score'] > last_10_games['home_score']))
        team2_wins = sum((last_10_games['home_team'] == team2) & (last_10_games['home_score'] > last_10_games['away_score'])) + \
                     sum((last_10_games['away_team'] == team2) & (last_10_games['away_score'] > last_10_games['home_score']))

        team1_scores = last_10_games.loc[last_10_games['home_team'] == team1, 'home_score'].sum() + \
                       last_10_games.loc[last_10_games['away_team'] == team1, 'away_score'].sum()
        team2_scores = last_10_games.loc[last_10_games['home_team'] == team2, 'home_score'].sum() + \
                       last_10_games.loc[last_10_games['away_team'] == team2, 'away_score'].sum()

        over_50_points_games = sum(total_points > 50)
        st.write(f"**Matchup Summary: {team1} vs {team2}**")
        st.write(f"Total games analyzed: {len(last_10_games)}")
        st.write(f"{team1} Wins: {team1_wins}")
        st.write(f"{team2} Wins: {team2_wins}")
        st.write(f"Average Total Points: {average_total_points}")
        st.write(f"Games with more than 50 total points: {over_50_points_games}")
        st.write(f"Total points scored by {team1}: {team1_scores}")
        st.write(f"Total points scored by {team2}: {team2_scores}")
        
        # Player-level statistics for current 2024 players
        current_players_team1 = player_stats_df[(player_stats_df['player_current_team'] == team1) & 
                                                (player_stats_df['season'] == 2024)]
        current_players_team2 = player_stats_df[(player_stats_df['player_current_team'] == team2) & 
                                                (player_stats_df['season'] == 2024)]

        players_team1_names = current_players_team1['player_display_name'].unique()
        players_team2_names = current_players_team2['player_display_name'].unique()

        historical_stats_team1 = player_stats_df[(player_stats_df['player_display_name'].isin(players_team1_names)) &
                                                 ((player_stats_df['home_team'] == team1) & (player_stats_df['away_team'] == team2) |
                                                  (player_stats_df['home_team'] == team2) & (player_stats_df['away_team'] == team1))]
        historical_stats_team2 = player_stats_df[(player_stats_df['player_display_name'].isin(players_team2_names)) &
                                                 ((player_stats_df['home_team'] == team1) & (player_stats_df['away_team'] == team2) |
                                                  (player_stats_df['home_team'] == team2) & (player_stats_df['away_team'] == team1))]

        # Add player position to the player display name for both teams
        historical_stats_team1['player_name_with_position'] = historical_stats_team1['player_display_name'] + " (" + historical_stats_team1['position'] + ")"
        historical_stats_team2['player_name_with_position'] = historical_stats_team2['player_display_name'] + " (" + historical_stats_team2['position'] + ")"

        # Function to order by position
        def sort_by_position(df):
            position_order = {'QB': 1, 'WR': 2, 'TE': 3, 'RB': 4}
            df['position_order'] = df['position'].map(position_order)
            return df.sort_values(by='position_order').drop(columns=['position_order'])

        # Summarize player stats for both teams
        if not historical_stats_team1.empty:
            summary_team1 = historical_stats_team1.groupby('player_name_with_position').agg({
                'receptions': 'mean',
                'targets': 'mean',
                'receiving_yards': 'mean',
                'receiving_tds': 'mean',
                'carries': 'mean',
                'rushing_yards': 'mean',
                'rushing_tds': 'mean',
                'passing_yards': 'mean',
                'passing_tds': 'mean',
                'interceptions': 'mean',
                'fantasy_points_ppr': 'mean'
            }).reset_index()
            summary_team1['games_played'] = historical_stats_team1.groupby('player_name_with_position')['game_id'].nunique().values
            sorted_summary_team1 = sort_by_position(historical_stats_team1).drop_duplicates(subset='player_name_with_position')
            st.write(f"\n**Average Historical Stats per Game for {team1} players vs {team2}:**")
            st.write(sorted_summary_team1)
        else:
            st.write(f"No historical stats found for {team1} players vs {team2}.")

        if not historical_stats_team2.empty:
            summary_team2 = historical_stats_team2.groupby('player_name_with_position').agg({
                'receptions': 'mean',
                'targets': 'mean',
                'receiving_yards': 'mean',
                'receiving_tds': 'mean',
                'carries': 'mean',
                'rushing_yards': 'mean',
                'rushing_tds': 'mean',
                'passing_yards': 'mean',
                'passing_tds': 'mean',
                'interceptions': 'mean',
                'fantasy_points_ppr': 'mean'
            }).reset_index()
            summary_team2['games_played'] = historical_stats_team2.groupby('player_name_with_position')['game_id'].nunique().values
            sorted_summary_team2 = sort_by_position(historical_stats_team2).drop_duplicates(subset='player_name_with_position')
            st.write(f"\n**Average Historical Stats per Game for {team2} players vs {team1}:**")
            st.write(sorted_summary_team2)
        else:
            st.write(f"No historical stats found for {team2} players vs {team1}.")
