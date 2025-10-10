import streamlit as st
import pandas as pd
import os
import plotly.express as px
import numpy as np
import base64

# NFL team color mapping (primary colors)
TEAM_COLORS = {
    'ARI': '#97233F', 'ATL': '#A71930', 'BAL': '#241773', 'BUF': '#00338D', 'CAR': '#0085CA',
    'CHI': '#0B162A', 'CIN': '#FB4F14', 'CLE': '#311D00', 'DAL': '#003594', 'DEN': '#FB4F14',
    'DET': '#0076B6', 'GB': '#203731', 'HOU': '#03202F', 'IND': '#002C5F', 'JAX': '#101820',
    'KC': '#E31837', 'LAC': '#0080C6', 'LAR': '#003594', 'LVR': '#000000', 'MIA': '#008E97',
    'MIN': '#4F2683', 'NE': '#002244', 'NO': '#D3BC8D', 'NYG': '#0B2265', 'NYJ': '#125740',
    'PHI': '#004C54', 'PIT': '#FFB612', 'SEA': '#002244', 'SF': '#AA0000', 'TB': '#D50A0A',
    'TEN': '#4B92DB', 'WAS': '#5A1414'
}

NFL_BLUE = '#013369'
NFL_RED = '#D50A0A'
PUSH_GRAY = '#7f7f7f'

def get_team_color(abbr: str) -> str:
    return TEAM_COLORS.get(str(abbr).upper(), '#555555')

# Page configuration
st.set_page_config(
    page_title="⚔️ Report Generator",
    page_icon="⚔️",
    layout="wide"   
)

# Global responsive styles for this page
st.markdown(
    """
    <style>
      /* Constrain overall content width and center it */
      .block-container {
        max-width: 1200px;
        padding-left: 1rem;
        padding-right: 1rem;
        margin: 0 auto;
      }

      /* Ensure Plotly charts always fill their container */
      [data-testid="stPlotlyChart"] > div {
        width: 100% !important;
      }

      /* Reduce excessive side padding on narrow screens */
      @media (max-width: 1100px) {
        h1 { font-size: 1.8rem; }
        .stButton > button { width: 100%; }
      }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div style="text-align: center;">
        <h1>Matchup Report Generator</h1>
    </div>
    """,
    unsafe_allow_html=True
)
st.write("")
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.caption("Select two teams to generate a detailed matchup report with head-to-head team trends and player stats.")

st.write("")
# st.divider()

# Load data files directly if not in session state
if 'df_games' not in st.session_state:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    df_games = pd.read_csv(os.path.join(current_dir, '../data', 'Games.csv'))
    df_playerstats = pd.read_csv(os.path.join(current_dir, '../data', 'PlayerStats.csv'))
    # Load 2025 roster as source of truth for current players
    df_roster2025 = pd.read_csv(os.path.join(current_dir, '../data/rosters', 'roster_2025.csv'))
    # Additional logs for defensive metrics
    try:
        df_team_game_logs = pd.read_csv(os.path.join(current_dir, '../data', 'all_team_game_logs.csv'))
    except Exception:
        df_team_game_logs = pd.DataFrame()
    try:
        df_defense_logs = pd.read_csv(os.path.join(current_dir, '../data', 'all_defense-game-logs.csv'))
    except Exception:
        df_defense_logs = pd.DataFrame()
    try:
        df_redzone = pd.read_csv(os.path.join(current_dir, '../data', 'all_redzone.csv'))
    except Exception:
        df_redzone = pd.DataFrame()
    
    # Store in session state for future use
    st.session_state['df_games'] = df_games
    st.session_state['df_playerstats'] = df_playerstats
    st.session_state['df_roster2025'] = df_roster2025
    st.session_state['df_team_game_logs'] = df_team_game_logs
    st.session_state['df_defense_logs'] = df_defense_logs
    st.session_state['df_redzone'] = df_redzone
else:
    df_games = st.session_state['df_games'] 
    df_playerstats = st.session_state['df_playerstats']
    df_roster2025 = st.session_state.get('df_roster2025')
    df_team_game_logs = st.session_state.get('df_team_game_logs')
    df_defense_logs = st.session_state.get('df_defense_logs')
    df_redzone = st.session_state.get('df_redzone')
    if df_roster2025 is None:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        df_roster2025 = pd.read_csv(os.path.join(current_dir, '../data/rosters', 'roster_2025.csv'))
        st.session_state['df_roster2025'] = df_roster2025
    if df_team_game_logs is None:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        try:
            df_team_game_logs = pd.read_csv(os.path.join(current_dir, '../data', 'all_team_game_logs.csv'))
        except Exception:
            df_team_game_logs = pd.DataFrame()
        st.session_state['df_team_game_logs'] = df_team_game_logs
    if df_defense_logs is None:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        try:
            df_defense_logs = pd.read_csv(os.path.join(current_dir, '../data', 'all_defense-game-logs.csv'))
        except Exception:
            df_defense_logs = pd.DataFrame()
        st.session_state['df_defense_logs'] = df_defense_logs
    if df_redzone is None:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        try:
            df_redzone = pd.read_csv(os.path.join(current_dir, '../data', 'all_redzone.csv'))
        except Exception:
            df_redzone = pd.DataFrame()
        st.session_state['df_redzone'] = df_redzone

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

def compute_top_skill_performers(historical_df: pd.DataFrame, top_n: int = 4) -> pd.DataFrame:
    """Return top-N non-QB skill players (WR/RB/TE/FB) sorted by:
    Rec TDs, Rec Yds, Rush TDs, Rush Yds (desc)."""
    if historical_df is None or historical_df.empty:
        return pd.DataFrame(columns=['Player','Pos','Total TDs','Rec Yds','Rush Yds','Rec TDs','Rush TDs'])

    df = historical_df.copy()
    # Ensure numeric fields
    for col in ['receiving_yards','rushing_yards','receiving_tds','rushing_tds']:
        if col not in df.columns:
            df[col] = 0
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    if 'position' not in df.columns or 'player_display_name' not in df.columns:
        return pd.DataFrame(columns=['Player','Pos','Total TDs','Rec Yds','Rush Yds','Rec TDs','Rush TDs'])

    skill = df[df['position'].isin(['WR','RB','TE','FB'])]
    if skill.empty:
        return pd.DataFrame(columns=['Player','Pos','Total TDs','Rec Yds','Rush Yds','Rec TDs','Rush TDs'])

    grouped = (
        skill.groupby(['player_display_name','position'], as_index=False)[['receiving_tds','rushing_tds','receiving_yards','rushing_yards']]
             .sum()
    )
    grouped = grouped.sort_values(['receiving_tds','receiving_yards','rushing_tds','rushing_yards'], ascending=[False, False, False, False]).head(top_n)
    display_top = grouped.rename(columns={
        'player_display_name':'Player',
        'position':'Pos',
        'receiving_yards':'Rec Yds',
        'rushing_yards':'Rush Yds',
        'receiving_tds':'Rec TDs',
        'rushing_tds':'Rush TDs'
    })
    cols_order = ['Player','Pos','Rec TDs','Rec Yds','Rush TDs','Rush Yds']
    return display_top[[c for c in cols_order if c in display_top.columns]]

def get_redzone_targets(df_redzone: pd.DataFrame, team: str, year: int = 2025) -> pd.DataFrame:
    """Return red-zone receiving targets for a team in a given year."""
    if df_redzone is None or df_redzone.empty:
        return pd.DataFrame(columns=['Player', 'Targets', 'Receptions', 'Catch%', 'TDs'])

    # Filter for receiving stats, specific team and year
    subset = df_redzone[(df_redzone['StatType'] == 'receiving') &
                       (df_redzone['Year'] == year) &
                       (df_redzone['Tm'] == team)].copy()

    if subset.empty:
        return pd.DataFrame(columns=['Player', 'Targets', 'Receptions', 'Catch%', 'TDs'])

    # Select and rename relevant columns
    subset = subset[['Player', 'Inside 20_Tgt', 'Inside 20_Rec', 'Inside 20_Ctch%', 'Inside 20_TD']]
    subset = subset.rename(columns={
        'Inside 20_Tgt': 'Targets',
        'Inside 20_Rec': 'Receptions',
        'Inside 20_Ctch%': 'Catch%',
        'Inside 20_TD': 'TDs'
    })

    # Convert to numeric and sort by targets descending
    for col in ['Targets', 'Receptions', 'TDs']:
        subset[col] = pd.to_numeric(subset[col], errors='coerce').fillna(0).astype(int)

    subset['Catch%'] = pd.to_numeric(subset['Catch%'], errors='coerce').fillna(0).round(1)

    # Sort by targets descending, then by player name
    subset = subset.sort_values(by=['Targets', 'Player'], ascending=[False, True]).reset_index(drop=True)

    return subset

