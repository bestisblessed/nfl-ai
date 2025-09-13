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

# Season selector
selected_season = st.selectbox("Select Season:", [2025, 2024], index=0)

# df_teams = pd.read_csv('./data/Teams.csv')
# df_games = pd.read_csv('./data/Games.csv')
# df_playerstats = pd.read_csv('./data/PlayerStats.csv')

# Store DataFrames in session state
# st.session_state['df_teams'] = df_teams
# st.session_state['df_games'] = df_games
# st.session_state['df_playerstats'] = df_playerstats
# st.session_state['df_team_game_logs'] = df_team_game_logs
# st.session_state['df_schedule_and_game_results'] = df_schedule_and_game_results
df_teams = st.session_state['df_teams']
df_games = st.session_state['df_games']
df_playerstats = st.session_state['df_playerstats']
df_team_game_logs = st.session_state['df_all_team_game_logs']
df_schedule_and_game_results = st.session_state['df_schedule_and_game_results']

st.divider()

tab1, tab2, tab3, tab4 = st.tabs(["QBs", "RBs", "WRs", "TEs"])

with tab1:
### SACKS ###
    st.header('Quarterback Sack Rankings')
    qb_selected_stats = df_playerstats[(df_playerstats['position'] == 'QB') & (df_playerstats['season'] == selected_season)]
    
    if not qb_selected_stats.empty:
        qb_sacked_selected = qb_selected_stats.groupby('player_display_name')['sacks'].sum().reset_index()
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
        qb_interceptions_selected = qb_selected_stats.groupby('player_display_name')['interceptions'].sum().reset_index()
        qb_interceptions_ranked_selected = qb_interceptions_selected.sort_values(by='interceptions', ascending=False)
        
        if len(qb_interceptions_ranked_selected) > 0:
            plt.figure(figsize=(12, max(6, len(qb_interceptions_ranked_selected) * 0.3)))
            bars = plt.barh(qb_interceptions_ranked_selected['player_display_name'], qb_interceptions_ranked_selected['interceptions'], color='salmon')
            plt.xlabel('Number of Interceptions', fontsize=14)
            plt.ylabel('Quarterbacks', fontsize=14)
            plt.title(f'Number of Interceptions for NFL Quarterbacks in {selected_season}', fontsize=16)
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
    rb_selected_stats = df_playerstats[(df_playerstats['position'] == 'RB') & (df_playerstats['season'] == selected_season)]
    
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
    wr_selected_stats = df_playerstats[(df_playerstats['position'] == 'WR') & (df_playerstats['season'] == selected_season)]
    
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
    te_selected_stats = df_playerstats[(df_playerstats['position'] == 'TE') & (df_playerstats['season'] == selected_season)]
    
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
