#!/bin/bash

# Check if week parameter is provided
if [ $# -eq 0 ]; then
    echo "What is the upcoming week of the 2025 season?"
    read -p "Enter week number (1-18): " WEEK_LIMIT
    if ! [[ "$WEEK_LIMIT" =~ ^[0-9]+$ ]]; then
        echo "❌ Please enter a valid number"
        exit 1
    fi
    if [ "$WEEK_LIMIT" -lt 1 ] || [ "$WEEK_LIMIT" -gt 18 ]; then
        echo "❌ Please enter a week number between 1 and 18"
        exit 1
    fi
    echo "🎯 Filtering out unplayed games after week $WEEK_LIMIT"
else
    WEEK_LIMIT=$1
fi

# Backup old log files if they exist (in the same directory)
# mkdir -p logs
# mv logs/log.txt logs/log.txt.bak
# mv logs/log-pfr.txt logs/log-pfr.txt.bak

echo "================================================================================="
echo "STARTING NFL DATA SCRAPER (2025 seasons, filtering unplayed games after week $WEEK_LIMIT)"
echo "================================================================================="
python -u ScraperFinal.py 2>&1 | tee log.txt

echo ""
echo "================================================================================="
echo "PFR ONLY DATABASE (2025 seasons, filtering unplayed games after week $WEEK_LIMIT)"
echo "================================================================================="
python -u ScraperFinal-PFR.py $WEEK_LIMIT 2>&1 | tee -a log.txt
