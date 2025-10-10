#!/bin/bash

cp -r ../../Scrapers/data ./ # Copy data directory from Scrapers
cp -f ../../Scrapers/nfl.db ./ # Copy nfl.db from Scrapers
cp ../../Scrapers/final_data/*OCT_10* data

rm -rf final_data_pfr
cp -r ../../Scrapers/final_data_pfr .

rm -rf __pycache__
echo "Copied data directory and nfl.db to current directory."
