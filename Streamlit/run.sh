#!/bin/bash

python data.py
# python nfl_odds.py
# cp ../../odds-monitoring/DASHBOARD/data/nfl_odds_movements.csv data/odds/
# mkdir -p data/odds/
# cp ../../odds-monitoring/NFL/Analysis/data/nfl_odds_movements.csv  data/odds/
# cp ../../odds-monitoring/NFL/Analysis/data/nfl_odds_movements_circa.csv  data/odds/
# cp ../../odds-monitoring/NFL/Analysis/data/odds/* data/odds/
# rsync -av --progress "Trinity:/home/trinity/odds-monitoring/NFL/Scraping/data/odds/*" data/odds/ 
streamlit run Home.py