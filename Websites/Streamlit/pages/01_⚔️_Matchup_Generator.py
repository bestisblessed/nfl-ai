import streamlit as st
import pandas as pd
import os
import plotly.express as px
import numpy as np

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
    # Additional logs for defensive metrics
    try:
        df_team_game_logs = pd.read_csv(os.path.join(current_dir, '../data', 'all_team_game_logs.csv'))
    except Exception:
        df_team_game_logs = pd.DataFrame()
    try:
        df_defense_logs = pd.read_csv(os.path.join(current_dir, '../data', 'all_defense-game-logs.csv'))
    except Exception:
        df_defense_logs = pd.DataFrame()
    
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
    for k in ['rg_hist_team1', 'rg_hist_team2', 'rg_team1', 'rg_team2']:
        st.session_state.pop(k, None)

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

            stats_md = f'''
<div style="text-align:center; font-size: 1.05rem; line-height: 1.65; margin-top:8px;">
<small><i>{len(last_10_games)} most recent games analyzed</i></small><br><br>
<b>{team1} Wins:</b> {team1_wins}<br>
<b>{team2} Wins:</b> {team2_wins}<br>
<b>Winning Streak:</b> {winner_team} has won {streak} games in a row<br>
<b>{team1} Avg PPG:</b> {team1_ppg:.1f}<br>
<b>{team2} Avg PPG:</b> {team2_ppg:.1f}<br>
<b>Average Total Points:</b> {average_total_points:.1f}<br>
<b>Games with more than 50 total points:</b> {over_50_points_games}<br>
</div>
'''
            st.markdown(stats_md, unsafe_allow_html=True)
            # st.divider()

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

                # st.write("")
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

            # ---------- Defensive Metrics (now after H2H) ----------
            if (isinstance(df_defense_logs, pd.DataFrame) and not df_defense_logs.empty) or (isinstance(df_team_game_logs, pd.DataFrame) and not df_team_game_logs.empty):
                st.write("")
                dcol1_early, spacer_mid_def_early, dcol2_early = st.columns([1, 0.12, 1])
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
            

            # (Pie charts moved under Top Performance Metrics below)

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

            # ---------- NEW: Top Performer Metrics side-by-side under pies ----------
            st.write("")
            st.write("")
            # top_left, top_right = st.columns(2)
            top_left, spacer_mid_perf, top_right = st.columns([1, 0.12, 1])
            with top_left:
                st.markdown(f"<div style='text-align:center; font-weight:bold;'>Top Performance Metrics — {team1}</div>", unsafe_allow_html=True)
                st.write(" ")
                t1_top = compute_top_skill_performers(historical_stats_team1, top_n=4)      
                if not t1_top.empty:
                    st.dataframe(t1_top, use_container_width=True, hide_index=True)
                else:
                    st.write("No skill-position data available")
            with top_right:
                st.markdown(f"<div style='text-align:center; font-weight:bold;'>Top Performance Metrics — {team2}</div>", unsafe_allow_html=True)
                st.write(" ")
                t2_top = compute_top_skill_performers(historical_stats_team2, top_n=4)
                if not t2_top.empty:
                    st.dataframe(t2_top, use_container_width=True, hide_index=True)
                else:
                    st.write("No skill-position data available")

            # Now show the pie charts under the Top Performance Metrics
            cpie1, cpie2 = st.columns(2)
            if (ats_t1_w + h2h['team2_ats'][0] + ats_push) > 0:
                pie_ats = px.pie(
                    values=[ats_t1_w, h2h['team2_ats'][0], ats_push],
                    names=[f"{team1} cover", f"{team2} cover", "Push"],
                    title="Head-to-Head ATS Distribution",
                    hole=0.45,
                    color_discrete_sequence=[get_team_color(team1), get_team_color(team2), PUSH_GRAY]
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
                cpie2.plotly_chart(pie_ou, use_container_width=True)

            # (Defensive metrics moved above; no rendering here now)

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
