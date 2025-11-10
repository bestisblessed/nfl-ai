#!/bin/bash

set -e

SCRIPT_DIR="/Users/td/Code/nfl-ai/Models/4-TOUCHDOWNS-2"

if [ -z "$1" ]; then
    echo "Usage: bash 4-TOUCHDOWNS-2/run.sh <week_number>"
    exit 1
fi
WEEK=$1

echo "--- Running Touchdown Model for Week $WEEK ---"
cd "$SCRIPT_DIR"
python run_touchdown_model.py $WEEK

echo "--- Generating TD Reports for Week $WEEK ---"
python generate_td_report.py $WEEK

echo "--- 4-TOUCHDOWNS-2 Pipeline Complete ---"
echo "Reports generated in: predictions-week-${WEEK}-TD/"
echo "Files:"
echo "  - Individual game reports: game_*.txt"
echo "  - Combined HTML report: final_week${WEEK}_TD_report.html"
echo "  - Leaderboard: final_week${WEEK}_anytime_td_report.csv"
