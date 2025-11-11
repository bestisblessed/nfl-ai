#!/bin/bash
set -e

WEEK=${1:-10}

echo "================================================"
echo "v3 Touchdown Prediction Pipeline - Week $WEEK"
echo "================================================"

echo ""
echo "Step 1: Preparing training data..."
python3 prepare_data_v3.py

echo ""
echo "Step 2: Training models and generating predictions..."
python3 train_predict_v3.py $WEEK

echo ""
echo "Step 3: Generating HTML report..."
python3 generate_html_report.py $WEEK

echo ""
echo "================================================"
echo "v3 Pipeline Complete!"
echo "================================================"
echo "Output directory: predictions-week-$WEEK-TD/"
