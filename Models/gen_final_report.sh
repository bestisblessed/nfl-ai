#!/bin/bash

# NFL Props Models - Master Runner Script
# Runs all three models (passing, rushing, receiving) 
# and generates final combined report

set -e

# Ask user for week number if not provided
if [ -z "$1" ]; then
    echo "🏈 NFL Props Models - Master Runner"
    echo "=================================="
    echo ""
    read -p "📅 Enter the week number to run (1-18): " WEEK
    echo ""
else
    WEEK=$1
fi
if ! [[ "$WEEK" =~ ^[1-9]$|^1[0-8]$ ]]; then
    echo "Error: Week must be 1-18"
    exit 1
fi

echo "Running Week $WEEK"

# Copy Scrapers/data/ directory to Models/data/
echo "Copying Scrapers/data/ to Models/data/..."
rm -rf data
cp -r ../Scrapers/data data
echo "✅ Data directory copied"

# Update upcoming games
echo "Updating upcoming_games.csv..."
python update_upcoming_games.py
if [ $? -ne 0 ]; then
    echo "Error: update_upcoming_games.py failed"
    exit 1
fi
echo "✅ Upcoming games updated"
echo "✅ Created upcoming_games.csv and upcoming_bye_week.csv"
echo "✅ QB files automatically updated based on playing vs bye week teams"
echo ""

# Scrape latest injury reports
echo "Updating injured_players.csv and questionable_players.csv..."
python scrape_injured_players.py
echo ""
# if [ $? -ne 0 ]; then
#     echo "❌ Error: Injury scraper failed!"
#     exit 1
# fi

# Clean up existing predictions
echo "Cleaning Week $WEEK..."
rm -rf 1-PASSING-YARDS/predictions-week-$WEEK-QB
rm -rf 2-RECEIVING-YARDS/predictions-week-$WEEK-*
rm -rf 3-RUSHING-YARDS/predictions-week-$WEEK-*
rm -f 0-FINAL-REPORTS/week${WEEK}_*

echo "Running Passing Model..."
cd 1-PASSING-YARDS
./run.sh $WEEK
if [ $? -ne 0 ]; then
    echo "Error: Passing model failed"
    exit 1
fi
echo "✅ Passing yards predictions complete"
cd ..

echo "Running Receiving Model..."
cd 2-RECEIVING-YARDS
./run.sh $WEEK
if [ $? -ne 0 ]; then
    echo "Error: Receiving model failed"
    exit 1
fi
echo "✅ Receiving yards predictions complete"
cd ..

echo "Running Rushing Model..."
cd 3-RUSHING-YARDS
./run.sh $WEEK
if [ $? -ne 0 ]; then
    echo "Error: Rushing model failed"
    exit 1
fi
echo "✅ Rushing yards predictions complete"
cd ..

echo "Generating Final Report..."
python generate_final_report.py $WEEK
if [ $? -ne 0 ]; then
    echo "Error: Report generation failed"
    exit 1
fi

echo "Generating Top 25 Analysis..."
python analyze_top_25.py $WEEK
if [ $? -ne 0 ]; then
    echo "Error: Top 25 analysis failed"
    exit 1
fi
echo "✅ Top 25 analysis complete"

echo "Fetching Betting Props from API..."
cd 10-ARBITRAGE
python fetch_upcoming_games_and_props.py $WEEK
if [ $? -ne 0 ]; then
    echo "Error: Fetching props failed"
    exit 1
fi
echo "✅ Betting props fetched"
cd ..

echo "Comparing Predictions vs Props to Find Value..."
cd 10-ARBITRAGE
python find_value_bets.py $WEEK
if [ $? -ne 0 ]; then
    echo "Error: Comparing predictions vs props failed"
    exit 1
fi
echo "✅ Value opportunities identified"
cd ..

echo "Generating Value Reports (HTML & PDF)..."
cd 10-ARBITRAGE
python render_value_reports.py $WEEK
if [ $? -ne 0 ]; then
    echo "Error: Generating value reports failed"
    exit 1
fi
echo "✅ Value reports generated"
cd ..

echo "‼️ DONE MODELING"
echo "  ✅ Passing Yards: QB predictions generated"
echo "  ✅ Receiving Yards: WR/RB/TE predictions generated"
echo "  ✅ Rushing Yards: QB/RB predictions generated"
echo "  ✅ Final Reports: Combined HTML/CSV reports created"
echo "  ✅ Top 25 Analysis PDF generated"
echo "  ✅ Betting Props: Fetched from API"
echo "  ✅ Value Opportunities: Identified and ranked"
echo "  ✅ Value Reports: HTML and PDF reports generated"
echo "📁 Reports saved to 0-FINAL-REPORTS/"
echo "📁 Value opportunities saved to 10-ARBITRAGE/data/"
echo ""
echo "🔗 Open report: file://$(pwd)/0-FINAL-REPORTS/week${WEEK}_complete_props_report.html"
echo "📊 Top 25 PDF: file://$(pwd)/0-FINAL-REPORTS/week${WEEK}_leader_tables.pdf"
echo "💰 Value report: file://$(pwd)/0-FINAL-REPORTS/week${WEEK}_value_complete_props_report.html"
echo "📊 Value PDF: file://$(pwd)/0-FINAL-REPORTS/week${WEEK}_value_leader_tables.pdf"
echo ""
git status .
read -p "Commit changes? (y/n): " COMMIT
if [[ "$COMMIT" =~ ^[Yy]$ ]]; then
    echo "UPDATING UPCOMING WEEK ${WEEK}.."

    git add upcoming_games.csv
    git add upcoming_bye_week.csv
    git add starting_qbs_2025.csv
    git add starting_qbs_2025_bye.csv
    git add injured_players.csv
    git add questionable_players.csv

    # git add 0-FINAL-REPORTS/week${WEEK}_*
    git add 0-FINAL-REPORTS/
    # git add 1-PASSING-YARDS/predictions-week-${WEEK}-*
    git add 1-PASSING-YARDS/
    # git add 2-RECEIVING-YARDS/predictions-week-${WEEK}-*
    git add 2-RECEIVING-YARDS/
    # git add 3-RUSHING-YARDS/predictions-week-${WEEK}-*
    git add 3-RUSHING-YARDS/
    echo ""
    echo "📋 Copy and run this command to update remote:"
    echo "git commit -m \"UPDATED UPCOMING WEEK ${WEEK} MODEL & REPORTS\" && git push"
    # git commit -m "UPDATED UPCOMING WEEK ${WEEK} MODEL & REPORTS""
    # echo "✅ Changes committed"
    # echo "Execute 'git push' to update remote repository"
else
    echo "Skipping commit"
fi