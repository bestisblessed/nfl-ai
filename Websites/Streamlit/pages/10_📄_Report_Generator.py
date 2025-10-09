import streamlit as st
import pandas as pd
import os
import plotly.express as px

# Page configuration
st.set_page_config(
    page_title="📄 Report Generator",
    page_icon="📄",
    layout="wide"   
)

st.markdown(
    """
    <div style="text-align: center;">
        <h1>Report Generator</h1>
        <p>Select two teams to generate a detailed matchup report, including team trends and player stats.</p>
    </div>
    """,
    unsafe_allow_html=True
)

# Load data files directly if not in session state
if 'df_games' not in st.session_state:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    df_games = pd.read_csv(os.path.join(current_dir, '../data', 'Games.csv'))
    df_playerstats = pd.read_csv(os.path.join(current_dir, '../data', 'PlayerStats.csv'))
    # Load 2025 roster as source of truth for current players
    df_roster2025 = pd.read_csv(os.path.join(current_dir, '../data/rosters', 'roster_2025.csv'))
    
    # Store in session state for future use
    st.session_state['df_games'] = df_games
    st.session_state['df_playerstats'] = df_playerstats
    st.session_state['df_roster2025'] = df_roster2025
else:
    df_games = st.session_state['df_games'] 
    df_playerstats = st.session_state['df_playerstats']
    df_roster2025 = st.session_state.get('df_roster2025')
    if df_roster2025 is None:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        df_roster2025 = pd.read_csv(os.path.join(current_dir, '../data/rosters', 'roster_2025.csv'))
        st.session_state['df_roster2025'] = df_roster2025

# Helper functions (module scope) so they can be used anywhere on the page
def sort_by_position(df):
    position_order = {'QB': 1, 'WR': 2, 'TE': 3, 'RB': 4}
    df = df.copy()
    df.loc[:, 'position_order'] = df['position'].map(position_order)
    return df.sort_values(by='position_order').drop(columns=['position_order'])

def show_condensed_players(historical_df, team_name, opponent_name):
    if historical_df.empty:
        st.write(f"No historical stats found for {team_name} players vs {opponent_name}.")
        return

    # compute summary metrics: Games, Avg Rec Yds, Avg FPTS, plus pass/rush means if present
    base = historical_df.groupby('player_name_with_position').agg({
        'game_id': 'nunique',
        'fantasy_points_ppr': 'mean'
    }).rename(columns={'game_id':'games','fantasy_points_ppr':'avg_fpts'}).reset_index()
    # add receiving/passing/rushing means if available
    if 'receiving_yards' in historical_df.columns:
        rec = historical_df.groupby('player_name_with_position')['receiving_yards'].mean().reset_index().rename(columns={'receiving_yards':'avg_rec_yds'})
        base = base.merge(rec, on='player_name_with_position', how='left')
    else:
        base['avg_rec_yds'] = 0.0
    if 'passing_yards' in historical_df.columns:
        pas = historical_df.groupby('player_name_with_position')['passing_yards'].mean().reset_index().rename(columns={'passing_yards':'avg_pass_yds'})
        base = base.merge(pas, on='player_name_with_position', how='left')
    else:
        base['avg_pass_yds'] = 0.0
    if 'rushing_yards' in historical_df.columns:
        rush = historical_df.groupby('player_name_with_position')['rushing_yards'].mean().reset_index().rename(columns={'rushing_yards':'avg_rush_yds'})
        base = base.merge(rush, on='player_name_with_position', how='left')
    else:
        base['avg_rush_yds'] = 0.0
    # determine player position (most common) per player
    pos_map = historical_df.groupby('player_name_with_position')['position'].agg(lambda s: s.mode().iloc[0] if not s.mode().empty else s.iloc[0]).reset_index().rename(columns={'position':'pos'})
    base = base.merge(pos_map, on='player_name_with_position', how='left')
    # round numeric values for display
    for c in ['avg_rec_yds','avg_pass_yds','avg_rush_yds','avg_fpts']:
        base[c] = base[c].fillna(0).round(1)

    # Choose primary metric per-player based on position
    def pick_primary(row):
        # Treat Fullbacks (FB) as RBs for rushing yards priority
        if row['pos'] == 'QB':
            return row['avg_pass_yds'], 'Avg Pass Yds'
        elif row['pos'] in ('RB', 'FB'):
            return row['avg_rush_yds'], 'Avg Rush Yds'
        else:
            return row['avg_rec_yds'], 'Avg Rec Yds'

    prim_vals = base.apply(lambda r: pick_primary(r), axis=1)
    base['primary_val'] = [v for v,_ in prim_vals]
    base['primary_label'] = [lbl for _,lbl in prim_vals]

    # include position and sort by position priority (QB, RB, WR, TE), then by games and primary metric
    display_df = base[['player_name_with_position','pos','games','primary_val','avg_fpts','primary_label']].copy()
    pos_priority = {'QB': 0, 'WR': 1, 'TE': 2, 'RB': 3}
    display_df['pos_order'] = display_df['pos'].map(lambda p: pos_priority.get(p, 4))
    display_df = display_df.sort_values(['pos_order','games','primary_val'], ascending=[True, False, False]).reset_index(drop=True)
    display_df = display_df[['player_name_with_position','games','primary_val','avg_fpts','primary_label','pos','pos_order']]
    display_df.columns = ['Player','Games','Primary','Avg FPTS','Primary Label','Pos','Pos Order']

    with st.container():
        st.subheader(f"**{team_name} Players**")
        st.dataframe(display_df[['Player','Pos','Games','Primary','Avg FPTS']], use_container_width=True, hide_index=True)
        for _, row in display_df.iterrows():
            pname = row['Player']
            with st.expander(pname, expanded=False):
                c1, c2, c3 = st.columns([1,1,1])
                c1.metric("Games", int(row['Games']))
                primary_label = row['Primary Label']
                c2.metric(primary_label, row['Primary'])
                c3.metric("Avg FPTS", row['Avg FPTS'])
                player_games = historical_df[historical_df['player_name_with_position'] == pname].sort_values('date', ascending=False).copy()
                metric_cols = ['season','week','game_id','date','home_team','away_team','receptions','targets','receiving_yards','receiving_tds','carries','rushing_yards','fantasy_points_ppr','passing_yards']
                available_cols = [c for c in metric_cols if c in player_games.columns]
                st.dataframe(player_games[available_cols], use_container_width=True, height=260, hide_index=True)

