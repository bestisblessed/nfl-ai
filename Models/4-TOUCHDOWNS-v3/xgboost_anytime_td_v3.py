#!/usr/bin/env python3
"""
Train calibrated XGBoost classifiers for Anytime TD - v3
Enhanced version combining best of v1 and v2 with improvements.
"""

import os
import sys
import warnings
import pandas as pd
import numpy as np
from xgboost import XGBClassifier
from sklearn.metrics import roc_auc_score, log_loss, brier_score_loss
from tabulate import tabulate

warnings.filterwarnings('ignore', category=RuntimeWarning, module='sklearn')


def probability_to_american_odds(prob: float) -> float:
    prob = max(min(prob, 1 - 1e-10), 1e-10)
    if prob > 0.5:
        return -100.0 * (prob / (1.0 - prob))
    return 100.0 * ((1.0 - prob) / prob)


def get_feature_columns() -> list:
    windows = [2, 3, 5, 8, 12]
    base_feats = ["rush_att", "rush_yds", "targets", "rec", "rec_yds", "scoring_tds"]
    rolling = [f"{f}_rm{w}" for f in base_feats for w in windows]
    touches_rolling = [f"touches_rm{w}" for w in windows]
    td_rate_rolling = [f"td_rate_rm{w}" for w in windows]
    context = [
        "home_flag",
        "Offense",
        "Defense",
        "opp_offense",
        "opp_defense",
        "rz_td_pct",
        "rz_att_pg",
    ]
    additional = ["consecutive_td_rm3"]
    dynamic_team = ["td_scored_rolling", "td_allowed_rolling", "opp_td_scored_rolling", "opp_td_allowed_rolling"]
    all_features = rolling + touches_rolling + td_rate_rolling + context + additional + dynamic_team
    return all_features


def train_calibrated_xgb(X: pd.DataFrame, y: pd.Series, pos: str):
    pos_count = y.sum()
    neg_count = len(y) - pos_count
    scale_pos_weight = neg_count / pos_count if pos_count > 0 else 1.0

    base_model = XGBClassifier(
        objective="binary:logistic",
        eval_metric="logloss",
        n_estimators=500,
        max_depth=5,
        learning_rate=0.03,
        subsample=0.85,
        colsample_bytree=0.85,
        random_state=42,
        reg_alpha=0.1,
        reg_lambda=1.5,
        scale_pos_weight=scale_pos_weight,
        min_child_weight=3,
        gamma=0.1,
    )

    feature_cols = [c for c in X.columns if c not in ["season", "week"]]
    X_features = X[feature_cols]
    
    if "season" in X.columns and "week" in X.columns:
        df_with_y = X[["season", "week"]].copy()
        df_with_y["y"] = y.values
        df_with_y = df_with_y.sort_values(["season", "week"]).reset_index(drop=True)

        train_indices = []
        val_indices = []
        
        for season in sorted(df_with_y["season"].unique()):
            season_data = df_with_y[df_with_y["season"] == season]
            if len(season_data) < 10:
                train_indices.extend(season_data.index.tolist())
            else:
                split_idx = int(len(season_data) * 0.8)
                train_indices.extend(season_data.index[:split_idx].tolist())
                val_indices.extend(season_data.index[split_idx:].tolist())

        if len(val_indices) == 0:
            val_indices = train_indices[-int(len(train_indices) * 0.2):]
            train_indices = train_indices[:-int(len(train_indices) * 0.2)]

        X_train = X_features.iloc[train_indices]
        y_train = y.iloc[train_indices]
        X_val = X_features.iloc[val_indices]
        y_val = y.iloc[val_indices]
    else:
        from sklearn.model_selection import train_test_split
        X_train, X_val, y_train, y_val = train_test_split(X_features, y, test_size=0.2, stratify=y, random_state=42)

    base_model.fit(
        X_train, y_train,
        eval_set=[(X_val, y_val)],
        early_stopping_rounds=50,
        verbose=False
    )

    p_val_raw = base_model.predict_proba(X_val)[:, 1]
    p_val_raw = np.clip(p_val_raw, 0.01, 0.99)
    
    from sklearn.isotonic import IsotonicRegression
    iso_reg = IsotonicRegression(out_of_bounds='clip')
    iso_reg.fit(p_val_raw, y_val)
    p_val = iso_reg.predict(p_val_raw)
    p_val = np.clip(p_val, 0.01, 0.99)

    try:
        auc = roc_auc_score(y_val, p_val)
        ll = log_loss(y_val, p_val)
        brier = brier_score_loss(y_val, p_val)
        print(f"AUC: {auc:.4f} | LogLoss: {ll:.4f} | Brier: {brier:.4f} | n_val={len(y_val)}")
        metrics = pd.DataFrame([{"auc": auc, "logloss": ll, "brier": brier, "n_val": len(y_val)}])
    except Exception:
        metrics = pd.DataFrame([{"auc": np.nan, "logloss": np.nan, "brier": np.nan, "n_val": len(y_val)}])

    val_df = pd.DataFrame({"y": y_val.reset_index(drop=True), "p": p_val})
    return (base_model, iso_reg), metrics, val_df


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
        .tail(1)[["player_id"] + [c for c in feature_cols if c in train_df.columns]]
    )

    inf = upcoming_players.copy()
    inf = inf.merge(latest, on="player_id", how="left")

    rolling_cols = [c for c in feature_cols if c.endswith(tuple([f"rm{w}" for w in [2, 3, 5, 8, 12]]))]
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

    if "td_scored_rolling" in train_df.columns:
        latest_team_features = (
            train_df.sort_values(["team", "season", "week"])
            .groupby("team")
            .tail(1)[["team", "td_scored_rolling", "td_allowed_rolling"]]
        )
        inf = inf.merge(latest_team_features, on="team", how="left")
        
        latest_opp_features = (
            train_df.sort_values(["opp", "season", "week"])
            .groupby("opp")
            .tail(1)[["opp", "td_scored_rolling", "td_allowed_rolling"]]
            .rename(columns={"td_scored_rolling": "opp_td_scored_rolling", "td_allowed_rolling": "opp_td_allowed_rolling"})
        )
        inf = inf.merge(latest_opp_features, on="opp", how="left")

    inf[per_pos_opp_col] = inf["opp"].map(opp_rate_map)
    fallback = train_df[per_pos_opp_col].dropna().mean()
    inf[per_pos_opp_col] = inf[per_pos_opp_col].fillna(fallback)

    required_ctx = ["home_flag", "Offense", "Defense", "opp_offense", "opp_defense", "rz_td_pct", "rz_att_pg", per_pos_opp_col]
    for c in required_ctx:
        if c not in inf.columns:
            inf[c] = 0.0

    for c in ["td_scored_rolling", "td_allowed_rolling", "opp_td_scored_rolling", "opp_td_allowed_rolling"]:
        if c not in inf.columns:
            inf[c] = 0.0

    X_cols = [c for c in feature_cols + [per_pos_opp_col] if c in inf.columns]
    return inf, X_cols


