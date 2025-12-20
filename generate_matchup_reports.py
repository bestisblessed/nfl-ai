import pandas as pd
import numpy as np
import os
import base64
import argparse
import sys
import asyncio
from playwright.async_api import async_playwright
import plotly.express as px

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

def _get_team_logo_html(team_abbrev):
    """Return an <img> tag with a base64-embedded team logo."""
    fname = f"{team_abbrev}.png"
    # Resolve potential locations relative to workspace root
    logo_path = os.path.join('/workspace/Websites/Streamlit/images/team-logos', fname)

    if logo_path and os.path.exists(logo_path):
        try:
            with open(logo_path, 'rb') as f:
                encoded = base64.b64encode(f.read()).decode('ascii')
            data_uri = f"data:image/png;base64,{encoded}"
            return f'<div class="team-logo"><img src="{data_uri}" alt="{team_abbrev}" /></div>'
        except Exception:
            return f'<div class="team-logo-fallback">{team_abbrev}</div>'
    else:
        return f'<div class="team-logo-fallback">{team_abbrev}</div>'

def compute_top_skill_performers(historical_df: pd.DataFrame, top_n: int = 4) -> pd.DataFrame:
    if historical_df is None or historical_df.empty:
        return pd.DataFrame(columns=['Player','Pos','Total TDs','Rec Yds','Rush Yds','Rec TDs','Rush TDs'])

    df = historical_df.copy()
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
    if df_redzone is None or df_redzone.empty:
        return pd.DataFrame(columns=['Player', 'Targets', 'Receptions', 'Catch%', 'TDs'])

    subset = df_redzone[(df_redzone['StatType'] == 'receiving') &
                       (df_redzone['Year'] == year) &
                       (df_redzone['Tm'] == team)].copy()

    if subset.empty:
        return pd.DataFrame(columns=['Player', 'Targets', 'Receptions', 'Catch%', 'TDs'])

    subset = subset[['Player', 'Inside 20_Tgt', 'Inside 20_Rec', 'Inside 20_Ctch%', 'Inside 20_TD']]
    subset = subset.rename(columns={
        'Inside 20_Tgt': 'Targets',
        'Inside 20_Rec': 'Receptions',
        'Inside 20_Ctch%': 'Catch%',
        'Inside 20_TD': 'TDs'
    })

    for col in ['Targets', 'Receptions', 'TDs']:
        subset[col] = pd.to_numeric(subset[col], errors='coerce').fillna(0).astype(int)

    subset['Catch%'] = pd.to_numeric(subset['Catch%'], errors='coerce').fillna(0).round(1)
    subset = subset.sort_values(by=['Targets', 'Player'], ascending=[False, True]).reset_index(drop=True)
    return subset

def calculate_defense_summary(df_defense_logs: pd.DataFrame, df_team_game_logs: pd.DataFrame, team: str, last_n_games: int = 10, df_games_ctx: pd.DataFrame = None) -> dict:
    out = {
        'avg_sacks_per_game': 0.0,
        'avg_qb_hits': 0.0,
        'avg_total_turnovers': 0.0,
        'avg_pass_yards_allowed': 0.0,
        'avg_rush_yards_allowed': 0.0,
    }
    if isinstance(df_defense_logs, pd.DataFrame) and not df_defense_logs.empty and 'team' in df_defense_logs.columns:
        team_def = df_defense_logs[df_defense_logs['team'] == team].copy()
        if not team_def.empty:
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
    
    if isinstance(df_team_game_logs, pd.DataFrame) and not df_team_game_logs.empty:
        logs_all = df_team_game_logs.copy()
        if 'home_team' not in logs_all.columns or 'away_team' not in logs_all.columns:
            parts = logs_all['game_id'].astype(str).str.split('_')
            try:
                logs_all.loc[:, 'away_team'] = parts.str[2]
                logs_all.loc[:, 'home_team'] = parts.str[3]
            except: pass

        if isinstance(df_games_ctx, pd.DataFrame) and not df_games_ctx.empty and 'date' in df_games_ctx.columns:
            games = df_games_ctx[(df_games_ctx['home_team'] == team) | (df_games_ctx['away_team'] == team)].dropna(subset=['home_score','away_score']).copy()
            games.loc[:, 'date'] = pd.to_datetime(games['date'], format='%Y-%m-%d %H:%M:%S', errors='coerce')
            games = games.sort_values('date').tail(last_n_games)
            recent_ids = set(games['game_id'].astype(str))
            logs = logs_all[logs_all['game_id'].astype(str).isin(recent_ids)].copy()
        else:
            mask = (logs_all['home_team'] == team) | (logs_all['away_team'] == team)
            logs = logs_all.loc[mask].copy()
        
        if not logs.empty:
            if 'date' in logs.columns:
                logs.loc[:, 'date'] = pd.to_datetime(logs['date'], format='%Y-%m-%d %H:%M:%S', errors='coerce')
                logs = logs.sort_values('date')
            elif 'game_id' in logs.columns:
                logs = logs.sort_values('game_id')
            logs = logs.tail(last_n_games)

            for k in ['home_pass_yds','away_pass_yds','home_rush_yds','away_rush_yds']:
                if k not in logs.columns:
                    logs.loc[:, k] = 0
                logs.loc[:, k] = pd.to_numeric(logs[k], errors='coerce').fillna(0)

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

