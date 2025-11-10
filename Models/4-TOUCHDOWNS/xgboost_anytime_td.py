#!/usr/bin/env python3
"""
Train calibrated XGBoost classifiers for Anytime TD:
- WR/RB/TE: rushing OR receiving TD
- QB: rushing TD only

Outputs:
- predictions-week-W-TD/final_weekW_anytime_td_report.csv (all positions)
- predictions-week-W-TD/final_weekW_{POS}_td_report.csv (per position)
- per-game TXT summaries in predictions-week-W-TD/
"""

import os
import sys
import warnings
import pandas as pd
import numpy as np
from xgboost import XGBClassifier
from sklearn.calibration import calibration_curve
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, log_loss
from tabulate import tabulate
import matplotlib.pyplot as plt

# Suppress sklearn numerical warnings during Platt scaling
warnings.filterwarnings('ignore', category=RuntimeWarning, module='sklearn')


def probability_to_american_odds(prob: float) -> float:
    prob = max(min(prob, 1 - 1e-10), 1e-10)
    if prob > 0.5:
        return -100.0 * (prob / (1.0 - prob))
    return 100.0 * ((1.0 - prob) / prob)

def temperature_scale(probs: np.ndarray, T: float) -> np.ndarray:
    """Shrink probabilities away from extremes via temperature scaling."""
    probs = np.clip(probs, 1e-6, 1 - 1e-6)
    logits = np.log(probs / (1.0 - probs))
    scaled = 1.0 / (1.0 + np.exp(-logits / T))
    return np.clip(scaled, 1e-6, 1 - 1e-6)

def get_feature_columns() -> list:
    windows = [3, 5, 8, 12]
    base_feats = ["rush_att", "rush_yds", "targets", "rec", "rec_yds", "scoring_tds"]
    rolling = [f"{f}_rm{w}" for f in base_feats for w in windows]
    context = [
        "home_flag",
        "Offense",
        "Defense",
        "opp_offense",
        "opp_defense",
        "rz_td_pct",
        "rz_att_pg",
    ]
    return rolling + context


def train_calibrated_xgb(X: pd.DataFrame, y: pd.Series):
    model = XGBClassifier(
        objective="binary:logistic",
        eval_metric="logloss",
        n_estimators=400,
        max_depth=4,
        learning_rate=0.05,
        subsample=0.9,
        colsample_bytree=0.9,
        random_state=42,
        reg_alpha=0.0,
        reg_lambda=1.0,
    )
    X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, stratify=y, random_state=42)
    # Fit base model
    model.fit(X_train, y_train)
    # Manual Platt scaling (logistic) on validation predictions
    p_val_raw = model.predict_proba(X_val)[:, 1]
    # Clip probabilities to tighter bounds to avoid numerical instability
    # Use 0.01-0.99 range instead of 1e-6 to avoid extreme logits
    p_val_raw = np.clip(p_val_raw, 0.01, 0.99)
    # Check for constant predictions (would cause fitting issues)
    if np.std(p_val_raw) < 1e-6:
        # If all predictions are nearly the same, use identity mapping
        platt = None
        p = p_val_raw
    else:
        # Use stronger regularization and liblinear solver (more stable for small datasets)
        platt = LogisticRegression(max_iter=1000, C=10.0, solver='liblinear', tol=1e-4)
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                platt.fit(p_val_raw.reshape(-1, 1), y_val)
                p = platt.predict_proba(p_val_raw.reshape(-1, 1))[:, 1]
            # Clip calibrated probabilities to safe range
            p = np.clip(p, 0.01, 0.99)
        except Exception:
            # Fallback to identity if Platt scaling fails
            platt = None
            p = p_val_raw
    try:
        auc = roc_auc_score(y_val, p)
        ll = log_loss(y_val, p)
        print(f"AUC: {auc:.4f} | LogLoss: {ll:.4f} | n_val={len(y_val)}")
        metrics = pd.DataFrame([{"auc": auc, "logloss": ll, "n_val": len(y_val)}])
    except Exception:
        metrics = pd.DataFrame([{"auc": np.nan, "logloss": np.nan, "n_val": len(y_val)}])
    val_df = pd.DataFrame({"y": y_val.reset_index(drop=True), "p": p})
    return model, platt, metrics, val_df


