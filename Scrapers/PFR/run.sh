#!/bin/bash

rm -f log.txt

echo "=== Running PFR Scraper ===" | tee -a log.txt
echo "=================================================================================" | tee -a log.txt

echo "Scraping games..." | tee -a log.txt
python -u games-pfr.py 2>&1 | tee -a log.txt
echo "=================================================================================" | tee -a log.txt && sleep 10

echo "Scraping player stats..." | tee -a log.txt
python -u player-stats-pfr.py 2>&1 | tee -a log.txt
echo "=================================================================================" | tee -a log.txt && sleep 10

echo "Scraping rosters..." | tee -a log.txt
python -u rosters-pfr.py 2>&1 | tee -a log.txt
echo "=================================================================================" | tee -a log.txt && sleep 10

echo "Scraping game logs..." | tee -a log.txt
python -u game-logs-pfr.py 2>&1 | tee -a log.txt
echo "=================================================================================" | tee -a log.txt && sleep 10

echo "Scraping passing/rushing/receiving..." | tee -a log.txt
python -u passing-rushing-receiving-pfr.py 2>&1 | tee -a log.txt
echo "=================================================================================" | tee -a log.txt && sleep 10

echo "Scraping defense..." | tee -a log.txt
python -u defense-pfr.py 2>&1 | tee -a log.txt
echo "=================================================================================" | tee -a log.txt && sleep 10

echo "PFR Scraper Complete" | tee -a log.txt