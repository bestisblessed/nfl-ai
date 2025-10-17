"""Shared feature engineering helpers for anytime touchdown models."""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import List, Tuple

import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR.parent / "final_data_pfr"
UPCOMING_GAMES_PATH = BASE_DIR.parent.parent / "upcoming_games.csv"

ROLLING_WINDOW = 3


@dataclass(frozen=True)
class ModelData:
    """Container bundling feature matrix, labels, and metadata."""

    features: pd.DataFrame
    target: pd.Series
    feature_columns: Tuple[str, ...]


@lru_cache(maxsize=1)
def load_player_stats() -> pd.DataFrame:
    """Load and clean player-level game logs."""
    df = pd.read_csv(DATA_DIR / "player_stats_pfr.csv")

    numeric_cols = [
        "rush_att",
        "rush_yds",
        "rush_td",
        "pass_att",
        "targets",
        "rec",
        "rec_yds",
        "rec_td",
        "fantasy_points_ppr",
    ]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)

    df["week"] = pd.to_numeric(df["week"], errors="coerce").fillna(0).astype(int)
    df["season"] = pd.to_numeric(df["season"], errors="coerce").astype(int)

    df["rush_td"] = df["rush_td"].fillna(0.0)
    df["rec_td"] = df["rec_td"].fillna(0.0)
    df["pass_att"] = df["pass_att"].fillna(0.0)

    df = df[(df["pass_att"] < 10) | ((df["rush_att"] + df["targets"]) > 0)]

    df["total_tds"] = df["rush_td"] + df["rec_td"]
    df["any_td"] = (df["total_tds"] > 0).astype(int)
    df["is_home"] = (df["home"].fillna("n") == "y").astype(int)
    df["role"] = np.where(df["targets"] >= df["rush_att"], "Receiver", "Rusher")

    df["team"] = df["team"].str.upper()
    df["opponent_team"] = df["opponent_team"].str.upper()

    return df


def _rolling_player_features(df: pd.DataFrame, window: int, include_current: bool) -> pd.DataFrame:
    """Compute rolling statistics for player usage and production."""
    df = df.sort_values(["player_id", "season", "week"]).copy()
    group_keys = ["player_id", "season"]
    shift_amount = 0 if include_current else 1

    base_cols = ["rush_att", "rush_yds", "targets", "rec", "rec_yds", "total_tds", "fantasy_points_ppr"]
    for col in base_cols:
        df[f"{col}_rolling_{window}"] = (
            df.groupby(group_keys)[col]
            .transform(lambda s: s.shift(shift_amount).rolling(window, min_periods=1).mean())
        )

    df[f"games_played_{window}"] = (
        df.groupby(group_keys)["game_id"]
        .transform(lambda s: s.shift(shift_amount).notna().rolling(window, min_periods=1).sum())
    )

    if not include_current:
        fill_cols = [f"{col}_rolling_{window}" for col in base_cols] + [f"games_played_{window}"]
        df[fill_cols] = df[fill_cols].fillna(0.0)
    return df


def _opponent_defense_features(df: pd.DataFrame, window: int, include_current: bool) -> pd.DataFrame:
    """Summarise touchdowns allowed by defenses."""
    defense = (
        df.groupby(["opponent_team", "season", "week", "game_id"])["total_tds"]
        .sum()
        .reset_index()
    )
    defense = defense.sort_values(["opponent_team", "season", "week"])

    group = defense.groupby(["opponent_team", "season"])

    counts = group.cumcount() + 1
    cumsum = group["total_tds"].cumsum().astype(float)
    if include_current:
        defense["tds_allowed_avg"] = cumsum / counts.astype(float)
    else:
        previous_counts = (counts - 1).replace(0, np.nan).astype(float)
        defense["tds_allowed_avg"] = (cumsum - defense["total_tds"].astype(float)) / previous_counts

    if include_current:
        defense[f"tds_allowed_rolling_{window}"] = group["total_tds"].transform(
            lambda s: s.rolling(window, min_periods=1).mean()
        )
    else:
        defense[f"tds_allowed_rolling_{window}"] = group["total_tds"].transform(
            lambda s: s.shift(1).rolling(window, min_periods=1).mean()
        )

    fill_cols = ["tds_allowed_avg", f"tds_allowed_rolling_{window}"]
    defense[fill_cols] = defense[fill_cols].fillna(defense[fill_cols].mean())

    defense = defense.drop(columns=["total_tds"])
    defense = defense.drop_duplicates(["opponent_team", "season", "week"])
    return defense


