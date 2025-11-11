#!/usr/bin/env python3

import os
import sys
import warnings
import pandas as pd
import numpy as np
from xgboost import XGBClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, log_loss
from tabulate import tabulate

warnings.filterwarnings("ignore", category=RuntimeWarning, module="sklearn")


def probability_to_american_odds(prob: float) -> float:
    prob = max(min(prob, 1 - 1e-10), 1e-10)
    if prob > 0.5:
        return -100.0 * (prob / (1.0 - prob))
    return 100.0 * ((1.0 - prob) / prob)


def get_feature_columns() -> list:
    windows = [3, 5, 8, 12]
    base = [
        "rush_att",
        "rush_yds",
        "targets",
        "rec",
        "rec_yds",
        "scoring_tds",
        "touches",
        "fantasy_points_ppr",
        "yards_from_scrimmage",
    ]
    rolling = [f"{f}_rm{w}" for f in base for w in windows]
    trend = ["games_played", "season_tds_to_date", "season_touches_to_date"]
    context = [
        "home_flag",
        "Offense",
        "Defense",
        "opp_offense",
        "opp_defense",
        "rz_td_pct",
        "rz_att_pg",
    ]
    return rolling + trend + context


def train_calibrated_xgb(X: pd.DataFrame, y: pd.Series):
    scale_pos_weight = ((len(y) - y.sum()) / y.sum()) if y.sum() > 0 else 1.0
    model = XGBClassifier(
        objective="binary:logistic",
        eval_metric="logloss",
        n_estimators=500,
        learning_rate=0.06,
        max_depth=4,
        min_child_weight=3,
        subsample=0.9,
        colsample_bytree=0.9,
        reg_lambda=1.0,
        reg_alpha=0.1,
        gamma=0.1,
        random_state=42,
        n_jobs=4,
        scale_pos_weight=scale_pos_weight,
    )
    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=0.25, stratify=y, random_state=42
    )
    model.fit(
        X_train,
        y_train,
        eval_set=[(X_val, y_val)],
        verbose=False,
        early_stopping_rounds=30,
    )
    p_val_raw = model.predict_proba(X_val)[:, 1]
    p_val_raw = np.clip(p_val_raw, 0.01, 0.99)
    if np.std(p_val_raw) < 1e-6:
        platt = None
        p_val = p_val_raw
    else:
        platt = LogisticRegression(max_iter=1000, C=5.0, solver="liblinear", tol=1e-4)
        platt.fit(p_val_raw.reshape(-1, 1), y_val)
        p_val = platt.predict_proba(p_val_raw.reshape(-1, 1))[:, 1]
        p_val = np.clip(p_val, 0.01, 0.99)
    auc = roc_auc_score(y_val, p_val)
    ll = log_loss(y_val, p_val)
    metrics = pd.DataFrame(
        [{"auc": auc, "logloss": ll, "n_val": len(y_val), "pos_rate": y_val.mean()}]
    )
    val_df = pd.DataFrame({"y": y_val.reset_index(drop=True), "p": p_val})
    feature_importance = pd.DataFrame(
        {
            "feature": X.columns,
            "importance": model.feature_importances_,
        }
    ).sort_values("importance", ascending=False)
    return model, platt, metrics, val_df, feature_importance


