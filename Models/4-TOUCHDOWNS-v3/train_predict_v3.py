#!/usr/bin/env python3
"""
v3 Touchdown Model: Hybrid position-specific + unified team features
- Trains separate models per position (like v1)
- Uses multi-window features + team context (best of v1+v2)
- Isotonic calibration for better probability estimates
- Enhanced filtering and feature engineering
"""

import os
import sys
import warnings
import pandas as pd
import numpy as np
from xgboost import XGBClassifier
from sklearn.calibration import CalibratedClassifierCV
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, log_loss, brier_score_loss
from tabulate import tabulate

warnings.filterwarnings('ignore', category=RuntimeWarning)


def probability_to_american_odds(prob: float) -> float:
    prob = max(min(prob, 1 - 1e-10), 1e-10)
    if prob > 0.5:
        return -100.0 * (prob / (1.0 - prob))
    return 100.0 * ((1.0 - prob) / prob)


def get_feature_columns() -> list:
    windows = [3, 5, 8]
    base_feats = [
        "rush_att", "rush_yds", "targets", "rec", "rec_yds", 
        "scoring_tds", "target_share", "rush_share"
    ]
    rolling = [f"{f}_rm{w}" for f in base_feats for w in windows]
    
    context = [
        "home_flag",
        "Offense",
        "Defense",
        "opp_offense",
        "opp_defense",
        "rz_td_pct",
        "rz_att_pg",
        "td_trend",
        "scoring_tds_season_avg",
        "targets_season_avg",
        "games_played_season"
    ]
    
    return rolling + context


def train_calibrated_xgb_v3(X: pd.DataFrame, y: pd.Series, pos: str):
    """
    Train XGBoost with isotonic calibration
    - Better than Platt for non-linear calibration issues
    - More robust than raw XGBoost probabilities
    """
    
    # Calculate class imbalance
    pos_count = y.sum()
    neg_count = len(y) - pos_count
    scale_pos_weight = neg_count / pos_count if pos_count > 0 else 1
    
    print(f"Class distribution: {pos_count} TDs / {neg_count} no TDs (ratio: {scale_pos_weight:.2f})")
    
    base_model = XGBClassifier(
        objective="binary:logistic",
        eval_metric="logloss",
        n_estimators=250,           # More than v2, less than v1
        max_depth=5,                # Slightly deeper for position nuances
        learning_rate=0.075,        # Balanced learning rate
        subsample=0.85,             # Moderate sampling
        colsample_bytree=0.85,      # Moderate feature sampling
        random_state=42,
        reg_alpha=0.5,              # Light L1 regularization
        reg_lambda=1.5,             # Moderate L2 regularization
        scale_pos_weight=scale_pos_weight,
        min_child_weight=3,         # Prevent overfitting on rare events
    )
    
    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=42
    )
    
    # Fit base model
    base_model.fit(
        X_train, y_train,
        eval_set=[(X_val, y_val)],
        verbose=False
    )
    
    # Get uncalibrated predictions
    p_val_uncal = base_model.predict_proba(X_val)[:, 1]
    
    # Apply isotonic calibration using full training set
    print("Applying isotonic calibration...")
    calibrated_model = CalibratedClassifierCV(
        base_model, 
        method='isotonic',  # Better for non-linear issues
        cv='prefit'         # Use existing train/val split
    )
    calibrated_model.fit(X_val, y_val)
    
    # Get calibrated predictions
    p_val_cal = calibrated_model.predict_proba(X_val)[:, 1]
    
    # Compute metrics
    try:
        auc_uncal = roc_auc_score(y_val, p_val_uncal)
        auc_cal = roc_auc_score(y_val, p_val_cal)
        
        ll_uncal = log_loss(y_val, p_val_uncal)
        ll_cal = log_loss(y_val, p_val_cal)
        
        brier_uncal = brier_score_loss(y_val, p_val_uncal)
        brier_cal = brier_score_loss(y_val, p_val_cal)
        
        print(f"Uncalibrated: AUC={auc_uncal:.4f} | LogLoss={ll_uncal:.4f} | Brier={brier_uncal:.4f}")
        print(f"Calibrated:   AUC={auc_cal:.4f} | LogLoss={ll_cal:.4f} | Brier={brier_cal:.4f}")
        
        metrics = pd.DataFrame([{
            "position": pos,
            "auc_uncal": auc_uncal,
            "auc_cal": auc_cal,
            "logloss_uncal": ll_uncal,
            "logloss_cal": ll_cal,
            "brier_uncal": brier_uncal,
            "brier_cal": brier_cal,
            "n_train": len(y_train),
            "n_val": len(y_val),
            "n_td_train": y_train.sum(),
            "n_td_val": y_val.sum()
        }])
    except Exception as e:
        print(f"Metrics computation failed: {e}")
        metrics = pd.DataFrame([{
            "position": pos,
            "auc_uncal": np.nan,
            "auc_cal": np.nan,
            "logloss_uncal": np.nan,
            "logloss_cal": np.nan,
            "brier_uncal": np.nan,
            "brier_cal": np.nan,
            "n_train": len(y_train),
            "n_val": len(y_val),
            "n_td_train": y_train.sum(),
            "n_td_val": y_val.sum()
        }])
    
    return calibrated_model, metrics


