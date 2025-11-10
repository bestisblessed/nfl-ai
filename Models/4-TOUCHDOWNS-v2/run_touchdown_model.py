"""
Script to train a touchdown‑prediction model and generate predictions for
upcoming games.  The model uses player statistics from Pro Football
Reference (PFR), team game logs and roster data to compute rolling
features and then fits an XGBoost classifier.  It outputs touchdown
probabilities and their implied American moneyline odds for each
player in the upcoming slate.

Assumptions:

* The PFR data is stored in a folder called ``final_data_pfr``
  containing at least ``player_stats_pfr.csv`` and ``game_logs_pfr.csv``.
* Roster data is in ``data/rosters.csv``.  It is used to filter
  players by position and activity in the current season.
* The upcoming matchups are defined in ``upcoming_games.csv`` with
  columns ``home_team`` and ``away_team``.

Example usage::

    python run_touchdown_model.py 10

This will train the model on historical data up to (but not including)
week 10 of the 2025 season and then output predictions for the
Week 10 matchups listed in ``upcoming_games.csv``.  The results are
written to ``td_predictions.csv`` in the current working directory.
"""

from __future__ import annotations

import argparse
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
from xgboost import XGBClassifier

# Suppress pandas FutureWarning about downcasting
pd.set_option('future.no_silent_downcasting', True)


def load_rosters(rosters_path: str, target_season: int) -> Dict[Tuple[str, str], str]:
    """Return a mapping from (player_name, team) to position for a given season.

    The roster file should contain at least the columns ``season``, ``team`` and
    ``full_name``.  Player names are cleaned (lower‑cased and stripped of
    leading/trailing whitespace) for matching.
    """
    rosters = pd.read_csv(rosters_path)
    season_rosters = rosters[rosters["season"] == target_season].copy()
    season_rosters["full_name_clean"] = season_rosters["full_name"].astype(str).str.strip().str.lower()
    position_map: Dict[Tuple[str, str], str] = {}
    for _, row in season_rosters.iterrows():
        key = (row["full_name_clean"], row["team"])
        position_map[key] = row["position"]
    return position_map


def assign_positions(player_stats: pd.DataFrame, position_map: Dict[Tuple[str, str], str]) -> pd.DataFrame:
    """Annotate the player_stats DataFrame with a ``position`` column using a mapping.

    Players whose names and teams are not present in the mapping will have an
    empty string as their position.
    """
    def get_position(row):
        key = (str(row["player"]).strip().lower(), row["team"])
        return position_map.get(key, "")

    player_stats = player_stats.copy()
    player_stats["position"] = player_stats.apply(get_position, axis=1)
    return player_stats


def prepare_team_features(
    game_logs: pd.DataFrame,
    upcoming_games: pd.DataFrame,
    upcoming_season: int,
    upcoming_week: int,
    rolling_window: int = 3,
) -> pd.DataFrame:
    """Compute rolling team offensive/defensive features.

    This function parses the ``game_logs`` table (with a ``game_id`` field
    like ``2025_02_DEN_CLE``) to extract season/week, home/away teams and
    touchdowns/points scored and allowed.  It then appends placeholder
    rows for the upcoming week so that rolling features include week‑to‑date
    data.  Finally, it calculates rolling averages (window = ``rolling_window``)
    and expanding season averages for each team.  The returned DataFrame
    contains one row per team per game with columns for the rolling
    features and a ``games_played_prior`` count.
    """
    logs = game_logs.copy()
    parts = logs["game_id"].str.split("_", expand=True)
    logs["season"] = parts[0].astype(int)
    logs["week"] = parts[1].astype(int)
    logs["away_team"] = parts[2]
    logs["home_team"] = parts[3]

    # compute touchdowns and points for home and away teams
    logs["home_td_scored"] = logs["home_pass_td"].fillna(0) + logs["home_rush_td"].fillna(0)
    logs["away_td_scored"] = logs["away_pass_td"].fillna(0) + logs["away_rush_td"].fillna(0)
    logs["home_td_allowed"] = logs["away_td_scored"]
    logs["away_td_allowed"] = logs["home_td_scored"]
    logs["home_pts"] = logs["home_pts_off"].fillna(0)
    logs["away_pts"] = logs["away_pts_off"].fillna(0)

    # build home and away rows
    home_rows = logs[[
        "season",
        "week",
        "home_team",
        "home_td_scored",
        "home_td_allowed",
        "home_pts",
        "away_pts",
    ]].rename(
        columns={
            "home_team": "team",
            "home_td_scored": "td_scored",
            "home_td_allowed": "td_allowed",
            "home_pts": "pts_scored",
            "away_pts": "pts_allowed",
        }
    )
    away_rows = logs[[
        "season",
        "week",
        "away_team",
        "away_td_scored",
        "away_td_allowed",
        "away_pts",
        "home_pts",
    ]].rename(
        columns={
            "away_team": "team",
            "away_td_scored": "td_scored",
            "away_td_allowed": "td_allowed",
            "away_pts": "pts_scored",
            "home_pts": "pts_allowed",
        }
    )
    team_games = pd.concat([home_rows, away_rows], ignore_index=True)
    team_games.sort_values(["team", "season", "week"], inplace=True)
    team_games.reset_index(drop=True, inplace=True)

    # append placeholder rows for the upcoming week
    placeholders: List[pd.Series] = []
    for team in sorted(set(upcoming_games["home_team"]) | set(upcoming_games["away_team"])):
        recent = team_games[(team_games["team"] == team) & (team_games["season"] == upcoming_season)]
        if recent.empty:
            continue
        template = recent.iloc[-1].copy()
        template["season"] = upcoming_season
        template["week"] = upcoming_week
        for col in ["td_scored", "td_allowed", "pts_scored", "pts_allowed"]:
            template[col] = np.nan
        template["is_placeholder"] = True
        placeholders.append(template)
    if placeholders:
        placeholder_df = pd.DataFrame(placeholders)
        team_games = pd.concat([team_games, placeholder_df], ignore_index=True)
    team_games.sort_values(["team", "season", "week"], inplace=True)
    team_games["is_placeholder"] = team_games.get("is_placeholder", False)

    # compute rolling and expanding averages
    grouped = team_games.groupby(["team", "season"], group_keys=False)
    for col in ["td_scored", "td_allowed", "pts_scored", "pts_allowed"]:
        rolling = grouped[col].apply(lambda s: s.shift().rolling(window=rolling_window, min_periods=1).mean())
        expanding = grouped[col].apply(lambda s: s.shift().expanding().mean())
        feature = rolling.fillna(expanding)
        feature = feature.fillna(team_games[col].mean())
        team_games[f"{col}_feature"] = feature
    team_games["games_played_prior"] = grouped.cumcount()
    return team_games