def _parse_games_datetime(df: pd.DataFrame) -> pd.DataFrame:
    if 'date' in df.columns:
        df = df.copy()
        df.loc[:, 'date'] = pd.to_datetime(df['date'], format='%Y-%m-%d %H:%M:%S', errors='coerce')
    return df

def _get_team_points(row: pd.Series, team_abbrev: str) -> tuple[float, float, float]:
    if row['home_team'] == team_abbrev:
        home_score = row.get('home_score', np.nan)
        away_score = row.get('away_score', np.nan)
        home_spread = row.get('home_spread', np.nan)
    else:
        away_score = row.get('away_score', np.nan)
        home_score = row.get('home_score', np.nan)
        home_spread = row.get('away_spread', np.nan)
    
    try: team_score = float(home_score) if pd.notna(home_score) else np.nan
    except: team_score = np.nan
    try: opp_score = float(away_score) if pd.notna(away_score) else np.nan
    except: opp_score = np.nan
    try: spread = float(home_spread) if pd.notna(home_spread) else np.nan
    except: spread = np.nan
    return team_score, opp_score, spread

def compute_head_to_head_bets(df_games: pd.DataFrame, team1: str, team2: str, limit: int = 10) -> dict:
    df_games = _parse_games_datetime(df_games)
    mask_matchup = ((df_games['home_team'] == team1) & (df_games['away_team'] == team2)) | \
                   ((df_games['home_team'] == team2) & (df_games['away_team'] == team1))
    games = df_games.loc[mask_matchup].dropna(subset=['home_score','away_score']).sort_values('date', ascending=False).head(limit)
    
    if games.empty:
        return {'games': games, 'team1_ats': (0,0,0), 'team2_ats': (0,0,0), 'ou': (0,0,0), 'fav_dog': {}}

    t1_margins, t2_margins = [], []
    overs = unders = ou_pushes = 0
    t1_fav = t1_dog = t2_fav = t2_dog = 0
    
    for _, row in games.iterrows():
        line_total = row.get('total_line', np.nan)
        if pd.notna(line_total):
            game_total = float(row['home_score']) + float(row['away_score'])
            if game_total > line_total: overs += 1
            elif game_total < line_total: unders += 1
            else: ou_pushes += 1

        fav = row.get('team_favorite')
        if isinstance(fav, str):
            if fav == team1: t1_fav += 1; t2_dog += 1
            elif fav == team2: t2_fav += 1; t1_dog += 1

        t1_pts, t2_pts, t1_spread = _get_team_points(row, team1)
        _, _, t2_spread = _get_team_points(row, team2)
        if pd.notna(t1_pts) and pd.notna(t1_spread):
            try: t1_margins.append(float(t1_pts) - float(t2_pts) + float(t1_spread))
            except: pass
        if pd.notna(t2_pts) and pd.notna(t2_spread):
            try: t2_margins.append(float(t2_pts) - float(t1_pts) + float(t2_spread))
            except: pass

    team1_covers = sum(1 for m in t1_margins if m > 0)
    team2_covers = sum(1 for m in t2_margins if m > 0)
    pushes = sum(1 for m in t1_margins if m == 0)

    return {
        'games': games,
        'team1_ats': (team1_covers, team2_covers, pushes),
        'team2_ats': (team2_covers, team1_covers, pushes),
        'ou': (overs, unders, ou_pushes),
        'fav_dog': {'team1_fav': t1_fav, 'team1_dog': t1_dog, 'team2_fav': t2_fav, 'team2_dog': t2_dog}
    }

