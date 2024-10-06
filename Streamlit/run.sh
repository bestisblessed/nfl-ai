#!/bin/bash

python data.py
# python nfl_odds.py
cp ../../odds-monitoring/DASHBOARD/data/nfl_odds_movements.csv data/odds/
streamlit run Home.py