def build_inference_rows(upcoming_players: pd.DataFrame, train_df: pd.DataFrame, pos: str) -> pd.DataFrame:
    feature_cols = get_feature_columns()
    per_pos_opp_col = "opp_td_rate_pos" if pos in ["WR", "RB", "TE"] else "opp_td_rate_qb_rush"

    def latest_opp_rate_map(df: pd.DataFrame) -> pd.DataFrame:
        recent_season = df["season"].max()
        sub = df[df["season"] == recent_season][["season", "opp", per_pos_opp_col]].dropna()
        if sub.empty:
            sub = df[["season", "opp", per_pos_opp_col]].dropna()
        return sub.groupby(["opp"])[per_pos_opp_col].mean().to_dict()

    opp_rate_map = latest_opp_rate_map(train_df)

    latest = (
        train_df.sort_values(["player_id", "season", "week"])
        .groupby("player_id")
        .tail(1)[["player_id"] + feature_cols]
    )

    inf = upcoming_players.copy()
    inf = inf.merge(latest, on="player_id", how="left")

    rolling_cols = [c for c in feature_cols if c.endswith(tuple(["rm3", "rm5", "rm8", "rm12"]))]
    if rolling_cols:
        inf[rolling_cols] = inf[rolling_cols].fillna(0.0)

    team_ratings = (
        train_df.sort_values(["season"])
        .drop_duplicates(subset=["team"], keep="last")[["team", "Offense", "Defense", "rz_td_pct", "rz_att_pg"]]
    )
    opp_ratings = (
        train_df.sort_values(["season"])
        .drop_duplicates(subset=["opp"], keep="last")[["opp", "opp_offense", "opp_defense"]]
        .rename(columns={"opp": "opp_key"})
    )
    inf = inf.merge(team_ratings, on="team", how="left")
    inf = inf.merge(opp_ratings, left_on="opp", right_on="opp_key", how="left")
    inf = inf.drop(columns=["opp_key"])

    inf[per_pos_opp_col] = inf["opp"].map(opp_rate_map)
    fallback = train_df[per_pos_opp_col].dropna().mean()
    inf[per_pos_opp_col] = inf[per_pos_opp_col].fillna(fallback)

    # Ensure required context columns exist for inference (fill missing with 0)
    required_ctx = ["home_flag", "Offense", "Defense", "opp_offense", "opp_defense", "rz_td_pct", "rz_att_pg", per_pos_opp_col]
    for c in required_ctx:
        if c not in inf.columns:
            inf[c] = 0.0
    X_cols = feature_cols + [per_pos_opp_col]
    return inf, X_cols


