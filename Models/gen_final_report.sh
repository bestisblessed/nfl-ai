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

print_section "‼️ DONE MODELING"
echo "✅ Passing Yards: QB predictions generated"
echo "✅ Receiving Yards: WR/RB/TE predictions generated"
echo "✅ Rushing Yards: QB/RB predictions generated"
echo "✅ Final Reports: Combined HTML/CSV reports created"
echo "✅ Top 25 Analysis PDF generated"
echo ""
echo "📁 Reports saved to 0-FINAL-REPORTS/"
echo ""
echo "🔗 Open report: file://$(pwd)/0-FINAL-REPORTS/week${WEEK}_complete_props_report.html"
echo "📊 Top 25 PDF: file://$(pwd)/0-FINAL-REPORTS/week${WEEK}_leader_tables.pdf"