def create_player_placeholders(
    player_stats: pd.DataFrame,
    upcoming_games: pd.DataFrame,
    upcoming_season: int,
    upcoming_week: int,
) -> pd.DataFrame:
    """Append placeholder rows for each player in the upcoming schedule.

    For each upcoming game, the latest stats for each player on the teams involved
    are copied forward to the upcoming week.  Numeric statistics are set to NaN so
    rolling features only use historical data, but categorical fields (player
    name, team, position) are preserved.  A boolean ``is_placeholder`` column
    marks these rows.
    """
    placeholders: List[pd.Series] = []
    numeric_cols = player_stats.select_dtypes(include=["number"]).columns.tolist()
    for _, game in upcoming_games.iterrows():
        home_team = game["home_team"]
        away_team = game["away_team"]
        game_id = f"{upcoming_season}_{upcoming_week:02d}_{away_team}_{home_team}"
        for team, home_flag in [(home_team, "y"), (away_team, "n")]:
            prior_games = player_stats[
                (player_stats["season"] == upcoming_season)
                & (player_stats["week"] < upcoming_week)
                & (player_stats["team"] == team)
            ]
            if prior_games.empty:
                continue
            latest_by_player = (
                prior_games.sort_values(["player", "week"]).groupby("player").tail(1)
            )
            for _, row in latest_by_player.iterrows():
                placeholder = row.copy()
                placeholder["week"] = upcoming_week
                placeholder["season"] = upcoming_season
                placeholder["game_id"] = game_id
                placeholder["home"] = home_flag
                placeholder["home_team"] = home_team
                placeholder["away_team"] = away_team
                placeholder["opponent_team"] = away_team if team == home_team else home_team
                placeholder["is_placeholder"] = True
                for col in numeric_cols:
                    if col not in {"season", "week"}:
                        placeholder[col] = np.nan
                placeholders.append(placeholder)
    if not placeholders:
        return player_stats.assign(is_placeholder=False)
    placeholder_df = pd.DataFrame(placeholders)
    player_stats = pd.concat([player_stats, placeholder_df], ignore_index=True)
    player_stats.sort_values(["player", "season", "week"], inplace=True)
    player_stats["is_placeholder"] = player_stats.get("is_placeholder", False).fillna(False).astype(bool)
    return player_stats


