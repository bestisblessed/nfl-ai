#!/bin/bash


# Check if week number is provided
if [ $# -eq 0 ]; then
    echo "=== NFL Rushing Yards Predictions ==="
    echo "Enter the week number (1-18):"
    read -p "Week: " WEEK_NUM
else
    WEEK_NUM=$1
fi
if ! [[ "$WEEK_NUM" =~ ^[1-9]$|^1[0-8]$ ]]; then # Validate week number (1-18 for NFL season)
    echo "Error: Week number must be between 1 and 18"
    exit 1
fi

# Data prep
mkdir -p data
cp ../../Scrapers/final_data_pfr/player_stats_pfr.csv data/
cp ../../Scrapers/data/rosters/roster_2025.csv data/
cp ../upcoming_games.csv data/
cp ../starting_qbs_2025.csv data/
cp ../injured_players.csv data/ 2>/dev/null || true
python prepare_data.py

# Run predictions
echo "=== Running predictions for Week $WEEK_NUM ==="
echo "Running QB predictions..."
python xgboost_rushing_yards_qb.py $WEEK_NUM
echo ""
echo "Running RB predictions..."
python xgboost_rushing_yards_rb.py $WEEK_NUM
echo ""
echo "=== All predictions complete for Week $WEEK_NUM ==="

echo ""
echo "Merging all position reports (QB, RB) into single files..."
python generate_txt_reports.py $WEEK_NUM
echo ""
echo "Creating HTML reports for all positions (QB, RB)..."
python generate_html_reports.py $WEEK_NUM