def _generate_player_html(historical_df, team_name, opponent_name):
    if historical_df.empty:
        return f"<p>No historical stats found for {team_name} players vs {opponent_name}.</p>"
    
    base = historical_df.groupby('player_name_with_position').agg({'game_id': 'nunique'}).rename(columns={'game_id':'games'}).reset_index()
    
    for col, name in [('receiving_yards','avg_rec_yds'), ('passing_yards','avg_pass_yds'), ('rushing_yards','avg_rush_yds')]:
        if col in historical_df.columns:
            stat = historical_df.groupby('player_name_with_position')[col].mean().reset_index().rename(columns={col:name})
            base = base.merge(stat, on='player_name_with_position', how='left')
        else:
            base[name] = 0.0

    for tdcol in ['passing_tds', 'rushing_tds', 'receiving_tds']:
        if tdcol in historical_df.columns:
            historical_df[tdcol] = pd.to_numeric(historical_df[tdcol], errors='coerce').fillna(0)

    for col, name in [('passing_tds','total_pass_tds'), ('receiving_tds','total_rec_tds'), ('rushing_tds','total_rush_tds')]:
        if col in historical_df.columns:
            stat = historical_df.groupby('player_name_with_position')[col].sum().reset_index().rename(columns={col:name})
            base = base.merge(stat, on='player_name_with_position', how='left')
        else:
            base[name] = 0

    base = base.fillna(0)
    
    pos_map = historical_df.groupby('player_name_with_position')['position'].agg(lambda s: s.mode().iloc[0] if not s.mode().empty else s.iloc[0]).reset_index().rename(columns={'position':'pos'})
    base = base.merge(pos_map, on='player_name_with_position', how='left')

    for c in ['avg_rec_yds','avg_pass_yds','avg_rush_yds']:
        base[c] = base[c].fillna(0).round(1)

    def pick_primary(row):
        if row['pos'] == 'QB': return row['avg_pass_yds'], 'Avg Pass Yds'
        elif row['pos'] in ('RB', 'FB'): return row['avg_rush_yds'], 'Avg Rush Yds'
        else: return row['avg_rec_yds'], 'Avg Rec Yds'
    
    def pick_primary_tds(row):
        if row['pos'] == 'QB': return int(row['total_pass_tds']), 'Total Pass TDs'
        elif row['pos'] in ('RB', 'FB'): return int(row['total_rush_tds']), 'Total Rush TDs'
        else: return int(row['total_rec_tds']), 'Total Rec TDs'

    prim_vals = base.apply(lambda r: pick_primary(r), axis=1)
    base['primary_val'] = [v for v,_ in prim_vals]
    base['primary_label'] = [lbl for _,lbl in prim_vals]
    
    prim_tds = base.apply(lambda r: pick_primary_tds(r), axis=1)
    base['primary_tds'] = [v for v,_ in prim_tds]
    base['primary_tds_label'] = [lbl for _,lbl in prim_tds]

    display_df = base[['player_name_with_position','pos','games','primary_tds','primary_val','primary_label','primary_tds_label']].copy()
    pos_priority = {'QB': 0, 'WR': 1, 'TE': 2, 'RB': 3}
    display_df['pos_order'] = display_df['pos'].map(lambda p: pos_priority.get(p, 4))
    display_df = display_df.sort_values(['pos_order','games','primary_val'], ascending=[True, False, False]).reset_index(drop=True)
    display_df = display_df[['player_name_with_position','games','primary_tds','primary_val','primary_label','primary_tds_label','pos','pos_order']]
    display_df.columns = ['Player','Games','Primary TDs','Primary','Primary Label','Primary TDs Label','Pos','Pos Order']

    summary_html = display_df[['Player','Pos','Games']].to_html(classes='table', escape=False, index=False)
    html_content = f'<div class="player-summary">{summary_html}</div>'

    for _, row in display_df.iterrows():
        pname = row['Player']
        ppos = row['Pos'] if 'Pos' in row else None
        player_games = historical_df[historical_df['player_name_with_position'] == pname].sort_values('date', ascending=False).copy()
        
        metrics_html = ""
        if ppos in ('RB', 'FB'):
            this_games = historical_df[historical_df['player_name_with_position'] == pname]
            rush_tds_sum = int(this_games['rushing_tds'].sum()) if 'rushing_tds' in this_games.columns else 0
            rec_tds_sum = int(this_games['receiving_tds'].sum()) if 'receiving_tds' in this_games.columns else 0
            metrics_html = f"""<div class="player-metrics"><div class="player-metric"><div class="player-metric-value">{int(row['Games'])}</div><div class="player-metric-label">Games</div></div><div class="player-metric"><div class="player-metric-value">{rush_tds_sum}</div><div class="player-metric-label">Total Rush TDs</div></div><div class="player-metric"><div class="player-metric-value">{rec_tds_sum}</div><div class="player-metric-label">Total Rec TDs</div></div></div>"""
        elif isinstance(ppos, str) and ppos.upper() == 'QB':
            qb_games = historical_df[historical_df['player_name_with_position'] == pname]
            qb_rush_tds_sum = int(qb_games['rushing_tds'].sum()) if 'rushing_tds' in qb_games.columns else 0
            metrics_html = f"""<div class="player-metrics"><div class="player-metric"><div class="player-metric-value">{int(row['Games'])}</div><div class="player-metric-label">Games</div></div><div class="player-metric"><div class="player-metric-value">{int(row['Primary TDs'])}</div><div class="player-metric-label">Total Pass TDs</div></div><div class="player-metric"><div class="player-metric-value">{qb_rush_tds_sum}</div><div class="player-metric-label">Total Rush TDs</div></div><div class="player-metric"><div class="player-metric-value">{row['Primary']}</div><div class="player-metric-label">{row['Primary Label']}</div></div></div>"""
        else:
            metrics_html = f"""<div class="player-metrics"><div class="player-metric"><div class="player-metric-value">{int(row['Games'])}</div><div class="player-metric-label">Games</div></div><div class="player-metric"><div class="player-metric-value">{int(row['Primary TDs'])}</div><div class="player-metric-label">{row['Primary TDs Label']}</div></div><div class="player-metric"><div class="player-metric-value">{row['Primary']}</div><div class="player-metric-label">{row['Primary Label']}</div></div></div>"""

        id_cols = ['season','week','home_team','away_team']
        if isinstance(ppos, str) and ppos.upper() == 'QB':
            metric_cols = id_cols + ['completions','attempts','passing_yards','passing_tds','interceptions','sacks','carries','rushing_yards','rushing_tds']
        else:
            pos_upper = (ppos or '').upper() if isinstance(ppos, str) else ''
            if pos_upper == 'WR': metric_cols = id_cols + ['receiving_yards', 'receiving_tds', 'targets', 'receptions']
            elif pos_upper in ('RB','FB'): metric_cols = id_cols + ['rushing_yards','rushing_tds', 'carries','receiving_yards','receiving_tds', 'receptions','targets']
            else: metric_cols = id_cols + ['receiving_yards', 'receiving_tds', 'targets', 'receptions']
        
        available_cols = [c for c in metric_cols if c in player_games.columns]
        display_games = player_games[available_cols].copy()
        if 'season' in display_games.columns: display_games['season'] = display_games['season'].astype(int)
        games_table_html = display_games.to_html(classes='table', escape=False, index=False)
        
        html_content += f"""<div class="player-detail"><input type="checkbox" id="player_{hash(pname)}"><label for="player_{hash(pname)}" class="player-name">{pname}</label><div class="player-content">{metrics_html}{games_table_html}</div></div>"""
    
    return html_content