def compute_player_features(
    player_stats: pd.DataFrame,
    team_features: pd.DataFrame,
    rolling_window: int = 3,
) -> Tuple[pd.DataFrame, List[str]]:
    """Compute rolling player‑level features and merge team context.

    Returns the DataFrame with new feature columns and a list of column names to
    be used for model training.
    """
    base_stats = [
        "rush_att",
        "rush_yds",
        "rush_long",
        "targets",
        "rec",
        "rec_yds",
        "rec_long",
        "fantasy_points_ppr",
    ]
    data = player_stats.copy()
    # ensure numeric stats are zero‑filled for computing touches/TDs
    data[["rush_td", "rec_td"]] = data[["rush_td", "rec_td"]].fillna(0)
    data[["rush_att", "targets", "rec"]] = data[["rush_att", "targets", "rec"]].fillna(0)
    data["total_tds"] = data["rush_td"] + data["rec_td"]
    data["touches"] = data["rush_att"] + data["targets"] + data["rec"]

    grouped = data.groupby(["player", "season"], group_keys=False)
    for stat in base_stats + ["touches", "total_tds"]:
        data[f"{stat}_rolling"] = grouped[stat].apply(
            lambda s: s.shift().rolling(window=rolling_window, min_periods=1).mean()
        )
        data[f"{stat}_season_avg"] = grouped[stat].apply(lambda s: s.shift().expanding().mean())
    data["games_played_prior"] = grouped.cumcount()
    data["is_home"] = (data["home"].str.lower() == "y").astype(int)
    data["scored_td"] = (data["total_tds"] > 0).astype(int)

    # merge team and opponent features
    def merge_team_features(
        df: pd.DataFrame,
        team_feats: pd.DataFrame,
        suffix: str,
        team_col: str,
    ) -> pd.DataFrame:
        merge_cols = [
            "season",
            "week",
            team_col,
            "td_scored_feature",
            "td_allowed_feature",
            "pts_scored_feature",
            "pts_allowed_feature",
            "games_played_prior",
            "is_placeholder",
        ]
        tf = team_feats[merge_cols]
        tf = tf.rename(
            columns={
                "td_scored_feature": f"{suffix}_td_scored_feature",
                "td_allowed_feature": f"{suffix}_td_allowed_feature",
                "pts_scored_feature": f"{suffix}_pts_scored_feature",
                "pts_allowed_feature": f"{suffix}_pts_allowed_feature",
                "games_played_prior": f"{suffix}_games_played_prior",
                "is_placeholder": f"{suffix}_row_is_placeholder",
            }
        )
        return df.merge(tf, on=["season", "week", team_col], how="left")

    # own team features
    data = merge_team_features(data, team_features, "team", "team")
    # opponent features (rename team to opponent_team)
    opp_feats = team_features.rename(columns={"team": "opponent_team"})
    data = merge_team_features(data, opp_feats, "opp", "opponent_team")

    feature_columns: List[str] = []
    for stat in base_stats + ["touches"]:
        feature_columns.append(f"{stat}_rolling")
    feature_columns.extend([
        "total_tds_rolling",
        "total_tds_season_avg",
        "games_played_prior",
        "is_home",
        "team_td_scored_feature",
        "team_td_allowed_feature",
        "team_pts_scored_feature",
        "team_pts_allowed_feature",
        "opp_td_scored_feature",
        "opp_td_allowed_feature",
        "opp_pts_scored_feature",
        "opp_pts_allowed_feature",
    ])
    # fill missing numeric values with 0
    data[feature_columns] = data[feature_columns].fillna(0.0)
    return data, feature_columns


def probability_to_american_odds(probability: float) -> float:
    """Convert a win probability (0–1) to American odds.

    Negative odds indicate the outcome is favored (probability >= 0.5).
    """
    eps = 1e-9
    probability = float(np.clip(probability, eps, 1 - eps))
    if probability >= 0.5:
        return -100.0 * probability / (1.0 - probability)
    return 100.0 * (1.0 - probability) / probability


