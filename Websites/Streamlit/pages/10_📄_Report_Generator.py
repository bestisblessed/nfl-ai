import streamlit as st
import pandas as pd
import os
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np

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
    
    # Load additional data for enhanced statistics
    df_team_game_logs = pd.read_csv(os.path.join(current_dir, '../data', 'all_team_game_logs.csv'))
    df_defense_logs = pd.read_csv(os.path.join(current_dir, '../data', 'all_defense-game-logs.csv'))
    
    # Store in session state for future use
    st.session_state['df_games'] = df_games
    st.session_state['df_playerstats'] = df_playerstats
    st.session_state['df_roster2025'] = df_roster2025
    st.session_state['df_team_game_logs'] = df_team_game_logs
    st.session_state['df_defense_logs'] = df_defense_logs
else:
    df_games = st.session_state['df_games'] 
    df_playerstats = st.session_state['df_playerstats']
    df_roster2025 = st.session_state.get('df_roster2025')
    df_team_game_logs = st.session_state.get('df_team_game_logs')
    df_defense_logs = st.session_state.get('df_defense_logs')
    
    if df_roster2025 is None:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        df_roster2025 = pd.read_csv(os.path.join(current_dir, '../data/rosters', 'roster_2025.csv'))
        st.session_state['df_roster2025'] = df_roster2025
    
    if df_team_game_logs is None:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        df_team_game_logs = pd.read_csv(os.path.join(current_dir, '../data', 'all_team_game_logs.csv'))
        st.session_state['df_team_game_logs'] = df_team_game_logs
    
    if df_defense_logs is None:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        df_defense_logs = pd.read_csv(os.path.join(current_dir, '../data', 'all_defense-game-logs.csv'))
        st.session_state['df_defense_logs'] = df_defense_logs

# Helper functions (module scope) so they can be used anywhere on the page
def display_team_logo(team_abbrev, size=100):
    fname = f"{team_abbrev}.png"
    # Path relative to this file (pages/ -> ../images/team-logos/TEAM.png)
    script_relative_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'images', 'team-logos', fname))
    # Repo-root relative path (works when CWD is project root)
    repo_relative_path = os.path.join('images', 'team-logos', fname)

    logo_path = None
    if os.path.exists(script_relative_path):
        logo_path = script_relative_path
    elif os.path.exists(repo_relative_path):
        logo_path = repo_relative_path

    if logo_path:
        st.image(logo_path, width=size)
    else:
        st.markdown(
            f"<div style='width: {size}px; height: {size}px; border: 1px solid #ccc; display: flex; align-items: center; justify-content: center; font-size: 24px; font-weight: bold;'>{team_abbrev}</div>",
            unsafe_allow_html=True
        )

def sort_by_position(df):
    position_order = {'QB': 1, 'WR': 2, 'TE': 3, 'RB': 4}
    df = df.copy()
    df.loc[:, 'position_order'] = df['position'].map(position_order)
    return df.sort_values(by='position_order').drop(columns=['position_order'])

