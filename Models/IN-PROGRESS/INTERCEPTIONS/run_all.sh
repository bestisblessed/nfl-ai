#!/bin/bash
#
# Master script to run complete QB Interception Odds Analysis pipeline
#
# Usage: ./run_all.sh
#

set -e  # Exit on error

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║     QB INTERCEPTION ODDS ANALYSIS - COMPLETE PIPELINE         ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Get week number from user
read -p "Enter NFL week number: " WEEK_NUM

# Validate input
if ! [[ "$WEEK_NUM" =~ ^[0-9]+$ ]]; then
    echo "❌ Error: Please enter a valid week number (e.g., 7)"
    exit 1
fi

echo ""
echo "📅 Running analysis for NFL Week $WEEK_NUM"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Step 1: Train models (optional - can skip if already trained)
echo "🔨 STEP 1: Training ML Models..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
read -p "Train models? (y/n, default=n): " TRAIN
if [[ "$TRAIN" =~ ^[Yy]$ ]]; then
    python3 train_qb_interceptions_model.py
    echo "✓ Models trained"
else
    echo "⊗ Skipped training (using existing models)"
fi
echo ""

# Step 2: Scrape odds
echo "🌐 STEP 2: Scraping DraftKings Odds..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python3 1_scrape_odds.py --force
echo "✓ Odds scraped"
echo ""

# Step 3: Generate predictions
echo "🎯 STEP 3: Generating Predictions (Week $WEEK_NUM)..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python3 predict_qb_interceptions.py --week $WEEK_NUM --model logistic_regression
echo "✓ Predictions generated"
echo ""

# Step 4: Calculate edges
echo "📊 STEP 4: Calculating Betting Edges..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python3 2_calculate_edges.py
echo ""

# Optional: Generate HTML report
read -p "Generate HTML report? (y/n, default=n): " REPORT
if [[ "$REPORT" =~ ^[Yy]$ ]]; then
    echo ""
    echo "📋 Generating Final Report..."
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    python3 generate_final_report.py --week $WEEK_NUM
    echo "✓ Report generated: predictions/week_${WEEK_NUM}_qb_interception_report.html"
fi

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                    ✅ ANALYSIS COMPLETE                        ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "📁 Output files:"
echo "   • Odds:        data/odds_interceptions_dk_latest.csv"
echo "   • Predictions: predictions/upcoming_qb_interception_logistic_regression_week_${WEEK_NUM}.csv"
echo "   • Edges:       predictions/betting_edges_latest.csv"
if [[ "$REPORT" =~ ^[Yy]$ ]]; then
    echo "   • Report:      predictions/week_${WEEK_NUM}_qb_interception_report.html"
fi
echo ""
echo "💡 Tip: Re-run 'python3 1_scrape_odds.py --force' if odds change significantly"
echo ""

# Cleanup
rm -rf __pycache__
rm -f utils/__pycache__
