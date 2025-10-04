#!/bin/bash

rm -f log.txt

echo "=== Running PFR Scraper ===" | tee -a log.txt
echo "=================================================================================" | tee -a log.txt

echo "1. Scraping games..." | tee -a log.txt
python -u games-pfr.py 2>&1 | tee -a log.txt
echo "=================================================================================" | tee -a log.txt && sleep 10

echo "2. Scraping player stats..." | tee -a log.txt
python -u player-stats-pfr.py 2>&1 | tee -a log.txt
echo "=================================================================================" | tee -a log.txt && sleep 10

echo "3. Scraping rosters..." | tee -a log.txt
python -u rosters-pfr.py 2>&1 | tee -a log.txt
echo "=================================================================================" | tee -a log.txt && sleep 10

echo "4. Scraping game logs..." | tee -a log.txt
python -u game-logs-pfr.py 2>&1 | tee -a log.txt
echo "=================================================================================" | tee -a log.txt && sleep 10

echo "5. Scraping passing/rushing/receiving..." | tee -a log.txt
python -u passing-rushing-receiving-pfr.py 2>&1 | tee -a log.txt
echo "=================================================================================" | tee -a log.txt && sleep 10

echo "6. Scraping defense..." | tee -a log.txt
python -u defense-pfr.py 2>&1 | tee -a log.txt
echo "=================================================================================" | tee -a log.txt && sleep 10

echo "7. Scraping box scores..." | tee -a log.txt
python -u box-scores-pfr.py 2>&1 | tee -a log.txt
echo "=================================================================================" | tee -a log.txt && sleep 10

echo "8. Scraping team schedule and game results..." | tee -a log.txt
python -u team-schedule-game-results-pfr.py 2>&1 | tee -a log.txt
echo "=================================================================================" | tee -a log.txt && sleep 10

echo "PFR Scraper Complete" | tee -a log.txt