def calculate_team_stats(df_games, df_team_game_logs, team, last_n_games=10):
    """Calculate comprehensive team statistics for the last N games"""
    # Get recent games for the team
    team_games = df_games[((df_games['home_team'] == team) | (df_games['away_team'] == team))].copy()
    team_games = team_games.dropna(subset=['home_score', 'away_score']).sort_values('date', ascending=False).head(last_n_games)
    
    if team_games.empty:
        return {}
    
    # Calculate basic stats
    team_scores = []
    opponent_scores = []
    spreads = []
    totals = []
    weather_conditions = []
    rest_days = []
    
    for _, game in team_games.iterrows():
        if game['home_team'] == team:
            team_scores.append(game['home_score'])
            opponent_scores.append(game['away_score'])
            spreads.append(game['home_spread'] if pd.notna(game['home_spread']) else 0)
            rest_days.append(game.get('home_rest', 7))  # Default to 7 if not available
        else:
            team_scores.append(game['away_score'])
            opponent_scores.append(game['home_score'])
            spreads.append(game['away_spread'] if pd.notna(game['away_spread']) else 0)
            rest_days.append(game.get('away_rest', 7))  # Default to 7 if not available
        
        totals.append(game['total_line'] if pd.notna(game['total_line']) else 0)
        weather_conditions.append({
            'temp': game.get('temp', 0),
            'wind': game.get('wind', 0),
            'roof': game.get('roof', 'unknown'),
            'surface': game.get('surface', 'unknown')
        })
    
    # Calculate averages and trends
    avg_points_for = np.mean(team_scores)
    avg_points_against = np.mean(opponent_scores)
    point_differential = avg_points_for - avg_points_against
    
    # Betting stats
    team_covered = sum(1 for i, score in enumerate(team_scores) if score + spreads[i] > opponent_scores[i])
    over_hit = sum(1 for i, total in enumerate(totals) if team_scores[i] + opponent_scores[i] > total)
    
    # Weather analysis
    avg_temp = np.mean([w['temp'] for w in weather_conditions if w['temp'] > 0])
    avg_wind = np.mean([w['wind'] for w in weather_conditions if w['wind'] > 0])
    indoor_games = sum(1 for w in weather_conditions if w['roof'] == 'dome')
    
    # Rest advantage analysis
    avg_rest_days = np.mean(rest_days)
    short_rest_games = sum(1 for rest in rest_days if rest < 7)
    
    # Calculate efficiency metrics from team game logs
    efficiency_metrics = calculate_efficiency_metrics(df_team_game_logs, team, team_games['game_id'].tolist())
    
    return {
        'games_analyzed': len(team_games),
        'avg_points_for': round(avg_points_for, 1),
        'avg_points_against': round(avg_points_against, 1),
        'point_differential': round(point_differential, 1),
        'ats_record': f"{team_covered}-{len(team_games) - team_covered}",
        'over_under': f"{over_hit}-{len(team_games) - over_hit}",
        'avg_temp': round(avg_temp, 1) if avg_temp > 0 else 'N/A',
        'avg_wind': round(avg_wind, 1) if avg_wind > 0 else 'N/A',
        'indoor_games': indoor_games,
        'avg_rest_days': round(avg_rest_days, 1),
        'short_rest_games': short_rest_games,
        'recent_scores': team_scores[:5],  # Last 5 games
        'recent_opponent_scores': opponent_scores[:5],
        **efficiency_metrics
    }

