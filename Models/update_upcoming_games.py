#!/usr/bin/env python3
"""Utility to refresh upcoming_games.csv from the master games schedule."""

from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path
from typing import Optional

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_GAMES_PATH = BASE_DIR.parent / "Scrapers" / "data" / "games.csv"
DEFAULT_OUTPUT_PATH = BASE_DIR / "upcoming_games.csv"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Update Models/upcoming_games.csv with the next unplayed games."
    )
    parser.add_argument(
        "--games-csv",
        type=Path,
        default=DEFAULT_GAMES_PATH,
        help="Path to Scrapers/data/games.csv (defaults to repository copy).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_PATH,
        help="Where to write the refreshed upcoming games CSV.",
    )
    parser.add_argument(
        "--reference-date",
        type=str,
        default=None,
        help=(
            "Optional ISO date (YYYY-MM-DD) to anchor \"upcoming\". "
            "Defaults to today's date."
        ),
    )
    parser.add_argument(
        "--week",
        type=str,
        default=None,
        help=(
            "Optional week identifier to force (e.g. '9' or 'WC'). "
            "If omitted, the script picks the earliest upcoming week."
        ),
    )
    parser.add_argument(
        "--game-type",
        type=str,
        default="REG",
        help="Game type to consider (REG, WC, DIV, CON, SB).",
    )
    return parser.parse_args()


def normalise_week(value: str | int | float) -> str:
    """Represent the week identifier as a clean string."""
    if pd.isna(value):
        return ""
    if isinstance(value, (int, float)) and float(value).is_integer():
        return str(int(value))
    return str(value)


def resolve_reference_date(raw: Optional[str]) -> pd.Timestamp:
    if raw is None:
        return pd.Timestamp(date.today())
    parsed = pd.to_datetime(raw, format="%Y-%m-%d", errors="coerce")
    if pd.isna(parsed):
        raise ValueError(
            f"Invalid --reference-date '{raw}'. Expected ISO format YYYY-MM-DD."
        )
    return parsed


def load_games(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Games CSV not found at {path}")
    return pd.read_csv(path, parse_dates=["date"], keep_default_na=True)


def select_upcoming_games(
    games: pd.DataFrame,
    *,
    reference_date: pd.Timestamp,
    week: Optional[str],
    game_type: Optional[str],
) -> tuple[pd.DataFrame, str, int, str]:
    """Slice the schedule down to the next set of unplayed games."""

    pending_mask = games["home_score"].isna() | games["away_score"].isna()
    pending = games.loc[pending_mask].copy()

    if game_type:
        pending = pending.loc[pending["game_type"] == game_type]

    if pending.empty:
        raise ValueError("No unplayed games remain that match the supplied filters.")

    if week is not None:
        week_key = normalise_week(week)
        pending = pending.loc[pending["week"].map(normalise_week) == week_key]
        if pending.empty:
            raise ValueError(
                f"No unplayed games found for week '{week_key}' and game type '{game_type}'."
            )
        # Use the most recent season that still has an unplayed game for the week.
        season = pending["season"].max()
        subset = pending.loc[pending["season"] == season]
        resolved_week = week_key
        resolved_game_type = game_type if game_type else subset["game_type"].iloc[0]
    else:
        future = pending.loc[pending["date"] >= reference_date]
        if future.empty:
            raise ValueError("Could not locate an upcoming week after the reference date.")
        first = future.sort_values(["date", "gametime", "game_id"]).iloc[0]
        season = int(first["season"])
        resolved_week = normalise_week(first["week"])
        resolved_game_type = str(first["game_type"])
        subset = pending.loc[
            (pending["season"] == season)
            & (pending["week"].map(normalise_week) == resolved_week)
            & (pending["game_type"] == resolved_game_type)
        ]

    if subset.empty:
        raise ValueError("Identified week has no matching games to export.")

    def _sort_key(series: pd.Series) -> pd.Series:
        if series.name == "gametime":
            return pd.to_datetime(series, format="%H:%M", errors="coerce")
        return series

    subset = subset.sort_values(["date", "gametime", "game_id"], key=_sort_key)

    return subset, resolved_week, season, resolved_game_type


def write_upcoming_games(games: pd.DataFrame, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    games.loc[:, ["home_team", "away_team"]].to_csv(output_path, index=False)


def main() -> None:
    args = parse_args()
    games = load_games(args.games_csv)
    reference_date = resolve_reference_date(args.reference_date)

    subset, week, season, game_type = select_upcoming_games(
        games,
        reference_date=reference_date,
        week=args.week,
        game_type=args.game_type,
    )

    write_upcoming_games(subset, args.output)
    print(
        "Saved",
        len(subset),
        f"upcoming {game_type} games for week {week} of season {season} to {args.output}",
    )


if __name__ == "__main__":
    main()
