"""Monte Carlo touchdown simulator based on rolling touchdown rates."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from tabulate import tabulate

if __package__ is None or __package__ == "":
    current_dir = Path(__file__).resolve().parent
    sys.path.append(str(current_dir))
    from data_utils import (
        DatasetBundle,
        load_league_baselines,
        prepare_datasets,
        probability_to_american_odds,
    )
else:  # pragma: no cover - fallback for package execution
    from .data_utils import (
        DatasetBundle,
        load_league_baselines,
        prepare_datasets,
        probability_to_american_odds,
    )


OUTPUT_DIR = "/Users/td/Code/nfl-ai/Models/IN-PROGRESS/touchdown_models/outputs"
Path(OUTPUT_DIR).mkdir(exist_ok=True)
SIMULATIONS = 10000


def compute_expected_tds(row: pd.Series, baselines: dict[str, float]) -> float:
    player_rate = row.get("total_tds_season_avg", 0.0)
    if not np.isfinite(player_rate) or player_rate <= 0:
        player_rate = baselines["player_td_rate"]

    team_factor = row.get("team_td_scored_feature", baselines["team_td_scored"])
    opp_factor = row.get("opp_td_allowed_feature", baselines["opp_td_allowed"])

    team_adj = team_factor / max(baselines["team_td_scored"], 1e-6)
    opp_adj = opp_factor / max(baselines["opp_td_allowed"], 1e-6)

    expected = player_rate * team_adj * opp_adj
    return float(max(expected, 1e-3))


def run_simulation(bundle: DatasetBundle) -> pd.DataFrame:
    baselines = load_league_baselines(bundle.train)
    records = []

    for _, row in bundle.upcoming.iterrows():
        lam = compute_expected_tds(row, baselines)
        sims = np.random.poisson(lam, SIMULATIONS)
        prob_ge_one = np.mean(sims >= 1)
        prob_ge_two = np.mean(sims >= 2)

        records.append(
            {
                "player": row.get("player"),
                "position": row.get("position") or "",
                "team": row.get("team"),
                "opponent_team": row.get("opponent_team"),
                "probability": prob_ge_one,
                "probability_two_plus": prob_ge_two,
                "american_odds": probability_to_american_odds(prob_ge_one),
            }
        )

    results = pd.DataFrame(records).sort_values("probability", ascending=False)
    results = results.drop_duplicates(subset=["player", "team", "opponent_team"])
    results["model"] = "monte_carlo"
    return results


def main(upcoming_week: int = 7) -> None:
    bundle = prepare_datasets(upcoming_week=upcoming_week)
    results = run_simulation(bundle)

    print(f"Top 30 simulated touchdown probabilities for Week {upcoming_week}")
    print(tabulate(results.head(30), headers='keys', tablefmt='presto', floatfmt='.3f', numalign='right', showindex=False))

    output_path = f"{OUTPUT_DIR}/monte_carlo_predictions_week{upcoming_week}.csv"
    results.to_csv(output_path, index=False)
    print(f"Saved predictions to {output_path}")


if __name__ == "__main__":
    main()
