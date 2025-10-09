import streamlit as st
import pandas as pd
import os
import numpy as np
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
    # Load teams lookup (abbr -> full name) and SR game logs for recent form/splits
    try:
        df_teams_lookup = pd.read_csv(os.path.join(current_dir, '../data', 'Teams.csv'))
    except Exception:
        df_teams_lookup = pd.DataFrame(columns=['TeamID', 'Team'])

    # Sports Reference team logs (seasonal game logs by team)
    try:
        sr_2024 = pd.read_csv(os.path.join(current_dir, '../data', 'SR-game-logs', 'all_teams_game_logs_2024.csv'))
    except Exception:
        sr_2024 = pd.DataFrame()
    try:
        sr_2025 = pd.read_csv(os.path.join(current_dir, '../data', 'SR-game-logs', 'all_teams_game_logs_2025.csv'))
    except Exception:
        sr_2025 = pd.DataFrame()
    df_sr_logs = pd.concat([sr_2024, sr_2025], ignore_index=True)
    # Normalize common fields
    if not df_sr_logs.empty:
        # Ensure date column is datetime where present
        if 'date' in df_sr_logs.columns:
            df_sr_logs.loc[:, 'date'] = pd.to_datetime(df_sr_logs['date'], errors='coerce')
        # Coerce numeric columns we will use
        for col in ['pass_yds','rush_yds','plays','total_yds','ypp','third_down_conv','third_down_att','fourth_down_conv','fourth_down_att','pass_att','rush_att','pass_sk']:
            if col in df_sr_logs.columns:
                df_sr_logs.loc[:, col] = pd.to_numeric(df_sr_logs[col], errors='coerce')
    
    # Store in session state for future use
    st.session_state['df_games'] = df_games
    st.session_state['df_playerstats'] = df_playerstats
    st.session_state['df_roster2025'] = df_roster2025
    st.session_state['df_teams_lookup'] = df_teams_lookup
    st.session_state['df_sr_logs'] = df_sr_logs
else:
    df_games = st.session_state['df_games'] 
    df_playerstats = st.session_state['df_playerstats']
    df_roster2025 = st.session_state.get('df_roster2025')
    df_teams_lookup = st.session_state.get('df_teams_lookup', pd.DataFrame(columns=['TeamID','Team']))
    df_sr_logs = st.session_state.get('df_sr_logs', pd.DataFrame())
    if df_roster2025 is None:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        df_roster2025 = pd.read_csv(os.path.join(current_dir, '../data/rosters', 'roster_2025.csv'))
        st.session_state['df_roster2025'] = df_roster2025

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

# --------------- Betting/handicapping helpers ---------------
def _parse_games_datetime(df: pd.DataFrame) -> pd.DataFrame:
    if 'date' in df.columns:
        df = df.copy()
        df.loc[:, 'date'] = pd.to_datetime(df['date'], errors='coerce')
    return df

def _get_team_points(row: pd.Series, team_abbrev: str) -> tuple[float, float, float]:
    if row['home_team'] == team_abbrev:
        return row['home_score'], row['away_score'], row['home_spread'] if 'home_spread' in row.index else np.nan
    else:
        return row['away_score'], row['home_score'], row['away_spread'] if 'away_spread' in row.index else np.nan

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
        # puppy counts infer from favorite
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

def _abbr_to_full(df_teams_lookup: pd.DataFrame, abbr: str) -> str:
    if df_teams_lookup.empty:
        return abbr
    match = df_teams_lookup.loc[df_teams_lookup['TeamID'] == abbr, 'Team']
    return str(match.iloc[0]) if not match.empty else abbr