def calculate_defense_summary(df_defense_logs: pd.DataFrame, df_team_game_logs: pd.DataFrame, team: str, last_n_games: int = 10, df_games_ctx: pd.DataFrame | None = None) -> dict:
    """Compute defensive metrics for a team over the last N games.
    Returns averages for sacks/game, QB hits, total turnovers, pass yards allowed, rush yards allowed.
    """
    out = {
        'avg_sacks_per_game': 0.0,
        'avg_qb_hits': 0.0,
        'avg_total_turnovers': 0.0,
        'avg_pass_yards_allowed': 0.0,
        'avg_rush_yards_allowed': 0.0,
    }
    # Defensive event logs (sacks, hits, turnovers)
    if isinstance(df_defense_logs, pd.DataFrame) and not df_defense_logs.empty and 'team' in df_defense_logs.columns:
        team_def = df_defense_logs[df_defense_logs['team'] == team].copy()
        if not team_def.empty:
            # Use last N unique games
            recent_game_ids = list(pd.unique(team_def['game_id']))[-last_n_games:]
            recent = team_def[team_def['game_id'].isin(recent_game_ids)]
            gcount = max(1, len(recent_game_ids))
            sacks = pd.to_numeric(recent.get('sacks', 0), errors='coerce').fillna(0).sum()
            qb_hits = pd.to_numeric(recent.get('qb_hits', 0), errors='coerce').fillna(0).sum()
            interceptions = pd.to_numeric(recent.get('def_int', 0), errors='coerce').fillna(0).sum()
            fumbles_rec = pd.to_numeric(recent.get('fumbles_rec', 0), errors='coerce').fillna(0).sum()
            out['avg_sacks_per_game'] = round(float(sacks) / gcount, 1)
            out['avg_qb_hits'] = round(float(qb_hits) / gcount, 1)
            out['avg_total_turnovers'] = round(float(interceptions + fumbles_rec) / gcount, 1)
    
    # Team game logs for yards allowed per game
    if isinstance(df_team_game_logs, pd.DataFrame) and not df_team_game_logs.empty:
        # Many team logs lack explicit home/away team columns but include them in game_id like '2017_01_AWAY_HOME'
        logs_all = df_team_game_logs.copy()
        if 'home_team' not in logs_all.columns or 'away_team' not in logs_all.columns:
            parts = logs_all['game_id'].astype(str).str.split('_')
            # Expecting [season, week, away, home]
            logs_all.loc[:, 'away_team'] = parts.str[2]
            logs_all.loc[:, 'home_team'] = parts.str[3]
        # Identify recent N games using df_games if available for better date sorting
        if isinstance(df_games_ctx, pd.DataFrame) and not df_games_ctx.empty and 'date' in df_games_ctx.columns:
            games = df_games_ctx[(df_games_ctx['home_team'] == team) | (df_games_ctx['away_team'] == team)].dropna(subset=['home_score','away_score']).copy()
            games.loc[:, 'date'] = pd.to_datetime(games['date'], errors='coerce')
            games = games.sort_values('date').tail(last_n_games)
            recent_ids = set(games['game_id'].astype(str))
            logs = logs_all[logs_all['game_id'].astype(str).isin(recent_ids)].copy()
        else:
            # Fallback: filter and take tail by game_id order
            mask = (logs_all['home_team'] == team) | (logs_all['away_team'] == team)
            logs = logs_all.loc[mask].copy()
        if not logs.empty:
            # Sort by any available date or game_id for recency and take last N
            if 'date' in logs.columns:
                logs.loc[:, 'date'] = pd.to_datetime(logs['date'], errors='coerce')
                logs = logs.sort_values('date')
            elif 'game_id' in logs.columns:
                logs = logs.sort_values('game_id')
            logs = logs.tail(last_n_games)

            # Ensure numeric source columns exist
            for k in ['home_pass_yds','away_pass_yds','home_rush_yds','away_rush_yds']:
                if k not in logs.columns:
                    logs.loc[:, k] = 0
                logs.loc[:, k] = pd.to_numeric(logs[k], errors='coerce').fillna(0)

            # Build per-row allowed yardage with safe lookups
            pass_allowed_vals, rush_allowed_vals = [], []
            for _, r in logs.iterrows():
                is_home = str(r.get('home_team')) == str(team)
                pass_allowed = float(r.get('away_pass_yds', 0)) if is_home else float(r.get('home_pass_yds', 0))
                rush_allowed = float(r.get('away_rush_yds', 0)) if is_home else float(r.get('home_rush_yds', 0))
                pass_allowed_vals.append(pass_allowed)
                rush_allowed_vals.append(rush_allowed)

            out['avg_pass_yards_allowed'] = round(float(np.nanmean(pass_allowed_vals)), 1) if len(pass_allowed_vals) else 0.0
            out['avg_rush_yards_allowed'] = round(float(np.nanmean(rush_allowed_vals)), 1) if len(rush_allowed_vals) else 0.0

    return out

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
    
    # Fix: Coerce TD columns to numeric BEFORE groupby sum
    for tdcol in ['passing_tds', 'rushing_tds', 'receiving_tds']:
        if tdcol in historical_df.columns:
            historical_df[tdcol] = pd.to_numeric(historical_df[tdcol], errors='coerce').fillna(0)
    
    # add total TDs metrics
    if 'passing_tds' in historical_df.columns:
        pass_tds = historical_df.groupby('player_name_with_position')['passing_tds'].sum().reset_index().rename(columns={'passing_tds':'total_pass_tds'})
        base = base.merge(pass_tds, on='player_name_with_position', how='left')
    else:
        base['total_pass_tds'] = 0
    if 'receiving_tds' in historical_df.columns:
        rec_tds = historical_df.groupby('player_name_with_position')['receiving_tds'].sum().reset_index().rename(columns={'receiving_tds':'total_rec_tds'})
        base = base.merge(rec_tds, on='player_name_with_position', how='left')
    else:
        base['total_rec_tds'] = 0
    if 'rushing_tds' in historical_df.columns:
        rush_tds = historical_df.groupby('player_name_with_position')['rushing_tds'].sum().reset_index().rename(columns={'rushing_tds':'total_rush_tds'})
        base = base.merge(rush_tds, on='player_name_with_position', how='left')
    else:
        base['total_rush_tds'] = 0

    # Fill NaN values with 0 for TD columns
    base['total_pass_tds'] = base['total_pass_tds'].fillna(0)
    base['total_rec_tds'] = base['total_rec_tds'].fillna(0)
    base['total_rush_tds'] = base['total_rush_tds'].fillna(0)
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
    
    # Choose primary TD metric per-player based on position
    def pick_primary_tds(row):
        if row['pos'] == 'QB':
            return int(row['total_pass_tds']), 'Total Pass TDs'
        elif row['pos'] in ('RB', 'FB'):
            return int(row['total_rush_tds']), 'Total Rush TDs'
        else:
            return int(row['total_rec_tds']), 'Total Rec TDs'

    prim_vals = base.apply(lambda r: pick_primary(r), axis=1)
    base['primary_val'] = [v for v,_ in prim_vals]
    base['primary_label'] = [lbl for _,lbl in prim_vals]
    
    prim_tds = base.apply(lambda r: pick_primary_tds(r), axis=1)
    base['primary_tds'] = [v for v,_ in prim_tds]
    base['primary_tds_label'] = [lbl for _,lbl in prim_tds]

    # include position and sort by position priority (QB, RB, WR, TE), then by games and primary metric
    display_df = base[['player_name_with_position','pos','games','primary_tds','primary_val','avg_fpts','primary_label','primary_tds_label']].copy()
    pos_priority = {'QB': 0, 'WR': 1, 'TE': 2, 'RB': 3}
    display_df['pos_order'] = display_df['pos'].map(lambda p: pos_priority.get(p, 4))
    display_df = display_df.sort_values(['pos_order','games','primary_val'], ascending=[True, False, False]).reset_index(drop=True)
    display_df = display_df[['player_name_with_position','games','primary_tds','primary_val','avg_fpts','primary_label','primary_tds_label','pos','pos_order']]
    display_df.columns = ['Player','Games','Primary TDs','Primary','Avg FPTS','Primary Label','Primary TDs Label','Pos','Pos Order']

    with st.container():
        # Summary: restore full players table at top
        st.dataframe(display_df[['Player','Pos','Games','Avg FPTS']], use_container_width=True, hide_index=True)
        for _, row in display_df.iterrows():
            pname = row['Player']
            ppos = row['Pos'] if 'Pos' in row else None
            with st.expander(pname, expanded=False):
                # Only show each metric once, and ensure "Games" is not repeated
                if ppos in ('RB', 'FB'):
                    c1, c2, c3, c4 = st.columns([1,1,1,1])
                    this_games = historical_df[historical_df['player_name_with_position'] == pname]
                    rush_tds_sum = int(this_games['rushing_tds'].sum()) if 'rushing_tds' in this_games.columns else 0
                    rec_tds_sum = int(this_games['receiving_tds'].sum()) if 'receiving_tds' in this_games.columns else 0
                    c1.metric("Games", int(row['Games']))
                    c2.metric("Total Rush TDs", rush_tds_sum)
                    c3.metric("Total Rec TDs", rec_tds_sum)
                    c4.metric("Avg FPTS", row['Avg FPTS'])
                else:
                    c1, c2, c3, c4 = st.columns([1,1,1,1])
                    c1.metric("Games", int(row['Games']))
                    primary_tds_label = row['Primary TDs Label']
                    c2.metric(primary_tds_label, int(row['Primary TDs']))
                    primary_label = row['Primary Label']
                    c3.metric(primary_label, row['Primary'])
                    c4.metric("Avg FPTS", row['Avg FPTS'])
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
                # Format the dataframe to ensure season is displayed as integer without commas
                display_games = player_games[available_cols].copy()
                if 'season' in display_games.columns:
                    display_games['season'] = display_games['season'].astype(int)
                st.dataframe(display_games, use_container_width=True, height=260, hide_index=True, 
                           column_config={
                               'season': st.column_config.NumberColumn(
                                   'season',
                                   format='%d'
                               )
                           })