def build_training_table(window: int = ROLLING_WINDOW) -> ModelData:
    """Prepare model-ready features and labels for historical games."""
    df = load_player_stats()

    latest_completed_season = df["season"].max() - 1
    train_df = df[df["season"] <= latest_completed_season].copy()

    train_df = _rolling_player_features(train_df, window=window, include_current=False)
    defense = _opponent_defense_features(train_df, window=window, include_current=False)
    train_df = train_df.merge(
        defense,
        on=["opponent_team", "season", "week", "game_id"],
        how="left",
    )

    feature_columns = [
        f"{col}_rolling_{window}" for col in [
            "rush_att",
            "rush_yds",
            "targets",
            "rec",
            "rec_yds",
            "total_tds",
            "fantasy_points_ppr",
        ]
    ]
    feature_columns += [f"games_played_{window}", f"tds_allowed_rolling_{window}", "tds_allowed_avg", "is_home"]

    train_df = train_df[train_df[f"games_played_{window}"] > 0].copy()
    train_df[feature_columns] = train_df[feature_columns].fillna(0.0)

    return ModelData(
        features=train_df[feature_columns],
        target=train_df["any_td"].astype(int),
        feature_columns=tuple(feature_columns),
    )


def upcoming_games_mapping(target_week: int, upcoming_path: Path | None = None) -> pd.DataFrame:
    """Return tidy upcoming schedule with home/away context."""
    path = upcoming_path or UPCOMING_GAMES_PATH
    games = pd.read_csv(path)

    home_side = games.rename(columns={"home_team": "team", "away_team": "opponent"}).assign(is_home=1)
    away_side = games.rename(columns={"away_team": "team", "home_team": "opponent"}).assign(is_home=0)

    combined = pd.concat(
        [home_side[["team", "opponent", "is_home"]], away_side[["team", "opponent", "is_home"]]],
        ignore_index=True,
    )
    combined["team"] = combined["team"].str.upper()
    combined["opponent"] = combined["opponent"].str.upper()
    combined["week"] = target_week
    return combined


def build_upcoming_features(
    season: int,
    last_completed_week: int,
    window: int = ROLLING_WINDOW,
    upcoming_path: Path | None = None,
) -> pd.DataFrame:
    """Create feature rows for players ahead of the next week."""
    df = load_player_stats()
    season_games = df[(df["season"] == season) & (df["week"] <= last_completed_week)].copy()

    if season_games.empty:
        raise ValueError(f"No stats for season {season} through week {last_completed_week}.")

    season_games = _rolling_player_features(season_games, window=window, include_current=True)
    defense = _opponent_defense_features(season_games, window=window, include_current=True)

    latest_players = season_games.sort_values(["player_id", "week"]).groupby("player_id").tail(1).copy()
    latest_players["week"] = last_completed_week + 1

    latest_defense = defense.sort_values(["opponent_team", "week"]).groupby("opponent_team").tail(1).copy()
    latest_defense["week"] = last_completed_week + 1

    schedule = upcoming_games_mapping(last_completed_week + 1, upcoming_path)
    merged = latest_players.merge(schedule, on="team", how="inner")
    merged["upcoming_opponent"] = merged["opponent"]
    merged["week"] = last_completed_week + 1
    merged = merged.drop(columns=[col for col in ["week_x", "week_y"] if col in merged.columns])
    if 'is_home_y' in merged.columns:
        merged['is_home'] = merged['is_home_y']
        merged = merged.drop(columns='is_home_y')
    if 'is_home_x' in merged.columns:
        merged = merged.drop(columns='is_home_x')

    latest_defense = latest_defense.rename(columns={"opponent_team": "opponent"})
    merged = merged.merge(latest_defense, on=["opponent", "season", "week"], how="left")

    feature_columns = [
        f"{col}_rolling_{window}" for col in [
            "rush_att",
            "rush_yds",
            "targets",
            "rec",
            "rec_yds",
            "total_tds",
            "fantasy_points_ppr",
        ]
    ]
    feature_columns += [f"games_played_{window}", f"tds_allowed_rolling_{window}", "tds_allowed_avg", "is_home"]

    merged[feature_columns] = merged[feature_columns].fillna(0.0)
    merged = merged[merged[f"games_played_{window}"] > 0]

    return merged

def top_players_for_team(team: str, season: int, week: int, top_n: int = 5) -> List[str]:
    """Return player_ids for the most involved skill players on a team."""
    df = load_player_stats()
    mask = (df["season"] == season) & (df["team"] == team) & (df["week"] <= week)
    team_df = df[mask]
    if team_df.empty:
        return []

    involvement = team_df.groupby(["player_id", "player"])[["rush_att", "targets", "rec"]].sum()
    involvement["volume_score"] = involvement[["rush_att", "targets", "rec"]].sum(axis=1)
    top_players = involvement.sort_values("volume_score", ascending=False).head(top_n)
    return top_players.index.get_level_values("player_id").tolist()