def calculate_efficiency_metrics(df_team_game_logs, team, game_ids):
    """Calculate offensive and defensive efficiency metrics"""
    # Filter team game logs for the specific games
    team_logs = df_team_game_logs[df_team_game_logs['game_id'].isin(game_ids)].copy()
    
    if team_logs.empty:
        return {}
    
    # Determine if team was home or away for each game
    home_games = []
    away_games = []
    
    for _, log in team_logs.iterrows():
        # Check if this is a home or away game by looking at the game_id pattern
        # This is a simplified approach - in practice you'd want to cross-reference with df_games
        if 'home' in log['game_id'].lower() or log.get('home_team', '') == team:
            home_games.append(log)
        else:
            away_games.append(log)
    
    # Calculate offensive metrics (using home stats when team is home, away stats when team is away)
    offensive_stats = []
    defensive_stats = []
    
    for _, log in team_logs.iterrows():
        # For now, we'll use a simplified approach and calculate averages
        # In a more sophisticated implementation, you'd properly identify home/away
        offensive_stats.append({
            'pass_yds_per_att': log.get('home_pass_yds_per_att', 0) if pd.notna(log.get('home_pass_yds_per_att')) else 0,
            'rush_yds_per_att': log.get('home_rush_yds_per_att', 0) if pd.notna(log.get('home_rush_yds_per_att')) else 0,
            'pass_cmp_pct': log.get('home_pass_cmp_perc', 0) if pd.notna(log.get('home_pass_cmp_perc')) else 0,
            'pass_rating': log.get('home_pass_rating', 0) if pd.notna(log.get('home_pass_rating')) else 0,
        })
        
        defensive_stats.append({
            'pass_yds_per_att_allowed': log.get('away_pass_yds_per_att', 0) if pd.notna(log.get('away_pass_yds_per_att')) else 0,
            'rush_yds_per_att_allowed': log.get('away_rush_yds_per_att', 0) if pd.notna(log.get('away_rush_yds_per_att')) else 0,
        })
    
    # Calculate averages
    if offensive_stats:
        avg_pass_yds_per_att = np.mean([s['pass_yds_per_att'] for s in offensive_stats])
        avg_rush_yds_per_att = np.mean([s['rush_yds_per_att'] for s in offensive_stats])
        avg_pass_cmp_pct = np.mean([s['pass_cmp_pct'] for s in offensive_stats])
        avg_pass_rating = np.mean([s['pass_rating'] for s in offensive_stats])
    else:
        avg_pass_yds_per_att = avg_rush_yds_per_att = avg_pass_cmp_pct = avg_pass_rating = 0
    
    if defensive_stats:
        avg_pass_yds_per_att_allowed = np.mean([s['pass_yds_per_att_allowed'] for s in defensive_stats])
        avg_rush_yds_per_att_allowed = np.mean([s['rush_yds_per_att_allowed'] for s in defensive_stats])
    else:
        avg_pass_yds_per_att_allowed = avg_rush_yds_per_att_allowed = 0
    
    return {
        'avg_pass_yds_per_att': round(avg_pass_yds_per_att, 1),
        'avg_rush_yds_per_att': round(avg_rush_yds_per_att, 1),
        'avg_pass_cmp_pct': round(avg_pass_cmp_pct, 1),
        'avg_pass_rating': round(avg_pass_rating, 1),
        'avg_pass_yds_per_att_allowed': round(avg_pass_yds_per_att_allowed, 1),
        'avg_rush_yds_per_att_allowed': round(avg_rush_yds_per_att_allowed, 1),
    }

def calculate_defensive_stats(df_defense_logs, team, last_n_games=10):
    """Calculate defensive statistics for the last N games"""
    # Get recent defensive stats for the team
    team_defense = df_defense_logs[df_defense_logs['team'] == team].copy()
    
    if team_defense.empty:
        return {}
    
    # Get recent games (assuming game_id contains date info)
    recent_games = team_defense['game_id'].unique()[-last_n_games:]
    recent_defense = team_defense[team_defense['game_id'].isin(recent_games)]
    
    # Calculate defensive metrics
    total_sacks = recent_defense['sacks'].sum()
    total_int = recent_defense['def_int'].sum()
    total_int_yds = recent_defense['def_int_yds'].sum()
    total_int_td = recent_defense['def_int_td'].sum()
    total_tackles = recent_defense['tackles_combined'].sum()
    total_qb_hits = recent_defense['qb_hits'].sum()
    total_fumbles_forced = recent_defense['fumbles_forced'].sum()
    total_fumbles_rec = recent_defense['fumbles_rec'].sum()
    
    games_count = len(recent_games)
    
    return {
        'avg_sacks_per_game': round(total_sacks / games_count, 1) if games_count > 0 else 0,
        'avg_interceptions': round(total_int / games_count, 1) if games_count > 0 else 0,
        'avg_int_return_yards': round(total_int_yds / games_count, 1) if games_count > 0 else 0,
        'avg_int_tds': round(total_int_td / games_count, 1) if games_count > 0 else 0,
        'avg_tackles': round(total_tackles / games_count, 1) if games_count > 0 else 0,
        'avg_qb_hits': round(total_qb_hits / games_count, 1) if games_count > 0 else 0,
        'avg_fumbles_forced': round(total_fumbles_forced / games_count, 1) if games_count > 0 else 0,
        'avg_fumbles_recovered': round(total_fumbles_rec / games_count, 1) if games_count > 0 else 0,
        'total_turnovers': total_int + total_fumbles_rec
    }

