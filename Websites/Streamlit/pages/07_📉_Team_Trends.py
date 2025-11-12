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
        return None

# Load all data
data_result = load_data()
if data_result is None:
    st.stop()
    
(df_teams, df_games, df_playerstats, df_team_game_logs, 
 df_schedule_and_game_results, df_team_game_logs_2024, df_team_game_logs_2025, df_box_scores) = data_result

# Sidebar with filters and navigation
with st.sidebar:
    st.header("🔧 Filters")
    selected_season = st.selectbox("Select Season:", [2025, 2024], index=0)
    
    st.divider()
    st.header("📑 Quick Navigation")
    st.markdown("""
    - **Record & Situational**
      - Home vs Away Record
      - 1H vs 2H Performance
      - Quarter Performance
    
    - **Offensive Trends**
      - Scoring (PPG Home/Away)
      - Yardage (Passing/Rushing)
      - Play Calling
    
    - **Defensive Trends**
      - Scoring Defense
      - Yardage Defense
      - Sacks
    """)

# Select the appropriate dataset based on season
if selected_season == 2025:
    df_team_game_logs_selected = df_team_game_logs_2025
else:
    df_team_game_logs_selected = df_team_game_logs_2024

# Both datasets use the same column names
team_name_col = 'team_name'
week_col = 'week'

dataframes = [df_teams, df_games, df_playerstats, df_team_game_logs, df_schedule_and_game_results]

# Create tabs
tab1, tab2, tab3 = st.tabs(["📊 Record & Situational", "⚡ Offensive Trends", "🛡️ Defensive Trends"])