# Utility to clear any previously generated report results
def _reset_report_results():
    for k in ['rg_hist_team1', 'rg_hist_team2', 'rg_team1', 'rg_team2', 'rg_report_data']:
        st.session_state.pop(k, None)

def generate_html_report(team1, team2, report_data):
    """Generate complete HTML report with all sections and interactive charts."""
    
    # Extract data from report_data dict
    summary_stats = report_data.get('summary_stats', {})
    h2h_betting = report_data.get('h2h_betting', {})
    defense_data = report_data.get('defense_data', {})
    top_performers = report_data.get('top_performers', {})
    redzone_targets = report_data.get('redzone_targets', {})
    pie_charts = report_data.get('pie_charts', {})
    historical_stats = report_data.get('historical_stats', {})
    
    # Get team colors
    team1_color = get_team_color(team1)
    team2_color = get_team_color(team2)
    
    # Start building HTML
    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{team1} vs {team2} Matchup Report</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f8f9fa;
            line-height: 1.6;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            text-align: center;
            color: #333;
            margin-bottom: 30px;
            font-size: 2.5rem;
        }}
        .subtitle {{
            text-align: center;
            color: #666;
            margin-bottom: 30px;
            font-style: italic;
        }}
        .section {{
            margin: 30px 0;
            padding: 20px;
            border: 1px solid #e6e6e6;
            border-radius: 8px;
            background-color: #fafafa;
        }}
        .stats-container {{
            margin: 30px 0;
            padding: 25px;
            background-color: white;
            border: 1px solid #e6e6e6;
            border-radius: 8px;
            border-left: 4px solid #007bff;
        }}
        .stats-list {{
            display: flex;
            flex-direction: column;
            gap: 0;
        }}
        .stat-item {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px 0;
            border-bottom: 1px solid #e9ecef;
        }}
        .stat-item:last-child {{
            border-bottom: none;
        }}
        .stat-label {{
            font-size: 1rem;
            color: #495057;
            font-weight: 500;
        }}
        .stat-value {{
            font-size: 1.3rem;
            font-weight: bold;
            color: #212529;
        }}
        .team1-stat {{ color: {team1_color}; }}
        .team2-stat {{ color: {team2_color}; }}
        .betting-box {{
            border: 1px solid #e6e6e6;
            border-radius: 10px;
            padding: 20px;
            background-color: white;
            margin: 20px 0;
        }}
        .betting-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-top: 15px;
        }}
        .betting-item {{
            text-align: center;
        }}
        .betting-value {{
            font-size: 1.8rem;
            font-weight: 800;
            margin: 5px 0;
        }}
        .defense-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin: 20px 0;
        }}
        .defense-box {{
            border: 1px solid #e6e6e6;
            background-color: rgba(0,0,0,0.02);
            border-radius: 8px;
            padding: 15px;
        }}
        .defense-title {{
            text-align: center;
            font-weight: 600;
            margin-bottom: 15px;
            font-size: 1.1rem;
        }}
        .defense-metrics {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 10px;
            margin-bottom: 10px;
        }}
        .defense-metric {{
            text-align: center;
        }}
        .defense-metric-value {{
            font-weight: 700;
            font-size: 1.1rem;
        }}
        .defense-yards {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
            margin-top: 10px;
        }}
        .performance-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin: 20px 0;
        }}
        .performance-title {{
            text-align: center;
            font-weight: bold;
            margin-bottom: 15px;
            font-size: 1.2rem;
        }}
        .chart-container {{
            margin: 20px 0;
            text-align: center;
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            align-items: start;
        }}
        .chart-item {{
            display: flex;
            flex-direction: column;
            align-items: center;
            width: 350px;
            margin: 0 auto;
        }}
        .player-section {{
            margin: 30px 0;
            padding: 20px;
            border: 1px solid #e6e6e6;
            border-radius: 8px;
            background-color: white;
        }}
        .player-header {{
            display: flex;
            align-items: center;
            margin-bottom: 20px;
            font-size: 2.2rem;
            font-weight: bold;
        }}
        .team-logo {{
            width: 60px;
            height: 60px;
            margin-right: 15px;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        .team-logo img {{
            width: 100%;
            height: 100%;
            object-fit: contain;
        }}
        .team-logo-fallback {{
            width: 60px;
            height: 60px;
            border: 1px solid #ccc;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 24px;
            font-weight: bold;
            margin-right: 15px;
            background-color: #f5f5f5;
        }}
        .player-summary {{
            margin-bottom: 20px;
        }}
        .player-detail {{
            margin: 30px 0;
            border: 1px solid #e6e6e6;
            border-radius: 6px;
            background-color: white;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        .player-name {{
            font-weight: bold;
            font-size: 1.1rem;
            padding: 12px 15px;
            margin: 0;
            color: #333;
            cursor: pointer;
            background-color: #f8f9fa;
            border-bottom: 1px solid #e6e6e6;
            border-radius: 4px 4px 0 0;
        }}
        .player-name:hover {{
            background-color: #e9ecef;
        }}
        .player-content {{
            padding: 15px;
            display: none;
            background-color: white;
            border-radius: 0 0 4px 4px;
        }}
        .player-detail input[type="checkbox"] {{
            display: none;
        }}
        .player-detail input[type="checkbox"]:checked ~ .player-content {{
            display: block;
        }}
        .player-metrics {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 12px;
            margin-bottom: 12px;
        }}
        .player-metric {{
            text-align: center;
            padding: 8px;
            background-color: #f8f9fa;
            border-radius: 4px;
            border: 1px solid #e6e6e6;
        }}
        .player-metric-value {{
            font-size: 1.3rem;
            font-weight: bold;
            color: #333;
        }}
        .player-metric-label {{
            font-size: 0.8rem;
            color: #666;
            margin-top: 3px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
            font-size: 0.9rem;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }}
        th {{
            background-color: #f2f2f2;
            font-weight: bold;
        }}
        tr:nth-child(even) {{
            background-color: #f9f9f9;
        }}
        .team1-color {{ color: {team1_color}; }}
        .team2-color {{ color: {team2_color}; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{team1} vs {team2} Matchup Report</h1>
        <div class="subtitle">{summary_stats.get('games_analyzed', 0)} most recent games analyzed</div>
"""
    
    # Add summary statistics
    html_content += f"""
        <div class="section">
            <h2>Head-to-Head Statistics</h2>
            <div class="stats-container">
                <div class="stats-list">
                    <div class="stat-item">
                        <span class="stat-label">{team1} Wins</span>
                        <span class="stat-value team1-stat">{summary_stats.get('team1_wins', 0)}</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">{team2} Wins</span>
                        <span class="stat-value team2-stat">{summary_stats.get('team2_wins', 0)}</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">Winning Streak ({summary_stats.get('winner_team', 'N/A')})</span>
                        <span class="stat-value">{summary_stats.get('winning_streak', 0)}</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">{team1} Avg PPG</span>
                        <span class="stat-value team1-stat">{summary_stats.get('team1_ppg', 0):.1f}</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">{team2} Avg PPG</span>
                        <span class="stat-value team2-stat">{summary_stats.get('team2_ppg', 0):.1f}</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">Average Total Points</span>
                        <span class="stat-value">{summary_stats.get('avg_total_points', 0):.1f}</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">Games with 50+ Points</span>
                        <span class="stat-value">{summary_stats.get('over_50_games', 0)}</span>
                    </div>
                </div>
            </div>
        </div>
"""
    
    # Add betting section
    if h2h_betting:
        ats_t1 = h2h_betting.get('team1_ats', (0,0,0))
        ats_t2 = h2h_betting.get('team2_ats', (0,0,0))
        ou = h2h_betting.get('ou', (0,0,0))
        fav_dog = h2h_betting.get('fav_dog', {})
        
        html_content += f"""
        <div class="section">
            <h2>Head-to-Head Betting</h2>
            <div class="betting-box">
                <div class="betting-grid">
                    <div class="betting-item">
                        <div>ATS: {team1}</div>
                        <div class="betting-value team1-color">{ats_t1[0]}-{ats_t1[1]}-{ats_t1[2]}</div>
                    </div>
                    <div class="betting-item">
                        <div>ATS: {team2}</div>
                        <div class="betting-value team2-color">{ats_t2[0]}-{ats_t2[1]}-{ats_t2[2]}</div>
                    </div>
                    <div class="betting-item">
                        <div>Totals (O-U-P)</div>
                        <div class="betting-value">{ou[0]}-{ou[1]}-{ou[2]}</div>
                    </div>
                    <div class="betting-item">
                        <div><strong>{team1}:</strong> Fav {fav_dog.get('team1_fav', 0)} - Dog {fav_dog.get('team1_dog', 0)}</div>
                        <div><strong>{team2}:</strong> Fav {fav_dog.get('team2_fav', 0)} - Dog {fav_dog.get('team2_dog', 0)}</div>
                    </div>
                </div>
            </div>
        </div>
"""
    
    # Add defense metrics
    if defense_data:
        t1_def = defense_data.get('team1', {})
        t2_def = defense_data.get('team2', {})
        
        html_content += f"""
        <div class="section">
            <h2>Defensive Metrics (Last 10 Games)</h2>
            <div class="defense-grid">
                <div class="defense-box">
                    <div class="defense-title">{team1} Defense</div>
                    <div class="defense-metrics">
                        <div class="defense-metric">
                            <div>Sacks/game</div>
                            <div class="defense-metric-value">{t1_def.get('avg_sacks_per_game', 0):.1f}</div>
                        </div>
                        <div class="defense-metric">
                            <div>QB Hits/game</div>
                            <div class="defense-metric-value">{t1_def.get('avg_qb_hits', 0):.1f}</div>
                        </div>
                        <div class="defense-metric">
                            <div>Turnovers/game</div>
                            <div class="defense-metric-value">{t1_def.get('avg_total_turnovers', 0):.1f}</div>
                        </div>
                    </div>
                    <div class="defense-yards">
                        <div class="defense-metric">
                            <div>Avg Pass Yds Allowed</div>
                            <div class="defense-metric-value">{t1_def.get('avg_pass_yards_allowed', 0):.1f}</div>
                        </div>
                        <div class="defense-metric">
                            <div>Avg Rush Yds Allowed</div>
                            <div class="defense-metric-value">{t1_def.get('avg_rush_yards_allowed', 0):.1f}</div>
                        </div>
                    </div>
                </div>
                <div class="defense-box">
                    <div class="defense-title">{team2} Defense</div>
                    <div class="defense-metrics">
                        <div class="defense-metric">
                            <div>Sacks/game</div>
                            <div class="defense-metric-value">{t2_def.get('avg_sacks_per_game', 0):.1f}</div>
                        </div>
                        <div class="defense-metric">
                            <div>QB Hits/game</div>
                            <div class="defense-metric-value">{t2_def.get('avg_qb_hits', 0):.1f}</div>
                        </div>
                        <div class="defense-metric">
                            <div>Turnovers/game</div>
                            <div class="defense-metric-value">{t2_def.get('avg_total_turnovers', 0):.1f}</div>
                        </div>
                    </div>
                    <div class="defense-yards">
                        <div class="defense-metric">
                            <div>Avg Pass Yds Allowed</div>
                            <div class="defense-metric-value">{t2_def.get('avg_pass_yards_allowed', 0):.1f}</div>
                        </div>
                        <div class="defense-metric">
                            <div>Avg Rush Yds Allowed</div>
                            <div class="defense-metric-value">{t2_def.get('avg_rush_yards_allowed', 0):.1f}</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
"""
    
    # Add top performers
    if top_performers:
        t1_top = top_performers.get('team1', pd.DataFrame())
        t2_top = top_performers.get('team2', pd.DataFrame())
        
        html_content += f"""
        <div class="section">
            <h2>Top Performance Metrics</h2>
            <div class="performance-grid">
                <div>
                    <div class="performance-title">{team1}</div>
"""
        if not t1_top.empty:
            html_content += t1_top.to_html(classes='table', table_id='team1_top', escape=False, index=False)
        else:
            html_content += "<p>No skill-position data available</p>"
        
        html_content += f"""
                </div>
                <div>
                    <div class="performance-title">{team2}</div>
"""
        if not t2_top.empty:
            html_content += t2_top.to_html(classes='table', table_id='team2_top', escape=False, index=False)
        else:
            html_content += "<p>No skill-position data available</p>"
        
        html_content += """
                </div>
            </div>
        </div>
"""

    # Add redzone targets
    if redzone_targets:
        rz_t1 = redzone_targets.get('team1', pd.DataFrame())
        rz_t2 = redzone_targets.get('team2', pd.DataFrame())

        html_content += f"""
        <div class="section">
            <h2>Red-Zone Targets (2025)</h2>
            <div class="performance-grid">
                <div>
                    <div class="performance-title">{team1}</div>
"""
        if not rz_t1.empty:
            html_content += rz_t1.to_html(classes='table', table_id='team1_redzone', escape=False, index=False)
        else:
            html_content += "<p>No red-zone data available</p>"

        html_content += f"""
                </div>
                <div>
                    <div class="performance-title">{team2}</div>
"""
        if not rz_t2.empty:
            html_content += rz_t2.to_html(classes='table', table_id='team2_redzone', escape=False, index=False)
        else:
            html_content += "<p>No red-zone data available</p>"

        html_content += """
                </div>
            </div>
        </div>
"""

    # Add pie charts
    if pie_charts:
        ats_chart = pie_charts.get('ats_chart')
        ou_chart = pie_charts.get('ou_chart')
        
        html_content += f"""
        <div class="section">
            <h2>Betting Distribution Charts</h2>
            <div class="chart-container">
"""
        if ats_chart:
            # Update chart layout to be bigger
            ats_chart.update_layout(
                width=350,
                height=350,
                margin=dict(l=30, r=30, t=50, b=30),
                showlegend=True,
                legend=dict(x=1.05, y=0.5)
            )
            html_content += f"""
                <div class="chart-item">
                    {ats_chart.to_html(include_plotlyjs=False, div_id='ats_chart', config={'displayModeBar': False, 'responsive': False})}
                </div>
"""
        if ou_chart:
            # Update chart layout to be bigger
            ou_chart.update_layout(
                width=350,
                height=350,
                margin=dict(l=30, r=30, t=50, b=30),
                showlegend=True,
                legend=dict(x=1.05, y=0.5)
            )
            html_content += f"""
                <div class="chart-item">
                    {ou_chart.to_html(include_plotlyjs=False, div_id='ou_chart', config={'displayModeBar': False, 'responsive': False})}
                </div>
"""
        
        html_content += """
            </div>
        </div>
"""
    
    # Add player sections
    if historical_stats:
        t1_stats = historical_stats.get('team1', pd.DataFrame())
        t2_stats = historical_stats.get('team2', pd.DataFrame())
        
        # Team 1 players
        if not t1_stats.empty:
            team1_logo_html = _get_team_logo_html(team1)
            html_content += f"""
        <div class="player-section">
            <div class="player-header">
                {team1_logo_html}
                <div>{team1} Players</div>
            </div>
"""
            # Process team 1 players
            html_content += _generate_player_html(t1_stats, team1, team2)
            html_content += """
        </div>
"""
        
        # Team 2 players
        if not t2_stats.empty:
            team2_logo_html = _get_team_logo_html(team2)
            html_content += f"""
        <div class="player-section">
            <div class="player-header">
                {team2_logo_html}
                <div>{team2} Players</div>
            </div>
"""
            # Process team 2 players
            html_content += _generate_player_html(t2_stats, team2, team1)
            html_content += """
        </div>
"""
    
    # Close HTML
    html_content += """
    </div>
</body>
</html>
"""
    
    return html_content

def _get_team_logo_html(team_abbrev):
    """Return an <img> tag with a base64-embedded team logo so the HTML is self-contained.

    Falls back to a styled abbreviation box when the logo file isn't available.
    """
    fname = f"{team_abbrev}.png"
    # Resolve potential locations
    script_relative_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), '..', 'images', 'team-logos', fname)
    )
    repo_relative_path = os.path.join('images', 'team-logos', fname)

    logo_path = None
    if os.path.exists(script_relative_path):
        logo_path = script_relative_path
    elif os.path.exists(repo_relative_path):
        # When running in repo root the relative path may work; but for download we embed anyway
        logo_path = repo_relative_path

    if logo_path and os.path.exists(logo_path):
        try:
            with open(logo_path, 'rb') as f:
                encoded = base64.b64encode(f.read()).decode('ascii')
            data_uri = f"data:image/png;base64,{encoded}"
            return f'<div class="team-logo"><img src="{data_uri}" alt="{team_abbrev}" /></div>'
        except Exception:
            # If anything goes wrong, use fallback
            return f'<div class="team-logo-fallback">{team_abbrev}</div>'
    else:
        return f'<div class="team-logo-fallback">{team_abbrev}</div>'

def _generate_player_html(historical_df, team_name, opponent_name):
    """Generate HTML for player section with expanded details."""
    if historical_df.empty:
        return f"<p>No historical stats found for {team_name} players vs {opponent_name}.</p>"
    
    # Use the same logic as show_condensed_players but generate HTML instead
    base = historical_df.groupby('player_name_with_position').agg({
        'game_id': 'nunique',
        'fantasy_points_ppr': 'mean'
    }).rename(columns={'game_id':'games','fantasy_points_ppr':'avg_fpts'}).reset_index()
    
    # Add receiving/passing/rushing means if available
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
    
    # Fix: Coerce TD columns to numeric BEFORE groupby sum
    for tdcol in ['passing_tds', 'rushing_tds', 'receiving_tds']:
        if tdcol in historical_df.columns:
            historical_df[tdcol] = pd.to_numeric(historical_df[tdcol], errors='coerce').fillna(0)
    
    # add total TDs metrics
    if 'passing_tds' in historical_df.columns:
        pass_tds = historical_df.groupby('player_name_with_position')['passing_tds'].sum().reset_index().rename(columns={'passing_tds':'total_pass_tds'})
        base = base.merge(pass_tds, on='player_name_with_position', how='left')
    else:
        base['total_pass_tds'] = 0
    if 'receiving_tds' in historical_df.columns:
        rec_tds = historical_df.groupby('player_name_with_position')['receiving_tds'].sum().reset_index().rename(columns={'receiving_tds':'total_rec_tds'})
        base = base.merge(rec_tds, on='player_name_with_position', how='left')
    else:
        base['total_rec_tds'] = 0
    if 'rushing_tds' in historical_df.columns:
        rush_tds = historical_df.groupby('player_name_with_position')['rushing_tds'].sum().reset_index().rename(columns={'rushing_tds':'total_rush_tds'})
        base = base.merge(rush_tds, on='player_name_with_position', how='left')
    else:
        base['total_rush_tds'] = 0

    # Fill NaN values with 0 for TD columns
    base['total_pass_tds'] = base['total_pass_tds'].fillna(0)
    base['total_rec_tds'] = base['total_rec_tds'].fillna(0)
    base['total_rush_tds'] = base['total_rush_tds'].fillna(0)
    
    # determine player position (most common) per player
    pos_map = historical_df.groupby('player_name_with_position')['position'].agg(lambda s: s.mode().iloc[0] if not s.mode().empty else s.iloc[0]).reset_index().rename(columns={'position':'pos'})
    base = base.merge(pos_map, on='player_name_with_position', how='left')
    
    # round numeric values for display
    for c in ['avg_rec_yds','avg_pass_yds','avg_rush_yds','avg_fpts']:
        base[c] = base[c].fillna(0).round(1)

    # Choose primary metric per-player based on position
    def pick_primary(row):
        if row['pos'] == 'QB':
            return row['avg_pass_yds'], 'Avg Pass Yds'
        elif row['pos'] in ('RB', 'FB'):
            return row['avg_rush_yds'], 'Avg Rush Yds'
        else:
            return row['avg_rec_yds'], 'Avg Rec Yds'
    
    # Choose primary TD metric per-player based on position
    def pick_primary_tds(row):
        if row['pos'] == 'QB':
            return int(row['total_pass_tds']), 'Total Pass TDs'
        elif row['pos'] in ('RB', 'FB'):
            return int(row['total_rush_tds']), 'Total Rush TDs'
        else:
            return int(row['total_rec_tds']), 'Total Rec TDs'

    prim_vals = base.apply(lambda r: pick_primary(r), axis=1)
    base['primary_val'] = [v for v,_ in prim_vals]
    base['primary_label'] = [lbl for _,lbl in prim_vals]
    
    prim_tds = base.apply(lambda r: pick_primary_tds(r), axis=1)
    base['primary_tds'] = [v for v,_ in prim_tds]
    base['primary_tds_label'] = [lbl for _,lbl in prim_tds]

    # include position and sort by position priority (QB, RB, WR, TE), then by games and primary metric
    display_df = base[['player_name_with_position','pos','games','primary_tds','primary_val','avg_fpts','primary_label','primary_tds_label']].copy()
    pos_priority = {'QB': 0, 'WR': 1, 'TE': 2, 'RB': 3}
    display_df['pos_order'] = display_df['pos'].map(lambda p: pos_priority.get(p, 4))
    display_df = display_df.sort_values(['pos_order','games','primary_val'], ascending=[True, False, False]).reset_index(drop=True)
    display_df = display_df[['player_name_with_position','games','primary_tds','primary_val','avg_fpts','primary_label','primary_tds_label','pos','pos_order']]
    display_df.columns = ['Player','Games','Primary TDs','Primary','Avg FPTS','Primary Label','Primary TDs Label','Pos','Pos Order']

    # Generate summary table HTML
    summary_html = display_df[['Player','Pos','Games','Avg FPTS']].to_html(classes='table', escape=False, index=False)
    
    html_content = f"""
            <div class="player-summary">
                {summary_html}
            </div>
"""
    
    # Generate individual player details
    for _, row in display_df.iterrows():
        pname = row['Player']
        ppos = row['Pos'] if 'Pos' in row else None
        
        # Get player games
        player_games = historical_df[historical_df['player_name_with_position'] == pname].sort_values('date', ascending=False).copy()
        
        # Generate metrics HTML
        if ppos in ('RB', 'FB'):
            this_games = historical_df[historical_df['player_name_with_position'] == pname]
            rush_tds_sum = int(this_games['rushing_tds'].sum()) if 'rushing_tds' in this_games.columns else 0
            rec_tds_sum = int(this_games['receiving_tds'].sum()) if 'receiving_tds' in this_games.columns else 0
            
            metrics_html = f"""
                <div class="player-metrics">
                    <div class="player-metric">
                        <div class="player-metric-value">{int(row['Games'])}</div>
                        <div class="player-metric-label">Games</div>
                    </div>
                    <div class="player-metric">
                        <div class="player-metric-value">{rush_tds_sum}</div>
                        <div class="player-metric-label">Total Rush TDs</div>
                    </div>
                    <div class="player-metric">
                        <div class="player-metric-value">{rec_tds_sum}</div>
                        <div class="player-metric-label">Total Rec TDs</div>
                    </div>
                    <div class="player-metric">
                        <div class="player-metric-value">{row['Avg FPTS']}</div>
                        <div class="player-metric-label">Avg FPTS</div>
                    </div>
                </div>
"""
        else:
            metrics_html = f"""
                <div class="player-metrics">
                    <div class="player-metric">
                        <div class="player-metric-value">{int(row['Games'])}</div>
                        <div class="player-metric-label">Games</div>
                    </div>
                    <div class="player-metric">
                        <div class="player-metric-value">{int(row['Primary TDs'])}</div>
                        <div class="player-metric-label">{row['Primary TDs Label']}</div>
                    </div>
                    <div class="player-metric">
                        <div class="player-metric-value">{row['Primary']}</div>
                        <div class="player-metric-label">{row['Primary Label']}</div>
                    </div>
                    <div class="player-metric">
                        <div class="player-metric-value">{row['Avg FPTS']}</div>
                        <div class="player-metric-label">Avg FPTS</div>
                    </div>
                </div>
"""
        
        # Generate game-by-game table
        id_cols = ['season','week','home_team','away_team']
        if isinstance(ppos, str) and ppos.upper() == 'QB':
            qb_cols = ['completions','attempts','passing_yards','passing_tds','interceptions','sacks',
                       'carries','rushing_yards','rushing_tds']
            metric_cols = id_cols + qb_cols
        else:
            pos_upper = (ppos or '').upper() if isinstance(ppos, str) else ''
            if pos_upper == 'WR':
                sk_cols = ['receiving_yards', 'receiving_tds', 'targets', 'receptions']
            elif pos_upper in ('RB','FB'):
                sk_cols = ['rushing_yards','rushing_tds', 'carries',
                           'receiving_yards','receiving_tds', 'receptions','targets']
            else:
                sk_cols = ['receiving_yards', 'receiving_tds', 'targets', 'receptions']
            metric_cols = id_cols + sk_cols
        
        available_cols = [c for c in metric_cols if c in player_games.columns]
        display_games = player_games[available_cols].copy()
        if 'season' in display_games.columns:
            display_games['season'] = display_games['season'].astype(int)
        
        games_table_html = display_games.to_html(classes='table', escape=False, index=False)
        
        html_content += f"""
            <div class="player-detail">
                <input type="checkbox" id="player_{hash(pname)}">
                <label for="player_{hash(pname)}" class="player-name">{pname}</label>
                <div class="player-content">
                    {metrics_html}
                    {games_table_html}
                </div>
            </div>
"""
    
    return html_content

# --------------- Betting/handicapping helpers ---------------

def _parse_games_datetime(df: pd.DataFrame) -> pd.DataFrame:
    if 'date' in df.columns:
        df = df.copy()
        df.loc[:, 'date'] = pd.to_datetime(df['date'], errors='coerce')
    return df

def _get_team_points(row: pd.Series, team_abbrev: str) -> tuple[float, float, float]:
    if row['home_team'] == team_abbrev:
        return row.get('home_score'), row.get('away_score'), row.get('home_spread', np.nan)
    else:
        return row.get('away_score'), row.get('home_score'), row.get('away_spread', np.nan)

def compute_head_to_head_bets(df_games: pd.DataFrame, team1: str, team2: str, limit: int = 10) -> dict:
    df_games = _parse_games_datetime(df_games)
    mask_matchup = ((df_games['home_team'] == team1) & (df_games['away_team'] == team2)) | \
                   ((df_games['home_team'] == team2) & (df_games['away_team'] == team1))
    games = df_games.loc[mask_matchup].dropna(subset=['home_score','away_score']).sort_values('date', ascending=False).head(limit)
    if games.empty:
        return {
            'games': games,
            'team1_ats': (0,0,0), 'team2_ats': (0,0,0), 'ou': (0,0,0),
            'team1_avg_cover_margin': 0.0, 'team2_avg_cover_margin': 0.0,
            'fav_dog': {'team1_fav': 0, 'team1_dog': 0, 'team2_fav': 0, 'team2_dog': 0}
        }

    # ATS tallies using team_covered where available, else compute via margin
    team1_covers = int((games.get('team_covered') == team1).sum()) if 'team_covered' in games.columns else 0
    team2_covers = int((games.get('team_covered') == team2).sum()) if 'team_covered' in games.columns else 0
    pushes = int((games.get('team_covered') == 'Push').sum()) if 'team_covered' in games.columns else 0

    # Compute cover margins and O/U
    t1_margins, t2_margins = [], []
    overs = unders = ou_pushes = 0
    t1_fav = t1_dog = t2_fav = t2_dog = 0
    for _, row in games.iterrows():
        # Over/Under
        line_total = row['total_line'] if 'total_line' in row.index else np.nan
        if pd.notna(line_total):
            game_total = float(row['home_score']) + float(row['away_score'])
            if game_total > line_total: overs += 1
            elif game_total < line_total: unders += 1
            else: ou_pushes += 1

        # Favorite/dog counts
        fav = row['team_favorite'] if 'team_favorite' in row.index else None
        if isinstance(fav, str):
            if fav == team1: t1_fav += 1
            elif fav == team2: t2_fav += 1
            elif fav.lower() in ('pick','pk','pickem','pck'): pass
        if isinstance(fav, str):
            if fav == team1: t2_dog += 1
            elif fav == team2: t1_dog += 1

        # Cover margins
        t1_pts, t2_pts, t1_spread = _get_team_points(row, team1)
        _, _, t2_spread = _get_team_points(row, team2)
        if pd.notna(t1_pts) and pd.notna(t1_spread):
            t1_margins.append(float(t1_pts) - float(t2_pts) + float(t1_spread))
        if pd.notna(t2_pts) and pd.notna(t2_spread):
            t2_margins.append(float(t2_pts) - float(t1_pts) + float(t2_spread))

    # If team_covered not present, infer ATS from margins
    if 'team_covered' not in games.columns:
        team1_covers = sum(1 for m in t1_margins if m > 0)
        team2_covers = sum(1 for m in t2_margins if m > 0)
        pushes = sum(1 for m in t1_margins if m == 0)

    return {
        'games': games,
        'team1_ats': (team1_covers, team2_covers, pushes),
        'team2_ats': (team2_covers, team1_covers, pushes),
        'ou': (overs, unders, ou_pushes),
        'team1_avg_cover_margin': float(np.nanmean(t1_margins)) if len(t1_margins) else 0.0,
        'team2_avg_cover_margin': float(np.nanmean(t2_margins)) if len(t2_margins) else 0.0,
        'fav_dog': {'team1_fav': t1_fav, 'team1_dog': t1_dog, 'team2_fav': t2_fav, 'team2_dog': t2_dog}
    }

def compute_recent_form(df_games: pd.DataFrame, team: str, n: int = 8) -> dict:
    df_games = _parse_games_datetime(df_games)
    mask_team = (df_games['home_team'] == team) | (df_games['away_team'] == team)
    games = df_games.loc[mask_team].dropna(subset=['home_score','away_score']).sort_values('date', ascending=False).head(n)
    if games.empty:
        return {'su': (0,0), 'ats': (0,0,0), 'ou': (0,0,0), 'avg_mov': 0.0, 'avg_ats_margin': 0.0}
    su_wins = su_losses = ats_w = ats_l = ats_p = over = under = ou_p = 0
    movs, ats_margins = [], []
    for _, row in games.iterrows():
        t_pts, o_pts, spr = _get_team_points(row, team)
        if pd.isna(t_pts) or pd.isna(o_pts):
            continue
        # SU
        if t_pts > o_pts: su_wins += 1
        elif t_pts < o_pts: su_losses += 1
        # ATS
        if pd.notna(spr):
            margin = (float(t_pts) - float(o_pts) + float(spr))
            ats_margins.append(margin)
            if margin > 0: ats_w += 1
            elif margin < 0: ats_l += 1
            else: ats_p += 1
        # O/U
        if 'total_line' in row.index and pd.notna(row['total_line']):
            total_pts = float(row['home_score']) + float(row['away_score'])
            if total_pts > row['total_line']: over += 1
            elif total_pts < row['total_line']: under += 1
            else: ou_p += 1
        movs.append(float(t_pts) - float(o_pts))
    return {
        'su': (su_wins, su_losses),
        'ats': (ats_w, ats_l, ats_p),
        'ou': (over, under, ou_p),
        'avg_mov': float(np.nanmean(movs)) if len(movs) else 0.0,
        'avg_ats_margin': float(np.nanmean(ats_margins)) if len(ats_margins) else 0.0
    }

# Clear any stale report results on page load so returning to this page doesn't show previous player tables
_reset_report_results()

# Selection controls (full-width, responsive)
# Team selection using selectbox with unique teams
unique_teams = sorted(df_games['home_team'].unique())
left_team_col, right_team_col = st.columns(2, gap="large")
with left_team_col:
    team1 = st.selectbox('Select Team 1:', options=unique_teams, index=unique_teams.index('BUF'), key='team1_select', on_change=_reset_report_results)
with right_team_col:
    team2 = st.selectbox('Select Team 2:', options=unique_teams, index=unique_teams.index('MIA'), key='team2_select', on_change=_reset_report_results)

# Center the generate button without fixed ratios
generate_clicked = False
btn_c1, btn_c2, btn_c3 = st.columns([1, 1, 1])
with btn_c2:
    generate_clicked = st.button('Generate Report', use_container_width=True)

# Auto-generate only for the default matchup when selections are BUF vs MIA
if team1 == 'BUF' and team2 == 'MIA':
    generate_clicked = True

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

            # Average points per game across these head-to-head matchups
            num_h2h_games = len(last_10_games)
            team1_ppg = float(team1_scores) / num_h2h_games if num_h2h_games > 0 else 0.0
            team2_ppg = float(team2_scores) / num_h2h_games if num_h2h_games > 0 else 0.0

            over_50_points_games = int((total_points > 50).sum())

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


            st.markdown(f"<div style='text-align: center;'><small><i>{len(last_10_games)} most recent games analyzed</i></small></div>", unsafe_allow_html=True)
            st.divider()
            # st.write("")
            # st.write("")
            
            stats_md2 = f'''
<div style="text-align:center; font-size: 1.05rem; line-height: 1.65;">
<b>{team1} Wins:</b> {team1_wins}<br>
<b>{team2} Wins:</b> {team2_wins}<br>
<b>Winning Streak:</b> {winner_team} has won {streak} games in a row<br>
<b>{team1} Avg PPG:</b> {team1_ppg:.1f}<br>
<b>{team2} Avg PPG:</b> {team2_ppg:.1f}<br>
<b>Average Total Points:</b> {average_total_points:.1f}<br>
<b>Games with more than 50 total points:</b> {over_50_points_games}<br>
</div>
'''
            st.markdown(stats_md2, unsafe_allow_html=True)

            # -------------------- Head-to-Head ATS & Totals --------------------
            st.write("")
            h2h = compute_head_to_head_bets(df_games, team1, team2, limit=10)
            ats_t1_w, ats_t1_l, ats_push = h2h['team1_ats']
            ats_t2_w, ats_t2_l, ats_t2_p = h2h['team2_ats']
            ou_over, ou_under, ou_push = h2h['ou']
            fav = h2h['fav_dog']
            box_style_bets = "border:1px solid #e6e6e6; border-radius:10px; padding:12px 14px;"
            html_bets = f"""
            <div style='{box_style_bets}'>
              <div style='text-align:center; font-weight:600; margin-bottom:12px;'>Head-to-Head Betting</div>
              <div style='display:flex; gap:10px; justify-content:space-between;'>
                <div style='flex:1; text-align:center;'>
                  <div style='font-size:1.05rem;'>ATS: {team1}</div>
                  <div style='font-weight:800; font-size:1.35rem;'>{ats_t1_w}-{ats_t1_l}-{ats_push}</div>
                </div>
                <div style='flex:1; text-align:center;'>
                  <div style='font-size:1.05rem;'>ATS: {team2}</div>
                  <div style='font-weight:800; font-size:1.35rem;'>{ats_t2_w}-{ats_t2_l}-{ats_t2_p}</div>
                </div>
                <div style='flex:1; text-align:center;'>
                  <div style='font-size:1.05rem;'>Totals (O-U-P)</div>
                  <div style='font-weight:800; font-size:1.35rem;'>{ou_over}-{ou_under}-{ou_push}</div>
                </div>
                <div style='flex:1; text-align:left;'>
                  <div style='font-size:1.05rem;'><b>{team1}:</b> <b>Fav {fav['team1_fav']}</b> - <b>Dog {fav['team1_dog']}</b></div>
                  <div style='font-size:1.05rem;'><b>{team2}:</b> <b>Fav {fav['team2_fav']}</b> - <b>Dog {fav['team2_dog']}</b></div>
                </div>
              </div>
            </div>
            """
            st.markdown(html_bets, unsafe_allow_html=True)
            st.write("")

            # Build per-game outcomes for interactive view
            games = h2h['games'].copy()
            if not games.empty:
                cols_needed = ['date','home_team','away_team','home_score','away_score','home_spread','away_spread','total_line','team_favorite']
                for c in cols_needed:
                    if c not in games.columns:
                        games[c] = np.nan
                games['date'] = pd.to_datetime(games['date'], errors='coerce')
                games = games.sort_values('date', ascending=False)

                def game_row_outcomes(row):
                    total_pts = float(row['home_score']) + float(row['away_score']) if pd.notna(row['home_score']) and pd.notna(row['away_score']) else np.nan
                    ou_result = 'Over' if pd.notna(row['total_line']) and total_pts > float(row['total_line']) else ('Under' if pd.notna(row['total_line']) and total_pts < float(row['total_line']) else 'Push')
                    # ATS for each team perspective
                    # team1
                    t1_pts, t2_pts, t1_spread = _get_team_points(row, team1)
                    t2_pts_b, t1_pts_b, t2_spread = _get_team_points(row, team2)
                    def ats_result(pts, opp_pts, spread):
                        if pd.isna(pts) or pd.isna(opp_pts) or pd.isna(spread):
                            return 'N/A'
                        margin = float(pts) - float(opp_pts) + float(spread)
                        if margin > 0: return 'Cover'
                        if margin < 0: return 'No Cover'
                        return 'Push'
                    t1_ats = ats_result(t1_pts, t2_pts, t1_spread)
                    t2_ats = ats_result(t2_pts_b, t1_pts_b, t2_spread)
                    return pd.Series({
                        'Total Pts': total_pts,
                        'O/U Result': ou_result,
                        f'{team1} Spread': t1_spread,
                        f'{team1} ATS': t1_ats,
                        f'{team2} Spread': t2_spread,
                        f'{team2} ATS': t2_ats,
                    })

                outcomes = games.apply(game_row_outcomes, axis=1)
                # Prefer game_id if present; otherwise build a readable id from date and teams
                if 'game_id' in games.columns:
                    games['game_id_display'] = games['game_id'].astype(str)
                else:
                    def _mk_id(r):
                        d = pd.to_datetime(r.get('date'), errors='coerce')
                        dstr = d.strftime('%Y-%m-%d') if pd.notna(d) else ''
                        return f"{dstr} {r.get('away_team','')} @ {r.get('home_team','')}"
                    games['game_id_display'] = games.apply(_mk_id, axis=1)

                show_df = pd.concat([games[['game_id_display','home_team','away_team','home_score','away_score','total_line','team_favorite']], outcomes], axis=1)
                show_df.rename(columns={'total_line':'Total Line','team_favorite':'Favorite','game_id_display':'game_id'}, inplace=True)

                with st.expander("Per-game results", expanded=False):
                    df_display = show_df.copy()
                    cols = ['game_id','home_team','away_team','home_score','away_score','Favorite','Total Line','O/U Result', f'{team1} Spread', f'{team1} ATS', f'{team2} Spread', f'{team2} ATS']
                    st.dataframe(df_display[cols], use_container_width=True, hide_index=True)
                    # st.download_button(
                    #     label="Download games (CSV)",
                    #     data=df_display.to_csv(index=False),
                    #     file_name=f"{team1}_vs_{team2}_h2h_betting_games.csv",
                    #     mime='text/csv'
                    # )

            # ---------- Pie Charts ----------
            cpie1, cpie2 = st.columns(2)
            if (ats_t1_w + h2h['team2_ats'][0] + ats_push) > 0:
                pie_ats = px.pie(
                    values=[ats_t1_w, h2h['team2_ats'][0], ats_push],
                    names=[f"{team1} cover", f"{team2} cover", "Push"],
                    title="Head-to-Head ATS Distribution",
                    hole=0.45,
                    color_discrete_sequence=[get_team_color(team1), get_team_color(team2), PUSH_GRAY]
                )
                # Legend on the left for left chart
                pie_ats.update_layout(
                    showlegend=True,
                    title_x=0.39,  # Shift title left to center over donut hole
                    legend=dict(
                        orientation="v",
                        yanchor="middle",
                        y=0.5,
                        xanchor="right",
                        x=-0.1
                    )
                )
                cpie1.plotly_chart(pie_ats, use_container_width=True)
            if (ou_over + ou_under + ou_push) > 0:
                pie_ou = px.pie(
                    values=[ou_over, ou_under, ou_push],
                    names=["Over", "Under", "Push"],
                    title="Head-to-Head Totals (O/U)",
                    hole=0.45,
                    color_discrete_sequence=[NFL_BLUE, NFL_RED, PUSH_GRAY]
                )
                # Legend on the right for right chart
                pie_ou.update_layout(
                    showlegend=True,
                    title_x=0.19,  # Shift title left to center over donut hole
                    legend=dict(
                        orientation="v",
                        yanchor="middle",
                        y=0.5,
                        xanchor="left",
                        x=1.02
                    )
                )
                cpie2.plotly_chart(pie_ou, use_container_width=True)

            # Store defensive metrics for full-width display below
            t1_def_early = calculate_defense_summary(df_defense_logs, df_team_game_logs, team1, last_n_games=10, df_games_ctx=df_games)
            t2_def_early = calculate_defense_summary(df_defense_logs, df_team_game_logs, team2, last_n_games=10, df_games_ctx=df_games)

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
                # Include games where the opponent is team2 AND the player's in-game team was NOT team2.
                # This keeps valid history vs the opponent (including when on current team) while
                # excluding cases where the player was ON the opponent facing their current team.
                mask_names_t1 = df_playerstats['player_display_name'].isin(players_team1_names)
                mask_game_has_team2 = (df_playerstats['home_team'] == team2) | (df_playerstats['away_team'] == team2)
                if 'player_current_team' in df_playerstats.columns:
                    mask_player_not_team2 = (df_playerstats['player_current_team'] != team2)
                    historical_stats_team1 = df_playerstats[mask_names_t1 & mask_game_has_team2 & mask_player_not_team2]
                else:
                    # Fallback if player team column missing: keep all games vs team2
                    historical_stats_team1 = df_playerstats[mask_names_t1 & mask_game_has_team2]
            else:
                st.info(f"No 2025 roster players found for {team1} matching the roster criteria.")

            if players_team2_names.size > 0:
                mask_names_t2 = df_playerstats['player_display_name'].isin(players_team2_names)
                mask_game_has_team1 = (df_playerstats['home_team'] == team1) | (df_playerstats['away_team'] == team1)
                if 'player_current_team' in df_playerstats.columns:
                    mask_player_not_team1 = (df_playerstats['player_current_team'] != team1)
                    historical_stats_team2 = df_playerstats[mask_names_t2 & mask_game_has_team1 & mask_player_not_team1]
                else:
                    historical_stats_team2 = df_playerstats[mask_names_t2 & mask_game_has_team1]
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

            # Store performance metrics and redzone data for full-width display below
            t1_top = compute_top_skill_performers(historical_stats_team1, top_n=4)      
            t2_top = compute_top_skill_performers(historical_stats_team2, top_n=4)
            rz_t1 = get_redzone_targets(df_redzone, team1, year=2025)
            rz_t2 = get_redzone_targets(df_redzone, team2, year=2025)

            # Save results to session state for full-width render below
            st.session_state['rg_team1'] = team1
            st.session_state['rg_team2'] = team2
            st.session_state['rg_hist_team1'] = historical_stats_team1
            st.session_state['rg_hist_team2'] = historical_stats_team2
            
            # Store comprehensive report data for HTML download
            report_data = {
                'summary_stats': {
                    'games_analyzed': len(last_10_games),
                    'team1_wins': team1_wins,
                    'team2_wins': team2_wins,
                    'winning_streak': streak,
                    'winner_team': winner_team,
                    'team1_ppg': team1_ppg,
                    'team2_ppg': team2_ppg,
                    'avg_total_points': average_total_points,
                    'over_50_games': over_50_points_games
                },
                'h2h_betting': {
                    'team1_ats': h2h['team1_ats'],
                    'team2_ats': h2h['team2_ats'],
                    'ou': h2h['ou'],
                    'fav_dog': h2h['fav_dog']
                },
                'defense_data': {
                    'team1': t1_def_early,
                    'team2': t2_def_early
                },
                'top_performers': {
                    'team1': t1_top,
                    'team2': t2_top
                },
                'redzone_targets': {
                    'team1': rz_t1,
                    'team2': rz_t2
                },
                'pie_charts': {
                    'ats_chart': pie_ats if (ats_t1_w + h2h['team2_ats'][0] + ats_push) > 0 else None,
                    'ou_chart': pie_ou if (ou_over + ou_under + ou_push) > 0 else None
                },
                'historical_stats': {
                    'team1': historical_stats_team1,
                    'team2': historical_stats_team2
                }
            }
            st.session_state['rg_report_data'] = report_data

# Full-width sections (rendered outside the centered column)
if all(k in st.session_state for k in ['rg_team1', 'rg_team2']):
    team1 = st.session_state['rg_team1']
    team2 = st.session_state['rg_team2']
    
    # ---------- Defensive Metrics (Full Width) ----------
    if (isinstance(df_defense_logs, pd.DataFrame) and not df_defense_logs.empty) or (isinstance(df_team_game_logs, pd.DataFrame) and not df_team_game_logs.empty):
        st.write("")
        # st.divider()
        # Defensive metrics two-column layout (responsive)
        dcol1_early, dcol2_early = st.columns(2, gap="large")
        t1_def_early = calculate_defense_summary(df_defense_logs, df_team_game_logs, team1, last_n_games=10, df_games_ctx=df_games)
        t2_def_early = calculate_defense_summary(df_defense_logs, df_team_game_logs, team2, last_n_games=10, df_games_ctx=df_games)
        with dcol1_early:
            st.markdown(f"<div style='text-align:center; font-weight:600; margin-bottom:8px;'>{team1} Defense</div>", unsafe_allow_html=True)
            def _fmt_local(v):
                try:
                    return f"{float(v):.1f}"
                except Exception:
                    return str(v)
            r1_html = f"""
            <div style='display:flex; gap:12px; justify-content:space-between;'>
              <div style='flex:1; text-align:center;'>
                <div>Sacks/game</div>
                <div style='font-weight:700;'>{_fmt_local(t1_def_early.get('avg_sacks_per_game','N/A'))}</div>
              </div>
              <div style='flex:1; text-align:center;'>
                <div>QB Hits/game</div>
                <div style='font-weight:700;'>{_fmt_local(t1_def_early.get('avg_qb_hits','N/A'))}</div>
              </div>
              <div style='flex:1; text-align:center;'>
                <div>Turnovers/game</div>
                <div style='font-weight:700;'>{_fmt_local(t1_def_early.get('avg_total_turnovers','N/A'))}</div>
              </div>
            </div>
            """
            r2_html = f"""
            <div style='display:flex; gap:12px; justify-content:space-evenly; margin-top:6px;'>
              <div style='flex:1; text-align:center;'>
                <div>Avg Pass Yds Allowed</div>
                <div style='font-weight:700;'>{_fmt_local(t1_def_early.get('avg_pass_yards_allowed','N/A'))}</div>
              </div>
              <div style='flex:1; text-align:center;'>
                <div>Avg Rush Yds Allowed</div>
                <div style='font-weight:700;'>{_fmt_local(t1_def_early.get('avg_rush_yards_allowed','N/A'))}</div>
              </div>
            </div>
            """
            box_style_local = "border:1px solid #e6e6e6; background-color: rgba(0,0,0,0.02); border-radius:8px; padding:12px 14px;"
            html_box_local = f"""
            <div style='{box_style_local}'>
              {r1_html}
              {r2_html}
            </div>
            """
            st.markdown(html_box_local, unsafe_allow_html=True)
        with dcol2_early:
            st.markdown(f"<div style='text-align:center; font-weight:600; margin-bottom:8px;'>{team2} Defense</div>", unsafe_allow_html=True)
            def _fmt_local2(v):
                try:
                    return f"{float(v):.1f}"
                except Exception:
                    return str(v)
            r1b_html = f"""
            <div style='display:flex; gap:12px; justify-content:space-between;'>
              <div style='flex:1; text-align:center;'>
                <div>Sacks/game</div>
                <div style='font-weight:700;'>{_fmt_local2(t2_def_early.get('avg_sacks_per_game','N/A'))}</div>
              </div>
              <div style='flex:1; text-align:center;'>
                <div>QB Hits/game</div>
                <div style='font-weight:700;'>{_fmt_local2(t2_def_early.get('avg_qb_hits','N/A'))}</div>
              </div>
              <div style='flex:1; text-align:center;'>
                <div>Turnovers/game</div>
                <div style='font-weight:700;'>{_fmt_local2(t2_def_early.get('avg_total_turnovers','N/A'))}</div>
              </div>
            </div>
            """
            r2b_html = f"""
            <div style='display:flex; gap:12px; justify-content:space-evenly; margin-top:6px;'>
              <div style='flex:1; text-align:center;'>
                <div>Avg Pass Yds Allowed</div>
                <div style='font-weight:700;'>{_fmt_local2(t2_def_early.get('avg_pass_yards_allowed','N/A'))}</div>
              </div>
              <div style='flex:1; text-align:center;'>
                <div>Avg Rush Yds Allowed</div>
                <div style='font-weight:700;'>{_fmt_local2(t2_def_early.get('avg_rush_yards_allowed','N/A'))}</div>
              </div>
            </div>
            """
            box_style_local2 = "border:1px solid #e6e6e6; background-color: rgba(0,0,0,0.02); border-radius:8px; padding:12px 14px;"
            html_box_local2 = f"""
            <div style='{box_style_local2}'>
              {r1b_html}
              {r2b_html}
            </div>
            """
            st.markdown(html_box_local2, unsafe_allow_html=True)

    # ---------- Top Performance Metrics (Full Width) ----------
    st.write("")
    st.write("")
    # Top performance metrics (two equal columns)
    top_left, top_right = st.columns(2, gap="large")
    with top_left:
        st.markdown(f"<div style='text-align:center; font-weight:bold;'>Top Performance Metrics — {team1}</div>", unsafe_allow_html=True)
        st.write(" ")
        t1_top = compute_top_skill_performers(st.session_state.get('rg_hist_team1', pd.DataFrame()), top_n=4)      
        if not t1_top.empty:
            st.dataframe(t1_top, use_container_width=True, hide_index=True)
        else:
            st.write("No skill-position data available")
    with top_right:
        st.markdown(f"<div style='text-align:center; font-weight:bold;'>Top Performance Metrics — {team2}</div>", unsafe_allow_html=True)
        st.write(" ")
        t2_top = compute_top_skill_performers(st.session_state.get('rg_hist_team2', pd.DataFrame()), top_n=4)
        if not t2_top.empty:
            st.dataframe(t2_top, use_container_width=True, hide_index=True)
        else:
            st.write("No skill-position data available")

    # ---------- Red Zone Targets (Full Width) ----------
    st.write("")
    st.write("")
    # Red zone targets (two equal columns)
    rz_left, rz_right = st.columns(2, gap="large")
    with rz_left:
        st.markdown(f"<div style='text-align:center; font-weight:bold;'>Red Zone Targets (2025) — {team1}</div>", unsafe_allow_html=True)
        st.write(" ")
        rz_t1 = get_redzone_targets(df_redzone, team1, year=2025)
        if not rz_t1.empty:
            st.dataframe(rz_t1, use_container_width=True, hide_index=True)
        else:
            st.write("No red-zone data available")
    with rz_right:
        st.markdown(f"<div style='text-align:center; font-weight:bold;'>Red Zone Targets (2025) — {team2}</div>", unsafe_allow_html=True)
        st.write(" ")
        rz_t2 = get_redzone_targets(df_redzone, team2, year=2025)
        if not rz_t2.empty:
            st.dataframe(rz_t2, use_container_width=True, hide_index=True)
        else:
            st.write("No red-zone data available")

# Full-width Player sections (rendered outside the centered column)
if all(k in st.session_state for k in ['rg_hist_team1','rg_hist_team2','rg_team1','rg_team2']):
    st.divider()
    # Player sections (two equal columns)
    a, b = st.columns(2, gap="large")
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

# Add download button at the bottom
if all(k in st.session_state for k in ['rg_report_data', 'rg_team1', 'rg_team2']):
    st.write("")
    st.write("")
    # st.divider()
    
    # Center the download button
    dl_col1, dl_col2, dl_col3 = st.columns([1, 1, 1])
    with dl_col2:
        # Generate HTML report
        html_content = generate_html_report(
            st.session_state['rg_team1'], 
            st.session_state['rg_team2'], 
            st.session_state['rg_report_data']
        )
        
        # Create download button
        st.download_button(
            label="📄 Download Report",
            data=html_content,
            file_name=f"{st.session_state['rg_team1']}_vs_{st.session_state['rg_team2']}_matchup_report.html",
            mime="text/html",
            use_container_width=True,
            type='primary'
        )
