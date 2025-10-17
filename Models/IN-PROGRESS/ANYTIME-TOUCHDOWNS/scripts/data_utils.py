"""Utility functions for loading data and building touchdown scoring features."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Sequence

import numpy as np
import pandas as pd

POSITIONS = {"RB", "WR", "TE"}
BASE_FEATURE_COLUMNS = [
    "rush_att",
    "rush_yds",
    "targets",
    "rec",
    "rec_yds",
    "fantasy_points_ppr",
]
ROLLING_WINDOWS = (3,)


def default_data_dir() -> Path:
    """Return the default directory that holds the final Pro Football Reference exports."""

    return Path(__file__).resolve().parents[2] / "final_data_pfr"


def default_upcoming_games_path() -> Path:
    """Return the default path for the upcoming games file."""

    return Path(__file__).resolve().parents[3] / "upcoming_games.csv"


@dataclass
class FeatureSet:
    """Container for feature metadata."""

    feature_columns: List[str]
    target_column: str = "td_scored"


def load_player_stats(data_dir: Path | None = None) -> pd.DataFrame:
    """Load the PFR player game logs with minimal cleaning."""

    data_dir = default_data_dir() if data_dir is None else data_dir
    player_path = data_dir / "player_stats_pfr.csv"
    df = pd.read_csv(player_path)

    numeric_columns = BASE_FEATURE_COLUMNS + [
        "rush_td",
        "rec_td",
        "fantasy_points_ppr",
    ]
    for column in numeric_columns:
        df[column] = pd.to_numeric(df[column], errors="coerce").fillna(0.0)

    df["td_scored"] = ((df["rush_td"] + df["rec_td"]) > 0).astype(int)

    touch_mask = (
        (df["rush_att"] > 0)
        | (df["targets"] > 0)
        | (df["rush_td"] > 0)
        | (df["rec_td"] > 0)
    )
    df = df[touch_mask].copy()

    if "position" not in df.columns or df["position"].dropna().empty:
        df["position"] = np.where(
            df["targets"] >= df["rush_att"],
            "WR",
            "RB",
        )

    df = df[df["position"].isin(POSITIONS)].copy()
    df["player_key"] = df["player_id"].fillna(df["player"])
    df.sort_values(["player_key", "season", "week"], inplace=True)
    return df


def _add_player_rolling_features(df: pd.DataFrame, windows: Sequence[int]) -> pd.DataFrame:
    group_cols = ["player_key", "season"]
    for window in windows:
        suffix = f"_l{window}"
        for column in BASE_FEATURE_COLUMNS:
            df[f"{column}{suffix}"] = (
                df.groupby(group_cols)[column]
                .transform(lambda s: s.shift(1).rolling(window, min_periods=1).mean())
            )
        df[f"td_rate{suffix}"] = (
            df.groupby(group_cols)["td_scored"]
            .transform(lambda s: s.shift(1).rolling(window, min_periods=1).mean())
        )
    df["games_played_prior"] = df.groupby(group_cols).cumcount()
    return df


def _aggregate_touchdowns(df: pd.DataFrame) -> pd.DataFrame:
    temp = df.copy()
    temp["total_td"] = temp["rush_td"] + temp["rec_td"]
    return temp


def _team_scoring_features(df: pd.DataFrame, windows: Sequence[int]) -> pd.DataFrame:
    scoring = (
        df.groupby(["season", "week", "team"], as_index=False)["total_td"].sum()
        .rename(columns={"total_td": "team_td_scored"})
    )
    scoring.sort_values(["team", "season", "week"], inplace=True)
    for window in windows:
        scoring[f"team_td_scored_l{window}"] = (
            scoring.groupby(["team", "season"])["team_td_scored"]
            .transform(lambda s: s.shift(1).rolling(window, min_periods=1).mean())
        )
    return scoring


def _team_allowed_features(df: pd.DataFrame, windows: Sequence[int]) -> pd.DataFrame:
    allowed = (
        df.groupby(["season", "week", "opponent_team"], as_index=False)["total_td"].sum()
        .rename(columns={"opponent_team": "team", "total_td": "team_td_allowed"})
    )
    allowed.sort_values(["team", "season", "week"], inplace=True)
    for window in windows:
        allowed[f"team_td_allowed_l{window}"] = (
            allowed.groupby(["team", "season"])["team_td_allowed"]
            .transform(lambda s: s.shift(1).rolling(window, min_periods=1).mean())
        )
    return allowed


def add_game_context_features(
    df: pd.DataFrame, windows: Sequence[int] = ROLLING_WINDOWS
) -> pd.DataFrame:
    df = _aggregate_touchdowns(df)
    df = _add_player_rolling_features(df, windows)
    scoring = _team_scoring_features(df, windows)
    allowed = _team_allowed_features(df, windows)

    df = df.merge(
        scoring[["season", "week", "team"] + [f"team_td_scored_l{w}" for w in windows]],
        on=["season", "week", "team"],
        how="left",
    )
    df = df.merge(
        allowed[["season", "week", "team"] + [f"team_td_allowed_l{w}" for w in windows]],
        left_on=["season", "week", "opponent_team"],
        right_on=["season", "week", "team"],
        how="left",
        suffixes=("", "_opp"),
    )
    rename_map = {}
    for window in windows:
        rename_map[f"team_td_allowed_l{window}"] = f"opp_td_allowed_l{window}"
        rename_map[f"team_td_allowed_l{window}_opp"] = f"opp_td_allowed_l{window}"
    df.rename(columns=rename_map, inplace=True)
    df.drop(columns=[col for col in df.columns if col.endswith("_opp")], inplace=True)
    return df


def build_feature_columns(windows: Iterable[int] = ROLLING_WINDOWS) -> FeatureSet:
    feature_columns: List[str] = ["games_played_prior"]
    for window in windows:
        suffix = f"_l{window}"
        feature_columns.extend(f"{col}{suffix}" for col in BASE_FEATURE_COLUMNS)
        feature_columns.append(f"td_rate{suffix}")
        feature_columns.append(f"team_td_scored{suffix}")
        feature_columns.append(f"opp_td_allowed{suffix}")
    return FeatureSet(feature_columns=feature_columns)


def prepare_training_frame(
    data_dir: Path | None = None,
    windows: Sequence[int] = ROLLING_WINDOWS,
    max_season: int = 2024,
) -> tuple[pd.DataFrame, FeatureSet]:
    df = load_player_stats(data_dir)
    df = add_game_context_features(df, windows)
    feature_set = build_feature_columns(windows)
    df = df[df["games_played_prior"] > 0]
    df = df[df["season"] <= max_season]
    df = df.dropna(subset=feature_set.feature_columns + [feature_set.target_column])
    return df, feature_set


def _team_form_next_game(team_df: pd.DataFrame, windows: Sequence[int]) -> pd.DataFrame:
    rows = []
    for team, group in team_df.groupby("team"):
        group = group.sort_values(["season", "week"])
        if group.empty:
            continue
        latest = group.iloc[-1]
        season = latest["season"]
        data = {"team": team, "season": season, "games_played": group.shape[0]}
        for window in windows:
            tail = group.tail(window)
            data[f"team_td_scored_l{window}"] = tail["team_td_scored"].mean()
        rows.append(data)
    return pd.DataFrame(rows)


def _team_allowed_form_next_game(allowed_df: pd.DataFrame, windows: Sequence[int]) -> pd.DataFrame:
    rows = []
    for team, group in allowed_df.groupby("team"):
        group = group.sort_values(["season", "week"])
        if group.empty:
            continue
        latest = group.iloc[-1]
        season = latest["season"]
        data = {"team": team, "season": season, "games_played": group.shape[0]}
        for window in windows:
            tail = group.tail(window)
            data[f"opp_td_allowed_l{window}"] = tail["team_td_allowed"].mean()
        rows.append(data)
    return pd.DataFrame(rows)


def _player_form_next_game(df: pd.DataFrame, windows: Sequence[int]) -> pd.DataFrame:
    rows = []
    for (player_key, season), group in df.groupby(["player_key", "season"]):
        group = group.sort_values("week")
        if group.empty:
            continue
        latest = group.iloc[-1]
        data = {
            "player_key": player_key,
            "player": latest["player"],
            "team": latest["team"],
            "position": latest["position"],
            "season": season,
            "games_played_prior": group.shape[0],
        }
        for window in windows:
            tail = group.tail(window)
            data[f"rush_att_l{window}"] = tail["rush_att"].mean()
            data[f"rush_yds_l{window}"] = tail["rush_yds"].mean()
            data[f"targets_l{window}"] = tail["targets"].mean()
            data[f"rec_l{window}"] = tail["rec"].mean()
            data[f"rec_yds_l{window}"] = tail["rec_yds"].mean()
            data[f"fantasy_points_ppr_l{window}"] = tail["fantasy_points_ppr"].mean()
            data[f"td_rate_l{window}"] = tail["td_scored"].mean()
        rows.append(data)
    return pd.DataFrame(rows)


def prepare_upcoming_features(
    df: pd.DataFrame,
    windows: Sequence[int] = ROLLING_WINDOWS,
    upcoming_games_path: Path | None = None,
    current_season: int | None = None,
) -> pd.DataFrame:
    if current_season is None:
        current_season = int(df["season"].max())

    upcoming_games_path = (
        default_upcoming_games_path() if upcoming_games_path is None else upcoming_games_path
    )
    schedule = pd.read_csv(upcoming_games_path)
    matchups = []
    for _, row in schedule.iterrows():
        matchups.append({"team": row["home_team"], "opponent_team": row["away_team"]})
        matchups.append({"team": row["away_team"], "opponent_team": row["home_team"]})
    schedule_df = pd.DataFrame(matchups)

    season_df = df[df["season"] == current_season].copy()
    season_df = season_df[season_df["week"] <= season_df["week"].max()]

    player_form = _player_form_next_game(season_df, windows)
    player_form = player_form.merge(schedule_df, on="team", how="inner")

    enriched = _aggregate_touchdowns(season_df)
    scoring = _team_scoring_features(enriched, windows)
    allowed = _team_allowed_features(enriched, windows)

    scoring_form = _team_form_next_game(scoring, windows)
    allowed_form = _team_allowed_form_next_game(allowed, windows)

    player_form = player_form.merge(
        scoring_form[["team"] + [f"team_td_scored_l{w}" for w in windows]],
        on="team",
        how="left",
    )
    player_form = player_form.merge(
        allowed_form[["team"] + [f"opp_td_allowed_l{w}" for w in windows]],
        left_on="opponent_team",
        right_on="team",
        how="left",
        suffixes=("", "_opp"),
    )
    player_form.rename(
        columns={f"opp_td_allowed_l{w}_opp": f"opp_td_allowed_l{w}" for w in windows}, inplace=True
    )
    player_form.drop(columns=[col for col in player_form.columns if col.endswith("_opp")], inplace=True)

    feature_columns = build_feature_columns(windows).feature_columns
    missing_cols = [col for col in feature_columns if col not in player_form.columns]
    for column in missing_cols:
        player_form[column] = np.nan

    return player_form


def league_touchdown_rate(df: pd.DataFrame, season: int | None = None) -> float:
    if season is not None:
        df = df[df["season"] == season]
    total_games = df.shape[0]
    if total_games == 0:
        return 0.0
    return df["td_scored"].sum() / total_games
