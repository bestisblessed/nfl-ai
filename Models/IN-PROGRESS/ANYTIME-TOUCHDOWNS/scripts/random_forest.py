"""Random forest touchdown probability model."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import accuracy_score, log_loss, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

from .data_utils import (
    FeatureSet,
    add_game_context_features,
    load_player_stats,
    prepare_training_frame,
    prepare_upcoming_features,
)


def probability_to_american_odds(probability: float) -> float:
    probability = np.clip(probability, 1e-6, 1 - 1e-6)
    if probability >= 0.5:
        return -100 * (probability / (1 - probability))
    return 100 * ((1 - probability) / probability)


def train_model() -> tuple[Pipeline, pd.DataFrame, FeatureSet]:
    full_history = add_game_context_features(load_player_stats())
    training_df, feature_set = prepare_training_frame()
    X = training_df[feature_set.feature_columns]
    y = training_df[feature_set.target_column]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=42, stratify=y
    )

    pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            (
                "rf",
                RandomForestClassifier(
                    n_estimators=300,
                    max_depth=8,
                    min_samples_leaf=40,
                    random_state=42,
                    class_weight="balanced_subsample",
                    n_jobs=-1,
                ),
            ),
        ]
    )
    pipeline.fit(X_train, y_train)

    y_proba = pipeline.predict_proba(X_test)[:, 1]
    y_pred = (y_proba >= 0.5).astype(int)

    metrics = {
        "accuracy": accuracy_score(y_test, y_pred),
        "roc_auc": roc_auc_score(y_test, y_proba),
        "log_loss": log_loss(y_test, y_proba),
    }

    print("=== Random Forest Evaluation ===")
    for name, value in metrics.items():
        print(f"{name:>10s}: {value:.3f}")

    return pipeline, full_history, feature_set


def upcoming_predictions(
    model: Pipeline,
    history_df: pd.DataFrame,
    feature_set: FeatureSet,
    upcoming_path: Path | None = None,
) -> pd.DataFrame:
    upcoming = prepare_upcoming_features(history_df, upcoming_games_path=upcoming_path)
    feature_matrix = upcoming[feature_set.feature_columns]
    probabilities = model.predict_proba(feature_matrix)[:, 1]
    return upcoming.assign(
        touchdown_probability=probabilities,
        american_odds=[probability_to_american_odds(p) for p in probabilities],
    ).sort_values("touchdown_probability", ascending=False)


def main(upcoming_path: str | None = None) -> None:
    model, history_df, feature_set = train_model()
    predictions = upcoming_predictions(
        model,
        history_df,
        feature_set,
        Path(upcoming_path) if upcoming_path is not None else None,
    )

    print("\n=== Upcoming Week Touchdown Probabilities (Random Forest) ===")
    for team, group in predictions.groupby("team"):
        print(f"\n{team} vs {group['opponent_team'].iloc[0]}")
        top_players = group.nlargest(5, "touchdown_probability")
        for _, row in top_players.iterrows():
            prob = row["touchdown_probability"]
            odds = row["american_odds"]
            print(f"  {row['player']:<25s} {prob:>6.2%}  odds: {odds:>7.0f}")

    output_path = Path(__file__).resolve().parents[0] / "random_forest_predictions.csv"
    predictions.to_csv(output_path, index=False)
    print(f"\nSaved predictions to {output_path}")


if __name__ == "__main__":
    main()
