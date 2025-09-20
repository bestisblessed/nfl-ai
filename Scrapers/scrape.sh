#!/bin/bash

# Backup old log files if they exist (in the same directory)
# mkdir -p logs
# mv logs/log.txt logs/log.txt.bak
# mv logs/log-pfr.txt logs/log-pfr.txt.bak

echo "================================================================================="
echo "STARTING NFL DATA SCRAPER"
echo "================================================================================="
python -u ScraperFinal.py 2>&1 | tee log.txt

echo ""
echo "================================================================================="
echo "PFR ONLY DATABASE"
echo "================================================================================="
python -u ScraperFinal-PFR.py 2>&1 | tee -a log.txt
