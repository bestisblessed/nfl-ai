#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "Usage: ./generate_matchup_report.sh <week number>"
  echo "Example: ./generate_matchup_report.sh 16"
  exit 1
fi

week="$1"

python3 -m pip install -r "Websites/Streamlit/requirements.txt"
python3 -m pip install -U playwright
python3 -m playwright install chromium

python3 "generate_matchup_report.py" "$week"

echo "Saved to reports/week${week}/"

