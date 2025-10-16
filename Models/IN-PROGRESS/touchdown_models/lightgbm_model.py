"""Touchdown probability model using LightGBM."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd
from lightgbm import LGBMClassifier
from sklearn.metrics import accuracy_score, classification_report, log_loss, roc_auc_score
from tabulate import tabulate

if __package__ is None or __package__ == "":
    current_dir = Path(__file__).resolve().parent
    sys.path.append(str(current_dir))
    from data_utils import DatasetBundle, prepare_datasets, probability_to_american_odds
else:  # pragma: no cover - fallback for package execution
    from .data_utils import DatasetBundle, prepare_datasets, probability_to_american_odds


OUTPUT_DIR = "/Users/td/Code/nfl-ai/Models/IN-PROGRESS/touchdown_models/outputs"
Path(OUTPUT_DIR).mkdir(exist_ok=True)


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
        "position",
        "team",
        "opponent_team",
    ]].copy()
    results["model"] = "lightgbm"
    results["probability"] = probabilities
    results["american_odds"] = results["probability"].apply(probability_to_american_odds)
    results["upcoming_week"] = upcoming_week

    results.sort_values("probability", ascending=False, inplace=True)
    results = results.drop_duplicates(subset=["player", "team", "opponent_team"])
    return results


def main(upcoming_week: int = 7, home_team: str = None, away_team: str = None) -> None:
    bundle = prepare_datasets(upcoming_week=upcoming_week)
    model = train_lightgbm(bundle)
    evaluate(model, bundle)

    predictions = run_inference(model, bundle, upcoming_week)

    # Filter by matchup if specified
    if home_team and away_team:
        predictions = predictions[
            ((predictions['team'] == home_team) & (predictions['opponent_team'] == away_team)) |
            ((predictions['team'] == away_team) & (predictions['opponent_team'] == home_team))
        ]
        matchup_str = f"{home_team} vs {away_team}"
        print(f"Top touchdown probabilities for Week {upcoming_week} - {matchup_str}")
    else:
        print(f"Top 30 touchdown probabilities for Week {upcoming_week}")

    display_count = len(predictions) if (home_team and away_team) else 30
    # Custom formatter to add + signs to positive numbers (whole numbers)
    def format_with_plus(val):
        try:
            num = float(val)
            if num > 0:
                return f"+{int(num)}"
            else:
                return f"{int(num)}"
        except (ValueError, TypeError):
            return str(val)

    formatted_predictions = predictions.head(display_count).copy()
    formatted_predictions['american_odds'] = formatted_predictions['american_odds'].apply(format_with_plus)

    print(tabulate(formatted_predictions, headers='keys', tablefmt='presto', floatfmt='.3f', numalign='right', showindex=False))

    output_path = f"{OUTPUT_DIR}/lightgbm_predictions_week{upcoming_week}.csv"
    predictions.to_csv(output_path, index=False)
    print(f"Saved predictions to {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='LightGBM Touchdown Predictor')
    parser.add_argument('--matchup', nargs=2, metavar=('HOME_TEAM', 'AWAY_TEAM'),
                       help='Filter predictions to specific matchup (e.g., PHI MIN)')
    args = parser.parse_args()

    main(home_team=args.matchup[0] if args.matchup else None,
         away_team=args.matchup[1] if args.matchup else None)