def build_inference_rows(upcoming_players: pd.DataFrame, train_df: pd.DataFrame, pos: str):
    feature_cols = get_feature_columns()
    per_pos_opp_col = "opp_td_rate_pos" if pos in ["WR", "RB", "TE"] else "opp_td_rate_qb_rush"
    
    # Get latest player stats
    latest = (
        train_df.sort_values(["player_id", "season", "week"])
        .groupby("player_id")
        .tail(1)[["player_id"] + feature_cols]
    )
    
    inf = upcoming_players.copy()
    inf = inf.merge(latest, on="player_id", how="left")
    
    # Fill missing rolling features with 0
    rolling_cols = [c for c in feature_cols if "_rm" in c]
    if rolling_cols:
        inf[rolling_cols] = inf[rolling_cols].fillna(0.0)
    
    # Get latest team ratings
    team_ratings = (
        train_df.sort_values(["season"])
        .drop_duplicates(subset=["team"], keep="last")
        [["team", "Offense", "Defense", "rz_td_pct", "rz_att_pg"]]
    )
    opp_ratings = (
        train_df.sort_values(["season"])
        .drop_duplicates(subset=["opp"], keep="last")
        [["opp", "opp_offense", "opp_defense"]]
        .rename(columns={"opp": "opp_key"})
    )
    
    inf = inf.merge(team_ratings, on="team", how="left")
    inf = inf.merge(opp_ratings, left_on="opp", right_on="opp_key", how="left")
    inf = inf.drop(columns=["opp_key"], errors="ignore")
    
    # Opponent TD rate
    recent_season = train_df["season"].max()
    opp_rate_map = (
        train_df[train_df["season"] == recent_season]
        .groupby("opp")[per_pos_opp_col]
        .mean()
        .to_dict()
    )
    inf[per_pos_opp_col] = inf["opp"].map(opp_rate_map)
    fallback = train_df[per_pos_opp_col].dropna().mean()
    inf[per_pos_opp_col] = inf[per_pos_opp_col].fillna(fallback)
    
    # Fill remaining context features
    context_cols = [
        "home_flag", "Offense", "Defense", "opp_offense", "opp_defense",
        "rz_td_pct", "rz_att_pg", "td_trend", "scoring_tds_season_avg",
        "targets_season_avg", "games_played_season", per_pos_opp_col
    ]
    for c in context_cols:
        if c not in inf.columns:
            inf[c] = 0.0
        else:
            inf[c] = inf[c].fillna(0.0)
    
    X_cols = feature_cols + [per_pos_opp_col]
    return inf, X_cols


