"""
Compare DraftKings Interceptions O/U implied probabilities against model output.

Inputs:
  --odds: CSV from scrape_interception_odds.py
  --pred: predictions/upcoming_qb_interception_<model>_week_<W>.csv
  --out:  merged comparison CSV with edge metrics
"""

from __future__ import annotations

import argparse
import os
from typing import List
import glob
import re

import pandas as pd
import datetime as dt

from odds_utils import american_to_prob, normalize_player_name, best_fuzzy_match


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Compare DK odds to model predictions")
    p.add_argument("--odds", type=str, default="", help="Odds CSV path (defaults to data/odds_interceptions_dk_latest.csv)")
    p.add_argument("--pred", type=str, default="", help="Model predictions CSV (defaults to latest LR week file)")
    p.add_argument("--out", type=str, default="", help="Output comparison CSV (defaults from week)")
    return p.parse_args()


def _find_latest_lr_pred() -> str:
    pattern = "/Users/td/Code/nfl-ai/Models/IN-PROGRESS/INTERCEPTIONS/predictions/upcoming_qb_interception_logistic_regression_week_*.csv"
    files = glob.glob(pattern)
    if not files:
        return ""
    files.sort(key=lambda f: os.path.getmtime(f), reverse=True)
    return files[0]


def _infer_week_from_filename(path: str) -> str:
    m = re.search(r"week_(\d+)\.csv$", path)
    return m.group(1) if m else ""


def to_implied_prob_series(american_series: pd.Series) -> pd.Series:
    return american_series.apply(american_to_prob)


def build_player_match_map(pred_players: List[str], odds_players: List[str]) -> dict:
    """Map model player names to odds player names using exact then fuzzy matching."""
    match_map: dict = {}
    odds_set = set(odds_players)
    # Exact (case-insensitive) first
    odds_norm_map = {normalize_player_name(p): p for p in odds_players}
    for p in pred_players:
        pn = normalize_player_name(p)
        if pn in odds_norm_map:
            match_map[p] = odds_norm_map[pn]
        else:
            best, score = best_fuzzy_match(p, odds_players, min_ratio=90)
            if best is not None:
                match_map[p] = best
    return match_map


