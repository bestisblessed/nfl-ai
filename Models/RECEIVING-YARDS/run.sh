#!/bin/bash

mkdir data
cp ../../Scrapers/data/all_passing_rushing_receiving.csv data/
cp ../upcoming_games.csv data/

python prepare_data.py

echo "Running WR predictions..."
python xgboost_receiving_yards_v3.py

echo ""
echo "Running RB predictions..."
python xgboost_receiving_yards_rb.py

echo ""  
echo "Running TE predictions..."
python xgboost_receiving_yards_te.py

echo ""
echo "=== All predictions complete! ==="