def main():
    if len(sys.argv) < 2:
        print("Usage: python train_predict_v3.py <week_number>")
        sys.exit(1)
    
    week_num = int(sys.argv[1])
    out_dir = f"predictions-week-{week_num}-TD"
    os.makedirs(out_dir, exist_ok=True)
    
    train_df = pd.read_csv("data/model_train.csv")
    upcoming_players = pd.read_csv("data/upcoming_players.csv")
    
    positions = ["QB", "RB", "WR", "TE"]
    all_outputs = []
    all_metrics = []
    
    for pos in positions:
        print(f"\n{'='*60}")
        print(f"Training {pos} model (v3)")
        print(f"{'='*60}")
        
        if pos == "QB":
            train_pos = train_df[train_df["position"] == "QB"].copy()
            y = train_pos["label_qb_rush"].astype(int)
            per_pos_col = "opp_td_rate_qb_rush"
        else:
            train_pos = train_df[train_df["position"] == pos].copy()
            y = train_pos["label_any"].astype(int)
            per_pos_col = "opp_td_rate_pos"
        
        # Require minimum games played for training
        train_pos = train_pos[train_pos["games_played_season"] >= 3].copy()
        y = y.loc[train_pos.index]
        
        X_cols_all = get_feature_columns() + [per_pos_col]
        X = train_pos[X_cols_all].fillna(0.0)
        
        if X.empty or y.nunique() < 2:
            print(f"Skipping {pos}: insufficient training data")
            continue
        
        model, metrics_df = train_calibrated_xgb_v3(X, y, pos)
        all_metrics.append(metrics_df)
        
        # Predict on upcoming players
        up_pos = upcoming_players[upcoming_players["position"] == pos].copy()
        if up_pos.empty:
            print(f"No upcoming players for {pos}")
            continue
        
        inf_rows, X_cols = build_inference_rows(up_pos, train_pos, pos)
        probs = model.predict_proba(inf_rows[X_cols].fillna(0.0))[:, 1]
        
        # Enhanced filtering
        # 1. Must have some historical activity (at least 2 touches per game avg in last 3)
        usage_cols = ["rush_att_rm3", "targets_rm3", "rec_rm3"]
        historical_touches = inf_rows[usage_cols].fillna(0).sum(axis=1)
        active_mask = historical_touches >= 2.0
        
        # 2. Must have played at least 3 games this season
        games_mask = inf_rows["games_played_season"].fillna(0) >= 3
        
        # 3. Position-specific minimums on season totals
        if pos != "QB":
            season_cols = {"WR": "rec", "TE": "rec", "RB": "rush_att"}
            season_stat = season_cols.get(pos, "rec")
            if season_stat in inf_rows.columns:
                season_totals = train_df.groupby("player_id")[season_stat].sum().to_dict()
                season_mask = inf_rows["player_id"].map(season_totals).fillna(0) >= {
                    "WR": 5, "TE": 3, "RB": 8
                }[pos]
            else:
                season_mask = pd.Series([True] * len(inf_rows), index=inf_rows.index)
        else:
            season_mask = pd.Series([True] * len(inf_rows), index=inf_rows.index)
        
        final_mask = active_mask & games_mask & season_mask
        inf_rows = inf_rows[final_mask].copy()
        probs = probs[final_mask]
        
        out = inf_rows[["full_name", "player_id", "team", "opp", "position", "home_flag"]].copy()
        out["prob_anytime_td"] = probs
        out["american_odds"] = out["prob_anytime_td"].apply(probability_to_american_odds).round(1)
        out["prop_type"] = "Anytime TD"
        out["model_version"] = "anytd_xgb_v3"
        out = out.sort_values("prob_anytime_td", ascending=False).reset_index(drop=True)
        out["rank"] = range(1, len(out) + 1)
        
        all_outputs.append(out)
        
        out_file = f"{out_dir}/final_week{week_num}_{pos}_td_report.csv"
        out.to_csv(out_file, index=False)
        print(f"Saved: {out_file} ({len(out)} players)")
    
    # Save combined metrics
    if all_metrics:
        combined_metrics = pd.concat(all_metrics, ignore_index=True)
        metrics_path = f"{out_dir}/model_metrics_v3.csv"
        combined_metrics.to_csv(metrics_path, index=False)
        print(f"\nSaved combined metrics: {metrics_path}")
        print("\nMetrics Summary:")
        print(combined_metrics.to_string(index=False))
    
    # Save combined predictions
    if all_outputs:
        all_df = pd.concat(all_outputs, ignore_index=True)
        all_df = all_df.sort_values("prob_anytime_td", ascending=False).reset_index(drop=True)
        all_df["overall_rank"] = range(1, len(all_df) + 1)
        
        all_csv = f"{out_dir}/final_week{week_num}_anytime_td_report.csv"
        all_df.to_csv(all_csv, index=False)
        print(f"\nSaved combined report: {all_csv} ({len(all_df)} total predictions)")
        
        # Generate per-game text reports
        try:
            upcoming = pd.read_csv("../upcoming_games.csv")
            games = []
            seen = set()
            for _, row in upcoming.iterrows():
                g = tuple(sorted([row["home_team"], row["away_team"]]))
                if g not in seen:
                    seen.add(g)
                    games.append((row["home_team"], row["away_team"]))
            
            for i, (home, away) in enumerate(games, 1):
                game_players = all_df[
                    ((all_df["team"] == home) & (all_df["opp"] == away)) |
                    ((all_df["team"] == away) & (all_df["opp"] == home))
                ].copy()
                
                if game_players.empty:
                    continue
                
                game_players = game_players.sort_values("prob_anytime_td", ascending=False)
                
                filename = f"{out_dir}/game_{i:02d}_{home}_vs_{away}_td_predictions.txt"
                with open(filename, "w") as f:
                    f.write("=" * 80 + "\n")
                    f.write(f"{home} vs {away} | Week {week_num} 2025 | Anytime TD Probabilities (v3)\n")
                    f.write("=" * 80 + "\n\n")
                    
                    table_data = []
                    for rank, (_, r) in enumerate(game_players.iterrows(), 1):
                        prob = r["prob_anytime_td"]
                        odds = r["american_odds"]
                        table_data.append([
                            str(rank),
                            r["full_name"],
                            r["team"],
                            r["position"],
                            f"{prob:.1%}",
                            f"{odds:+.0f}" if odds > 0 else f"{odds:.0f}",
                        ])
                    
                    f.write(tabulate(
                        table_data,
                        headers=["Rank", "Player", "Team", "Pos", "TD Prob", "Odds"],
                        tablefmt="outline"
                    ))
                
                print(f"Generated game report: {filename}")
        except Exception as e:
            print(f"Warning: Could not generate game reports: {e}")
    
    print(f"\n{'='*60}")
    print("v3 Touchdown modeling complete!")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