def create_performance_chart(team1_stats, team2_stats, team1_name, team2_name):
    """Create a comparison chart of team performance metrics"""
    metrics = ['avg_points_for', 'avg_points_against', 'point_differential']
    team1_values = [team1_stats.get(metric, 0) for metric in metrics]
    team2_values = [team2_stats.get(metric, 0) for metric in metrics]
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        name=team1_name,
        x=['Points For', 'Points Against', 'Point Differential'],
        y=team1_values,
        marker_color='lightblue'
    ))
    
    fig.add_trace(go.Bar(
        name=team2_name,
        x=['Points For', 'Points Against', 'Point Differential'],
        y=team2_values,
        marker_color='lightcoral'
    ))
    
    fig.update_layout(
        title='Team Performance Comparison (Last 10 Games)',
        xaxis_title='Metrics',
        yaxis_title='Points',
        barmode='group',
        height=400
    )
    
    return fig

def create_trend_chart(team1_scores, team2_scores, team1_name, team2_name):
    """Create a trend chart showing recent game scores"""
    games = list(range(1, len(team1_scores) + 1))
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=games,
        y=team1_scores,
        mode='lines+markers',
        name=team1_name,
        line=dict(color='blue', width=3),
        marker=dict(size=8)
    ))
    
    fig.add_trace(go.Scatter(
        x=games,
        y=team2_scores,
        mode='lines+markers',
        name=team2_name,
        line=dict(color='red', width=3),
        marker=dict(size=8)
    ))
    
    fig.update_layout(
        title='Recent Scoring Trends (Last 5 Games)',
        xaxis_title='Games Ago',
        yaxis_title='Points Scored',
        height=400,
        hovermode='x unified'
    )
    
    return fig

def create_efficiency_chart(team1_stats, team2_stats, team1_name, team2_name):
    """Create a radar chart showing offensive efficiency metrics"""
    categories = ['Pass Yds/Att', 'Rush Yds/Att', 'Pass Comp %', 'Pass Rating']
    
    team1_values = [
        team1_stats.get('avg_pass_yds_per_att', 0),
        team1_stats.get('avg_rush_yds_per_att', 0),
        team1_stats.get('avg_pass_cmp_pct', 0) / 10,  # Scale down for radar chart
        team1_stats.get('avg_pass_rating', 0) / 10   # Scale down for radar chart
    ]
    
    team2_values = [
        team2_stats.get('avg_pass_yds_per_att', 0),
        team2_stats.get('avg_rush_yds_per_att', 0),
        team2_stats.get('avg_pass_cmp_pct', 0) / 10,  # Scale down for radar chart
        team2_stats.get('avg_pass_rating', 0) / 10   # Scale down for radar chart
    ]
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=team1_values,
        theta=categories,
        fill='toself',
        name=team1_name,
        line_color='blue'
    ))
    
    fig.add_trace(go.Scatterpolar(
        r=team2_values,
        theta=categories,
        fill='toself',
        name=team2_name,
        line_color='red'
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, max(max(team1_values), max(team2_values)) * 1.1]
            )),
        showlegend=True,
        title="Offensive Efficiency Comparison",
        height=500
    )
    
    return fig

