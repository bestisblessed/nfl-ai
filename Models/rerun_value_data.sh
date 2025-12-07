#!/bin/bash

# Refresh value betting data without rerunning model predictions.
# Reruns the 10-ARBITRAGE scraping/processing steps and copies outputs
# into the Streamlit app data directory so the Value page updates.

set -euo pipefail
shopt -s nullglob

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# --- Input validation ---
WEEK="${1:-}"
if [[ -z "$WEEK" ]]; then
    read -rp "Enter the week number to refresh (1-18): " WEEK
fi

if ! [[ "$WEEK" =~ ^[1-9]$|^1[0-8]$ ]]; then
    echo "Error: Week must be an integer between 1 and 18."
    exit 1
fi

PREDICTIONS_FILE="0-FINAL-REPORTS/week${WEEK}_all_props_summary.csv"
if [[ ! -f "$PREDICTIONS_FILE" ]]; then
    echo "Error: ${PREDICTIONS_FILE} not found. Run gen_final_report.sh first to create model predictions."
    exit 1
fi

# --- Rerun arbitrage pipeline ---
echo "\n🔄 Refreshing odds and value outputs for week ${WEEK}..."
pushd "10-ARBITRAGE" >/dev/null
python fetch_upcoming_games_and_props.py "$WEEK"
python find_value_bets.py "$WEEK"
python render_value_reports.py "$WEEK"
popd >/dev/null

echo "\n✅ Odds scraping and value calculations complete."

# --- Copy updated outputs to Streamlit ---
STREAMLIT_PROJECTIONS_DIR="${SCRIPT_DIR}/../Websites/Streamlit/data/projections"
mkdir -p "$STREAMLIT_PROJECTIONS_DIR"
STREAMLIT_ODDS_DIR="${SCRIPT_DIR}/../Websites/Streamlit/data/odds"
mkdir -p "$STREAMLIT_ODDS_DIR"

copy_if_exists() {
    local source_file="$1"
    local dest_dir="$2"
    if [[ -f "$source_file" ]];
    then
        cp "$source_file" "$dest_dir/"
        echo "Copied $(basename "$source_file") to $(realpath "$dest_dir")"
    else
        echo "Warning: ${source_file} not found; skipping copy." >&2
    fi
}

# Value data used by the Streamlit Value page
copy_if_exists "10-ARBITRAGE/data/week${WEEK}_value_opportunities.csv" "$STREAMLIT_PROJECTIONS_DIR"
copy_if_exists "10-ARBITRAGE/data/week${WEEK}_top_edges_by_prop.csv" "$STREAMLIT_PROJECTIONS_DIR"

# Value report assets (HTML/PDF) for reference in Streamlit downloads
copy_if_exists "0-FINAL-REPORTS/week${WEEK}_value_complete_props_report.html" "$STREAMLIT_PROJECTIONS_DIR"
copy_if_exists "0-FINAL-REPORTS/week${WEEK}_value_leader_tables.pdf" "$STREAMLIT_PROJECTIONS_DIR"

# Odds snapshots used for ordering matchups by start time in the Value page
copy_matching_files() {
    local pattern="$1"
    local source_dir="$2"
    local dest_dir="$3"

    local matched_files=()
    for file in "$source_dir"/$pattern; do
        matched_files+=("$file")
    done

    if [[ ${#matched_files[@]} -eq 0 ]]; then
        echo "No files matching ${pattern} found in ${source_dir}; skipping odds sync."
        return
    fi

    for file in "${matched_files[@]}"; do
        cp "$file" "$dest_dir/"
        echo "Copied $(basename "$file") to $(realpath "$dest_dir")"
    done
}

copy_matching_files "nfl_odds_*.json" "10-ARBITRAGE/data" "$STREAMLIT_ODDS_DIR"
copy_matching_files "*odds*.csv" "10-ARBITRAGE/data" "$STREAMLIT_ODDS_DIR"

echo "\n🎯 Streamlit Value page data refreshed for week ${WEEK}."
