import streamlit as st
import pandas as pd
import os
import plotly.express as px

# Page configuration
st.set_page_config(
    page_title="📄 Report Generator",
    page_icon="📄",
    layout="centered"
)

st.title('Report Generator')
st.write('Select two teams to generate a detailed matchup report, including team trends and player stats.')

# Load data files directly if not in session state
if 'df_games' not in st.session_state:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    df_games = pd.read_csv(os.path.join(current_dir, '../data', 'Games.csv'))
    df_playerstats = pd.read_csv(os.path.join(current_dir, '../data', 'PlayerStats.csv'))
    
    # Store in session state for future use
    st.session_state['df_games'] = df_games
    st.session_state['df_playerstats'] = df_playerstats
else:
    df_games = st.session_state['df_games'] 
    df_playerstats = st.session_state['df_playerstats']

# Team selection using selectbox with unique teams
unique_teams = sorted(df_games['home_team'].unique())
team1 = st.selectbox('Select Team 1:', options=unique_teams, index=unique_teams.index('BUF'))
team2 = st.selectbox('Select Team 2:', options=unique_teams, index=unique_teams.index('MIA'))

# When the button is clicked, the report is generated
if st.button('Generate Report'):
    
    # Filter for recent matchups between the two teams
    team_matchups = df_games[((df_games['home_team'] == team1) & (df_games['away_team'] == team2)) |
                             ((df_games['home_team'] == team2) & (df_games['away_team'] == team1))]
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
        
        # Enhanced matchup analysis
        st.divider()
        st.subheader("📊 Matchup Analysis")
        
        # Get all games between these two teams
        all_matchup_games = df_playerstats[((df_playerstats['home_team'] == team1) & (df_playerstats['away_team'] == team2)) |
                                           ((df_playerstats['home_team'] == team2) & (df_playerstats['away_team'] == team1))]

        # Merge game-level scores/teams from df_games into all_matchup_games using game_id
        all_matchup_games = all_matchup_games.merge(
            df_games[['game_id', 'season','week', 'home_team', 'away_team', 'home_score', 'away_score', 'date']],
            on='game_id',
            how='left',
            suffixes=('', '_game')
        )

        if not all_matchup_games.empty:
            # 1. Game-by-Game Breakdown
            st.write("**📅 Game-by-Game Results:**")
            # Only one row per game
            game_summary = all_matchup_games[['season', 'week', 'game_id', 'home_team', 'away_team', 'home_score', 'away_score', 'date']].drop_duplicates()

            # Format and display
            game_results = []
            for _, game in game_summary.iterrows():
                winner = game['home_team'] if game['home_score'] > game['away_score'] else game['away_team']
                loser = game['away_team'] if game['home_team'] == winner else game['home_team']
                winner_score = game['home_score'] if game['home_team'] == winner else game['away_score']
                loser_score = game['away_score'] if game['home_team'] == winner else game['home_score']
                game_results.append({
                    'Season': int(game['season']),
                    'Week': int(game['week']),
                    'Winner': winner,
                    'Score': f"{winner_score}-{loser_score}",
                    'Margin': abs(game['home_score'] - game['away_score'])
                })
            game_results_df = pd.DataFrame(game_results).sort_values(['Season', 'Week'], ascending=[False, False])
            st.dataframe(game_results_df, use_container_width=True)
            
            # 2. Key Performance Metrics
            st.write("**🎯 Key Performance Metrics:**")
            
            # Separate by team
            team1_stats = all_matchup_games[all_matchup_games['player_current_team'] == team1]
            team2_stats = all_matchup_games[all_matchup_games['player_current_team'] == team2]
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**{team1} Performance:**")
                if not team1_stats.empty:
                    # Top performers
                    top_passers = team1_stats[team1_stats['position'] == 'QB'].groupby('player_display_name').agg({
                        'passing_yards': 'sum',
                        'passing_tds': 'sum',
                        'interceptions': 'sum'
                    }).reset_index().sort_values('passing_yards', ascending=False).head(3)
                    
                    top_receivers = team1_stats[team1_stats['position'].isin(['WR', 'TE'])].groupby('player_display_name').agg({
                        'receiving_yards': 'sum',
                        'receiving_tds': 'sum',
                        'receptions': 'sum'
                    }).reset_index().sort_values('receiving_yards', ascending=False).head(3)
                    
                    if not top_passers.empty:
                        st.write("**Top Passers:**")
                        st.dataframe(top_passers, use_container_width=True)
                    
                    if not top_receivers.empty:
                        st.write("**Top Receivers:**")
                        st.dataframe(top_receivers, use_container_width=True)
                else:
                    st.write("No player data available")
            
            with col2:
                st.write(f"**{team2} Performance:**")
                if not team2_stats.empty:
                    # Top performers
                    top_passers = team2_stats[team2_stats['position'] == 'QB'].groupby('player_display_name').agg({
                        'passing_yards': 'sum',
                        'passing_tds': 'sum',
                        'interceptions': 'sum'
                    }).reset_index().sort_values('passing_yards', ascending=False).head(3)
                    
                    top_receivers = team2_stats[team2_stats['position'].isin(['WR', 'TE'])].groupby('player_display_name').agg({
                        'receiving_yards': 'sum',
                        'receiving_tds': 'sum',
                        'receptions': 'sum'
                    }).reset_index().sort_values('receiving_yards', ascending=False).head(3)
                    
                    if not top_passers.empty:
                        st.write("**Top Passers:**")
                        st.dataframe(top_passers, use_container_width=True)
                    
                    if not top_receivers.empty:
                        st.write("**Top Receivers:**")
                        st.dataframe(top_receivers, use_container_width=True)
                else:
                    st.write("No player data available")
            
            # 3. Trends and Insights
            st.write("**📈 Matchup Trends:**")
            
            # Calculate trends
            team1_wins = sum(1 for game in game_results if game['Winner'] == team1)
            team2_wins = sum(1 for game in game_results if game['Winner'] == team2)
            avg_margin = game_results_df['Margin'].mean()
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(f"{team1} Win Rate", f"{team1_wins}/{len(game_results)}", f"{team1_wins/len(game_results)*100:.1f}%")
            with col2:
                st.metric(f"{team2} Win Rate", f"{team2_wins}/{len(game_results)}", f"{team2_wins/len(game_results)*100:.1f}%")
            with col3:
                st.metric("Avg Margin", f"{avg_margin:.1f}", "points")
            
            # Recent trend
            if len(game_results) >= 3:
                recent_games = game_results_df.head(3)
                recent_team1_wins = sum(1 for game in recent_games.itertuples() if game.Winner == team1)
                st.write(f"**Recent Trend:** {team1} has won {recent_team1_wins} of the last 3 meetings")
            
        else:
            st.write("No historical matchup data found between these teams.")
