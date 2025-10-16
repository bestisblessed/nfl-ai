import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os
# from Home import df_teams, df_games, df_playerstats, df_team_game_logs, df_schedule_and_game_results

# Page configuration
st.set_page_config(
    page_title="📈 Player Trends",
    page_icon="📈",
    layout="wide"
)

# # Define the base directory
# base_dir = os.path.abspath('../data')

# # Use absolute paths
# df_teams = pd.read_csv(os.path.join(base_dir, 'Teams.csv'))
# df_games = pd.read_csv(os.path.join(base_dir, 'Games.csv'))
# df_playerstats = pd.read_csv(os.path.join(base_dir, 'PlayerStats.csv'))

### --- Title and Data --- ###
st.title('Player Trends')

# Load data using cached function
@st.cache_data(show_spinner=False)
def load_data():
    """Load all required CSV files for Player Trends"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    try:
        df_teams = pd.read_csv(os.path.join(current_dir, '../data', 'Teams.csv'))
        df_games = pd.read_csv(os.path.join(current_dir, '../data', 'Games.csv'))
        df_playerstats = pd.read_csv(os.path.join(current_dir, '../data', 'PlayerStats.csv'))
        df_team_game_logs = pd.read_csv(os.path.join(current_dir, '../data', 'all_team_game_logs.csv'))
        df_schedule_and_game_results = pd.read_csv(os.path.join(current_dir, '../data', 'all_teams_schedule_and_game_results_merged.csv'))
        # Add the detailed passing/rushing/receiving data for 2025 trends
        df_all_passing_rushing_receiving = pd.read_csv(os.path.join(current_dir, '../data', 'all_passing_rushing_receiving.csv'))
        
        return df_teams, df_games, df_playerstats, df_team_game_logs, df_schedule_and_game_results, df_all_passing_rushing_receiving
    except FileNotFoundError as e:
        st.error(f"Error loading data files: {e}")
        st.stop()

# Load all data
df_teams, df_games, df_playerstats, df_team_game_logs, df_schedule_and_game_results, df_all_passing_rushing_receiving = load_data()

# Function to get the standardized dataset for any season
def get_player_data_for_season(season):
    """Return the standardized player dataset for any season"""
    # Use the detailed passing/rushing/receiving data for all seasons
    df_standard = df_all_passing_rushing_receiving.copy()
    # Extract season from game_id (format: YYYY_XX_TEAM1_TEAM2)
    df_standard['season'] = df_standard['game_id'].str[:4].astype(int)
    
    # Map column names to match the standard format used in the page
    column_mapping = {
        'player': 'player_display_name',
        'pass_sacked': 'sacks',
        'pass_int': 'interceptions', 
        'pass_yds': 'passing_yards',
        'pass_td': 'passing_tds',
        'pass_att': 'passing_attempts',
        'rush_yds': 'rushing_yards',
        'rush_td': 'rushing_tds',
        'rec_yds': 'receiving_yards',
        'rec_td': 'receiving_tds'
    }
    
    # Rename columns to match the expected format
    df_standard = df_standard.rename(columns=column_mapping)
    
    return df_standard

# Season selector - now includes all available years from the standardized dataset
available_seasons = [2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025]
selected_season = st.selectbox("Select Season:", available_seasons, index=available_seasons.index(2025))  # Default to 2025

st.divider()

tab1, tab2, tab3, tab4 = st.tabs(["QBs", "RBs", "WRs", "TEs"])

with tab1:
### SACKS ###
    st.header('Quarterback Sack Rankings')
    # Get the appropriate dataset for the selected season
    current_player_data = get_player_data_for_season(selected_season)
    qb_selected_stats = current_player_data[(current_player_data['position'] == 'QB') & (current_player_data['season'] == selected_season)]
    
    if not qb_selected_stats.empty:
        qb_sacked_selected = qb_selected_stats.groupby('player_display_name')['sacks'].sum().reset_index()
        # Filter out QBs with 0 sacks
        qb_sacked_selected = qb_sacked_selected[qb_sacked_selected['sacks'] > 0]
        qb_sacked_ranked_selected = qb_sacked_selected.sort_values(by='sacks', ascending=False)
        
        if len(qb_sacked_ranked_selected) > 0:
            plt.figure(figsize=(12, max(6, len(qb_sacked_ranked_selected) * 0.3)))
            bars = plt.barh(qb_sacked_ranked_selected['player_display_name'], qb_sacked_ranked_selected['sacks'], color='skyblue')
            plt.xlabel('Number of Sacks', fontsize=14)
            plt.ylabel('Quarterbacks', fontsize=14)
            plt.title(f'Number of Sacks for NFL Quarterbacks in {selected_season}', fontsize=16)
            plt.xticks(fontsize=10)
            plt.yticks(fontsize=10)
            plt.bar_label(bars)
            plt.tight_layout()
            st.pyplot(plt)
        else:
            st.write("No QB sack data available for the selected season.")
    else:
        st.write("No QB data available for the selected season.")

    ### INTERCEPTIONS ###
    st.header('Quarterback Interception Rankings')
    if not qb_selected_stats.empty:
        # Group by player and sum both interceptions and passing attempts
        qb_interceptions_selected = qb_selected_stats.groupby('player_display_name').agg({
            'interceptions': 'sum',
            'passing_attempts': 'sum'
        }).reset_index()
        
        # Filter for QBs with at least 10 passing attempts
        qb_interceptions_selected = qb_interceptions_selected[qb_interceptions_selected['passing_attempts'] >= 10]
        
        qb_interceptions_ranked_selected = qb_interceptions_selected.sort_values(by='interceptions', ascending=False)
        
        if len(qb_interceptions_ranked_selected) > 0:
            plt.figure(figsize=(12, max(6, len(qb_interceptions_ranked_selected) * 0.3)))
            bars = plt.barh(qb_interceptions_ranked_selected['player_display_name'], qb_interceptions_ranked_selected['interceptions'], color='salmon')
            plt.xlabel('Number of Interceptions', fontsize=14)
            plt.ylabel('Quarterbacks', fontsize=14)
            plt.title(f'Number of Interceptions for NFL Quarterbacks in {selected_season} (Min. 10 Pass Attempts)', fontsize=16)
            plt.xticks(fontsize=10)
            plt.yticks(fontsize=10)
            plt.bar_label(bars)
            plt.tight_layout()
            st.pyplot(plt)
        else:
            st.write("No QB interception data available for the selected season.")
    else:
        st.write("No QB data available for the selected season.")

with tab2:
    st.header('Running Back Rankings')
    # Get the appropriate dataset for the selected season
    current_player_data = get_player_data_for_season(selected_season)
    rb_selected_stats = current_player_data[(current_player_data['position'] == 'RB') & (current_player_data['season'] == selected_season)]
    
    if not rb_selected_stats.empty:
        # Rushing Yards
        rb_rushing_selected = rb_selected_stats.groupby('player_display_name')['rushing_yards'].sum().reset_index()
        rb_rushing_ranked = rb_rushing_selected.sort_values(by='rushing_yards', ascending=False).head(20)
        
        if len(rb_rushing_ranked) > 0:
            plt.figure(figsize=(12, max(6, len(rb_rushing_ranked) * 0.3)))
            bars = plt.barh(rb_rushing_ranked['player_display_name'], rb_rushing_ranked['rushing_yards'], color='green')
            plt.xlabel('Rushing Yards', fontsize=14)
            plt.ylabel('Running Backs', fontsize=14)
            plt.title(f'Top 20 Rushing Yards for NFL Running Backs in {selected_season}', fontsize=16)
            plt.xticks(fontsize=10)
            plt.yticks(fontsize=10)
            plt.bar_label(bars)
            plt.tight_layout()
            st.pyplot(plt)
        else:
            st.write("No RB rushing data available for the selected season.")
    else:
        st.write("No RB data available for the selected season.")

with tab3:
    st.header('Wide Receiver Rankings')
    # Get the appropriate dataset for the selected season
    current_player_data = get_player_data_for_season(selected_season)
    wr_selected_stats = current_player_data[(current_player_data['position'] == 'WR') & (current_player_data['season'] == selected_season)]
    
    if not wr_selected_stats.empty:
        # Receiving Yards
        wr_receiving_selected = wr_selected_stats.groupby('player_display_name')['receiving_yards'].sum().reset_index()
        wr_receiving_ranked = wr_receiving_selected.sort_values(by='receiving_yards', ascending=False).head(20)
        
        if len(wr_receiving_ranked) > 0:
            plt.figure(figsize=(12, max(6, len(wr_receiving_ranked) * 0.3)))
            bars = plt.barh(wr_receiving_ranked['player_display_name'], wr_receiving_ranked['receiving_yards'], color='purple')
            plt.xlabel('Receiving Yards', fontsize=14)
            plt.ylabel('Wide Receivers', fontsize=14)
            plt.title(f'Top 20 Receiving Yards for NFL Wide Receivers in {selected_season}', fontsize=16)
            plt.xticks(fontsize=10)
            plt.yticks(fontsize=10)
            plt.bar_label(bars)
            plt.tight_layout()
            st.pyplot(plt)
        else:
            st.write("No WR receiving data available for the selected season.")
    else:
        st.write("No WR data available for the selected season.")

with tab4:
    st.header('Tight End Rankings')
    # Get the appropriate dataset for the selected season
    current_player_data = get_player_data_for_season(selected_season)
    te_selected_stats = current_player_data[(current_player_data['position'] == 'TE') & (current_player_data['season'] == selected_season)]
    
    if not te_selected_stats.empty:
        # Receiving Yards
        te_receiving_selected = te_selected_stats.groupby('player_display_name')['receiving_yards'].sum().reset_index()
        te_receiving_ranked = te_receiving_selected.sort_values(by='receiving_yards', ascending=False).head(20)
        
        if len(te_receiving_ranked) > 0:
            plt.figure(figsize=(12, max(6, len(te_receiving_ranked) * 0.3)))
            bars = plt.barh(te_receiving_ranked['player_display_name'], te_receiving_ranked['receiving_yards'], color='orange')
            plt.xlabel('Receiving Yards', fontsize=14)
            plt.ylabel('Tight Ends', fontsize=14)
            plt.title(f'Top 20 Receiving Yards for NFL Tight Ends in {selected_season}', fontsize=16)
            plt.xticks(fontsize=10)
            plt.yticks(fontsize=10)
            plt.bar_label(bars)
            plt.tight_layout()
            st.pyplot(plt)
        else:
            st.write("No TE receiving data available for the selected season.")
    else:
        st.write("No TE data available for the selected season.")
