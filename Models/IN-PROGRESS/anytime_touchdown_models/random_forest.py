"""Random forest classifier for anytime touchdown prediction."""
from __future__ import annotations

from pathlib import Path

import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, roc_auc_score
from sklearn.model_selection import train_test_split

from feature_engineering import (
    ROLLING_WINDOW,
    build_training_table,
    build_upcoming_features,
    load_player_stats,
)


def train_model(test_size: float = 0.2, random_state: int = 42) -> tuple[RandomForestClassifier, tuple[str, ...]]:
    model_data = build_training_table(window=ROLLING_WINDOW)
    X_train, X_valid, y_train, y_valid = train_test_split(
        model_data.features,
        model_data.target,
        test_size=test_size,
        random_state=random_state,
        stratify=model_data.target,
    )

    model = RandomForestClassifier(
        n_estimators=300,
        max_depth=8,
        min_samples_leaf=50,
        class_weight="balanced",
        random_state=random_state,
        n_jobs=-1,
    )
    model.fit(X_train, y_train)

    y_proba = model.predict_proba(X_valid)[:, 1]
    y_pred = (y_proba >= 0.5).astype(int)

    print("Validation metrics:")
    print(f"  accuracy: {accuracy_score(y_valid, y_pred):.3f}")
    print(f"  roc_auc: {roc_auc_score(y_valid, y_proba):.3f}")

    return model, model_data.feature_columns


def latest_season_and_week() -> tuple[int, int]:
    stats = load_player_stats()
    season = stats["season"].max()
    last_week = int(stats.loc[stats["season"] == season, "week"].max())
    return season, last_week


def generate_predictions(model: RandomForestClassifier, feature_columns: tuple[str, ...]) -> pd.DataFrame:
    season, last_week = latest_season_and_week()
    upcoming = build_upcoming_features(season=season, last_completed_week=last_week, window=ROLLING_WINDOW)
    feature_frame = upcoming.reindex(columns=feature_columns, fill_value=0.0)
    upcoming = upcoming.copy()
    upcoming["random_forest_anytime_td_prob"] = model.predict_proba(feature_frame)[:, 1]
    upcoming = upcoming.sort_values(["team", "random_forest_anytime_td_prob"], ascending=[True, False])
    return upcoming


def save_predictions(predictions: pd.DataFrame, output_path: Path) -> None:
    columns = [
        "player",
        "team",
        "upcoming_opponent",
        "role",
        "games_played_3",
        "random_forest_anytime_td_prob",
    ]
    available = [c for c in columns if c in predictions.columns]
    predictions[available].to_csv(output_path, index=False)
    print(f"Saved predictions to {output_path}")


def main() -> None:
    model, feature_columns = train_model()
    predictions = generate_predictions(model, feature_columns)

    output_dir = Path(__file__).resolve().parent
    save_predictions(predictions, output_dir / "random_forest_week7.csv")

    print("Top probabilities by team:")
    display_cols = ["player", "team", "upcoming_opponent", "role", "random_forest_anytime_td_prob"]
    summary = predictions.groupby("team").head(3)[display_cols]
    print(summary.to_string(index=False, formatters={"random_forest_anytime_td_prob": "{:.2%}".format}))


if __name__ == "__main__":
    main()