def main():
    if len(sys.argv) < 2:
        print("Usage: python xgboost_anytime_td_v3.py <week_number>")
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

        feature_cols = get_feature_columns()
        X_cols_all = [c for c in feature_cols + [per_pos_col] if c in train_pos.columns]
        X = train_pos[X_cols_all].fillna(0.0)

        if X.empty or y.nunique() < 2:
            print(f"Skipping {pos}: insufficient training data.")
            continue

        X_with_meta = X.copy()
        if "season" in train_pos.columns:
            X_with_meta["season"] = train_pos["season"].values
        if "week" in train_pos.columns:
            X_with_meta["week"] = train_pos["week"].values
        
        (base_model, iso_reg), metrics_df, val_df = train_calibrated_xgb(X_with_meta, y, pos)

        up_pos = upcoming_players[upcoming_players["position"] == pos].copy()
        if up_pos.empty:
            print(f"No upcoming players found for position {pos}")
            continue
        inf_rows, X_cols = build_inference_rows(up_pos, train_pos, pos)
        probs_raw = base_model.predict_proba(inf_rows[X_cols].fillna(0.0))[:, 1]
        probs_raw = np.clip(probs_raw, 0.01, 0.99)
        probs = iso_reg.predict(probs_raw)
        probs = np.clip(probs, 0.001, 0.999)

        usage_cols = ["rush_att_rm3", "targets_rm3", "rec_rm3"]
        historical_touches = inf_rows[usage_cols].fillna(0).sum(axis=1)
        active_mask = historical_touches >= 1.5
        inf_rows = inf_rows[active_mask].copy()
        probs = probs[active_mask]

        if pos != "QB":
            season_cols = {
                "WR": "rec",
                "TE": "rec",
                "RB": "rush_att"
            }
            season_stat = season_cols.get(pos, "rec")
            if season_stat in train_df.columns:
                season_totals = train_df.groupby("player_id")[season_stat].sum().to_dict()
                active_mask = inf_rows["player_id"].map(season_totals).fillna(0) >= {
                    "WR": 3,
                    "TE": 2,
                    "RB": 4
                }[pos]
                inf_rows = inf_rows[active_mask].copy()
                probs = probs[active_mask]

        out = inf_rows[["full_name", "player_id", "team", "opp", "position", "home_flag"]].copy()
        out["prob_anytime_td"] = probs
        out["american_odds"] = out["prob_anytime_td"].apply(probability_to_american_odds).round(1)
        out["prop_type"] = "Anytime TD"
        out["model_version"] = "anytd_xgb_v3"
        out = out.sort_values("prob_anytime_td", ascending=False)
        all_outputs.append(out)

        out_file = f"{out_dir}/final_week{week_num}_{pos}_td_report.csv"
        out.to_csv(out_file, index=False)
        print(f"Saved: {out_file} ({len(out)} rows)")

        metrics_path = f"{out_dir}/metrics_{pos}.csv"
        metrics_df.to_csv(metrics_path, index=False)
        print(f"Wrote metrics: {metrics_path}")

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
                f.write(
                    tabulate(
                        table_data,
                        headers=["Rank", "Player", "Team", "Pos", "TD Prob", "Odds"],
                        tablefmt="outline",
                    )
                )
            print(f"Generated TD report: {filename_text}")

    print("\nAnytime TD modeling complete (4-TOUCHDOWNS-v3).")


if __name__ == "__main__":
    main()
