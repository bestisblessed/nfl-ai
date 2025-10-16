#!/bin/bash

rm -rf data
rm -rf final_data_pfr
cp -r /Users/td/Code/nfl-ai/Scrapers/data ./ # Copy data directory from Scrapers
cp -f /Users/td/Code/nfl-ai/Scrapers/nfl.db ./data/ # Copy nfl.db from Scrapers
cp /Users/td/Code/nfl-ai/Scrapers/final_data/* data/
cp -r /Users/td/Code/nfl-ai/Scrapers/final_data_pfr .

rm -rf __pycache__
echo "Copied data directory and nfl.db to current directory."
