#!/bin/bash

cp -r ../../Scrapers/data ./ # Copy data directory from Scrapers
cp -f ../../Scrapers/nfl.db ./ # Copy nfl.db from Scrapers

echo "Copied data directory and nfl.db to current directory."
