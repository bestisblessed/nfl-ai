#!/bin/bash

set -e

if [ -z "$1" ]; then
    echo "Usage: bash 4-TOUCHDOWNS-v3/run.sh <week_number>"
    exit 1
fi

WEEK="$1"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATA_DIR="$SCRIPT_DIR/data"

mkdir -p "$DATA_DIR"

cp "$SCRIPT_DIR/../../Scrapers/final_data_pfr/player_stats_pfr.csv" "$DATA_DIR/" 2>/dev/null || true
cp "$SCRIPT_DIR/../../Scrapers/final_data_pfr/schedule_game_results_pfr.csv" "$DATA_DIR/" 2>/dev/null || true
cp "$SCRIPT_DIR/../../Scrapers/final_data_pfr/team_conversions_pfr.csv" "$DATA_DIR/" 2>/dev/null || true
cp "$SCRIPT_DIR/../../Scrapers/data/rosters/roster_2025.csv" "$DATA_DIR/" 2>/dev/null || true
cp "$SCRIPT_DIR/../upcoming_games.csv" "$DATA_DIR/" 2>/dev/null || true
cp "$SCRIPT_DIR/../starting_qbs_2025.csv" "$DATA_DIR/" 2>/dev/null || true
cp "$SCRIPT_DIR/../injured_players.csv" "$DATA_DIR/" 2>/dev/null || true
cp "$SCRIPT_DIR/../questionable_players.csv" "$DATA_DIR/" 2>/dev/null || true

cd "$SCRIPT_DIR"

echo "--- Preparing data for Touchdowns v3 ---"
python "$SCRIPT_DIR/prepare_data.py"

echo "--- Training Touchdowns v3 model ---"
python "$SCRIPT_DIR/train_model.py" "$WEEK"

echo "--- Rendering Touchdowns v3 HTML report ---"
python "$SCRIPT_DIR/generate_html_reports.py" "$WEEK"

echo "--- 4-TOUCHDOWNS-v3 pipeline complete ---"

