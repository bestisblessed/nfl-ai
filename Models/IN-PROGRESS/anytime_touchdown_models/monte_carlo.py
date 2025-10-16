"""Monte Carlo touchdown probabilities using Poisson scoring."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from feature_engineering import ROLLING_WINDOW, build_upcoming_features, load_player_stats

SIMULATIONS = 10_000
SEED = 2024


def latest_season_and_week() -> tuple[int, int]:
    stats = load_player_stats()
    season = stats["season"].max()
    last_week = int(stats.loc[stats["season"] == season, "week"].max())
    return season, last_week


def run_simulation(row: pd.Series, league_avg_allowed: float) -> float:
    player_rate = max(row.get(f"total_tds_rolling_{ROLLING_WINDOW}", 0.0), 0.0)
    defense_recent = max(row.get(f"tds_allowed_rolling_{ROLLING_WINDOW}", league_avg_allowed), 0.0)
    defense_baseline = max(row.get("tds_allowed_avg", league_avg_allowed), 1e-6)

    defense_factor = defense_recent / defense_baseline if defense_baseline else 1.0
    adjusted_lambda = max(player_rate * defense_factor, 1e-4)

    rng = np.random.default_rng(SEED)
    samples = rng.poisson(adjusted_lambda, size=SIMULATIONS)
    return (samples >= 1).mean()


def main() -> None:
    season, last_week = latest_season_and_week()
    upcoming = build_upcoming_features(season=season, last_completed_week=last_week, window=ROLLING_WINDOW)

    league_avg_allowed = upcoming.get("tds_allowed_avg", pd.Series([1.0])).mean()
    probabilities = upcoming.apply(run_simulation, axis=1, args=(league_avg_allowed,))
    upcoming = upcoming.copy()
    upcoming["monte_carlo_anytime_td_prob"] = probabilities

    output_dir = Path(__file__).resolve().parent
    output_path = output_dir / "monte_carlo_week7.csv"
    columns = [
        "player",
        "team",
        "upcoming_opponent",
        "role",
        "games_played_3",
        "monte_carlo_anytime_td_prob",
    ]
    available = [c for c in columns if c in upcoming.columns]
    upcoming[available].to_csv(output_path, index=False)
    print(f"Saved Monte Carlo results to {output_path}")

    summary = upcoming.sort_values("monte_carlo_anytime_td_prob", ascending=False).groupby("team").head(3)
    display_cols = ["player", "team", "upcoming_opponent", "role", "monte_carlo_anytime_td_prob"]
    print(summary[display_cols].to_string(index=False, formatters={"monte_carlo_anytime_td_prob": "{:.2%}".format}))


if __name__ == "__main__":
    main()