def create_betting_analysis_chart(team1_stats, team2_stats, team1_name, team2_name):
    """Create a chart showing betting performance"""
    metrics = ['ATS Record', 'Over/Under']
    
    # Parse ATS records
    team1_ats = team1_stats.get('ats_record', '0-0').split('-')
    team2_ats = team2_stats.get('ats_record', '0-0').split('-')
    
    team1_ats_wins = int(team1_ats[0]) if team1_ats[0].isdigit() else 0
    team1_ats_losses = int(team1_ats[1]) if team1_ats[1].isdigit() else 0
    
    team2_ats_wins = int(team2_ats[0]) if team2_ats[0].isdigit() else 0
    team2_ats_losses = int(team2_ats[1]) if team2_ats[1].isdigit() else 0
    
    # Parse Over/Under records
    team1_ou = team1_stats.get('over_under', '0-0').split('-')
    team2_ou = team2_stats.get('over_under', '0-0').split('-')
    
    team1_overs = int(team1_ou[0]) if team1_ou[0].isdigit() else 0
    team1_unders = int(team1_ou[1]) if team1_ou[1].isdigit() else 0
    
    team2_overs = int(team2_ou[0]) if team2_ou[0].isdigit() else 0
    team2_unders = int(team2_ou[1]) if team2_ou[1].isdigit() else 0
    
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=('ATS Performance', 'Over/Under Performance'),
        specs=[[{"type": "bar"}, {"type": "bar"}]]
    )
    
    # ATS chart
    fig.add_trace(go.Bar(
        name=f"{team1_name} ATS",
        x=['Wins', 'Losses'],
        y=[team1_ats_wins, team1_ats_losses],
        marker_color='lightblue'
    ), row=1, col=1)
    
    fig.add_trace(go.Bar(
        name=f"{team2_name} ATS",
        x=['Wins', 'Losses'],
        y=[team2_ats_wins, team2_ats_losses],
        marker_color='lightcoral'
    ), row=1, col=1)
    
    # Over/Under chart
    fig.add_trace(go.Bar(
        name=f"{team1_name} O/U",
        x=['Overs', 'Unders'],
        y=[team1_overs, team1_unders],
        marker_color='lightgreen',
        showlegend=False
    ), row=1, col=2)
    
    fig.add_trace(go.Bar(
        name=f"{team2_name} O/U",
        x=['Overs', 'Unders'],
        y=[team2_overs, team2_unders],
        marker_color='orange',
        showlegend=False
    ), row=1, col=2)
    
    fig.update_layout(
        title="Betting Performance Analysis",
        height=400,
        showlegend=True
    )
    
    return fig

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
        st.dataframe(display_df[['Player','Pos','Games','Avg FPTS']], use_container_width=True, hide_index=True)
        for _, row in display_df.iterrows():
            pname = row['Player']
            ppos = row['Pos'] if 'Pos' in row else None
            with st.expander(pname, expanded=False):
                c1, c2, c3 = st.columns([1,1,1])
                c1.metric("Games", int(row['Games']))
                primary_label = row['Primary Label']
                c2.metric(primary_label, row['Primary'])
                c3.metric("Avg FPTS", row['Avg FPTS'])
                player_games = historical_df[historical_df['player_name_with_position'] == pname].sort_values('date', ascending=False).copy()
                # Base identifying columns always shown
                id_cols = ['season','week','home_team','away_team']
                # Position-specific columns
                if isinstance(ppos, str) and ppos.upper() == 'QB':
                    qb_cols = ['completions','attempts','passing_yards','passing_tds','interceptions','sacks',
                               'carries','rushing_yards','rushing_tds']
                    metric_cols = id_cols + qb_cols
                else:
                    pos_upper = (ppos or '').upper() if isinstance(ppos, str) else ''
                    if pos_upper == 'WR':
                        # WR: no rushing stats
                        sk_cols = ['receiving_yards', 'receiving_tds', 'targets', 'receptions']
                    elif pos_upper in ('RB','FB'):
                        # RB/FB: show rushing stats first, then receiving
                        sk_cols = ['rushing_yards','rushing_tds', 'carries',
                                   'receiving_yards','receiving_tds', 'receptions','targets'
                                   ]
                    else:
                        # Default (e.g., TE): keep receiving + rushing (no passing)
                        sk_cols = ['receiving_yards', 'receiving_tds', 'targets', 'receptions']
                    metric_cols = id_cols + sk_cols
                available_cols = [c for c in metric_cols if c in player_games.columns]
                st.dataframe(player_games[available_cols], use_container_width=True, height=260, hide_index=True)