def main() -> None:
    args = parse_args()

    # Resolve defaults
    odds_path = args.odds or "/Users/td/Code/nfl-ai/Models/IN-PROGRESS/INTERCEPTIONS/data/odds_interceptions_dk_latest.csv"
    if not os.path.exists(odds_path):
        raise FileNotFoundError(f"Odds file not found: {odds_path}")
    pred_path = args.pred or _find_latest_lr_pred()
    if not pred_path:
        raise FileNotFoundError("No logistic regression predictions found. Run predict_upcoming_starting_qbs.py first.")

    odds_df = pd.read_csv(odds_path)
    pred_df = pd.read_csv(pred_path)

    # Compute implied probabilities from American odds (DK Over/Under)
    odds_df['dk_prob_over'] = to_implied_prob_series(odds_df['over_american_odds'])
    odds_df['dk_prob_under'] = to_implied_prob_series(odds_df['under_american_odds'])

    # Normalize player names
    odds_df['player_norm'] = odds_df['player'].apply(normalize_player_name)
    pred_df['player_norm'] = pred_df['player'].apply(normalize_player_name) if 'player' in pred_df.columns else pred_df['player']

    # If prediction file lacks player column name assumptions, try common alternatives
    if 'player' not in pred_df.columns:
        for alt in ('QB', 'starting_qb', 'name'):
            if alt in pred_df.columns:
                pred_df['player'] = pred_df[alt]
                pred_df['player_norm'] = pred_df['player'].apply(normalize_player_name)
                break

    # Extract model probabilities from our outputs by converting back from odds if probabilities not present
    # In our pipeline, predictions CSV includes american odds only; recover probabilities from those.
    if 'interception_american_odds' in pred_df.columns:
        pred_df['model_prob_interception'] = to_implied_prob_series(pred_df['interception_american_odds'])
    elif 'interception_prob' in pred_df.columns:
        pred_df['model_prob_interception'] = pd.to_numeric(pred_df['interception_prob'], errors='coerce')
    else:
        raise ValueError("Predictions file must include interception_american_odds or interception_prob")

    if 'no_interception_american_odds' in pred_df.columns:
        pred_df['model_prob_no_interception'] = to_implied_prob_series(pred_df['no_interception_american_odds'])
    elif 'no_interception_prob' in pred_df.columns:
        pred_df['model_prob_no_interception'] = pd.to_numeric(pred_df['no_interception_prob'], errors='coerce')
    else:
        # derive from complement if not present
        pred_df['model_prob_no_interception'] = 1.0 - pred_df['model_prob_interception']

    # Build player mapping and join
    match_map = build_player_match_map(pred_df['player'].tolist(), odds_df['player'].tolist())
    # Targeted alias: Cam Ward -> Cameron Ward
    if 'Cam Ward' in pred_df['player'].values and 'Cameron Ward' in odds_df['player'].values:
        match_map['Cam Ward'] = 'Cameron Ward'
    pred_df['player_odds_name'] = pred_df['player'].map(match_map)

    merged = pred_df.merge(
        odds_df,
        left_on='player_odds_name',
        right_on='player',
        how='left',
        suffixes=('_model', '_dk'),
    )

    # Compute edges
    merged['edge_interception'] = merged['model_prob_interception'] - merged['dk_prob_over']
    merged['edge_no_interception'] = merged['model_prob_no_interception'] - merged['dk_prob_under']
    merged['abs_edge'] = (merged['edge_interception'].abs()).fillna(0.0)

    # Select and sort columns
    out_cols = [
        'player_model',
        'team_model' if 'team_model' in merged.columns else 'team',
        'opponent_model' if 'opponent_model' in merged.columns else 'opponent',
        'home_away_model' if 'home_away_model' in merged.columns else 'home_away',
        'interception_american_odds',
        'no_interception_american_odds',
        'over_american_odds',
        'under_american_odds',
        'model_prob_interception',
        'model_prob_no_interception',
        'dk_prob_over',
        'dk_prob_under',
        'edge_interception',
        'edge_no_interception',
        'abs_edge',
        'event_id',
        'start_time',
        'source',
    ]
    # Filter for availability
    out_cols = [c for c in out_cols if c in merged.columns]
    out_df = merged[out_cols].sort_values('abs_edge', ascending=False)

    # Resolve output paths if not provided
    out_path = args.out
    if not out_path:
        wk = _infer_week_from_filename(pred_path) or "latest"
        out_path = f"/Users/td/Code/nfl-ai/Models/IN-PROGRESS/INTERCEPTIONS/predictions/upcoming_qb_interception_compare_logistic_regression_week_{wk}.csv"
    # No longer saving the raw comparison CSV; we save a final edges CSV matching the terminal table below

    # We will save a final CSV aligned to the printed table below

    # Helper: parse american odds string to numeric int for sorting
    def parse_american_int(x):
        if pd.isna(x):
            return None
        s = str(x).strip().replace('\u2212', '-')
        if s.startswith('+'):
            s = s[1:]
        try:
            return int(s)
        except Exception:
            return None

    # Helper: format start_time to local short time like 1:00pm
    def format_start_time(x: str) -> str:
        if pd.isna(x) or not str(x).strip():
            return ''
        s = str(x).strip().replace('Z', '+00:00')
        try:
            d = dt.datetime.fromisoformat(s)
            d_local = d.astimezone()
            # %-I is portable on mac/linux; fallback to %I with lstrip('0') if needed
            try:
                return d_local.strftime('%-I:%M%p').lower()
            except Exception:
                return d_local.strftime('%I:%M%p').lstrip('0').lower()
        except Exception:
            return str(x)

    # Helper: normalize American odds display (ASCII minus, explicit + for dogs)
    def fmt_american(x) -> str:
        if pd.isna(x) or str(x).strip().lower() == 'nan':
            return '-'
        s = str(x).strip().replace('\u2212', '-')
        if s.startswith('+') or s.startswith('-'):
            return s
        # if numeric string without sign, add '+'
        try:
            val = int(s)
            return f"{val:+d}"
        except Exception:
            return s

    # Always print a terminal summary table of all QBs sorted by model_line (favorite -> dog)
    try:
        from tabulate import tabulate  # type: ignore

        # Build an essential-columns DataFrame with friendly headers
        col_player = 'player_model'
        col_team = 'team_model' if 'team_model' in out_df.columns else 'team'
        col_opp = 'opponent_model' if 'opponent_model' in out_df.columns else 'opponent'
        # No H/A column per request

        # Drop rows with missing key values (book line/prob and opponent/team where available)
        drop_subset = ['over_american_odds', 'dk_prob_over']
        if col_team in out_df.columns:
            drop_subset.append(col_team)
        if col_opp in out_df.columns:
            drop_subset.append(col_opp)
        base_df = out_df.dropna(subset=[c for c in drop_subset if c in out_df.columns])

        disp = base_df[[c for c in [col_player, 'interception_american_odds', 'over_american_odds', 'model_prob_interception', 'dk_prob_over', 'edge_interception', col_team, col_opp, 'start_time'] if c in base_df.columns]].copy()

        # Rename columns for clarity
        rename_map = {
            col_player: 'Player',
            col_team: 'Tm',
            col_opp: 'Opp',
            'interception_american_odds': 'Model Line',
            'over_american_odds': 'Book Line',
            'model_prob_interception': 'Model %',
            'dk_prob_over': 'Book %',
            'edge_interception': 'Edge',
            'start_time': 'Time',
        }
        disp.rename(columns=rename_map, inplace=True)

        # Format probabilities and edge for readability
        for col in ('Model %', 'Book %', 'Edge'):
            if col in disp.columns:
                disp[col] = disp[col].map(lambda x: f"{x*100:.1f}%" if pd.notnull(x) else "")

        # Format odds compactly and normalize minus sign; replace missing with '-'
        if 'Model Line' in disp.columns:
            disp['Model Line'] = disp['Model Line'].map(fmt_american)
        if 'Book Line' in disp.columns:
            disp['Book'] = disp['Book Line'].map(fmt_american)

        # Add numeric for sorting by model_line favorite -> dog
        if 'Model Line' in disp.columns:
            disp['_model_line_num'] = disp['Model Line'].map(parse_american_int)
            disp.sort_values('_model_line_num', inplace=True, kind='mergesort')
            disp.drop(columns=['_model_line_num'], inplace=True)

        # Add Rank column (1-based) for a clear ordering in the display
        disp.insert(0, 'Rank', range(1, len(disp) + 1))

        # Reorder columns: Rank, Player, Model, Book, Model %, Book %, Edge, Tm, Opp, Time
        preferred_order = ['Rank', 'Player', 'Model Line', 'Book Line', 'Model %', 'Book %', 'Edge', 'Tm', 'Opp', 'Time']
        disp = disp[[c for c in preferred_order if c in disp.columns]]

        # Format start_time to short human readable local time
        if 'Time' in disp.columns:
            disp['Time'] = disp['Time'].map(format_start_time)

        # Save final CSV with the same columns as displayed in the table
        wk = _infer_week_from_filename(pred_path) or "latest"
        final_csv_path = f"/Users/td/Code/nfl-ai/Models/IN-PROGRESS/INTERCEPTIONS/predictions/upcoming_qb_interception_edges_week_{wk}.csv"
        os.makedirs(os.path.dirname(final_csv_path), exist_ok=True)
        disp.to_csv(final_csv_path, index=False)
        print(f"Saved edges to {final_csv_path}")

        print("\nAll QBs sorted by model line (favorite → dog):")
        tbl = tabulate(
            disp,
            headers='keys',
            tablefmt='github',
            showindex=False,
            colalign=("right","left","right","right","right","right","right","left","left","right"),
        )
        # Add a blank line between data rows for readability
        try:
            lines = tbl.splitlines()
            if len(lines) > 2:
                body_spaced = []
                for ln in lines[2:]:
                    body_spaced.append(ln)
                    body_spaced.append("")
                tbl = "\n".join(lines[:2] + body_spaced)
        except Exception:
            pass
        print(tbl)
    except Exception:
        # Fallback: basic CSV-like print
        cols = [
            'player_model',
            'interception_american_odds',
            'over_american_odds',
            'model_prob_interception',
            'dk_prob_over',
            'edge_interception',
            'team_model' if 'team_model' in out_df.columns else 'team',
            'opponent_model' if 'opponent_model' in out_df.columns else 'opponent',
            'start_time',
        ]
        cols = [c for c in cols if c in out_df.columns]
        tmp = out_df[cols].copy()
        # Sort by model_line
        if 'interception_american_odds' in tmp.columns:
            tmp['_mln'] = tmp['interception_american_odds'].map(parse_american_int)
            tmp.sort_values('_mln', inplace=True, kind='mergesort')
            tmp.drop(columns=['_mln'], inplace=True)
        print("\nAll QBs sorted by model_line (basic print):")
        print(tmp.to_string(index=False))


if __name__ == "__main__":
    main()