def build_inference_rows(
    upcoming_players: pd.DataFrame,
    train_df: pd.DataFrame,
    pos: str,
    feature_cols: list,
    per_pos_col: str,
) -> tuple[pd.DataFrame, list]:
    latest = (
        train_df.sort_values(["player_id", "season", "week"])
        .groupby("player_id")
        .tail(1)[["player_id"] + feature_cols + [per_pos_col]]
    )
    inf = upcoming_players.merge(latest, on="player_id", how="left")

    inf[feature_cols] = inf[feature_cols].fillna(0.0)
    fallback_map = train_df[per_pos_col].dropna()
    fallback_value = fallback_map.mean() if not fallback_map.empty else 0.1
    inf[per_pos_col] = inf[per_pos_col].fillna(fallback_value)

    team_context = (
        train_df.groupby("team")[["Offense", "Defense", "rz_td_pct", "rz_att_pg"]]
        .median()
        .rename_axis("team")
    )
    opp_context = (
        train_df.groupby("opp")[["opp_offense", "opp_defense"]]
        .median()
        .rename_axis("opp")
    )

    for col in ["Offense", "Defense", "rz_td_pct", "rz_att_pg"]:
        inf[col] = inf[col].fillna(inf["team"].map(team_context[col]))
    for col in ["opp_offense", "opp_defense"]:
        inf[col] = inf[col].fillna(inf["opp"].map(opp_context[col]))

    inf["usage_last3"] = inf["touches_rm3"]
    inf["fantasy_last3"] = inf["fantasy_points_ppr_rm3"]
    inf["season_tds"] = inf["season_tds_to_date"]

    use_cols = feature_cols + [per_pos_col]
    return inf, use_cols


def add_confidence(prob: float) -> str:
    if prob >= 0.35:
        return "A"
    if prob >= 0.25:
        return "B"
    if prob >= 0.18:
        return "C"
    return "Watch"


