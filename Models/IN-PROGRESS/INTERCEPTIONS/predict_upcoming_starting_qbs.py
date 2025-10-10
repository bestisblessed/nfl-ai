import os
import pickle
import pandas as pd
import numpy as np
import argparse

from sklearn.linear_model import LogisticRegression

import config

STARTING_QBS_PATH = '/Users/td/Code/nfl-ai/Models/starting_qbs_2025.csv'
PLAYER_STATS_PATH = config.DATA_PATH
UPCOMING_GAMES_PATH_CANDIDATES = [
    '/Users/td/Code/nfl-ai/Models/upcoming_games.csv',
]

parser = argparse.ArgumentParser(description="Predict QB interception probabilities for upcoming games.")
parser.add_argument("--model", type=str, default="logistic_regression",
                   choices=["logistic_regression", "random_forest", "xgboost"],
                   help="Which trained model to use for predictions (default: logistic_regression)")
args = parser.parse_args()

MODEL_PATH = f'/Users/td/Code/nfl-ai/Models/IN-PROGRESS/INTERCEPTIONS/{args.model}_model.pkl'


def load_model(model_path: str):
    if os.path.exists(model_path):
        with open(model_path, 'rb') as f:
            model = pickle.load(f)
        return model
    raise FileNotFoundError(f"Trained model not found at {model_path}. Please run training first.")


def load_upcoming_games():
    for path in UPCOMING_GAMES_PATH_CANDIDATES:
        if os.path.exists(path):
            try:
                df = pd.read_csv(path)
                return df
            except Exception:
                continue
    return None


def build_qb_feature_rows(player_stats_df: pd.DataFrame, starting_qbs_df: pd.DataFrame, features: list) -> pd.DataFrame:
    # Filter to QBs only
    # Identify passing rows (QB-like) using at least 2 pass attempts (consistent with training)
    qb_df = player_stats_df.copy()
    passing_mask = qb_df['pass_att'].fillna(0) >= 2
    qb_df = qb_df[passing_mask]

    # Global means for fallback
    global_means = qb_df[features].mean()

    rows = []
    for _, row in starting_qbs_df.iterrows():
        team = row['team'] if 'team' in row else row['Team'] if 'Team' in row else row.get('TeamID')
        qb_name = row['starting_qb'] if 'starting_qb' in row else row.get('QB') or row.get('player')

        qb_games = qb_df[qb_df['player'] == qb_name]
        if not qb_games.empty:
            # Use most recent game stats (by season then week)
            qb_games_sorted = qb_games.sort_values(['season', 'week'])
            latest = qb_games_sorted.iloc[-1]
            feat_vals = latest[features]
        else:
            # Fallback: averages by team recent QB, else global
            team_games = qb_df[qb_df['team'] == team]
            if not team_games.empty:
                feat_vals = team_games[features].mean()
            else:
                feat_vals = global_means
        out = {
            'team': team,
            'player': qb_name,
        }
        out.update({f: float(feat_vals[f]) if pd.notna(feat_vals[f]) else float(global_means[f]) for f in features})
        rows.append(out)

    pred_input = pd.DataFrame(rows)
    # Ensure no NaNs
    pred_input[features] = pred_input[features].fillna(global_means)
    return pred_input


def attach_opponents(pred_input: pd.DataFrame, upcoming_games_df: pd.DataFrame) -> pd.DataFrame:
    if upcoming_games_df is None:
        pred_input['opponent'] = np.nan
        pred_input['home_away'] = np.nan
        return pred_input

    games = upcoming_games_df.copy()
    # Normalize column names common patterns
    games.columns = [c.lower() for c in games.columns]
    # Expect columns like home_team, away_team
    home_col = 'home_team' if 'home_team' in games.columns else None
    away_col = 'away_team' if 'away_team' in games.columns else None

    if home_col is None or away_col is None:
        pred_input['opponent'] = np.nan
        pred_input['home_away'] = np.nan
        return pred_input

    team_to_opp = {}
    team_to_ha = {}
    for _, g in games.iterrows():
        home = g[home_col]
        away = g[away_col]
        if pd.isna(home) or pd.isna(away):
            continue
        team_to_opp[home] = away
        team_to_opp[away] = home
        team_to_ha[home] = 'HOME'
        team_to_ha[away] = 'AWAY'

    pred_input['opponent'] = pred_input['team'].map(team_to_opp)
    pred_input['home_away'] = pred_input['team'].map(team_to_ha)
    return pred_input


