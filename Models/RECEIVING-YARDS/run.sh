#!/bin/bash

mkdir data
cp ../../Scrapers/data/all_passing_rushing_receiving.csv data/
cp ../upcoming_games.csv data/
python prepare_data.py

# Check if week number is provided
if [ $# -eq 0 ]; then
    echo "Usage: $0 <week_number>"
    echo "Example: $0 1"
    exit 1
fi
WEEK_NUM=$1

# Validate week number (1-18 for NFL season)
if ! [[ "$WEEK_NUM" =~ ^[1-9]$|^1[0-8]$ ]]; then
    echo "Error: Week number must be between 1 and 18"
    exit 1
fi

# Run predictions
echo "=== Running predictions for Week $WEEK_NUM ==="

echo "Running WR predictions..."
python xgboost_receiving_yards_wr.py $WEEK_NUM
# python xgboost_receiving_yards_v3.py $WEEK_NUM

echo ""
echo "Running RB predictions..."
python xgboost_receiving_yards_rb.py $WEEK_NUM
# python xgboost_receiving_yards_rb.py $WEEK_NUM

echo ""  
echo "Running TE predictions..."
python xgboost_receiving_yards_te.py $WEEK_NUM
# python xgboost_receiving_yards_te.py $WEEK_NUM

echo ""
echo "=== All predictions complete for Week $WEEK_NUM ==="