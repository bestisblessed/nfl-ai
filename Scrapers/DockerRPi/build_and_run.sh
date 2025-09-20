#!/bin/bash

# mkdir -p ./FINAL
# docker-compose up --build
# echo "Done. Check ./FINAL for output."

echo "Building NFL PFR scraper container for Raspberry Pi..."
# docker-compose build
docker build -t nfl-pfr-scraper-rpi .

echo "Starting NFL PFR scraper for Raspberry Pi..."
# docker-compose run --rm nfl-pfr-scraper
# docker-compose up -d nfl-pfr-scraper
# docker run --rm -v $(pwd)/FINAL:/app/FINAL nfl-pfr-scraper-rpi >> log.log 2>&1 &
nohup docker run --rm -v $(pwd)/FINAL:/app/FINAL nfl-pfr-scraper-rpi >> log.log 2>&1 &

echo ""
echo "✅ Container started successfully!"
echo "🎉 NFL PFR Scraper just ran!"
echo "📁 Check ./FINAL for output files"
# docker-compose down