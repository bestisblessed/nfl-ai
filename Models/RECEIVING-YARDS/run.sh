#!/bin/bash

mkdir data
# cp ../../Scrapers/data/rosters.csv data/
cp ../../Scrapers/data/all_passing_rushing_receiving.csv data/
cp ../upcoming_games.csv data/

python prepare_data.py
python xgboost_receiving_yards_v3.py