def main():
    if len(sys.argv) < 2:
        print("Usage: python xgboost_anytime_td.py <week_number>")
        sys.exit(1)
    week_num = int(sys.argv[1])
    out_dir = f"predictions-week-{week_num}-TD"
    os.makedirs(out_dir, exist_ok=True)

    train_df = pd.read_csv("data/model_train.csv")
    upcoming_players = pd.read_csv("data/upcoming_players.csv")

    positions = ["WR", "RB", "TE", "QB"]
    all_outputs = []

    for pos in positions:
        print(f"\n=== Training {pos} model ===")
        if pos == "QB":
            train_pos = train_df[train_df["position"] == "QB"].copy()
            y = train_pos["label_qb_rush"].astype(int)
            per_pos_col = "opp_td_rate_qb_rush"
        else:
            train_pos = train_df[train_df["position"] == pos].copy()
            y = train_pos["label_any"].astype(int)
            per_pos_col = "opp_td_rate_pos"

        X_cols_all = get_feature_columns() + [per_pos_col]
        X = train_pos[X_cols_all].fillna(0.0)

        if X.empty or y.nunique() < 2:
            print(f"Skipping {pos}: insufficient training data.")
            continue

        model, platt, metrics_df, val_df = train_calibrated_xgb(X, y)

        up_pos = upcoming_players[upcoming_players["position"] == pos].copy()
        if up_pos.empty:
            print(f"No upcoming players found for position {pos}")
            continue
        inf_rows, X_cols = build_inference_rows(up_pos, train_pos, pos)
        probs_raw = model.predict_proba(inf_rows[X_cols].fillna(0.0))[:, 1]
        # Clip raw probabilities to same bounds as training
        probs_raw = np.clip(probs_raw, 0.01, 0.99)
        if platt is not None:
            try:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    probs = platt.predict_proba(probs_raw.reshape(-1, 1))[:, 1]
                probs = np.clip(probs, 0.01, 0.99)
            except Exception:
                probs = probs_raw
        else:
            probs = probs_raw

        # Position-specific temperature scaling, floors and caps for realism
        temp_map = {"WR": 1.8, "RB": 1.6, "TE": 1.9, "QB": 2.2}
        cap_map = {"WR": 0.45, "RB": 0.55, "TE": 0.35, "QB": 0.35}
        floor_map = {"WR": 0.015, "RB": 0.020, "TE": 0.010, "QB": 0.010}
        T = temp_map.get(pos, 1.8)
        probs = temperature_scale(probs, T)

        # For players with no recent usage history, use conservative floor
        usage_cols = [c for c in ["rush_att_rm3", "targets_rm3", "rec_rm3"] if c in inf_rows.columns]
        if usage_cols:
            usage_sum = inf_rows[usage_cols].fillna(0).sum(axis=1)
            no_usage_mask = usage_sum <= 0
        else:
            no_usage_mask = np.zeros(len(probs), dtype=bool)
        probs[no_usage_mask] = floor_map.get(pos, 0.015)

        # Soft-cap using per-position 99.5th percentile scaling to preserve variance
        cap = cap_map.get(pos, 0.5)
        floor = floor_map.get(pos, 0.015)
        q = np.quantile(probs, 0.995) if len(probs) > 10 else cap
        if q > 0:
            probs = probs * (cap / max(q, 1e-6))
        probs = np.clip(probs, floor, cap)

        out = inf_rows[["full_name", "player_id", "team", "opp", "position", "home_flag"]].copy()
        out["prob_anytime_td"] = probs
        out["american_odds"] = out["prob_anytime_td"].apply(probability_to_american_odds).round(1)
        out["prop_type"] = "Anytime TD"
        out["model_version"] = "anytd_xgb_v1"
        out = out.sort_values("prob_anytime_td", ascending=False)
        all_outputs.append(out)

        out_file = f"{out_dir}/final_week{week_num}_{pos}_td_report.csv"
        out.to_csv(out_file, index=False)
        print(f"Saved: {out_file} ({len(out)} rows)")

        metrics_path = f"{out_dir}/metrics_{pos}.csv"
        metrics_df.to_csv(metrics_path, index=False)
        print(f"Wrote metrics: {metrics_path}")

        # PNG calibration plots commented out
        # try:
        #     frac_pos, mean_pred = calibration_curve(val_df["y"], val_df["p"], n_bins=10, strategy="quantile")
        #     plt.figure(figsize=(4, 4))
        #     plt.plot([0, 1], [0, 1], "k--", label="Perfect")
        #     plt.plot(mean_pred, frac_pos, marker="o", label="Model")
        #     plt.xlabel("Predicted probability")
        #     plt.ylabel("Observed frequency")
        #     plt.title(f"Calibration - {pos}")
        #     plt.legend()
        #     plt.tight_layout()
        #     cal_path = f"{out_dir}/calibration_{pos}.png"
        #     plt.savefig(cal_path, dpi=150)
        #     plt.close()
        #     print(f"Wrote calibration plot: {cal_path}")
        # except Exception as e:
        #     print(f"Calibration plot failed for {pos}: {e}")

    if all_outputs:
        all_df = pd.concat(all_outputs, ignore_index=True)
        all_csv = f"{out_dir}/final_week{week_num}_anytime_td_report.csv"
        all_df.to_csv(all_csv, index=False)
        print(f"\nSaved combined report: {all_csv} ({len(all_df)} rows)")

        upcoming = pd.read_csv("data/upcoming_games.csv")
        games = []
        seen = set()
        for _, row in upcoming.iterrows():
            g = tuple(sorted([row["home_team"], row["away_team"]]))
            if g not in seen:
                seen.add(g)
                games.append((row["home_team"], row["away_team"]))

        for i, (home, away) in enumerate(games, 1):
            game_players = all_df[
                ((all_df["team"] == home) & (all_df["opp"] == away))
                | ((all_df["team"] == away) & (all_df["opp"] == home))
            ].copy()
            if game_players.empty:
                continue
            game_players = game_players.sort_values("prob_anytime_td", ascending=False)

            filename_text = f"{out_dir}/game_{i:02d}_{home}_vs_{away}_td_predictions.txt"
            with open(filename_text, "w") as f:
                f.write("=" * 80 + "\n")
                f.write(f"{home} vs {away} | Week {week_num} 2025 | Anytime TD Probabilities\n")
                f.write("=" * 80 + "\n\n")
                top_12 = game_players.head(12)
                table_data = []
                for _, r in top_12.iterrows():
                    prob = r["prob_anytime_td"]
                    odds = r["american_odds"]
                    table_data.append(
                        [
                            r["full_name"],
                            r["team"],
                            r["position"],
                            f"{prob:.1%}",
                            f"{odds:+.0f}" if odds > 0 else f"{odds:.0f}",
                        ]
                    )
                f.write(
                    tabulate(
                        table_data,
                        headers=["Player", "Team", "Pos", "TD Prob", "Odds"],
                        tablefmt="outline",
                    )
                )
            print(f"Generated TD report: {filename_text}")

            # PNG per-game charts commented out
            # chart = game_players.head(10)[["full_name", "prob_anytime_td"]].iloc[::-1]
            # plt.figure(figsize=(8, 5))
            # plt.barh(chart["full_name"], chart["prob_anytime_td"] * 100.0, color="#2d6cdf")
            # plt.xlabel("Anytime TD Probability (%)")
            # plt.title(f"Week {week_num} {home} vs {away} - Top 10 TD Probabilities")
            # plt.tight_layout()
            # png_file = f"{out_dir}/game_{i:02d}_{home}_vs_{away}_td_predictions.png"
            # plt.savefig(png_file, dpi=150)
            # plt.close()
            # print(f"Wrote chart: {png_file}")

    print("\nAnytime TD modeling complete (4-TOUCHDOWNS).")


if __name__ == "__main__":
    main()