# Utility to clear any previously generated report results
def _reset_report_results():
    for k in ['rg_hist_team1', 'rg_hist_team2', 'rg_team1', 'rg_team2']:
        st.session_state.pop(k, None)

# Clear any stale report results on page load so returning to this page doesn't show previous player tables
_reset_report_results()

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
            # Calculate enhanced team statistics
            team1_stats = calculate_team_stats(df_games, df_team_game_logs, team1)
            team2_stats = calculate_team_stats(df_games, df_team_game_logs, team2)
            team1_defense = calculate_defensive_stats(df_defense_logs, team1)
            team2_defense = calculate_defensive_stats(df_defense_logs, team2)
            
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

            # Display matchup summary with logos
            # col_logo1, col_vs, col_logo2 = st.columns([1, 2, 1])
            # with col_logo1:
            #     display_team_logo(team1, size=60)
            # with col_vs:
            #     st.markdown("<h2 style='text-align: center; margin: 0;'>VS</h2>", unsafe_allow_html=True)
            # with col_logo2:
            #     display_team_logo(team2, size=60)

            # Only here: compute and show streak, winner_team, and center-stats block
            recent_games_for_streak = last_10_games.sort_values(by='date', ascending=False)
            most_recent = recent_games_for_streak.iloc[0]
            if most_recent['home_score'] > most_recent['away_score']:
                winner_team = most_recent['home_team']
            else:
                winner_team = most_recent['away_team']

            streak = 0
            for _, g in recent_games_for_streak.iterrows():
                home_win = g['home_score'] > g['away_score']
                away_win = g['away_score'] > g['home_score']
                team_won = (home_win and g['home_team'] == winner_team) or (away_win and g['away_team'] == winner_team)
                if team_won:
                    streak += 1
                else:
                    break

            # Enhanced statistics display
            st.markdown("### 📊 Matchup Analysis")
            
            # Create columns for enhanced stats
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown(f"#### {team1} Recent Form")
                st.metric("Avg Points For", team1_stats.get('avg_points_for', 'N/A'))
                st.metric("Avg Points Against", team1_stats.get('avg_points_against', 'N/A'))
                st.metric("Point Differential", team1_stats.get('point_differential', 'N/A'))
                st.metric("ATS Record", team1_stats.get('ats_record', 'N/A'))
                st.metric("Over/Under", team1_stats.get('over_under', 'N/A'))
            
            with col2:
                st.markdown("#### Head-to-Head")
                st.metric(f"{team1} Wins", team1_wins)
                st.metric(f"{team2} Wins", team2_wins)
                st.metric("Winning Streak", f"{winner_team} ({streak})")
                st.metric("Avg Total Points", f"{average_total_points:.1f}")
                st.metric("50+ Point Games", over_50_points_games)
            
            with col3:
                st.markdown(f"#### {team2} Recent Form")
                st.metric("Avg Points For", team2_stats.get('avg_points_for', 'N/A'))
                st.metric("Avg Points Against", team2_stats.get('avg_points_against', 'N/A'))
                st.metric("Point Differential", team2_stats.get('point_differential', 'N/A'))
                st.metric("ATS Record", team2_stats.get('ats_record', 'N/A'))
                st.metric("Over/Under", team2_stats.get('over_under', 'N/A'))
            
            # Add defensive statistics
            if team1_defense or team2_defense:
                st.markdown("### 🛡️ Defensive Statistics (Last 10 Games)")
                def_col1, def_col2 = st.columns(2)
                
                with def_col1:
                    st.markdown(f"#### {team1} Defense")
                    if team1_defense:
                        st.metric("Avg Sacks/Game", team1_defense.get('avg_sacks_per_game', 'N/A'))
                        st.metric("Avg Interceptions", team1_defense.get('avg_interceptions', 'N/A'))
                        st.metric("Avg QB Hits", team1_defense.get('avg_qb_hits', 'N/A'))
                        st.metric("Avg Fumbles Forced", team1_defense.get('avg_fumbles_forced', 'N/A'))
                    else:
                        st.write("No defensive data available")
                
                with def_col2:
                    st.markdown(f"#### {team2} Defense")
                    if team2_defense:
                        st.metric("Avg Sacks/Game", team2_defense.get('avg_sacks_per_game', 'N/A'))
                        st.metric("Avg Interceptions", team2_defense.get('avg_interceptions', 'N/A'))
                        st.metric("Avg QB Hits", team2_defense.get('avg_qb_hits', 'N/A'))
                        st.metric("Avg Fumbles Forced", team2_defense.get('avg_fumbles_forced', 'N/A'))
                    else:
                        st.write("No defensive data available")
            
            # Add efficiency metrics
            if any(team1_stats.get(metric, 0) != 0 for metric in ['avg_pass_yds_per_att', 'avg_rush_yds_per_att', 'avg_pass_cmp_pct']):
                st.markdown("### ⚡ Efficiency Metrics (Last 10 Games)")
                eff_col1, eff_col2 = st.columns(2)
                
                with eff_col1:
                    st.markdown(f"#### {team1} Offense")
                    st.metric("Pass Yds/Att", team1_stats.get('avg_pass_yds_per_att', 'N/A'))
                    st.metric("Rush Yds/Att", team1_stats.get('avg_rush_yds_per_att', 'N/A'))
                    st.metric("Pass Comp %", f"{team1_stats.get('avg_pass_cmp_pct', 'N/A')}%")
                    st.metric("Pass Rating", team1_stats.get('avg_pass_rating', 'N/A'))
                
                with eff_col2:
                    st.markdown(f"#### {team2} Offense")
                    st.metric("Pass Yds/Att", team2_stats.get('avg_pass_yds_per_att', 'N/A'))
                    st.metric("Rush Yds/Att", team2_stats.get('avg_rush_yds_per_att', 'N/A'))
                    st.metric("Pass Comp %", f"{team2_stats.get('avg_pass_cmp_pct', 'N/A')}%")
                    st.metric("Pass Rating", team2_stats.get('avg_pass_rating', 'N/A'))
            
            # Add defensive efficiency
            if any(team1_stats.get(metric, 0) != 0 for metric in ['avg_pass_yds_per_att_allowed', 'avg_rush_yds_per_att_allowed']):
                st.markdown("### 🛡️ Defensive Efficiency (Last 10 Games)")
                def_eff_col1, def_eff_col2 = st.columns(2)
                
                with def_eff_col1:
                    st.markdown(f"#### {team1} Defense")
                    st.metric("Pass Yds/Att Allowed", team1_stats.get('avg_pass_yds_per_att_allowed', 'N/A'))
                    st.metric("Rush Yds/Att Allowed", team1_stats.get('avg_rush_yds_per_att_allowed', 'N/A'))
                
                with def_eff_col2:
                    st.markdown(f"#### {team2} Defense")
                    st.metric("Pass Yds/Att Allowed", team2_stats.get('avg_pass_yds_per_att_allowed', 'N/A'))
                    st.metric("Rush Yds/Att Allowed", team2_stats.get('avg_rush_yds_per_att_allowed', 'N/A'))
            
            # Add rest advantage analysis
            if team1_stats.get('avg_rest_days') or team2_stats.get('avg_rest_days'):
                st.markdown("### ⏰ Rest Advantage Analysis")
                rest_col1, rest_col2 = st.columns(2)
                
                with rest_col1:
                    st.markdown(f"#### {team1} Rest Patterns")
                    st.metric("Avg Rest Days", f"{team1_stats.get('avg_rest_days', 'N/A')} days")
                    st.metric("Short Rest Games", team1_stats.get('short_rest_games', 'N/A'))
                
                with rest_col2:
                    st.markdown(f"#### {team2} Rest Patterns")
                    st.metric("Avg Rest Days", f"{team2_stats.get('avg_rest_days', 'N/A')} days")
                    st.metric("Short Rest Games", team2_stats.get('short_rest_games', 'N/A'))
            
            # Add weather and venue analysis
            if team1_stats.get('avg_temp') != 'N/A' or team2_stats.get('avg_temp') != 'N/A':
                st.markdown("### 🌤️ Weather & Venue Analysis")
                weather_col1, weather_col2 = st.columns(2)
                
                with weather_col1:
                    st.markdown(f"#### {team1} Recent Conditions")
                    st.metric("Avg Temperature", f"{team1_stats.get('avg_temp', 'N/A')}°F")
                    st.metric("Avg Wind Speed", f"{team1_stats.get('avg_wind', 'N/A')} mph")
                    st.metric("Indoor Games", team1_stats.get('indoor_games', 'N/A'))
                
                with weather_col2:
                    st.markdown(f"#### {team2} Recent Conditions")
                    st.metric("Avg Temperature", f"{team2_stats.get('avg_temp', 'N/A')}°F")
                    st.metric("Avg Wind Speed", f"{team2_stats.get('avg_wind', 'N/A')} mph")
                    st.metric("Indoor Games", team2_stats.get('indoor_games', 'N/A'))
            
            # Add visualizations
            st.markdown("### 📈 Performance Visualizations")
            
            # Performance comparison chart
            if team1_stats and team2_stats:
                perf_chart = create_performance_chart(team1_stats, team2_stats, team1, team2)
                st.plotly_chart(perf_chart, use_container_width=True)
            
            # Scoring trends chart
            if team1_stats.get('recent_scores') and team2_stats.get('recent_scores'):
                trend_chart = create_trend_chart(
                    team1_stats['recent_scores'], 
                    team2_stats['recent_scores'], 
                    team1, 
                    team2
                )
                st.plotly_chart(trend_chart, use_container_width=True)
            
            # Efficiency radar chart
            if any(team1_stats.get(metric, 0) != 0 for metric in ['avg_pass_yds_per_att', 'avg_rush_yds_per_att', 'avg_pass_cmp_pct']):
                efficiency_chart = create_efficiency_chart(team1_stats, team2_stats, team1, team2)
                st.plotly_chart(efficiency_chart, use_container_width=True)
            
            # Betting analysis chart
            if team1_stats.get('ats_record') != '0-0' or team2_stats.get('ats_record') != '0-0':
                betting_chart = create_betting_analysis_chart(team1_stats, team2_stats, team1, team2)
                st.plotly_chart(betting_chart, use_container_width=True)

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
        row_logo, row_title = st.columns([0.1, 0.88])
        with row_logo:
            display_team_logo(st.session_state['rg_team1'], size=60)
        with row_title:
            st.markdown(f"<span style='font-size:2.2rem; font-weight:bold; vertical-align:middle; display:inline-block; margin-left:8px;'>{st.session_state['rg_team1']} Players</span>", unsafe_allow_html=True)
        show_condensed_players(st.session_state['rg_hist_team1'], st.session_state['rg_team1'], st.session_state['rg_team2'])
    with b:
        row_logo, row_title = st.columns([0.1, 0.88])
        with row_logo:
            display_team_logo(st.session_state['rg_team2'], size=60)
        with row_title:
            st.markdown(f"<span style='font-size:2.2rem; font-weight:bold; vertical-align:middle; display:inline-block; margin-left:8px;'>{st.session_state['rg_team2']} Players</span>", unsafe_allow_html=True)
        show_condensed_players(st.session_state['rg_hist_team2'], st.session_state['rg_team2'], st.session_state['rg_team1'])
