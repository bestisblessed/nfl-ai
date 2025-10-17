"""Backtesting utilities for anytime touchdown models."""
from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterable, Tuple

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, brier_score_loss, log_loss, roc_auc_score
from xgboost import XGBClassifier

from feature_engineering import ROLLING_WINDOW, build_training_table

OUTPUT_DIR = Path("/workspace/nfl-ai/Models/IN-PROGRESS/anytime_touchdown_models")
RANDOM_STATE = 42


def _prob_to_american(probabilities: Iterable[float]) -> np.ndarray:
    """Convert probabilities to American moneyline odds."""
    probs = np.clip(np.asarray(list(probabilities), dtype=float), 1e-6, 1 - 1e-6)
    favorites = probs >= 0.5
    odds = np.empty_like(probs)
    odds[favorites] = -100 * probs[favorites] / (1 - probs[favorites])
    odds[~favorites] = 100 * (1 - probs[~favorites]) / probs[~favorites]
    return odds


def _monte_carlo_probs(feature_frame: pd.DataFrame) -> np.ndarray:
    """Closed-form approximation of the Monte Carlo model."""
    player_rate = feature_frame[f"total_tds_rolling_{ROLLING_WINDOW}"].clip(lower=0.0).to_numpy()
    defense_recent = feature_frame[f"tds_allowed_rolling_{ROLLING_WINDOW}"].clip(lower=0.0).to_numpy()
    defense_baseline = feature_frame["tds_allowed_avg"].clip(lower=1e-6).to_numpy()
    defense_factor = np.divide(
        defense_recent,
        defense_baseline,
        out=np.ones_like(defense_recent),
        where=defense_baseline > 0,
    )
    lam = np.clip(player_rate * defense_factor, 1e-4, None)
    return 1.0 - np.exp(-lam)


def _evaluate_predictions(y_true: np.ndarray, y_prob: np.ndarray, actual_line: float) -> Dict[str, float]:
    clipped = np.clip(y_prob, 1e-6, 1 - 1e-6)
    metrics: Dict[str, float] = {
        "brier": brier_score_loss(y_true, clipped),
        "log_loss": log_loss(y_true, clipped),
        "accuracy": accuracy_score(y_true, clipped >= 0.5),
        "line_mae": float(np.mean(np.abs(_prob_to_american(clipped) - actual_line))),
        "probability_mae": float(np.mean(np.abs(clipped - y_true))),
    }
    if len(np.unique(y_true)) > 1:
        metrics["roc_auc"] = roc_auc_score(y_true, clipped)
    else:
        metrics["roc_auc"] = float("nan")
    return metrics


def _fit_models(X_train: pd.DataFrame, y_train: pd.Series) -> Dict[str, object]:
    models: Dict[str, object] = {}

    logreg = LogisticRegression(max_iter=2000, class_weight="balanced", random_state=RANDOM_STATE)
    logreg.fit(X_train, y_train)
    models["logistic_regression"] = logreg

    forest = RandomForestClassifier(
        n_estimators=150,
        max_depth=8,
        min_samples_leaf=50,
        class_weight="balanced",
        random_state=RANDOM_STATE,
        n_jobs=-1,
    )
    forest.fit(X_train, y_train)
    models["random_forest"] = forest

    xgb = XGBClassifier(
        objective="binary:logistic",
        eval_metric="logloss",
        learning_rate=0.05,
        max_depth=4,
        subsample=0.8,
        colsample_bytree=0.8,
        n_estimators=250,
        reg_lambda=1.0,
        reg_alpha=0.5,
        random_state=RANDOM_STATE,
        n_jobs=-1,
        tree_method="hist",
        verbosity=0,
    )
    xgb.fit(X_train, y_train)
    models["xgboost"] = xgb

    return models


def run_backtest() -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Run a season-wise walk-forward backtest for each model."""
    model_data = build_training_table(window=ROLLING_WINDOW)
    features = model_data.features
    target = model_data.target
    metadata = model_data.metadata

    seasons = sorted(metadata["season"].unique())
    season_results = []

    for season in seasons:
        train_mask = metadata["season"] < season
        test_mask = metadata["season"] == season
        if not train_mask.any() or not test_mask.any():
            continue

        print(f"Evaluating season {season}...", flush=True)

        X_train = features.loc[train_mask]
        y_train = target.loc[train_mask]
        X_test = features.loc[test_mask]
        y_test = target.loc[test_mask]

        models = _fit_models(X_train, y_train)
        actual_prob = (y_test.sum() + 1) / (len(y_test) + 2)
        actual_line = float(_prob_to_american([actual_prob])[0])

        for name, model in models.items():
            y_prob = model.predict_proba(X_test)[:, 1]
            metrics = _evaluate_predictions(y_test.to_numpy(), y_prob, actual_line)
            season_results.append(
                {
                    "season": season,
                    "model": name,
                    "samples": len(y_test),
                    "actual_probability": actual_prob,
                    **metrics,
                }
            )

        # Monte Carlo style evaluation using closed-form estimate
        mc_probs = _monte_carlo_probs(X_test)
        metrics = _evaluate_predictions(y_test.to_numpy(), mc_probs, actual_line)
        season_results.append(
            {
                "season": season,
                "model": "monte_carlo",
                "samples": len(y_test),
                "actual_probability": actual_prob,
                **metrics,
            }
        )

        print(f"  Completed season {season} with {len(y_test)} samples.", flush=True)

    season_df = pd.DataFrame(season_results)
    if season_df.empty:
        raise RuntimeError("No seasons available for backtesting.")

    weighted = season_df.groupby("model").apply(
        lambda df: pd.Series(
            {
                "brier": np.average(df["brier"], weights=df["samples"]),
                "log_loss": np.average(df["log_loss"], weights=df["samples"]),
                "accuracy": np.average(df["accuracy"], weights=df["samples"]),
                "roc_auc": np.average(df["roc_auc"].fillna(0.5), weights=df["samples"]),
                "line_mae": np.average(df["line_mae"], weights=df["samples"]),
                "probability_mae": np.average(df["probability_mae"], weights=df["samples"]),
                "samples": df["samples"].sum(),
            }
        ),
        include_groups=False,
    )
    weighted = weighted.reset_index().sort_values("brier")

    return season_df, weighted


def main() -> None:
    season_df, summary_df = run_backtest()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    season_path = OUTPUT_DIR / "backtest_season_results.csv"
    summary_path = OUTPUT_DIR / "backtest_summary.csv"
    season_df.to_csv(season_path, index=False)
    summary_df.to_csv(summary_path, index=False)

    print("Backtest summary (lower is better for Brier, log_loss, line_mae):")
    print(
        summary_df.to_string(
            index=False,
            formatters={
                "brier": "{:.4f}".format,
                "log_loss": "{:.4f}".format,
                "accuracy": "{:.3f}".format,
                "roc_auc": "{:.3f}".format,
                "line_mae": "{:.1f}".format,
                "probability_mae": "{:.3f}".format,
            },
        )
    )
    print(f"Detailed season metrics saved to {season_path}")
    print(f"Summary metrics saved to {summary_path}")


if __name__ == "__main__":
    main()