# Utility to clear any previously generated report results
def _reset_report_results():
    for k in ['rg_hist_team1', 'rg_hist_team2', 'rg_team1', 'rg_team2']:
        st.session_state.pop(k, None)

# On first load of this page, clear stale results so player sections don't show by default
if 'rg_initialized' not in st.session_state:
    _reset_report_results()
    st.session_state['rg_initialized'] = True

# Center the top section (narrower middle column)
col1, col2, col3 = st.columns([0.2, .5, 0.2]) # Middle ~60% width
with col2:
    # Team selection using selectbox with unique teams
    unique_teams = sorted(df_games['home_team'].unique())
    left_team_col, spacer_mid, right_team_col = st.columns([1, 0.0001, 1])
    with left_team_col:
        team1 = st.selectbox('Select Team 1:', options=unique_teams, index=unique_teams.index('BUF'), key='team1_select', on_change=_reset_report_results)
    with right_team_col:
        team2 = st.selectbox('Select Team 2:', options=unique_teams, index=unique_teams.index('MIA'), key='team2_select', on_change=_reset_report_results)

    # Center the generate button
    btn_c1, btn_c2, btn_c3 = st.columns([1, 0.4, 1])
    with btn_c2:
        generate_clicked = st.button('Generate Report', use_container_width=True)
    if generate_clicked:
        
        # Filter for recent matchups between the two teams (already sorted by date, most recent first)
        team_matchups = df_games[((df_games['home_team'] == team1) & (df_games['away_team'] == team2)) |
                                 ((df_games['home_team'] == team2) & (df_games['away_team'] == team1))]
        
        # Filter out unplayed games (NaN scores) FIRST, then take the 10 most recent completed games
        completed_matchups = team_matchups.dropna(subset=['home_score', 'away_score'])
        last_10_games = completed_matchups.sort_values(by='date', ascending=False).head(10)

        if last_10_games.empty:
            st.write(f"No recent games found between {team1} and {team2}.")
        else:
            # Team-level statistics (using only completed games)
            total_points = last_10_games['home_score'] + last_10_games['away_score']
            average_total_points = total_points.mean()
            team1_wins = int(((last_10_games['home_team'] == team1) & (last_10_games['home_score'] > last_10_games['away_score'])).sum() +
                         ((last_10_games['away_team'] == team1) & (last_10_games['away_score'] > last_10_games['home_score'])).sum())
            team2_wins = int(((last_10_games['home_team'] == team2) & (last_10_games['home_score'] > last_10_games['away_score'])).sum() +
                         ((last_10_games['away_team'] == team2) & (last_10_games['away_score'] > last_10_games['home_score'])).sum())

            team1_scores = last_10_games.loc[last_10_games['home_team'] == team1, 'home_score'].sum() + \
                           last_10_games.loc[last_10_games['away_team'] == team1, 'away_score'].sum()
            team2_scores = last_10_games.loc[last_10_games['home_team'] == team2, 'home_score'].sum() + \
                           last_10_games.loc[last_10_games['away_team'] == team2, 'away_score'].sum()

            over_50_points_games = int((total_points > 50).sum())

            st.write(f"**Matchup Summary: {team1} vs {team2}**")
            st.write(f"{len(last_10_games)} Most Recent Games Analyzed")
            st.write(f"{team1} Wins: {team1_wins}")
            st.write(f"{team2} Wins: {team2_wins}")
            st.write(f"Average Total Points: {average_total_points:.1f}")
            st.write(f"Games with more than 50 total points: {over_50_points_games}")
            st.write(f"Total points scored by {team1}: {team1_scores}")
            st.write(f"Total points scored by {team2}: {team2_scores}")

            # Use official 2025 roster to determine who is currently on each team (exclude CUT/RET)
            roster = df_roster2025
            roster_team1 = roster[(roster['season'] == 2025) & (roster['team'] == team1) & (~roster['status'].isin(['CUT','RET']))]
            roster_team2 = roster[(roster['season'] == 2025) & (roster['team'] == team2) & (~roster['status'].isin(['CUT','RET']))]

            players_team1_names = roster_team1['full_name'].dropna().unique()
            players_team2_names = roster_team2['full_name'].dropna().unique()

            # Initialize historical_stats_team1 and historical_stats_team2 outside the conditional blocks
            historical_stats_team1 = pd.DataFrame(columns=df_playerstats.columns)
            historical_stats_team2 = pd.DataFrame(columns=df_playerstats.columns)

            if players_team1_names.size > 0:
                historical_stats_team1 = df_playerstats[(df_playerstats['player_display_name'].isin(players_team1_names)) &
                                                        (((df_playerstats['home_team'] == team1) & (df_playerstats['away_team'] == team2)) |
                                                         ((df_playerstats['home_team'] == team2) & (df_playerstats['away_team'] == team1)))]
            else:
                st.info(f"No 2025 roster players found for {team1} matching the roster criteria.")

            if players_team2_names.size > 0:
                historical_stats_team2 = df_playerstats[(df_playerstats['player_display_name'].isin(players_team2_names)) &
                                                        (((df_playerstats['home_team'] == team1) & (df_playerstats['away_team'] == team2)) |
                                                         ((df_playerstats['home_team'] == team2) & (df_playerstats['away_team'] == team1)))]
            else:
                st.info(f"No 2025 roster players found for {team2} matching the roster criteria.")

            # Merge in game dates from df_games so we can sort and chart by date
            if not historical_stats_team1.empty:
                if 'date' not in historical_stats_team1.columns:
                    historical_stats_team1 = historical_stats_team1.merge(df_games[['game_id', 'date']], on='game_id', how='left')
                historical_stats_team1.loc[:, 'date'] = pd.to_datetime(historical_stats_team1['date'], errors='coerce')
            if not historical_stats_team2.empty:
                if 'date' not in historical_stats_team2.columns:
                    historical_stats_team2 = historical_stats_team2.merge(df_games[['game_id', 'date']], on='game_id', how='left')
                historical_stats_team2.loc[:, 'date'] = pd.to_datetime(historical_stats_team2['date'], errors='coerce')

            # Add player position to the player display name for both teams (avoid SettingWithCopyWarning)
            if not historical_stats_team1.empty:
                historical_stats_team1 = historical_stats_team1.copy()
                historical_stats_team1.loc[:, 'player_name_with_position'] = historical_stats_team1['player_display_name'] + " (" + historical_stats_team1['position'] + ")"
            if not historical_stats_team2.empty:
                historical_stats_team2 = historical_stats_team2.copy()
                historical_stats_team2.loc[:, 'player_name_with_position'] = historical_stats_team2['player_display_name'] + " (" + historical_stats_team2['position'] + ")"

            # Save results to session state for full-width render below
            st.session_state['rg_team1'] = team1
            st.session_state['rg_team2'] = team2
            st.session_state['rg_hist_team1'] = historical_stats_team1
            st.session_state['rg_hist_team2'] = historical_stats_team2

# Full-width Player sections (rendered outside the centered column)
if all(k in st.session_state for k in ['rg_hist_team1','rg_hist_team2','rg_team1','rg_team2']):
    st.divider()
    a, b = st.columns(2)
    with a:
        show_condensed_players(st.session_state['rg_hist_team1'], st.session_state['rg_team1'], st.session_state['rg_team2'])
    with b:
        show_condensed_players(st.session_state['rg_hist_team2'], st.session_state['rg_team2'], st.session_state['rg_team1'])
