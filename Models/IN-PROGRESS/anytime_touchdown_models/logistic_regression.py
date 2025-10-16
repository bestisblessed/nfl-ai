"""Logistic regression baseline for anytime touchdown probabilities."""
from __future__ import annotations

from pathlib import Path

import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, brier_score_loss, roc_auc_score
from sklearn.model_selection import train_test_split

from feature_engineering import (
    ROLLING_WINDOW,
    build_training_table,
    build_upcoming_features,
    load_player_stats,
)


def train_model(test_size: float = 0.2, random_state: int = 42) -> tuple[LogisticRegression, pd.DataFrame, tuple[str, ...]]:
    model_data = build_training_table(window=ROLLING_WINDOW)

    X_train, X_valid, y_train, y_valid = train_test_split(
        model_data.features,
        model_data.target,
        test_size=test_size,
        random_state=random_state,
        stratify=model_data.target,
    )

    model = LogisticRegression(max_iter=2000, class_weight="balanced")
    model.fit(X_train, y_train)

    y_proba = model.predict_proba(X_valid)[:, 1]
    y_pred = (y_proba >= 0.5).astype(int)

    metrics = {
        "accuracy": accuracy_score(y_valid, y_pred),
        "roc_auc": roc_auc_score(y_valid, y_proba),
        "brier": brier_score_loss(y_valid, y_proba),
    }
    print("Validation metrics:")
    for name, value in metrics.items():
        print(f"  {name}: {value:.3f}")

    return model, model_data.features, model_data.feature_columns


def latest_season_and_week() -> tuple[int, int]:
    stats = load_player_stats()
    current_season = stats["season"].max()
    last_completed_week = int(stats.loc[stats["season"] == current_season, "week"].max())
    return current_season, last_completed_week


def generate_predictions(model: LogisticRegression, feature_columns: tuple[str, ...]) -> pd.DataFrame:
    season, last_week = latest_season_and_week()
    upcoming = build_upcoming_features(season=season, last_completed_week=last_week, window=ROLLING_WINDOW)

    feature_frame = upcoming.reindex(columns=feature_columns, fill_value=0.0)
    probabilities = model.predict_proba(feature_frame)[:, 1]
    upcoming = upcoming.copy()
    upcoming["logreg_anytime_td_prob"] = probabilities
    upcoming = upcoming.sort_values(["team", "logreg_anytime_td_prob"], ascending=[True, False])
    return upcoming


def save_predictions(predictions: pd.DataFrame, output_path: Path) -> None:
    columns = [
        "player",
        "team",
        "upcoming_opponent",
        "role",
        "games_played_3",
        "logreg_anytime_td_prob",
    ]
    # Some helper columns may be missing depending on dummy expansion.
    available_columns = [col for col in columns if col in predictions.columns]
    predictions[available_columns].to_csv(output_path, index=False)
    print(f"Saved predictions to {output_path}")


def main() -> None:
    model, _, feature_columns = train_model()
    predictions = generate_predictions(model, feature_columns)

    output_dir = Path(__file__).resolve().parent
    save_predictions(predictions, output_dir / "logistic_regression_week7.csv")

    print("Top probabilities by team:")
    summary = (
        predictions
        .groupby(["team"])
        .head(3)
        .loc[:, ["player", "team", "upcoming_opponent", "role", "logreg_anytime_td_prob"]]
    )
    print(summary.to_string(index=False, formatters={"logreg_anytime_td_prob": "{:.2%}".format}))


if __name__ == "__main__":
    main()