def main():
    parser = argparse.ArgumentParser(description="Train touchdown model and predict upcoming TD scorers for 2025 season.")
    parser.add_argument(
        "--player-stats-path",
        default="../../Scrapers/final_data_pfr/player_stats_pfr.csv",
        help="Path to player_stats_pfr.csv",
    )
    parser.add_argument(
        "--game-logs-path",
        default="../../Scrapers/final_data_pfr/game_logs_pfr.csv",
        help="Path to game_logs_pfr.csv",
    )
    parser.add_argument(
        "--rosters-path",
        default="../data/rosters.csv",
        help="Path to rosters.csv",
    )
    parser.add_argument(
        "--upcoming-games-path",
        default="../upcoming_games.csv",
        help="Path to upcoming_games.csv",
    )
    parser.add_argument(
        "upcoming_week",
        type=int,
        help="Week number (e.g. 10) for the upcoming games",
    )
    parser.add_argument(
        "--output-path",
        default="td_predictions.csv",
        help="Where to write the predictions CSV",
    )
    args = parser.parse_args()

    # Hardcoded season
    upcoming_season = 2025

    # Load data
    print(f"Loading player stats from {args.player_stats_path}…")
    player_stats = pd.read_csv(args.player_stats_path)
    print(f"Loading game logs from {args.game_logs_path}…")
    game_logs = pd.read_csv(args.game_logs_path)
    print(f"Loading rosters from {args.rosters_path}…")
    rosters = pd.read_csv(args.rosters_path)
    print(f"Loading upcoming games from {args.upcoming_games_path}…")
    upcoming_games = pd.read_csv(args.upcoming_games_path)

    # Assign positions
    position_map = load_rosters(args.rosters_path, upcoming_season)
    player_stats = assign_positions(player_stats, position_map)

    # Filter player_stats to meaningful touches and active 2025 players
    # require at least two touches per game
    player_stats[["rush_att", "targets", "rec"]] = player_stats[["rush_att", "targets", "rec"]].fillna(0)
    player_stats["meaningful_touches"] = player_stats[["rush_att", "targets", "rec"]].sum(axis=1)
    player_stats = player_stats[player_stats["meaningful_touches"] >= 2].copy()
    # filter to active players in the target season: 10+ pass attempts OR 3+ targets OR 3+ rush attempts
    ps_target = player_stats[player_stats["season"] == upcoming_season]
    player_activity = ps_target.groupby("player")[["pass_att", "targets", "rush_att"]].sum().fillna(0)
    active_players = player_activity[
        (player_activity["pass_att"] >= 10)
        | (player_activity["targets"] >= 3)
        | (player_activity["rush_att"] >= 3)
    ].index
    player_stats = player_stats[player_stats["player"].isin(active_players)]

    # clean season/week
    player_stats = player_stats[player_stats["season"].notna()]
    player_stats["season"] = player_stats["season"].astype(int)
    player_stats["week"] = player_stats["week"].astype(int)
    player_stats["opponent_team"] = player_stats["opponent_team"].fillna("")
    player_stats["home"] = player_stats["home"].fillna("n")
    player_stats["team"] = player_stats["team"].fillna("")
    player_stats["home_team"] = player_stats["home_team"].fillna("")
    player_stats["away_team"] = player_stats["away_team"].fillna("")

    # Prepare team features and append placeholders
    team_features = prepare_team_features(
        game_logs,
        upcoming_games,
        upcoming_season=upcoming_season,
        upcoming_week=args.upcoming_week,
    )
    # Append player placeholders
    player_stats_with_placeholders = create_player_placeholders(
        player_stats,
        upcoming_games,
        upcoming_season=upcoming_season,
        upcoming_week=args.upcoming_week,
    )
    # Compute player features and merge team context
    player_features, feature_columns = compute_player_features(
        player_stats_with_placeholders,
        team_features,
    )

    # Filter model‑ready rows: at least one prior game and have an opponent team
    model_ready = player_features[
        (player_features["games_played_prior"] >= 1)
        & (player_features["opponent_team"].ne(""))
    ].copy()
    # Train on historical data (seasons < upcoming or weeks < upcoming week)
    train = model_ready[
        (~model_ready["is_placeholder"])
        & (
            (model_ready["season"] < upcoming_season)
            | (
                (model_ready["season"] == upcoming_season)
                & (model_ready["week"] < args.upcoming_week)
            )
        )
    ]
    upcoming_df = model_ready[model_ready["is_placeholder"]].copy()

    X_train = train[feature_columns]
    y_train = train["scored_td"]
    # handle class imbalance
    pos_count = y_train.sum()
    neg_count = len(y_train) - pos_count
    scale_pos_weight = neg_count / pos_count if pos_count > 0 else 1
    model = XGBClassifier(
        n_estimators=150,
        learning_rate=0.1,
        max_depth=4,
        subsample=0.8,
        colsample_bytree=0.8,
        objective="binary:logistic",
        eval_metric="logloss",
        n_jobs=4,
        scale_pos_weight=scale_pos_weight,
    )
    print("Training model…")
    model.fit(X_train, y_train)
    print("Training complete.")

    # Predict on upcoming rows
    X_up = upcoming_df[feature_columns]
    probas = model.predict_proba(X_up)[:, 1]
    upcoming_df["pred_prob"] = probas
    upcoming_df["implied_odds"] = [probability_to_american_odds(p) for p in probas]

    # Sort predictions by probability descending
    upcoming_sorted = upcoming_df.sort_values("pred_prob", ascending=False)
    # Write results
    output_cols = ["player", "team", "opponent_team", "pred_prob", "implied_odds"]
    upcoming_sorted[output_cols].to_csv(args.output_path, index=False)
    print(f"Wrote {len(upcoming_sorted)} predictions to {args.output_path}.")

    # Display top predictions
    print("Top 10 projected TD scorers:")
    print(upcoming_sorted[output_cols].head(10).to_string(index=False))


if __name__ == "__main__":
    main()