"""Touchdown probability model using LightGBM."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
from lightgbm import LGBMClassifier
from sklearn.metrics import accuracy_score, classification_report, log_loss, roc_auc_score

if __package__ is None or __package__ == "":
    current_dir = Path(__file__).resolve().parent
    sys.path.append(str(current_dir))
    from data_utils import DatasetBundle, prepare_datasets, probability_to_american_odds
else:  # pragma: no cover - fallback for package execution
    from .data_utils import DatasetBundle, prepare_datasets, probability_to_american_odds


OUTPUT_DIR = Path(__file__).resolve().parent / "outputs"
OUTPUT_DIR.mkdir(exist_ok=True)


def train_lightgbm(bundle: DatasetBundle) -> LGBMClassifier:
    features = bundle.feature_columns
    X = bundle.train[features]
    y = bundle.train["scored_td"]

    model = LGBMClassifier(
        objective="binary",
        boosting_type="gbdt",
        learning_rate=0.05,
        n_estimators=600,
        num_leaves=48,
        subsample=0.9,
        colsample_bytree=0.8,
        reg_alpha=0.2,
        reg_lambda=0.6,
        random_state=42,
        class_weight="balanced",
    )
    model.fit(X, y)
    return model


def evaluate(model: LGBMClassifier, bundle: DatasetBundle) -> None:
    if bundle.validation.empty:
        print("No in-season validation data available for evaluation.")
        return

    features = bundle.feature_columns
    X_val = bundle.validation[features]
    y_val = bundle.validation["scored_td"]

    proba = model.predict_proba(X_val)[:, 1]
    preds = (proba >= 0.5).astype(int)

    print("Validation accuracy:", accuracy_score(y_val, preds))
    print("Validation ROC-AUC:", roc_auc_score(y_val, proba))
    print("Validation log loss:", log_loss(y_val, proba))
    print("Class breakdown:\n", classification_report(y_val, preds, digits=3))


def run_inference(
    model: LGBMClassifier,
    bundle: DatasetBundle,
    upcoming_week: int,
) -> pd.DataFrame:
    features = bundle.feature_columns
    X_upcoming = bundle.upcoming[features]
    probabilities = model.predict_proba(X_upcoming)[:, 1]

    results = bundle.upcoming[[
        "player",
        "team",
        "opponent_team",
        "games_played_prior",
        "touches_rolling",
        "total_tds_rolling",
        "total_tds_season_avg",
    ]].copy()
    results["model"] = "lightgbm"
    results["probability"] = probabilities
    results["american_odds"] = results["probability"].apply(probability_to_american_odds)
    results["upcoming_week"] = upcoming_week

    results.sort_values("probability", ascending=False, inplace=True)
    results = results.drop_duplicates(subset=["player", "team", "opponent_team"])
    return results


def main(upcoming_week: int = 7) -> None:
    bundle = prepare_datasets(upcoming_week=upcoming_week)
    model = train_lightgbm(bundle)
    evaluate(model, bundle)

    predictions = run_inference(model, bundle, upcoming_week)
    print("Top 10 touchdown probabilities for Week", upcoming_week)
    print(predictions.head(10))

    output_path = OUTPUT_DIR / f"lightgbm_predictions_week{upcoming_week}.csv"
    predictions.to_csv(output_path, index=False)
    print(f"Saved predictions to {output_path}")


if __name__ == "__main__":
    main()