def generate_html_report(team1, team2, report_data):
    summary_stats = report_data.get('summary_stats', {})
    h2h_betting = report_data.get('h2h_betting', {})
    defense_data = report_data.get('defense_data', {})
    top_performers = report_data.get('top_performers', {})
    redzone_targets = report_data.get('redzone_targets', {})
    pie_charts = report_data.get('pie_charts', {})
    historical_stats = report_data.get('historical_stats', {})
    
    team1_color = get_team_color(team1)
    team2_color = get_team_color(team2)
    
    html_content = f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>{team1} vs {team2} Matchup Report</title><script src="https://cdn.plot.ly/plotly-latest.min.js"></script><style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px; background-color: #f8f9fa; line-height: 1.6; }}
        .container {{ max-width: 1200px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1 {{ text-align: center; color: #333; margin-bottom: 30px; font-size: 2.5rem; }}
        .subtitle {{ text-align: center; color: #666; margin-bottom: 30px; font-style: italic; }}
        .section {{ margin: 30px 0; padding: 20px; border: 1px solid #e6e6e6; border-radius: 8px; background-color: #fafafa; }}
        .stats-container {{ margin: 30px 0; padding: 25px; background-color: white; border: 1px solid #e6e6e6; border-radius: 8px; border-left: 4px solid #007bff; }}
        .stats-list {{ display: flex; flex-direction: column; gap: 0; }}
        .stat-item {{ display: flex; justify-content: space-between; align-items: center; padding: 12px 0; border-bottom: 1px solid #e9ecef; }}
        .stat-item:last-child {{ border-bottom: none; }}
        .stat-label {{ font-size: 1rem; color: #495057; font-weight: 500; }}
        .stat-value {{ font-size: 1.3rem; font-weight: bold; color: #212529; }}
        .team1-stat {{ color: {team1_color}; }}
        .team2-stat {{ color: {team2_color}; }}
        .betting-box {{ border: 1px solid #e6e6e6; border-radius: 10px; padding: 20px; background-color: white; margin: 20px 0; }}
        .betting-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-top: 15px; }}
        .betting-item {{ text-align: center; }}
        .betting-value {{ font-size: 1.8rem; font-weight: 800; margin: 5px 0; }}
        .defense-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin: 20px 0; }}
        .defense-box {{ border: 1px solid #e6e6e6; background-color: rgba(0,0,0,0.02); border-radius: 8px; padding: 15px; }}
        .defense-title {{ text-align: center; font-weight: 600; margin-bottom: 15px; font-size: 1.1rem; }}
        .defense-metrics {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-bottom: 10px; }}
        .defense-metric {{ text-align: center; }}
        .defense-metric-value {{ font-weight: 700; font-size: 1.1rem; }}
        .defense-yards {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 10px; }}
        .performance-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin: 20px 0; }}
        .performance-title {{ text-align: center; font-weight: bold; margin-bottom: 15px; font-size: 1.2rem; }}
        .chart-container {{ margin: 20px 0; text-align: center; display: grid; grid-template-columns: 1fr 1fr; gap: 20px; align-items: start; }}
        .chart-item {{ display: flex; flex-direction: column; align-items: center; width: 350px; margin: 0 auto; }}
        .player-section {{ margin: 30px 0; padding: 20px; border: 1px solid #e6e6e6; border-radius: 8px; background-color: white; }}
        .player-header {{ display: flex; align-items: center; margin-bottom: 20px; font-size: 2.2rem; font-weight: bold; }}
        .team-logo {{ width: 60px; height: 60px; margin-right: 15px; display: flex; align-items: center; justify-content: center; }}
        .team-logo img {{ width: 100%; height: 100%; object-fit: contain; }}
        .team-logo-fallback {{ width: 60px; height: 60px; border: 1px solid #ccc; display: flex; align-items: center; justify-content: center; font-size: 24px; font-weight: bold; margin-right: 15px; background-color: #f5f5f5; }}
        .player-summary {{ margin-bottom: 20px; }}
        .player-detail {{ margin: 30px 0; border: 1px solid #e6e6e6; border-radius: 6px; background-color: white; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
        .player-name {{ font-weight: bold; font-size: 1.1rem; padding: 12px 15px; margin: 0; color: #333; cursor: pointer; background-color: #f8f9fa; border-bottom: 1px solid #e6e6e6; border-radius: 4px 4px 0 0; display: block; }}
        .player-name:hover {{ background-color: #e9ecef; }}
        .player-content {{ padding: 15px; display: none; background-color: white; border-radius: 0 0 4px 4px; }}
        .player-detail input[type="checkbox"] {{ display: none; }}
        .player-detail input[type="checkbox"]:checked ~ .player-content {{ display: block; }}
        .player-metrics {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 12px; }}
        .player-metric {{ text-align: center; padding: 8px; background-color: #f8f9fa; border-radius: 4px; border: 1px solid #e6e6e6; }}
        .player-metric-value {{ font-size: 1.3rem; font-weight: bold; color: #333; }}
        .player-metric-label {{ font-size: 0.8rem; color: #666; margin-top: 3px; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 0.9rem; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; font-weight: bold; }}
        tr:nth-child(even) {{ background-color: #f9f9f9; }}
        .team1-color {{ color: {team1_color}; }}
        .team2-color {{ color: {team2_color}; }}
    </style></head><body><div class="container"><h1>{team1} vs {team2} Matchup Report</h1><div class="subtitle">{summary_stats.get('games_analyzed', 0)} most recent games analyzed</div>"""

    html_content += f"""<div class="section"><h2>Head-to-Head Statistics</h2><div class="stats-container"><div class="stats-list"><div class="stat-item"><span class="stat-label">{team1} Wins</span><span class="stat-value team1-stat">{summary_stats.get('team1_wins', 0)}</span></div><div class="stat-item"><span class="stat-label">{team2} Wins</span><span class="stat-value team2-stat">{summary_stats.get('team2_wins', 0)}</span></div><div class="stat-item"><span class="stat-label">Winning Streak ({summary_stats.get('winner_team', 'N/A')})</span><span class="stat-value">{summary_stats.get('winning_streak', 0)}</span></div><div class="stat-item"><span class="stat-label">{team1} Avg PPG</span><span class="stat-value team1-stat">{summary_stats.get('team1_ppg', 0):.1f}</span></div><div class="stat-item"><span class="stat-label">{team2} Avg PPG</span><span class="stat-value team2-stat">{summary_stats.get('team2_ppg', 0):.1f}</span></div><div class="stat-item"><span class="stat-label">Average Total Points</span><span class="stat-value">{summary_stats.get('avg_total_points', 0):.1f}</span></div><div class="stat-item"><span class="stat-label">Games with 50+ Points</span><span class="stat-value">{summary_stats.get('over_50_games', 0)}</span></div></div></div></div>"""

    if h2h_betting:
        ats_t1 = h2h_betting.get('team1_ats', (0,0,0))
        ats_t2 = h2h_betting.get('team2_ats', (0,0,0))
        ou = h2h_betting.get('ou', (0,0,0))
        fav_dog = h2h_betting.get('fav_dog', {})
        html_content += f"""<div class="section"><h2>Head-to-Head Betting</h2><div class="betting-box"><div class="betting-grid"><div class="betting-item"><div>ATS: {team1}</div><div class="betting-value team1-color">{ats_t1[0]}-{ats_t1[1]}-{ats_t1[2]}</div></div><div class="betting-item"><div>ATS: {team2}</div><div class="betting-value team2-color">{ats_t2[0]}-{ats_t2[1]}-{ats_t2[2]}</div></div><div class="betting-item"><div>Totals (O-U-P)</div><div class="betting-value">{ou[0]}-{ou[1]}-{ou[2]}</div></div><div class="betting-item"><div><strong>{team1}:</strong> Fav {fav_dog.get('team1_fav', 0)} - Dog {fav_dog.get('team1_dog', 0)}</div><div><strong>{team2}:</strong> Fav {fav_dog.get('team2_fav', 0)} - Dog {fav_dog.get('team2_dog', 0)}</div></div></div></div></div>"""

    if defense_data:
        t1_def = defense_data.get('team1', {})
        t2_def = defense_data.get('team2', {})
        html_content += f"""<div class="section"><h2>Defensive Metrics (Last 10 Games)</h2><div class="defense-grid"><div class="defense-box"><div class="defense-title">{team1} Defense</div><div class="defense-metrics"><div class="defense-metric"><div>Sacks/game</div><div class="defense-metric-value">{t1_def.get('avg_sacks_per_game', 0):.1f}</div></div><div class="defense-metric"><div>QB Hits/game</div><div class="defense-metric-value">{t1_def.get('avg_qb_hits', 0):.1f}</div></div><div class="defense-metric"><div>Turnovers/game</div><div class="defense-metric-value">{t1_def.get('avg_total_turnovers', 0):.1f}</div></div></div><div class="defense-yards"><div class="defense-metric"><div>Avg Pass Yds Allowed</div><div class="defense-metric-value">{t1_def.get('avg_pass_yards_allowed', 0):.1f}</div></div><div class="defense-metric"><div>Avg Rush Yds Allowed</div><div class="defense-metric-value">{t1_def.get('avg_rush_yards_allowed', 0):.1f}</div></div></div></div><div class="defense-box"><div class="defense-title">{team2} Defense</div><div class="defense-metrics"><div class="defense-metric"><div>Sacks/game</div><div class="defense-metric-value">{t2_def.get('avg_sacks_per_game', 0):.1f}</div></div><div class="defense-metric"><div>QB Hits/game</div><div class="defense-metric-value">{t2_def.get('avg_qb_hits', 0):.1f}</div></div><div class="defense-metric"><div>Turnovers/game</div><div class="defense-metric-value">{t2_def.get('avg_total_turnovers', 0):.1f}</div></div></div><div class="defense-yards"><div class="defense-metric"><div>Avg Pass Yds Allowed</div><div class="defense-metric-value">{t2_def.get('avg_pass_yards_allowed', 0):.1f}</div></div><div class="defense-metric"><div>Avg Rush Yds Allowed</div><div class="defense-metric-value">{t2_def.get('avg_rush_yards_allowed', 0):.1f}</div></div></div></div></div></div>"""

    if top_performers:
        t1_top = top_performers.get('team1', pd.DataFrame())
        t2_top = top_performers.get('team2', pd.DataFrame())
        html_content += f"""<div class="section"><h2>Top Performance Metrics</h2><div class="performance-grid"><div><div class="performance-title">{team1}</div>"""
        if not t1_top.empty: html_content += t1_top.to_html(classes='table', table_id='team1_top', escape=False, index=False)
        else: html_content += "<p>No skill-position data available</p>"
        html_content += f"""</div><div><div class="performance-title">{team2}</div>"""
        if not t2_top.empty: html_content += t2_top.to_html(classes='table', table_id='team2_top', escape=False, index=False)
        else: html_content += "<p>No skill-position data available</p>"
        html_content += "</div></div></div>"

    if redzone_targets:
        rz_t1 = redzone_targets.get('team1', pd.DataFrame())
        rz_t2 = redzone_targets.get('team2', pd.DataFrame())
        html_content += f"""<div class="section"><h2>Red-Zone Targets (2025)</h2><div class="performance-grid"><div><div class="performance-title">{team1}</div>"""
        if not rz_t1.empty: html_content += rz_t1.to_html(classes='table', table_id='team1_redzone', escape=False, index=False)
        else: html_content += "<p>No red-zone data available</p>"
        html_content += f"""</div><div><div class="performance-title">{team2}</div>"""
        if not rz_t2.empty: html_content += rz_t2.to_html(classes='table', table_id='team2_redzone', escape=False, index=False)
        else: html_content += "<p>No red-zone data available</p>"
        html_content += "</div></div></div>"

    if pie_charts:
        ats_chart = pie_charts.get('ats_chart')
        ou_chart = pie_charts.get('ou_chart')
        html_content += """<div class="section"><h2>Betting Distribution Charts</h2><div class="chart-container">"""
        if ats_chart:
            ats_chart.update_layout(title_x=0.5, title_font_size=14, showlegend=True, legend=dict(orientation="h", yanchor="top", y=-0.15, xanchor="center", x=0.5), margin=dict(l=20, r=20, t=60, b=60))
            html_content += f"""<div class="chart-item">{ats_chart.to_html(include_plotlyjs=False, div_id='ats_chart', config={'displayModeBar': False, 'responsive': False})}</div>"""
        if ou_chart:
            ou_chart.update_layout(title_x=0.5, title_font_size=14, showlegend=True, legend=dict(orientation="h", yanchor="top", y=-0.15, xanchor="center", x=0.5), margin=dict(l=20, r=20, t=60, b=60))
            html_content += f"""<div class="chart-item">{ou_chart.to_html(include_plotlyjs=False, div_id='ou_chart', config={'displayModeBar': False, 'responsive': False})}</div>"""
        html_content += "</div></div>"

    if historical_stats:
        t1_stats = historical_stats.get('team1', pd.DataFrame())
        t2_stats = historical_stats.get('team2', pd.DataFrame())
        
        if not t1_stats.empty:
            team1_logo_html = _get_team_logo_html(team1)
            html_content += f"""<div class="player-section"><div class="player-header">{team1_logo_html}<div>{team1} Players</div></div>{_generate_player_html(t1_stats, team1, team2)}</div>"""
        
        if not t2_stats.empty:
            team2_logo_html = _get_team_logo_html(team2)
            html_content += f"""<div class="player-section"><div class="player-header">{team2_logo_html}<div>{team2} Players</div></div>{_generate_player_html(t2_stats, team2, team1)}</div>"""

    html_content += "</div></body></html>"
    return html_content

async def save_as_image(html_path, output_path):
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto(f'file://{os.path.abspath(html_path)}')
        await page.screenshot(path=output_path, full_page=True)
        await browser.close()

def main():
    parser = argparse.ArgumentParser(description='Generate matchup reports')
    parser.add_argument('week', type=int, help='Week number')
    args = parser.parse_args()
    
    week_num = args.week
    base_dir = '/workspace/Websites/Streamlit/data'
    
    print(f"Loading data for Week {week_num}...")
    try:
        df_games = pd.read_csv(os.path.join(base_dir, 'Games.csv'))
        df_playerstats = pd.read_csv(os.path.join(base_dir, 'all_passing_rushing_receiving.csv'))
        
        # Data prep
        df_playerstats['player_display_name'] = df_playerstats['player']
        df_playerstats['player_current_team'] = df_playerstats['team']
        df_playerstats['passing_yards'] = df_playerstats['pass_yds']
        df_playerstats['rushing_yards'] = df_playerstats['rush_yds']
        df_playerstats['receiving_yards'] = df_playerstats['rec_yds']
        df_playerstats['passing_tds'] = df_playerstats['pass_td']
        df_playerstats['rushing_tds'] = df_playerstats['rush_td']
        df_playerstats['receiving_tds'] = df_playerstats['rec_td']
        
        game_id_parts = df_playerstats['game_id'].str.split('_', expand=True)
        df_playerstats['week'] = pd.to_numeric(game_id_parts[1], errors='coerce')
        df_playerstats['away_team'] = game_id_parts[2]
        df_playerstats['home_team'] = game_id_parts[3]
        
        df_roster2025 = pd.read_csv(os.path.join(base_dir, 'rosters', 'roster_2025.csv'))
        roster_to_games_team_map = {'LV': 'LVR', 'LA': 'LAR'}
        if 'team' in df_roster2025.columns:
            df_roster2025['team'] = df_roster2025['team'].map(lambda x: roster_to_games_team_map.get(x, x))
            
        try:
            df_team_game_logs = pd.read_csv(os.path.join(base_dir, 'all_team_game_logs.csv'))
        except: df_team_game_logs = pd.DataFrame()
        
        try:
            df_defense_logs = pd.read_csv(os.path.join(base_dir, 'all_defense-game-logs.csv'))
            if 'team' in df_defense_logs.columns:
                 defense_to_games_team_map = {'GNB': 'GB', 'KAN': 'KC', 'NOR': 'NO', 'NWE': 'NE', 'OAK': 'LVR', 'SFO': 'SF', 'TAM': 'TB'}
                 df_defense_logs['team'] = df_defense_logs['team'].map(lambda x: defense_to_games_team_map.get(x, x))
        except: df_defense_logs = pd.DataFrame()
        
        try:
            df_redzone = pd.read_csv(os.path.join(base_dir, 'all_redzone.csv'))
        except: df_redzone = pd.DataFrame()

    except Exception as e:
        print(f"Error loading data: {e}")
        return

    # Filter games for the week
    # Assuming df_games has 'week' column or we can derive it. Games.csv usually has 'week'.
    # Checking Games.csv structure from original code, it implies game_id is YYYY_WW_AWAY_HOME.
    # But filtering by week:
    if 'week' not in df_games.columns:
        # Derive week from game_id
        g_parts = df_games['game_id'].astype(str).str.split('_', expand=True)
        if len(g_parts.columns) >= 2:
            df_games['week'] = pd.to_numeric(g_parts[1], errors='coerce')
    
    # Filter for year 2025? The prompt implies "entire week of games". Usually means upcoming or current season.
    # The original script defaults to 2025 rosters.
    # Let's filter df_games for week and season 2025 if possible, or just week.
    # Assuming the user knows the week number aligns with the dataset.
    
    week_games = df_games[df_games['week'] == week_num]
    
    # If no games found, try to assume 2025
    if week_games.empty and 'season' in df_games.columns:
         week_games = df_games[(df_games['week'] == week_num) & (df_games['season'] == 2025)]

    if week_games.empty:
        # Just try week match irrespective of season, but maybe filter for recent games (last 200 games?) to avoid old seasons?
        # Actually, let's just stick to week match and assume the file contains current season at the end.
        # But Games.csv likely has all history.
        # We should filter for 2025 (or latest year).
        # Let's check max season.
        if 'season' in df_games.columns:
            max_season = df_games['season'].max()
            week_games = df_games[(df_games['week'] == week_num) & (df_games['season'] == max_season)]
    
    if week_games.empty:
        print(f"No games found for week {week_num}")
        return

    output_dir = 'reports'
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"Found {len(week_games)} games for Week {week_num}.")

    for _, game in week_games.iterrows():
        team1 = game['away_team']
        team2 = game['home_team']
        print(f"Generating report for {team1} vs {team2}...")

        # --- Replicating 'generate_clicked' logic ---
        team_matchups = df_games[((df_games['home_team'] == team1) & (df_games['away_team'] == team2)) |
                                 ((df_games['home_team'] == team2) & (df_games['away_team'] == team1))]
        
        completed_matchups = team_matchups.dropna(subset=['home_score', 'away_score'])
        last_10_games = completed_matchups.sort_values(by='date', ascending=False).head(10)
        
        if last_10_games.empty:
            summary_stats = {}
            h2h = {'team1_ats': (0,0,0), 'team2_ats': (0,0,0), 'ou': (0,0,0), 'fav_dog': {}}
        else:
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
             
             num_h2h_games = len(last_10_games)
             team1_ppg = float(team1_scores) / num_h2h_games if num_h2h_games > 0 else 0.0
             team2_ppg = float(team2_scores) / num_h2h_games if num_h2h_games > 0 else 0.0
             over_50_points_games = int((total_points > 50).sum())
             
             most_recent = last_10_games.iloc[0]
             winner_team = most_recent['home_team'] if most_recent['home_score'] > most_recent['away_score'] else most_recent['away_team']
             
             streak = 0
             for _, g in last_10_games.iterrows():
                 home_win = g['home_score'] > g['away_score']
                 away_win = g['away_score'] > g['home_score']
                 team_won = (home_win and g['home_team'] == winner_team) or (away_win and g['away_team'] == winner_team)
                 if team_won: streak += 1
                 else: break
            
             summary_stats = {
                'games_analyzed': len(last_10_games),
                'team1_wins': team1_wins,
                'team2_wins': team2_wins,
                'winning_streak': streak,
                'winner_team': winner_team,
                'team1_ppg': team1_ppg,
                'team2_ppg': team2_ppg,
                'avg_total_points': average_total_points,
                'over_50_games': over_50_points_games
             }
             
             h2h = compute_head_to_head_bets(df_games, team1, team2, limit=10)

        # Charts
        pie_charts = {}
        if last_10_games.empty: pass
        else:
            ats_t1_w, ats_t1_l, ats_push = h2h.get('team1_ats', (0,0,0))
            if (ats_t1_w + h2h.get('team2_ats', (0,0,0))[0] + ats_push) > 0:
                 pie_charts['ats_chart'] = px.pie(
                    values=[ats_t1_w, h2h['team2_ats'][0], ats_push],
                    names=[f"{team1} cover", f"{team2} cover", "Push"],
                    hole=0.45,
                    color_discrete_sequence=[get_team_color(team1), get_team_color(team2), PUSH_GRAY]
                )
            ou_over, ou_under, ou_push = h2h.get('ou', (0,0,0))
            if (ou_over + ou_under + ou_push) > 0:
                 pie_charts['ou_chart'] = px.pie(
                    values=[ou_over, ou_under, ou_push],
                    names=["Over", "Under", "Push"],
                    hole=0.45,
                    color_discrete_sequence=[NFL_BLUE, NFL_RED, PUSH_GRAY]
                )

        t1_def_early = calculate_defense_summary(df_defense_logs, df_team_game_logs, team1, last_n_games=10, df_games_ctx=df_games)
        t2_def_early = calculate_defense_summary(df_defense_logs, df_team_game_logs, team2, last_n_games=10, df_games_ctx=df_games)

        roster = df_roster2025
        roster_team1 = roster[(roster['season'] == 2025) & (roster['team'] == team1) & (~roster['status'].isin(['CUT','RET']))]
        roster_team2 = roster[(roster['season'] == 2025) & (roster['team'] == team2) & (~roster['status'].isin(['CUT','RET']))]
        players_team1_names = roster_team1['full_name'].dropna().unique()
        players_team2_names = roster_team2['full_name'].dropna().unique()

        historical_stats_team1 = pd.DataFrame()
        historical_stats_team2 = pd.DataFrame()

        if len(players_team1_names) > 0:
            mask_names_t1 = df_playerstats['player_display_name'].isin(players_team1_names)
            mask_game_has_team2 = (df_playerstats['home_team'] == team2) | (df_playerstats['away_team'] == team2)
            if 'player_current_team' in df_playerstats.columns:
                mask_player_not_team2 = (df_playerstats['player_current_team'] != team2)
                historical_stats_team1 = df_playerstats[mask_names_t1 & mask_game_has_team2 & mask_player_not_team2]
            else:
                historical_stats_team1 = df_playerstats[mask_names_t1 & mask_game_has_team2]

        if len(players_team2_names) > 0:
             mask_names_t2 = df_playerstats['player_display_name'].isin(players_team2_names)
             mask_game_has_team1 = (df_playerstats['home_team'] == team1) | (df_playerstats['away_team'] == team1)
             if 'player_current_team' in df_playerstats.columns:
                mask_player_not_team1 = (df_playerstats['player_current_team'] != team1)
                historical_stats_team2 = df_playerstats[mask_names_t2 & mask_game_has_team1 & mask_player_not_team1]
             else:
                historical_stats_team2 = df_playerstats[mask_names_t2 & mask_game_has_team1]

        # Merge dates
        if not historical_stats_team1.empty:
             if 'date' not in historical_stats_team1.columns:
                 historical_stats_team1 = historical_stats_team1.merge(df_games[['game_id', 'date']], on='game_id', how='left')
             historical_stats_team1.loc[:, 'date'] = pd.to_datetime(historical_stats_team1['date'], format='%Y-%m-%d %H:%M:%S', errors='coerce')
             historical_stats_team1 = historical_stats_team1.copy()
             historical_stats_team1.loc[:, 'player_name_with_position'] = historical_stats_team1['player_display_name'] + " (" + historical_stats_team1['position'] + ")"

        if not historical_stats_team2.empty:
             if 'date' not in historical_stats_team2.columns:
                 historical_stats_team2 = historical_stats_team2.merge(df_games[['game_id', 'date']], on='game_id', how='left')
             historical_stats_team2.loc[:, 'date'] = pd.to_datetime(historical_stats_team2['date'], format='%Y-%m-%d %H:%M:%S', errors='coerce')
             historical_stats_team2 = historical_stats_team2.copy()
             historical_stats_team2.loc[:, 'player_name_with_position'] = historical_stats_team2['player_display_name'] + " (" + historical_stats_team2['position'] + ")"

        t1_top = compute_top_skill_performers(historical_stats_team1, top_n=4)
        t2_top = compute_top_skill_performers(historical_stats_team2, top_n=4)
        rz_t1 = get_redzone_targets(df_redzone, team1, year=2025)
        rz_t2 = get_redzone_targets(df_redzone, team2, year=2025)

        report_data = {
            'summary_stats': summary_stats,
            'h2h_betting': h2h,
            'defense_data': {'team1': t1_def_early, 'team2': t2_def_early},
            'top_performers': {'team1': t1_top, 'team2': t2_top},
            'redzone_targets': {'team1': rz_t1, 'team2': rz_t2},
            'pie_charts': pie_charts,
            'historical_stats': {'team1': historical_stats_team1, 'team2': historical_stats_team2}
        }

        html = generate_html_report(team1, team2, report_data)
        
        filename_base = f"week_{week_num}_{team1}_vs_{team2}"
        html_path = os.path.join(output_dir, f"{filename_base}.html")
        with open(html_path, 'w') as f:
            f.write(html)
        print(f"Saved HTML to {html_path}")
        
        # Save as Image using Playwright
        image_path = os.path.join(output_dir, f"{filename_base}.png")
        try:
            asyncio.run(save_as_image(html_path, image_path))
            print(f"Saved Image to {image_path}")
        except Exception as e:
            print(f"Failed to generate image: {e}")

if __name__ == "__main__":
    main()
