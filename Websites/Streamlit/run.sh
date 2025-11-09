#!/bin/bash

python data.py
mkdir -p data/projections/
cp /Users/td/Code/nfl-ai/Scrapers/final_data_pfr/player_stats_pfr.csv data/
cp /Users/td/Code/nfl-ai/Models/0-FINAL-REPORTS/* data/projections/
cp /Users/td/Code/nfl-ai/Models/upcoming_games.csv .
cp ../../Models/10-ARBITRAGE/data/* data/projections/

# python nfl_odds.py
# cp ../../odds-monitoring/DASHBOARD/data/nfl_odds_movements.csv data/odds/
# mkdir -p data/odds/
# cp ../../odds-monitoring/NFL/Analysis/data/nfl_odds_movements.csv  data/odds/
# cp ../../odds-monitoring/NFL/Analysis/data/nfl_odds_movements_circa.csv  data/odds/
# cp ../../odds-monitoring/NFL/Analysis/data/odds/* data/odds/
# rsync -av --progress "Trinity:/home/trinity/odds-monitoring/NFL/Scraping/data/odds/*" data/odds/ 

# echo "Copying receiving yards projections..."
# cp /Users/td/Code/nfl-ai/Models/RECEIVING-YARDS/predictions-week-1-WR/final_week1_WR_rec_yards_report.csv data/projections/
# cp /Users/td/Code/nfl-ai/Models/RECEIVING-YARDS/predictions-week-1-WR/final_week1_WR_rec_yards_report.html data/projections/
# cp /Users/td/Code/nfl-ai/Models/RECEIVING-YARDS/predictions-week-1-RB/final_week1_RB_rec_yards_report.csv data/projections/
# cp /Users/td/Code/nfl-ai/Models/RECEIVING-YARDS/predictions-week-1-RB/final_week1_RB_rec_yards_report.html data/projections/
# cp /Users/td/Code/nfl-ai/Models/RECEIVING-YARDS/predictions-week-1-TE/final_week1_TE_rec_yards_report.csv data/projections/
# cp /Users/td/Code/nfl-ai/Models/RECEIVING-YARDS/predictions-week-1-TE/final_week1_TE_rec_yards_report.html data/projections/

streamlit run Home.py