def compute_recent_off_def_splits(df_sr_logs: pd.DataFrame, df_teams_lookup: pd.DataFrame, team_abbr: str, n: int = 8) -> dict:
    if df_sr_logs is None or df_sr_logs.empty:
        return {
            'offense': {'pass_yds_pg': np.nan, 'rush_yds_pg': np.nan, 'plays_pg': np.nan, 'ypp': np.nan, 'third_pct': np.nan},
            'defense': {'pass_yds_all_pg': np.nan, 'rush_yds_all_pg': np.nan, 'plays_all_pg': np.nan, 'ypp_all': np.nan, 'third_pct_all': np.nan},
            'sacks': {'taken_pg': np.nan, 'made_pg': np.nan}
        }
    team_full = _abbr_to_full(df_teams_lookup, team_abbr)
    df = df_sr_logs.copy()
    # Clean
    if 'date' in df.columns:
        df = df.sort_values('date', ascending=False)
    # Normalize PFR opp codes (e.g., GNB->GB, NWE->NE)
    pfr_to_std = {
        'CRD':'ARI','ATL':'ATL','RAV':'BAL','BUF':'BUF','CAR':'CAR','CHI':'CHI','CIN':'CIN','CLE':'CLE',
        'DAL':'DAL','DEN':'DEN','DET':'DET','GNB':'GB','HTX':'HOU','CLT':'IND','JAX':'JAX','KAN':'KC',
        'SDG':'LAC','RAM':'LAR','RAI':'LVR','MIA':'MIA','MIN':'MIN','NWE':'NE','NOR':'NO','NYG':'NYG',
        'NYJ':'NYJ','PHI':'PHI','PIT':'PIT','SEA':'SEA','SFO':'SF','TAM':'TB','OTI':'TEN','WAS':'WAS'
    }
    if 'opp' in df.columns:
        df.loc[:, 'opp_std'] = df['opp'].astype(str).str.upper().map(pfr_to_std).fillna(df['opp'].astype(str).str.upper())
    # Offense: rows for team
    off = df[df.get('team_name') == team_full].head(n)
    # Defense allowed: rows where opponent equals this team
    if 'opp_std' in df.columns:
        d_all = df[df['opp_std'] == team_abbr].head(n)
    else:
        d_all = df[df.get('opp') == team_abbr].head(n)
    def pct(numer, denom):
        numer = float(numer) if pd.notna(numer) else 0.0
        denom = float(denom) if pd.notna(denom) and denom != 0 else np.nan
        return (numer / denom) if pd.notna(denom) else np.nan
    offense = {
        'pass_yds_pg': float(off['pass_yds'].mean()) if 'pass_yds' in off else np.nan,
        'rush_yds_pg': float(off['rush_yds'].mean()) if 'rush_yds' in off else np.nan,
        'plays_pg': float(off['plays'].mean()) if 'plays' in off else np.nan,
        'ypp': float(off['ypp'].mean()) if 'ypp' in off else np.nan,
        'third_pct': pct(off['third_down_conv'].sum(), off['third_down_att'].sum()) if {'third_down_conv','third_down_att'}.issubset(off.columns) else np.nan,
        'sacks_taken_pg': float(off['pass_sk'].mean()) if 'pass_sk' in off else np.nan
    }
    defense = {
        'pass_yds_all_pg': float(d_all['pass_yds'].mean()) if 'pass_yds' in d_all else np.nan,
        'rush_yds_all_pg': float(d_all['rush_yds'].mean()) if 'rush_yds' in d_all else np.nan,
        'plays_all_pg': float(d_all['plays'].mean()) if 'plays' in d_all else np.nan,
        'ypp_all': float(d_all['ypp'].mean()) if 'ypp' in d_all else np.nan,
        'third_pct_all': pct(d_all['third_down_conv'].sum(), d_all['third_down_att'].sum()) if {'third_down_conv','third_down_att'}.issubset(d_all.columns) else np.nan,
        'sacks_made_pg': float(d_all['pass_sk'].mean()) if 'pass_sk' in d_all else np.nan
    }
    return {'offense': offense, 'defense': defense, 'sacks': {'taken_pg': offense['sacks_taken_pg'], 'made_pg': defense['sacks_made_pg']}}

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

            stats_md = f'''
<div style="text-align:center; font-size: 1.05rem; line-height: 1.65; margin-top:8px;">
<small><i>{len(last_10_games)} most recent games analyzed</i></small><br><br>
<b>{team1} Wins:</b> {team1_wins}<br>
<b>{team2} Wins:</b> {team2_wins}<br>
<b>Winning Streak:</b> {winner_team} has won {streak} games in a row<br>
<b>Average Total Points:</b> {average_total_points:.1f}<br>
<b>Games with more than 50 total points:</b> {over_50_points_games}<br>
<b>Total points scored by {team1}:</b> {team1_scores}<br>
<b>Total points scored by {team2}:</b> {team2_scores}
</div>
'''
            st.markdown(stats_md, unsafe_allow_html=True)

            # -------------------- Head-to-Head ATS & Totals --------------------
            h2h = compute_head_to_head_bets(df_games, team1, team2, limit=10)
            ats_t1_w, ats_t1_l, ats_push = h2h['team1_ats']
            ou_over, ou_under, ou_push = h2h['ou']
            st.subheader("Head-to-Head Betting Results (last 10)")
            m1, m2, m3, m4 = st.columns(4)
            m1.metric(f"ATS: {team1}", f"{ats_t1_w}-{ats_t1_l}-{ats_push}", h2h['team1_avg_cover_margin'])
            m2.metric(f"ATS: {team2}", f"{h2h['team2_ats'][0]}-{h2h['team2_ats'][1]}-{h2h['team2_ats'][2]}", h2h['team2_avg_cover_margin'])
            m3.metric("Totals (O-U-P)", f"{ou_over}-{ou_under}-{ou_push}")
            fav = h2h['fav_dog']
            m4.metric("Fav/Dog counts", f"{team1} F:{fav['team1_fav']} D:{fav['team1_dog']} | {team2} F:{fav['team2_fav']} D:{fav['team2_dog']}")

            # Compact pies for ATS and O/U
            if (ats_t1_w + h2h['team2_ats'][0] + ats_push) > 0:
                pie_ats = px.pie(
                    values=[ats_t1_w, h2h['team2_ats'][0], ats_push],
                    names=[f"{team1} cover", f"{team2} cover", "Push"],
                    title="Head-to-Head ATS Distribution",
                    hole=0.45,
                    color_discrete_sequence=["#2ca02c", "#d62728", "#7f7f7f"]
                )
                st.plotly_chart(pie_ats, use_container_width=True)
            if (ou_over + ou_under + ou_push) > 0:
                pie_ou = px.pie(
                    values=[ou_over, ou_under, ou_push],
                    names=["Over", "Under", "Push"],
                    title="Head-to-Head Totals (O/U)",
                    hole=0.45,
                    color_discrete_sequence=["#1f77b4", "#ff7f0e", "#7f7f7f"]
                )
                st.plotly_chart(pie_ou, use_container_width=True)

            # -------------------- Recent Form (last 8 overall) --------------------
            st.subheader("Recent Form – last 8 games (overall)")
            form1 = compute_recent_form(df_games, team1, n=8)
            form2 = compute_recent_form(df_games, team2, n=8)
            c1, c2 = st.columns(2)
            with c1:
                st.markdown(f"**{team1}**")
                st.write({
                    'SU': f"{form1['su'][0]}-{form1['su'][1]}",
                    'ATS': f"{form1['ats'][0]}-{form1['ats'][1]}-{form1['ats'][2]}",
                    'O/U': f"{form1['ou'][0]}-{form1['ou'][1]}-{form1['ou'][2]}",
                    'Avg MOV': round(form1['avg_mov'], 1),
                    'Avg ATS Mgn': round(form1['avg_ats_margin'], 1)
                })
            with c2:
                st.markdown(f"**{team2}**")
                st.write({
                    'SU': f"{form2['su'][0]}-{form2['su'][1]}",
                    'ATS': f"{form2['ats'][0]}-{form2['ats'][1]}-{form2['ats'][2]}",
                    'O/U': f"{form2['ou'][0]}-{form2['ou'][1]}-{form2['ou'][2]}",
                    'Avg MOV': round(form2['avg_mov'], 1),
                    'Avg ATS Mgn': round(form2['avg_ats_margin'], 1)
                })

            # -------------------- Offense vs Defense Splits (SR logs) --------------------
            if isinstance(df_sr_logs, pd.DataFrame) and not df_sr_logs.empty:
                splits1 = compute_recent_off_def_splits(df_sr_logs, df_teams_lookup, team1, n=8)
                splits2 = compute_recent_off_def_splits(df_sr_logs, df_teams_lookup, team2, n=8)

                def _bars_for_team(team_lbl, s_off, s_def):
                    bars = pd.DataFrame({
                        'Metric': ['Pass Yds/g', 'Rush Yds/g', 'Yards/Play', 'Plays/g', '3rd Down %'],
                        team_lbl + ' Off': [
                            s_off['pass_yds_pg'], s_off['rush_yds_pg'], s_off['ypp'], s_off['plays_pg'],
                            None if pd.isna(s_off['third_pct']) else round(100*s_off['third_pct'], 1)
                        ],
                        team_lbl + ' Def Allow': [
                            s_def['pass_yds_all_pg'], s_def['rush_yds_all_pg'], s_def['ypp_all'], s_def['plays_all_pg'],
                            None if pd.isna(s_def['third_pct_all']) else round(100*s_def['third_pct_all'], 1)
                        ]
                    })
                    return bars

                st.subheader("Matchup Splits (last 8 – offense vs opponent defense)")
                left, right = st.columns(2)
                with left:
                    df_bars1 = _bars_for_team(team1, splits1['offense'], splits2['defense'])
                    fig1 = px.bar(df_bars1.melt(id_vars='Metric', var_name='Type', value_name='Value'), x='Metric', y='Value', color='Type', barmode='group', title=f"{team1} Offense vs {team2} Defense")
                    st.plotly_chart(fig1, use_container_width=True)
                    st.caption(f"Sacks – Taken/g: {round(splits1['sacks']['taken_pg'] or 0,1)} | {team2} Made/g: {round(splits2['sacks']['made_pg'] or 0,1)}")
                with right:
                    df_bars2 = _bars_for_team(team2, splits2['offense'], splits1['defense'])
                    fig2 = px.bar(df_bars2.melt(id_vars='Metric', var_name='Type', value_name='Value'), x='Metric', y='Value', color='Type', barmode='group', title=f"{team2} Offense vs {team1} Defense")
                    st.plotly_chart(fig2, use_container_width=True)
                    st.caption(f"Sacks – Taken/g: {round(splits2['sacks']['taken_pg'] or 0,1)} | {team1} Made/g: {round(splits1['sacks']['made_pg'] or 0,1)}")

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
