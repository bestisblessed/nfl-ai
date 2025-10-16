#!/bin/bash

echo "Copying data directory and nfl.db to data/.."
cp -r /Users/td/Code/nfl-ai/Scrapers/data . # Copy data directory from Scrapers
cp -f /Users/td/Code/nfl-ai/Scrapers/nfl.db data/ # Copy nfl.db from Scrapers
cp /Users/td/Code/nfl-ai/Scrapers/final_data/* data/
# rm -rf final_data_pfr && cp -r /Users/td/Code/nfl-ai/Scrapers/final_data_pfr ./

echo "Running Touchdown-Scorers-Basics.py"
python Touchdown-Scorers-Basics.py

echo "Cleaning up..."
rm -rf __pycache__