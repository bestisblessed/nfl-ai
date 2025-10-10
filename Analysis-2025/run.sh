#!/bin/bash

# Setup
cp -r ../Scrapers/data .
cp -r ../Scrapers/nfl.db data/

# Analyze
python analyze.py