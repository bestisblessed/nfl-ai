#!/bin/bash

if [ -z "$1" ]; then
    echo "Usage: $0 <week_number>"
    exit 1
fi

WEEK=$1
echo "Generating matchup reports for Week $WEEK..."

# Set PYTHONPATH if needed, but the script is in workspace root and uses absolute paths
python3 /workspace/generate_matchup_reports.py "$WEEK"

echo "Done. Reports are in /workspace/reports/"