def main():
    print(f'Predicting with {args.model} model....')
    model = load_model(MODEL_PATH)

    # Load data
    player_stats = pd.read_csv(PLAYER_STATS_PATH, low_memory=False)
    starting_qbs = pd.read_csv(STARTING_QBS_PATH)

    # Build features
    features = config.FEATURES
    pred_input = build_qb_feature_rows(player_stats, starting_qbs, features)

    # Attach opponents if available
    upcoming_games = load_upcoming_games()
    pred_input = attach_opponents(pred_input, upcoming_games)

    # Infer week number for prediction file naming (take max week in starting_qbs or games, fallback to 1)
    predicted_week = None
    if 'week' in starting_qbs.columns:
        try:
            week_vals = pd.to_numeric(starting_qbs['week'], errors='coerce').dropna()
            if not week_vals.empty:
                predicted_week = int(week_vals.max())
        except Exception:
            pass
    if predicted_week is None and upcoming_games is not None and 'week' in upcoming_games.columns:
        try:
            week_vals = pd.to_numeric(upcoming_games['week'], errors='coerce').dropna()
            if not week_vals.empty:
                predicted_week = int(week_vals.max())
        except Exception:
            pass
    if predicted_week is None:
        predicted_week = 1  # fallback if not found (could enhance with datetime if needed)

    # Predict
    probs = model.predict_proba(pred_input[features])

    # Convert probabilities to American odds
    def prob_to_american(p):
        epsilon = 1e-9
        p = min(max(float(p), epsilon), 1.0 - epsilon)
        if p >= 0.5:
            return -int(round((p / (1.0 - p)) * 100))
        else:
            return int(round(((1.0 - p) / p) * 100))

    interception_probs = probs[:, 1]
    no_interception_probs = probs[:, 0]

    # Prepare output with American odds
    output = pred_input[['player', 'team', 'opponent', 'home_away']].copy()
    output['interception_american_odds'] = [prob_to_american(p) for p in interception_probs]
    output['no_interception_american_odds'] = [prob_to_american(p) for p in no_interception_probs]

    # Sort by interception probability desc (but display odds)
    sort_indices = interception_probs.argsort()[::-1]  # Sort by interception prob descending
    output = output.iloc[sort_indices].reset_index(drop=True)

    # Print full table of all QBs with + signs for positive odds
    try:
        from tabulate import tabulate
        output_display = output.copy()
        output_display['interception_american_odds'] = output_display['interception_american_odds'].apply(lambda v: f"+{v}" if v > 0 else str(v))
        output_display['no_interception_american_odds'] = output_display['no_interception_american_odds'].apply(lambda v: f"+{v}" if v > 0 else str(v))
        print('QB Interception American Odds:\n')
        print(tabulate(output_display, headers='keys', tablefmt='github', showindex=False))
    except ImportError:
        print('QB Interception American Odds:')
        print(output)

    # Save full table in predictions/ with week number and model name in filename
    predictions_dir = "/Users/td/Code/nfl-ai/Models/IN-PROGRESS/INTERCEPTIONS/predictions"
    os.makedirs(predictions_dir, exist_ok=True)
    out_path = os.path.join(predictions_dir, f"upcoming_qb_interception_{args.model}_week_{predicted_week}.csv")
    output.to_csv(out_path, index=False)
    print(f"\nSaved American odds to {out_path}")


if __name__ == '__main__':
    main()
