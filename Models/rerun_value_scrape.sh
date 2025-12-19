#!/bin/bash

# Refresh odds scraping and value reports without rerunning model training

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Ask user for week number if not provided
if [[ -z "${1-}" ]]; then
    read -p "Enter the week number to refresh (1-18): " WEEK
else
    WEEK="$1"
fi

if ! [[ "$WEEK" =~ ^[1-9]$|^1[0-8]$ ]]; then
    echo "Error: Week must be between 1 and 18"
    exit 1
fi

SUMMARY_FILE="$SCRIPT_DIR/0-FINAL-REPORTS/week${WEEK}_all_props_summary.csv"
if [[ ! -f "$SUMMARY_FILE" ]]; then
    echo "Missing predictions summary: $SUMMARY_FILE"
    echo "Run gen_final_report.sh first so predictions exist for this week."
    exit 1
fi

echo "Rescraping odds and regenerating value reports for week ${WEEK}..."
pushd "$SCRIPT_DIR/10-ARBITRAGE" >/dev/null
python fetch_upcoming_games_and_props.py "$WEEK"
python find_value_bets.py "$WEEK"
python render_value_reports.py "$WEEK"
popd >/dev/null

echo "Validating generated outputs..."
VALUE_CSV="$SCRIPT_DIR/10-ARBITRAGE/data/week${WEEK}_value_opportunities.csv"
EDGES_CSV="$SCRIPT_DIR/10-ARBITRAGE/data/week${WEEK}_top_edges_by_prop.csv"
VALUE_HTML="$SCRIPT_DIR/0-FINAL-REPORTS/week${WEEK}_value_complete_props_report.html"
VALUE_PDF="$SCRIPT_DIR/0-FINAL-REPORTS/week${WEEK}_value_leader_tables.pdf"

for file in "$VALUE_CSV" "$EDGES_CSV" "$VALUE_HTML" "$VALUE_PDF"; do
    if [[ ! -f "$file" ]]; then
        echo "Expected output not found: $file"
        exit 1
    fi
    echo "Found: $file"
fi

STREAMLIT_PROJECTIONS_DIR="$SCRIPT_DIR/../Websites/Streamlit/data/projections"
mkdir -p "$STREAMLIT_PROJECTIONS_DIR"

cp "$VALUE_CSV" "$STREAMLIT_PROJECTIONS_DIR/"
cp "$EDGES_CSV" "$STREAMLIT_PROJECTIONS_DIR/"
cp "$VALUE_HTML" "$STREAMLIT_PROJECTIONS_DIR/"
cp "$VALUE_PDF" "$STREAMLIT_PROJECTIONS_DIR/"

echo "Updated Streamlit assets:"
echo "  - $STREAMLIT_PROJECTIONS_DIR/$(basename "$VALUE_CSV")"
echo "  - $STREAMLIT_PROJECTIONS_DIR/$(basename "$EDGES_CSV")"
echo "  - $STREAMLIT_PROJECTIONS_DIR/$(basename "$VALUE_HTML")"
echo "  - $STREAMLIT_PROJECTIONS_DIR/$(basename "$VALUE_PDF")"

echo "✅ Value scrape refresh complete."
