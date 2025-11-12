#!/bin/bash

set -e

SCRIPT_DIR="/Users/td/Code/nfl-ai/Models/4-TOUCHDOWNS"
DATA_DIR="$SCRIPT_DIR/data"

if [ -z "$1" ]; then
    echo "Usage: bash 4-TOUCHDOWNS/run.sh <week_number>"
    exit 1
fi
WEEK=$1

# Data prep
echo "--- Preparing Data for 4-TOUCHDOWNS ---"
mkdir -p "$DATA_DIR"
cd "$SCRIPT_DIR"
cp ../../Scrapers/final_data_pfr/player_stats_pfr.csv data/ 2>/dev/null || true
cp ../../Scrapers/data/rosters/roster_2025.csv data/ 2>/dev/null || true
cp ../../Scrapers/final_data_pfr/schedule_game_results_pfr.csv data/ 2>/dev/null || true
cp ../../Scrapers/final_data_pfr/team_conversions_pfr.csv data/ 2>/dev/null || true
cp ../upcoming_games.csv data/ 2>/dev/null || true
cp ../starting_qbs_2025.csv data/ 2>/dev/null || true
cp ../injured_players.csv data/ 2>/dev/null || true
cp ../questionable_players.csv data/ 2>/dev/null || true
echo "--- Data copied ---"

echo "--- Building Anytime TD Features (4.1) ---"
python "$SCRIPT_DIR/prepare_data.py"

echo "--- Running Anytime TD XGBoost (4.1) ---"
python "$SCRIPT_DIR/xgboost_anytime_td.py" $WEEK

echo "--- Generating Anytime TD HTML Report (4.1) ---"
python "$SCRIPT_DIR/generate_html_reports.py" $WEEK

echo "--- 4-TOUCHDOWNS Pipeline Complete ---"


