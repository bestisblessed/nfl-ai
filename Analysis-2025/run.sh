#!/bin/bash

# Setup
cp -r ../Scrapers/data .
cp -r ../Scrapers/nfl.db data/

# Analyze
python analyze1-basics.py
python analyze2-betting-edges.py
python analyze3-advanced-edges.py
python analyze4-situational-edges.py
python analyze5-final-edges.py