"""Utilities for preparing touchdown prediction datasets."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd


DATA_DIR = "/Users/td/Code/nfl-ai/Models/IN-PROGRESS/touchdown_models/data/final_data_pfr"
UPCOMING_GAMES_PATH = "/Users/td/Code/nfl-ai/Models/upcoming_games.csv"


BASE_STATS = [
    "rush_att",
    "rush_yds",
    "rush_long",
    "targets",
    "rec",
    "rec_yds",
    "rec_long",
    "fantasy_points_ppr",
]
TD_COLUMNS = ["rush_td", "rec_td"]
ROLLING_WINDOW = 3


@dataclass
class DatasetBundle:
    """Container for model-ready datasets."""

    feature_columns: List[str]
    train: pd.DataFrame
    validation: pd.DataFrame
    upcoming: pd.DataFrame


def probability_to_american_odds(probability: float) -> float:
    """Convert a win probability (0-1) to American odds."""

    eps = 1e-9
    probability = float(np.clip(probability, eps, 1 - eps))
    if probability >= 0.5:
        return -100.0 * probability / (1.0 - probability)
    return 100.0 * (1.0 - probability) / probability


def _load_raw_data(data_dir: str | None = None) -> Tuple[pd.DataFrame, pd.DataFrame]:
    data_dir = data_dir or DATA_DIR
    player_stats = pd.read_csv(f"{data_dir}/player_stats_pfr.csv")

    # Load and merge position data from rosters
    rosters = pd.read_csv("/Users/td/Code/nfl-ai/Models/IN-PROGRESS/touchdown_models/data/rosters.csv")

    # Create position mapping for 2025 (most recent season available in rosters)
    roster_2025 = rosters[rosters['season'] == 2025].copy()

    # Clean player names for better matching
    def clean_name(name):
        if pd.isna(name):
            return ""
        return str(name).strip()

    roster_2025['full_name_clean'] = roster_2025['full_name'].apply(clean_name)

    # Create position mapping by cleaned player name only (ignore team since players move)
    position_map_2025 = {}
    for _, row in roster_2025.iterrows():
        key = row['full_name_clean'].lower()
        position_map_2025[key] = row['position']

    # Merge position data into player stats
    # Use 2025 roster data for all seasons (most current available)
    def get_position(row):
        player_name = clean_name(row['player']).lower()
        return position_map_2025.get(player_name, '')

    player_stats['position'] = player_stats.apply(get_position, axis=1)

    game_logs = pd.read_csv(f"{data_dir}/game_logs_pfr.csv")
    return player_stats, game_logs


def _parse_game_logs(game_logs: pd.DataFrame) -> pd.DataFrame:
    """Return a team-level game log with offensive and defensive touchdown totals."""

    logs = game_logs.copy()
    parts = logs["game_id"].str.split("_", expand=True)
    logs["season"] = parts[0].astype(int)
    logs["week"] = parts[1].astype(int)
    logs["away_team"] = parts[2]
    logs["home_team"] = parts[3]

    logs["home_td_scored"] = logs["home_pass_td"].fillna(0) + logs["home_rush_td"].fillna(0)
    logs["away_td_scored"] = logs["away_pass_td"].fillna(0) + logs["away_rush_td"].fillna(0)
    logs["home_td_allowed"] = logs["away_td_scored"]
    logs["away_td_allowed"] = logs["home_td_scored"]
    logs["home_pts"] = logs["home_pts_off"].fillna(0)
    logs["away_pts"] = logs["away_pts_off"].fillna(0)

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
    return team_games


def _attach_team_placeholders(
    team_games: pd.DataFrame,
    upcoming_games: pd.DataFrame,
    target_season: int,
    target_week: int,
) -> pd.DataFrame:
    """Append placeholder rows for the upcoming week so rolling stats include week-to-date data."""

    placeholders = []
    numeric_cols = team_games.select_dtypes(include=["number"]).columns
    for team in sorted(set(upcoming_games["home_team"]) | set(upcoming_games["away_team"])):
        recent = team_games[(team_games["team"] == team) & (team_games["season"] == target_season)]
        if recent.empty:
            continue
        template = recent.iloc[-1].copy()
        template["season"] = target_season
        template["week"] = target_week
        for col in numeric_cols:
            if col not in {"season", "week"} and col in template.index:
                template[col] = np.nan
        template["is_placeholder"] = True
        placeholders.append(template)

    if not placeholders:
        return team_games.assign(is_placeholder=False)

    placeholder_df = pd.DataFrame(placeholders)
    placeholder_df["is_placeholder"] = True
    team_games = pd.concat([team_games, placeholder_df], ignore_index=True)
    team_games.sort_values(["team", "season", "week"], inplace=True)
    team_games["is_placeholder"] = team_games.get("is_placeholder", False)
    return team_games


def _compute_team_features(
    team_games: pd.DataFrame,
    rolling_window: int = ROLLING_WINDOW,
) -> pd.DataFrame:
    """Compute rolling touchdown and point rates for each team."""

    team_games = team_games.copy()
    team_games["is_placeholder"] = team_games.get("is_placeholder", False)
    grouped = team_games.groupby(["team", "season"], group_keys=False)

    for column in ["td_scored", "td_allowed", "pts_scored", "pts_allowed"]:
        shifted = grouped[column].shift()
        rolling = grouped[column].apply(
            lambda s: s.shift().rolling(window=rolling_window, min_periods=1).mean()
        )
        expanding = grouped[column].apply(lambda s: s.shift().expanding().mean())
        feature = rolling.fillna(expanding)
        feature = feature.fillna(team_games[column].mean())
        team_games[f"{column}_feature"] = feature

    team_games["games_played_prior"] = grouped.cumcount()
    return team_games


def _eligible_players(player_stats: pd.DataFrame) -> pd.DataFrame:
    """Filter the raw player stats to the skill positions we care about."""

    data = player_stats.copy()
    data = data.fillna({stat: 0 for stat in BASE_STATS + TD_COLUMNS})
    touches = data["rush_att"].fillna(0) + data["targets"].fillna(0) + data["rec"].fillna(0)
    data = data[touches > 0]
    data = data[data["season"].notna()]
    data["season"] = data["season"].astype(int)
    data["week"] = data["week"].astype(int)
    data["home"] = data["home"].fillna("n")
    data["opponent_team"] = data["opponent_team"].fillna("")
    data["team"] = data["team"].fillna("")
    data["home_team"] = data["home_team"].fillna("")
    data["away_team"] = data["away_team"].fillna("")
    return data


def _create_player_placeholders(
    player_stats: pd.DataFrame,
    upcoming_games: pd.DataFrame,
    target_season: int,
    target_week: int,
) -> pd.DataFrame:
    """Append placeholder rows for each player in the upcoming schedule."""

    placeholders = []
    numeric_cols = player_stats.select_dtypes(include=["number"]).columns.tolist()
    for _, game in upcoming_games.iterrows():
        home_team = game["home_team"]
        away_team = game["away_team"]
        game_id = f"{target_season}_{target_week:02d}_{away_team}_{home_team}"

        for team, home_flag in [(home_team, "y"), (away_team, "n")]:
            prior_games = player_stats[
                (player_stats["season"] == target_season)
                & (player_stats["week"] < target_week)
                & (player_stats["team"] == team)
            ]
            if prior_games.empty:
                continue

            latest_by_player = (
                prior_games.sort_values(["player", "week"]).groupby("player").tail(1)
            )
            for _, row in latest_by_player.iterrows():
                placeholder = row.copy()
                placeholder["week"] = target_week
                placeholder["season"] = target_season
                placeholder["game_id"] = game_id
                placeholder["home"] = home_flag
                placeholder["home_team"] = home_team
                placeholder["away_team"] = away_team
                placeholder["opponent_team"] = away_team if team == home_team else home_team
                placeholder["is_placeholder"] = True
                # Preserve position and other non-numeric columns
                for col in numeric_cols:
                    if col not in {"season", "week"}:
                        placeholder[col] = np.nan
                placeholders.append(placeholder)

    if not placeholders:
        return player_stats.assign(is_placeholder=False)

    placeholder_df = pd.DataFrame(placeholders)
    placeholder_df["is_placeholder"] = True

    combined = pd.concat([player_stats, placeholder_df], ignore_index=True)
    combined.sort_values(["player", "season", "week"], inplace=True)
    combined["is_placeholder"] = combined.get("is_placeholder", False)
    return combined


def _compute_player_features(
    player_stats: pd.DataFrame,
    team_features: pd.DataFrame,
    rolling_window: int = ROLLING_WINDOW,
) -> Tuple[pd.DataFrame, List[str]]:
    """Compute rolling player-level features for model training and inference."""

    data = player_stats.copy()
    data["is_placeholder"] = data.get("is_placeholder", False)
    data["total_tds"] = data["rush_td"].fillna(0) + data["rec_td"].fillna(0)
    data["touches"] = data["rush_att"].fillna(0) + data["targets"].fillna(0) + data["rec"].fillna(0)

    grouped = data.groupby(["player", "season"], group_keys=False)

    for stat in BASE_STATS + ["touches", "total_tds"]:
        data[f"{stat}_rolling"] = grouped[stat].apply(
            lambda s: s.shift().rolling(window=rolling_window, min_periods=1).mean()
        )
        data[f"{stat}_season_avg"] = grouped[stat].apply(lambda s: s.shift().expanding().mean())

    data["games_played_prior"] = grouped.cumcount()
    data["is_home"] = (data["home"].str.lower() == "y").astype(int)
    data["scored_td"] = (data["total_tds"] > 0).astype(int)

    feature_columns = []
    for stat in BASE_STATS + ["touches"]:
        feature_columns.append(f"{stat}_rolling")
    feature_columns.append("total_tds_rolling")
    feature_columns.append("total_tds_season_avg")
    feature_columns.append("games_played_prior")
    feature_columns.append("is_home")

    merge_cols = [
        "season",
        "week",
        "team",
        "td_scored_feature",
        "td_allowed_feature",
        "pts_scored_feature",
        "pts_allowed_feature",
        "games_played_prior",
        "is_placeholder",
    ]

    team_feats = team_features[merge_cols]
    data = data.merge(
        team_feats.rename(
            columns={
                "td_scored_feature": "team_td_scored_feature",
                "td_allowed_feature": "team_td_allowed_feature",
                "pts_scored_feature": "team_pts_scored_feature",
                "pts_allowed_feature": "team_pts_allowed_feature",
                "games_played_prior": "team_games_played_prior",
                "is_placeholder": "team_row_is_placeholder",
            }
        ),
        on=["season", "week", "team"],
        how="left",
    )

    opp_feats = team_features[merge_cols]
    data = data.merge(
        opp_feats.rename(
            columns={
                "team": "opponent_team",
                "td_scored_feature": "opp_td_scored_feature",
                "td_allowed_feature": "opp_td_allowed_feature",
                "pts_scored_feature": "opp_pts_scored_feature",
                "pts_allowed_feature": "opp_pts_allowed_feature",
                "games_played_prior": "opp_games_played_prior",
                "is_placeholder": "opp_row_is_placeholder",
            }
        ),
        on=["season", "week", "opponent_team"],
        how="left",
    )

    feature_columns.extend(
        [
            "team_td_scored_feature",
            "team_td_allowed_feature",
            "team_pts_scored_feature",
            "team_pts_allowed_feature",
            "opp_td_scored_feature",
            "opp_td_allowed_feature",
            "opp_pts_scored_feature",
            "opp_pts_allowed_feature",
        ]
    )

    data[feature_columns] = data[feature_columns].fillna(0.0)
    return data, feature_columns


def prepare_datasets(
    upcoming_week: int,
    upcoming_season: int = 2024,
    rolling_window: int = ROLLING_WINDOW,
    min_games: int = 1,
    data_dir: str | None = None,
    upcoming_games_path: str | None = None,
) -> DatasetBundle:
    """Return train/validation/upcoming datasets with aligned feature sets."""

    player_stats_raw, game_logs_raw = _load_raw_data(data_dir)
    player_stats = _eligible_players(player_stats_raw)
    print(f"Eligible players: {len(player_stats)} rows")

    upcoming_games = pd.read_csv(upcoming_games_path or UPCOMING_GAMES_PATH)
    upcoming_games = upcoming_games.dropna(subset=["home_team", "away_team"])
    print(f"Upcoming games: {len(upcoming_games)} games")

    team_games = _parse_game_logs(game_logs_raw)
    team_games = _attach_team_placeholders(team_games, upcoming_games, upcoming_season, upcoming_week)
    team_features = _compute_team_features(team_games, rolling_window=rolling_window)

    player_stats = _create_player_placeholders(player_stats, upcoming_games, upcoming_season, upcoming_week)
    player_features, feature_columns = _compute_player_features(player_stats, team_features, rolling_window)
    print(f"Player features computed: {len(feature_columns)} features")

    # Suppress the FutureWarning by using pandas' recommended approach
    with pd.option_context('future.no_silent_downcasting', True):
        player_features["is_placeholder"] = player_features["is_placeholder"].fillna(False).astype(bool)
    player_features[feature_columns] = player_features[feature_columns].fillna(0.0)

    valid_mask = (
        (player_features["games_played_prior"] >= min_games)
        & player_features["opponent_team"].ne("")
    )
    model_ready = player_features[valid_mask].copy()
    print(f"Model-ready data: {len(model_ready)} rows")

    train = model_ready[
        (~model_ready["is_placeholder"]) & (model_ready["season"] < upcoming_season)
    ].copy()
    validation = model_ready[
        (~model_ready["is_placeholder"]) & (model_ready["season"] == upcoming_season) & (model_ready["week"] < upcoming_week)
    ].copy()
    upcoming = model_ready[model_ready["is_placeholder"]].copy()

    print(f"Final datasets - Train: {len(train)} rows, Validation: {len(validation)} rows, Upcoming: {len(upcoming)} rows")
    print("Dataset preparation complete!")

    return DatasetBundle(
        feature_columns=feature_columns,
        train=train,
        validation=validation,
        upcoming=upcoming,
    )


def load_league_baselines(train_df: pd.DataFrame) -> Dict[str, float]:
    """Return simple league-wide averages for Monte Carlo adjustments."""

    baselines = {
        "player_td_rate": (train_df["total_tds"].sum() / train_df["games_played_prior"].sum())
        if train_df["games_played_prior"].sum() > 0
        else 0.1,
        "team_td_scored": train_df["team_td_scored_feature"].mean(),
        "opp_td_allowed": train_df["opp_td_allowed_feature"].mean(),
    }
    return baselines
