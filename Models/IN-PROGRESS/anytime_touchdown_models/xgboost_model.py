"""XGBoost classifier mirroring the experimental notebooks."""
from __future__ import annotations

from pathlib import Path

import pandas as pd
from sklearn.metrics import accuracy_score, roc_auc_score
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier

from feature_engineering import (
    ROLLING_WINDOW,
    build_training_table,
    build_upcoming_features,
    load_player_stats,
)


OUTPUT_DIR = Path("/workspace/nfl-ai/Models/IN-PROGRESS/anytime_touchdown_models")


def train_model(test_size: float = 0.2, random_state: int = 42) -> tuple[XGBClassifier, tuple[str, ...]]:
    model_data = build_training_table(window=ROLLING_WINDOW)
    X_train, X_valid, y_train, y_valid = train_test_split(
        model_data.features,
        model_data.target,
        test_size=test_size,
        random_state=random_state,
        stratify=model_data.target,
    )

    model = XGBClassifier(
        objective="binary:logistic",
        eval_metric="logloss",
        learning_rate=0.05,
        max_depth=4,
        subsample=0.8,
        colsample_bytree=0.8,
        n_estimators=250,
        reg_lambda=1.0,
        reg_alpha=0.5,
        random_state=random_state,
        n_jobs=-1,
        tree_method="hist",
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


def generate_predictions(model: XGBClassifier, feature_columns: tuple[str, ...]) -> pd.DataFrame:
    season, last_week = latest_season_and_week()
    upcoming = build_upcoming_features(season=season, last_completed_week=last_week, window=ROLLING_WINDOW)
    feature_frame = upcoming.reindex(columns=feature_columns, fill_value=0.0)
    upcoming = upcoming.copy()
    upcoming["xgboost_anytime_td_prob"] = model.predict_proba(feature_frame)[:, 1]
    upcoming = upcoming.sort_values(["team", "xgboost_anytime_td_prob"], ascending=[True, False])
    return upcoming


def save_predictions(predictions: pd.DataFrame, output_path: Path) -> None:
    columns = [
        "player",
        "team",
        "upcoming_opponent",
        "role",
        "games_played_3",
        "xgboost_anytime_td_prob",
    ]
    available = [c for c in columns if c in predictions.columns]
    predictions[available].to_csv(output_path, index=False)
    print(f"Saved predictions to {output_path}")


def main() -> None:
    model, feature_columns = train_model()
    predictions = generate_predictions(model, feature_columns)

    save_predictions(predictions, OUTPUT_DIR / "xgboost_week7.csv")

    print("Top probabilities by team:")
    display_cols = ["player", "team", "upcoming_opponent", "role", "xgboost_anytime_td_prob"]
    summary = predictions.groupby("team").head(3)[display_cols]
    print(summary.to_string(index=False, formatters={"xgboost_anytime_td_prob": "{:.2%}".format}))


if __name__ == "__main__":
    main()