# ============================================================================
# TAB 1: RECORD & SITUATIONAL
# ============================================================================
with tab1:
    st.markdown(f"<h2 style='text-align: center; color: #2E86AB; margin-bottom: 2rem;'>Record & Situational Trends ({selected_season})</h2>", unsafe_allow_html=True)
    
    # Home vs Away Record
    with st.expander("🏠 Home vs Away Record (W/L)", expanded=True):
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

        win_loss_df = pd.DataFrame.from_dict(win_loss_records, orient='index')
        home_records_df = win_loss_df[['home_wins', 'home_losses']].sort_values(by='home_wins', ascending=False)
        away_records_df = win_loss_df[['away_wins', 'away_losses']].sort_values(by='away_wins', ascending=False)
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("<h5 style='text-align: center; color: grey;'>Home</h5>", unsafe_allow_html=True)
            st.dataframe(home_records_df, use_container_width=True)
            selected_home_team = st.selectbox("Select a team to see their home games", home_records_df.index, key="home_team_select")
            if selected_home_team:
                with st.expander(f"Home Games for {selected_home_team} in {selected_season}", expanded=False):
                    home_games = games_selected[(games_selected['home_team'] == selected_home_team) & (games_selected['season'] == selected_season) & (games_selected['week'].between(1, 18))]
                    home_games_sorted = home_games.sort_values(by='week')
                    st.dataframe(home_games_sorted, use_container_width=True)
        with col2:
            st.markdown("<h5 style='text-align: center; color: grey;'>Away</h5>", unsafe_allow_html=True)
            st.dataframe(away_records_df, use_container_width=True)
            selected_away_team = st.selectbox("Select a team to see their away games", away_records_df.index, key="away_team_select")
            if selected_away_team:
                with st.expander(f"Away Games for {selected_away_team} in {selected_season}", expanded=False):
                    away_games = games_selected[(games_selected['away_team'] == selected_away_team) & (games_selected['season'] == selected_season) & (games_selected['week'].between(1, 18))]
                    away_games_sorted = away_games.sort_values(by='week')
                    st.dataframe(away_games_sorted, use_container_width=True)

    # 1H vs 2H Performance Trends
    with st.expander("⏱️ 1H vs 2H Performance Trends", expanded=True):
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
                'Kansas City Chiefs': 'KC', 'New England Patriots': 'NE', 'New York Jets': 'NYJ', 'Buffalo Bills': 'BUF',
                'Atlanta Falcons': 'ATL', 'Chicago Bears': 'CHI', 'Baltimore Ravens': 'BAL', 'Cincinnati Bengals': 'CIN',
                'Pittsburgh Steelers': 'PIT', 'Cleveland Browns': 'CLE', 'Arizona Cardinals': 'ARI', 'Detroit Lions': 'DET',
                'Jacksonville Jaguars': 'JAX', 'Houston Texans': 'HOU', 'Oakland Raiders': 'LVR', 'Las Vegas Raiders': 'LVR',
                'Tennessee Titans': 'TEN', 'Philadelphia Eagles': 'PHI', 'Washington Redskins': 'WAS', 'Washington Football Team': 'WAS',
                'Washington Commanders': 'WAS', 'Indianapolis Colts': 'IND', 'Los Angeles Rams': 'LAR', 'St. Louis Rams': 'LAR',
                'Seattle Seahawks': 'SEA', 'Minnesota Vikings': 'MIN', 'Green Bay Packers': 'GB', 'Tampa Bay Buccaneers': 'TB',
                'New Orleans Saints': 'NO', 'San Francisco 49ers': 'SF', 'Los Angeles Chargers': 'LAC', 'San Diego Chargers': 'LAC',
                'Denver Broncos': 'DEN', 'Miami Dolphins': 'MIA', 'Carolina Panthers': 'CAR', 'New York Giants': 'NYG', 'Dallas Cowboys': 'DAL'
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
        fig = px.bar(
            team_half_scores_df,
            x='TeamID',
            y=['1H', '2H'],
            color_discrete_map={'1H': '#8A2BE2', '2H': '#9370DB'},
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

        with st.expander("View Table", expanded=False):
            st.dataframe(team_half_scores, use_container_width=True)

        st.write("#####")

        # Calculate and display 1H vs 2H differential
        st.markdown(f"<h5 style='text-align: center; color: grey;'>2H vs 1H Scoring Differential by Team ({selected_season})</h5>", unsafe_allow_html=True)
        st.write("Teams with positive values score more in the 2nd half. Teams with negative values score more in the 1st half.")

        team_half_scores_diff = team_half_scores.copy()
        team_half_scores_diff['Differential'] = team_half_scores_diff['2H'] - team_half_scores_diff['1H']
        team_half_scores_diff_sorted = team_half_scores_diff.sort_values(by='Differential', ascending=False)

        team_half_scores_diff_sorted_reset = team_half_scores_diff_sorted.reset_index()
        team_half_scores_diff_sorted_reset['color'] = team_half_scores_diff_sorted_reset['Differential'].apply(lambda x: '#1E90FF' if x > 0 else '#DC143C')

        chart = alt.Chart(team_half_scores_diff_sorted_reset).mark_bar(size=20).encode(
            x=alt.X('Differential:Q', title='Point Differential (2H - 1H)'),
            y=alt.Y('TeamID:N', title='Teams', sort='-x'),
            color=alt.Color('color:N', scale=None, legend=None),
            tooltip=['TeamID', 'Differential']
        ).properties(
            width=800,
            height=1000,
        ).configure_axisX(
            grid=True,
            labelColor='#333333'
        ).configure_axisY(
            grid=False,
            labelColor='#333333'
        ).add_params(alt.selection_interval())

        st.altair_chart(chart, use_container_width=True)

        with st.expander("View Table", expanded=False):
            st.dataframe(team_half_scores_diff_sorted[['Differential']], use_container_width=True)

    # Quarter Performance Trends
    with st.expander("📅 Quarter Performance Trends", expanded=False):
        st.info("**Coming Soon**")

# ============================================================================
# TAB 2: OFFENSIVE TRENDS
# ============================================================================
with tab2:
    st.markdown(f"<h2 style='text-align: center; color: #06A77D; margin-bottom: 2rem;'>Offensive Trends ({selected_season})</h2>", unsafe_allow_html=True)
    
    # PPG Home vs Away
    with st.expander("🏈 Scoring - PPG Home vs Away", expanded=True):
        games_selected = df_games[(df_games['season'] == selected_season) & (df_games['week'].between(1, 18))]
        
        st.markdown(f"<h5 style='text-align: center; color: grey;'>Average Points Per Game - Home vs. Away ({selected_season})</h5>", unsafe_allow_html=True)
        avg_points_scored_home = games_selected.groupby('home_team')['home_score'].mean()
        avg_points_scored_away = games_selected.groupby('away_team')['away_score'].mean()
        avg_points = pd.concat([avg_points_scored_home, avg_points_scored_away], axis=1)
        avg_points.columns = ['Home', 'Away']
        avg_points = avg_points.reset_index()
        avg_points.rename(columns={'index': 'Team'}, inplace=True)

        fig = px.bar(
            avg_points,
            x='Team',
            y=['Home', 'Away'],
            color_discrete_map={'Home': '#2E8B57', 'Away': '#123829'},
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

        with st.expander("View Table", expanded=False):
            st.dataframe(avg_points.set_index('Team'), use_container_width=True)

    # Passing & Rushing Yards
    with st.expander("📏 Yardage - Passing & Rushing Yards Per Game", expanded=True):
        col1, col2 = st.columns(2)

        with col1:
            st.write(f"**Passing Yards ({selected_season})**")
            df_team_game_logs_filtered = df_team_game_logs_selected[(df_team_game_logs_selected[week_col] >= 1) & (df_team_game_logs_selected[week_col] <= 18)]
            merged_data = pd.merge(df_team_game_logs_filtered, df_teams, left_on=team_name_col, right_on='Team', how='left')
            team_passing_yards = merged_data.groupby('TeamID')['pass_yds'].mean().reset_index()
            team_passing_yards_ranked = team_passing_yards.sort_values(by='pass_yds', ascending=False).reset_index(drop=True)
            
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
            
            st.write(f"**Top 5 Passing Offenses ({selected_season}):**")
            top_5_pass_yds = team_passing_yards_ranked.head(5)
            st.dataframe(top_5_pass_yds, use_container_width=True, hide_index=True)

        with col2:
            st.write(f"**Rushing Yards ({selected_season})**")
            df_team_game_logs_filtered = df_team_game_logs_selected[(df_team_game_logs_selected[week_col] >= 1) & (df_team_game_logs_selected[week_col] <= 18)]
            merged_data = pd.merge(df_team_game_logs_filtered, df_teams, left_on=team_name_col, right_on='Team', how='left')
            team_rushing_yards = merged_data.groupby('TeamID')['rush_yds'].mean().reset_index()
            team_rushing_yards_ranked = team_rushing_yards.sort_values(by='rush_yds', ascending=False).reset_index(drop=True)
            
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
            
            st.write(f"**Top 5 Rushing Offenses ({selected_season}):**")
            top_5_rush_yds = team_rushing_yards_ranked.head(5)
            st.dataframe(top_5_rush_yds, use_container_width=True, hide_index=True)

    # Play Calling
    with st.expander("🎯 Play Calling - Passing vs Rushing Plays", expanded=True):
        season_data = df_team_game_logs_selected.copy()
        team_averages = season_data.groupby(team_name_col).agg({'pass_att': 'mean', 'rush_att': 'mean'}).reset_index()

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

        team_averages_pass_sorted = team_averages.sort_values('pass_att', ascending=False)
        team_averages_rush_sorted = team_averages.sort_values('rush_att', ascending=False)

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

# ============================================================================
# TAB 3: DEFENSIVE TRENDS
# ============================================================================
with tab3:
    st.markdown(f"<h2 style='text-align: center; color: #D62828; margin-bottom: 2rem;'>Defensive Trends ({selected_season})</h2>", unsafe_allow_html=True)
    
    # Opp PPG Home vs Away
    with st.expander("🛡️ Scoring Defense - Opp PPG Home vs Away", expanded=True):
        games_selected = df_games[(df_games['season'] == selected_season) & (df_games['week'].between(1, 18))]
        
        st.markdown(f"<h5 style='text-align: center; color: grey;'>Average Opponent Points Per Game - Home vs. Away ({selected_season})</h5>", unsafe_allow_html=True)
        avg_points_allowed_home = games_selected.groupby('home_team')['away_score'].mean()
        avg_points_allowed_away = games_selected.groupby('away_team')['home_score'].mean()
        avg_points_allowed = pd.concat([avg_points_allowed_home, avg_points_allowed_away], axis=1)
        avg_points_allowed.columns = ['Home', 'Away']
        avg_points_allowed = avg_points_allowed.reset_index()
        avg_points_allowed.rename(columns={'index': 'Team'}, inplace=True)

        fig = px.bar(
            avg_points_allowed,
            x='Team',
            y=['Home', 'Away'],
            color_discrete_map={'Home': '#2E8B57', 'Away': '#123829'},
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

        with st.expander("View Table", expanded=False):
            st.dataframe(avg_points_allowed.set_index('Team'), use_container_width=True)

    # Opponent Passing & Rushing Yards Allowed
    with st.expander("📏 Yardage Defense - Opponent Passing & Rushing Yards Allowed", expanded=True):
        col1, col2 = st.columns(2)

        filtered_df_teams = df_teams.copy()
        filtered_df_teams.loc[:, 'TeamID'] = filtered_df_teams['TeamID'].str.lower()

        df_schedule_results = df_schedule_and_game_results.copy()
        df_schedule_results.loc[:, 'Week'] = pd.to_numeric(df_schedule_results['Week'], errors='coerce')
        df_schedule_results = df_schedule_results.dropna(subset=['Day'])

        team_abbreviation_mapping = {
            'gnb': 'gb', 'htx': 'hou', 'clt': 'ind', 'kan': 'kc',
            'sdg': 'lac', 'ram': 'lar', 'rai': 'lvr', 'nwe': 'ne',
            'nor': 'no', 'sfo': 'sf', 'tam': 'tb', 'oti': 'ten',
            'rav': 'bal', 'crd': 'ari'
        }
        df_schedule_results.loc[:, 'Team'] = df_schedule_results['Team'].map(team_abbreviation_mapping).fillna(df_schedule_results['Team'])
        df_schedule_and_game_results_filtered = df_schedule_results[(df_schedule_results['Season'] == selected_season) & (df_schedule_results['Week'] >= 1) & (df_schedule_results['Week'] <= 18)]

        with col1:
            st.write(f"**Passing Yards Allowed ({selected_season})**")
            results_passing_yards_allowed = []
            for team in filtered_df_teams['TeamID']:
                team_filtered_data = df_schedule_and_game_results_filtered[df_schedule_and_game_results_filtered['Team'] == team]
                avg_passing_yards_allowed = team_filtered_data['OppPassY'].mean()
                results_passing_yards_allowed.append({'Team': team.upper(), 'Avg Passing Yards Allowed': avg_passing_yards_allowed})
            
            df_passing_allowed_chart = pd.DataFrame(results_passing_yards_allowed)
            df_passing_allowed_chart_sorted = df_passing_allowed_chart.sort_values(by='Avg Passing Yards Allowed', ascending=True)
            
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
            
            st.write(f"**Top 5 Passing Defenses ({selected_season}):**")
            df_passing_allowed = pd.DataFrame(results_passing_yards_allowed)
            top_5_pass_allowed = df_passing_allowed.sort_values(by='Avg Passing Yards Allowed', ascending=True).head(5)
            st.dataframe(top_5_pass_allowed, use_container_width=True, hide_index=True)

        with col2:
            st.write(f"**Rushing Yards Allowed ({selected_season})**")
            results_rushing_yards_allowed = []
            for team in filtered_df_teams['TeamID']:
                team_filtered_data = df_schedule_and_game_results_filtered[df_schedule_and_game_results_filtered['Team'] == team]
                avg_rushing_yards_allowed = team_filtered_data['OppRushY'].mean()
                results_rushing_yards_allowed.append({'Team': team.upper(), 'Avg Rushing Yards Allowed': avg_rushing_yards_allowed})
            
            df_rushing_allowed_chart = pd.DataFrame(results_rushing_yards_allowed)
            df_rushing_allowed_chart_sorted = df_rushing_allowed_chart.sort_values(by='Avg Rushing Yards Allowed', ascending=True)
            
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
            
            st.write(f"**Top 5 Rushing Defenses ({selected_season}):**")
            df_rushing_allowed = pd.DataFrame(results_rushing_yards_allowed)
            top_5_rush_allowed = df_rushing_allowed.sort_values(by='Avg Rushing Yards Allowed', ascending=True).head(5)
            st.dataframe(top_5_rush_allowed, use_container_width=True, hide_index=True)

    # Sacks
    with st.expander("💥 Sacks - Made vs Taken", expanded=True):
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

        st.markdown(f"<h5 style='text-align: center; color: grey;'>Total Sacks ({selected_season})</h5>", unsafe_allow_html=True)
        sacks_made_sorted = sack_stats_df.sort_values('sacks_made', ascending=False)

        chart_sacks = alt.Chart(sacks_made_sorted).mark_bar().encode(
            x=alt.X('team:N', title='Teams', sort='-y'),
            y=alt.Y('sacks_made:Q', title='Sacks Made'),
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

        st.markdown(f"<h5 style='text-align: center; color: grey;'>Total Sacks Taken ({selected_season})</h5>", unsafe_allow_html=True)
        sacks_taken_sorted = sack_stats_df.sort_values('sacks_taken', ascending=False)

        chart_sacks_taken = alt.Chart(sacks_taken_sorted).mark_bar().encode(
            x=alt.X('team:N', title='Teams', sort='-y'),
            y=alt.Y('sacks_taken:Q', title='Sacks Taken'),
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
