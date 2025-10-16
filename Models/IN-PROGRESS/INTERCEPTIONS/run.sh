#!/bin/bash

# cd /Users/td/Code/nfl-ai/Models/IN-PROGRESS/INTERCEPTIONS


read -p "Enter the NFL week number to predict: " WEEK_NUM

# Validate input is a number
if ! [[ "$WEEK_NUM" =~ ^[0-9]+$ ]]; then
    echo "❌ Error: Please enter a valid week number (e.g., 7)"
    exit 1
fi

echo "📅 Running predictions for NFL Week $WEEK_NUM"
echo ""

# Train all models
python train_qb_interceptions_model.py
printf "\n\n%s\n\n" "$(printf '=%.0s' {1..100})"

# Predict upcoming games with all models
echo "🎯 Predicting with Logistic Regression (Week $WEEK_NUM)..."
python predict_qb_interceptions.py --model logistic_regression --week $WEEK_NUM
printf "\n\n%s\n\n" "$(printf '=%.0s' {1..50})"

echo "🎯 Predicting with Random Forest (Week $WEEK_NUM)..."
python predict_qb_interceptions.py --model random_forest --week $WEEK_NUM
printf "\n\n%s\n\n" "$(printf '=%.0s' {1..50})"

echo "🎯 Predicting with XGBoost (Week $WEEK_NUM)..."
python predict_qb_interceptions.py --model xgboost --week $WEEK_NUM
printf "\n\n%s\n\n" "$(printf '=%.0s' {1..50})"

# Scrape DraftKings Interceptions O/U odds (latest)
echo "Scraping DraftKings Interceptions O/U odds..."
python scrape_qb_interceptions_odds.py

# Compare predictions (uses latest LR predictions automatically)
echo "Comparing model predictions vs DK odds (Week $WEEK_NUM)..."
python calc_edges.py

# Create final visual report
echo "📋 Creating final visual report..."
python generate_final_report.py --week $WEEK_NUM
FINAL_REPORT="predictions/week_${WEEK_NUM}_qb_interception_report.html"

echo ""
echo "✅ Week $WEEK_NUM predictions complete!"
echo "📁 Files saved to 'predictions/' directory:"
echo "   📄 CSV files: Individual model predictions"
echo "   📊 Edge analysis: Betting opportunities"
echo "   🌐 Final report: $FINAL_REPORT (open in browser)"
echo ""
echo "🔗 To view the report: open $FINAL_REPORT in your web browser"

# Clean up
rm -rf __pycache*
rm *_model.pkl