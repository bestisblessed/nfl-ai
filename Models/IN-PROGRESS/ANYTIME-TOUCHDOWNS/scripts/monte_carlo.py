"""Monte Carlo touchdown simulation using Poisson draws."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from .data_utils import (
    add_game_context_features,
    league_touchdown_rate,
    load_player_stats,
    prepare_upcoming_features,
)

SIMULATIONS = 20000
MIN_BASE_RATE = 0.02


def compute_league_baselines(history_df: pd.DataFrame, season: int) -> dict[str, float]:
    season_df = history_df[history_df["season"] == season].copy()
    season_df["total_td"] = season_df["rush_td"] + season_df["rec_td"]
    player_rate = league_touchdown_rate(history_df, season=season)
    team_scored = season_df.groupby(["week", "team"], as_index=False)["total_td"].sum()
    team_allowed = season_df.groupby(["week", "opponent_team"], as_index=False)["total_td"].sum()
    return {
        "player_rate": max(player_rate, MIN_BASE_RATE),
        "team_scored": max(team_scored["total_td"].mean(), MIN_BASE_RATE),
        "team_allowed": max(team_allowed["total_td"].mean(), MIN_BASE_RATE),
    }


def simulate_touchdowns(
    player_row: pd.Series,
    baselines: dict[str, float],
    window: int = 3,
    simulations: int = SIMULATIONS,
) -> dict[str, float]:
    player_rate = player_row.get(f"td_rate_l{window}", np.nan)
    if not np.isfinite(player_rate) or player_rate <= 0:
        player_rate = baselines["player_rate"]

    team_rate = player_row.get(f"team_td_scored_l{window}", np.nan)
    if not np.isfinite(team_rate) or team_rate <= 0:
        team_rate = baselines["team_scored"]

    opponent_rate = player_row.get(f"opp_td_allowed_l{window}", np.nan)
    if not np.isfinite(opponent_rate) or opponent_rate <= 0:
        opponent_rate = baselines["team_allowed"]

    opponent_factor = opponent_rate / baselines["team_allowed"]
    team_factor = team_rate / baselines["team_scored"]

    lam = max(player_rate * opponent_factor * team_factor, MIN_BASE_RATE)
    samples = np.random.poisson(lam, simulations)

    probability_any = (samples >= 1).mean()
    probability_two = (samples >= 2).mean()
    mean_tds = samples.mean()

    return {
        "expected_tds": mean_tds,
        "probability_at_least_one": probability_any,
        "probability_at_least_two": probability_two,
        "american_odds_any": probability_to_american_odds(probability_any),
    }


def probability_to_american_odds(probability: float) -> float:
    probability = np.clip(probability, 1e-6, 1 - 1e-6)
    if probability >= 0.5:
        return -100 * (probability / (1 - probability))
    return 100 * ((1 - probability) / probability)


def main(upcoming_path: str | None = None) -> None:
    raw_df = load_player_stats()
    history_df = add_game_context_features(raw_df)
    current_season = int(history_df["season"].max())
    baselines = compute_league_baselines(history_df, current_season)

    upcoming = prepare_upcoming_features(
        history_df,
        upcoming_games_path=Path(upcoming_path) if upcoming_path is not None else None,
        current_season=current_season,
    )

    results = []
    for _, row in upcoming.iterrows():
        simulation = simulate_touchdowns(row, baselines)
        results.append({**row.to_dict(), **simulation})

    results_df = pd.DataFrame(results)
    results_df.sort_values("probability_at_least_one", ascending=False, inplace=True)

    print("=== Monte Carlo Touchdown Simulation ===")
    for team, group in results_df.groupby("team"):
        print(f"\n{team} vs {group['opponent_team'].iloc[0]}")
        top_players = group.nlargest(5, "probability_at_least_one")
        for _, player in top_players.iterrows():
            prob = player["probability_at_least_one"]
            odds = player["american_odds_any"]
            exp_tds = player["expected_tds"]
            print(
                f"  {player['player']:<25s} {prob:>6.2%}  exp TDs: {exp_tds:>4.2f}  odds: {odds:>7.0f}"
            )

    output_path = Path(__file__).resolve().parents[0] / "monte_carlo_predictions.csv"
    results_df.to_csv(output_path, index=False)
    print(f"\nSaved simulations to {output_path}")


if __name__ == "__main__":
    main()