def main():
    if len(sys.argv) < 2:
        print("Usage: python train_model.py <week_number>")
        sys.exit(1)
    week_num = int(sys.argv[1])
    out_dir = f"predictions-week-{week_num}-TD"
    os.makedirs(out_dir, exist_ok=True)

    train_df = pd.read_csv("data/model_train_v3.csv")
    upcoming_players = pd.read_csv("data/upcoming_players_v3.csv")

    positions = ["WR", "RB", "TE", "QB"]
    feature_cols = get_feature_columns()

    all_outputs = []
    metrics_frames = []
    feature_frames = []

    for pos in positions:
        print(f"\n=== Training {pos} model (v3) ===")
        if pos == "QB":
            train_pos = train_df[train_df["position"] == "QB"].copy()
            y = train_pos["label_qb_rush"].astype(int)
            per_pos_col = "opp_td_rate_qb_rush"
        else:
            train_pos = train_df[train_df["position"] == pos].copy()
            y = train_pos["label_any"].astype(int)
            per_pos_col = "opp_td_rate_pos"

        X = train_pos[feature_cols + [per_pos_col]].fillna(0.0)

        if X.empty or y.nunique() < 2:
            print(f"Skipping {pos}: insufficient data.")
            continue

        model, platt, metrics_df, val_df, feature_importance = train_calibrated_xgb(X, y)
        metrics_df["position"] = pos
        metrics_frames.append(metrics_df)
        feature_importance["position"] = pos
        feature_frames.append(feature_importance)

        up_pos = upcoming_players[upcoming_players["position"] == pos].copy()
        if up_pos.empty:
            print(f"No upcoming players found for {pos}.")
            continue
        inf_rows, use_cols = build_inference_rows(up_pos, train_pos, pos, feature_cols, per_pos_col)
        probs_raw = model.predict_proba(inf_rows[use_cols].fillna(0.0))[:, 1]
        probs_raw = np.clip(probs_raw, 0.001, 0.999)
        if platt is not None:
            probs = platt.predict_proba(probs_raw.reshape(-1, 1))[:, 1]
        else:
            probs = probs_raw

        active_mask = inf_rows["usage_last3"].fillna(0.0) >= 1.5
        inf_rows = inf_rows[active_mask].copy()
        probs = probs[active_mask.values]

        if pos != "QB":
            season_totals = train_df.groupby("player_id")["season_touches_to_date"].max()
            inf_rows["season_touch_total"] = inf_rows["player_id"].map(season_totals).fillna(0.0)
            min_touches = {"WR": 4, "TE": 4, "RB": 6}[pos]
            touch_mask = inf_rows["season_touch_total"] >= min_touches
            inf_rows = inf_rows[touch_mask].copy()
            probs = probs[touch_mask.values]

        out = inf_rows[
            [
                "full_name",
                "player_id",
                "team",
                "opp",
                "position",
                "home_flag",
                "usage_last3",
                "fantasy_last3",
                "season_tds",
            ]
        ].copy()
        out["prob_anytime_td"] = probs
        out["american_odds"] = out["prob_anytime_td"].apply(probability_to_american_odds).round(1)
        out["confidence_tier"] = out["prob_anytime_td"].apply(add_confidence)
        out["model_version"] = "anytd_xgb_v3"
        out = out.sort_values("prob_anytime_td", ascending=False)
        out_file = f"{out_dir}/final_week{week_num}_{pos}_td_report.csv"
        out.to_csv(out_file, index=False)
        print(f"Saved: {out_file} ({len(out)} rows)")
        all_outputs.append(out)

        metrics_path = f"{out_dir}/metrics_{pos}.csv"
        metrics_df.to_csv(metrics_path, index=False)
        print(f"Wrote metrics: {metrics_path}")

        feat_path = f"{out_dir}/feature_importance_{pos}.csv"
        feature_importance.to_csv(feat_path, index=False)
        print(f"Wrote feature importance: {feat_path}")

    if all_outputs:
        combined = pd.concat(all_outputs, ignore_index=True)
        combined = combined.sort_values("prob_anytime_td", ascending=False)
        combined["rank"] = range(1, len(combined) + 1)
        combined_csv = f"{out_dir}/final_week{week_num}_anytime_td_report.csv"
        combined.to_csv(combined_csv, index=False)
        print(f"\nSaved combined report: {combined_csv} ({len(combined)} rows)")

        upcoming_games = pd.read_csv("data/upcoming_games.csv")
        games = []
        seen = set()
        for _, row in upcoming_games.iterrows():
            game_key = tuple(sorted([row["home_team"], row["away_team"]]))
            if game_key in seen:
                continue
            seen.add(game_key)
            games.append((row["home_team"], row["away_team"]))

        for idx, (home, away) in enumerate(games, 1):
            game_players = combined[
                ((combined["team"] == home) & (combined["opp"] == away))
                | ((combined["team"] == away) & (combined["opp"] == home))
            ].copy()
            if game_players.empty:
                continue
            game_players = game_players.sort_values("prob_anytime_td", ascending=False)
            filename_text = f"{out_dir}/game_{idx:02d}_{home}_vs_{away}_td_predictions.txt"
            lines = ["=" * 96]
            lines.append(f"{home} vs {away} | Week {week_num} 2025 | Anytime TD Probabilities (v3)")
            lines.append("=" * 96)
            lines.append("")
            table_rows = []
            for rank, (_, row) in enumerate(game_players.iterrows(), 1):
                odds = row["american_odds"]
                odds_str = f"{odds:+.0f}" if odds > 0 else f"{odds:.0f}"
                table_rows.append(
                    [
                        f"{rank}",
                        row["full_name"],
                        row["team"],
                        row["position"],
                        f"{row['prob_anytime_td']:.1%}",
                        odds_str,
                        f"{row['usage_last3']:.2f}",
                        f"{row['fantasy_last3']:.2f}",
                        row["confidence_tier"],
                    ]
                )
            lines.append(
                tabulate(
                    table_rows,
                    headers=[
                        "Rank",
                        "Player",
                        "Team",
                        "Pos",
                        "TD Prob",
                        "Odds",
                        "Touches L3",
                        "FPTS L3",
                        "Tier",
                    ],
                    tablefmt="outline",
                )
            )
            with open(filename_text, "w") as f:
                f.write("\n".join(lines))
            print(f"Generated TD report: {filename_text}")

    if metrics_frames:
        metrics_all = pd.concat(metrics_frames, ignore_index=True)
        metrics_all.to_csv(f"{out_dir}/validation_metrics.csv", index=False)
    if feature_frames:
        feature_all = pd.concat(feature_frames, ignore_index=True)
        feature_all.to_csv(f"{out_dir}/feature_importance_all.csv", index=False)

    print("\nAnytime TD modeling complete (v3).")


if __name__ == "__main__":
    main()

