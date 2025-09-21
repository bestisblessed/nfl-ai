#!/bin/bash

echo "================================================================================="
echo "MASTER PFR-ONLY NFL DATA SCRAPER (2015-2024 seasons)"
echo "================================================================================="

# Run the master PFR scraper
python -u ScraperMasterPFR.py 2>&1 | tee logMasterPFR.log

echo ""
echo "================================================================================="
echo "🎉 MASTER PFR SCRAPER COMPLETED! (2015-2024 seasons)"
echo "================================================================================="