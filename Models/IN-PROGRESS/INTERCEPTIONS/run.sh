#!/bin/bash

# cd /Users/td/Code/nfl-ai/Models/IN-PROGRESS/INTERCEPTIONS

# Train all models
python train_interception_model.py
printf "\n\n%s\n\n" "$(printf '=%.0s' {1..100})"

# Predict upcoming games with all models
echo "Predicting with Logistic Regression..."
python predict_upcoming_starting_qbs.py --model logistic_regression
printf "\n\n%s\n\n" "$(printf '=%.0s' {1..50})"
echo "Predicting with Random Forest..."
python predict_upcoming_starting_qbs.py --model random_forest
printf "\n\n%s\n\n" "$(printf '=%.0s' {1..50})"
echo "Predicting with XGBoost..."
python predict_upcoming_starting_qbs.py --model xgboost

# Scrape DraftKings Interceptions O/U odds (latest)
echo "Scraping DraftKings Interceptions O/U odds..."
python scrape_interception_odds.py

# Compare predictions (uses latest LR predictions automatically)
echo "Comparing model predictions vs DK odds..."
python compare_odds_to_model.py

# Clean up
rm -rf __pycache*
rm *_model.pkl