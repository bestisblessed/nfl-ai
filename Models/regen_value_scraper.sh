#!/bin/bash

# set -euo pipefail
# shopt -s nullglob

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

WEEK="${1:-}"
[[ -z "$WEEK" ]] && read -rp "Enter the week number to refresh (1-18): " WEEK

[[ ! "$WEEK" =~ ^[1-9]$|^1[0-8]$ ]] && echo "Error: Week must be an integer between 1 and 18." && exit 1
[[ ! -f "0-FINAL-REPORTS/week${WEEK}_all_props_summary.csv" ]] && echo "Error: 0-FINAL-REPORTS/week${WEEK}_all_props_summary.csv not found. Run gen_final_report.sh first." && exit 1

echo "Fetching Betting Props from API..."
cd 10-ARBITRAGE
python fetch_upcoming_games_and_props.py $WEEK
if [ $? -ne 0 ]; then
    echo "Error: Fetching props failed"
    exit 1
fi
echo "✅ Betting props fetched"
cd ..

echo "Comparing Predictions vs Props to Find Value..."
cd 10-ARBITRAGE
# Backup existing value opportunities before regenerating
OLD_FILE="data/week${WEEK}_value_opportunities.csv"
BACKUP_FILE="data/week${WEEK}_value_opportunities_backup.csv"
[[ -f "$OLD_FILE" ]] && cp "$OLD_FILE" "$BACKUP_FILE"

python find_value_bets.py $WEEK
if [ $? -ne 0 ]; then
    echo "Error: Comparing predictions vs props failed"
    exit 1
fi

# Merge with backup to preserve already-played games
if [[ -f "$BACKUP_FILE" ]] && [[ -f "$OLD_FILE" ]]; then
    python3 -c "
import pandas as pd
old = pd.read_csv('$BACKUP_FILE')
new = pd.read_csv('$OLD_FILE')
if 'home_team' in old.columns and 'away_team' in old.columns and 'home_team' in new.columns and 'away_team' in new.columns:
    old_games = set(zip(old['home_team'], old['away_team'])) | set(zip(old['away_team'], old['home_team']))
    new_games = set(zip(new['home_team'], new['away_team'])) | set(zip(new['away_team'], new['home_team']))
    played_games = old_games - new_games
    if played_games:
        def is_played_game(row):
            return (row['home_team'], row['away_team']) in played_games or (row['away_team'], row['home_team']) in played_games
        old_played = old[old.apply(is_played_game, axis=1)]
        merged = pd.concat([old_played, new], ignore_index=True)
        merged.to_csv('$OLD_FILE', index=False)
        print(f'Preserved {len(played_games)} already-played game(s)')
"
    rm -f "$BACKUP_FILE"
fi

echo "✅ Value opportunities identified"
cd ..

echo "Generating Value Reports (HTML & PDF)..."
cd 10-ARBITRAGE
python render_value_reports.py $WEEK
if [ $? -ne 0 ]; then
    echo "Error: Generating value reports failed"
    exit 1
fi
echo "✅ Value reports generated"
cd ..

cp "10-ARBITRAGE/data/week${WEEK}_value_opportunities.csv" "${SCRIPT_DIR}/../Websites/Streamlit/data/projections/" 2>/dev/null || true
cp "10-ARBITRAGE/data/week${WEEK}_top_edges_by_prop.csv" "${SCRIPT_DIR}/../Websites/Streamlit/data/projections/" 2>/dev/null || true
cp "0-FINAL-REPORTS/week${WEEK}_value_complete_props_report.html" "${SCRIPT_DIR}/../Websites/Streamlit/data/projections/" 2>/dev/null || true
cp "0-FINAL-REPORTS/week${WEEK}_value_leader_tables.pdf" "${SCRIPT_DIR}/../Websites/Streamlit/data/projections/" 2>/dev/null || true
cp "10-ARBITRAGE/data"/nfl_odds_*.json "10-ARBITRAGE/data"/*odds*.csv "${SCRIPT_DIR}/../Websites/Streamlit/data/odds/" 2>/dev/null || true
echo "\n🎯 Streamlit Value page data refreshed for week ${WEEK}."
