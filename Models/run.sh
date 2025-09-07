#!/bin/bash

# NFL Props Models - Master Runner Script
# Runs all three models (passing, rushing, receiving) and generates final combined report

set -e  # Exit on any error

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

# Validate week number
if ! [[ "$WEEK" =~ ^[1-9]$|^1[0-8]$ ]]; then
    echo "❌ Error: Week must be between 1 and 18"
    exit 1
fi

echo "🏈 NFL Props Models - Master Runner"
echo "=================================="
echo "Running all models for Week $WEEK"
echo ""

# Function to print section headers
print_section() {
    echo ""
    echo "$(printf '=%.0s' {1..60})"
    echo "$1"
    echo "$(printf '=%.0s' {1..60})"
    echo ""
}

# Function to check if directory exists
check_directory() {
    if [ ! -d "$1" ]; then
        echo "❌ Error: Directory $1 not found!"
        exit 1
    fi
}

# Check that all model directories exist
print_section "🔍 Checking Model Directories"
check_directory "1-PASSING-YARDS"
check_directory "2-RECEIVING-YARDS" 
check_directory "3-RUSHING-YARDS"
echo "✅ All model directories found"

# Clean up existing predictions for this specific week only
print_section "🧹 Cleaning Week $WEEK Predictions"
echo "Checking for existing Week $WEEK predictions..."

# Remove specific week predictions if they exist
if [ -d "1-PASSING-YARDS/predictions-week-$WEEK-QB" ]; then
    echo "Removing existing Week $WEEK passing predictions..."
    rm -rf 1-PASSING-YARDS/predictions-week-$WEEK-QB
fi

if [ -d "2-RECEIVING-YARDS/predictions-week-$WEEK-WR" ] || [ -d "2-RECEIVING-YARDS/predictions-week-$WEEK-RB" ] || [ -d "2-RECEIVING-YARDS/predictions-week-$WEEK-TE" ]; then
    echo "Removing existing Week $WEEK receiving predictions..."
    rm -rf 2-RECEIVING-YARDS/predictions-week-$WEEK-*
fi

if [ -d "3-RUSHING-YARDS/predictions-week-$WEEK-QB" ] || [ -d "3-RUSHING-YARDS/predictions-week-$WEEK-RB" ]; then
    echo "Removing existing Week $WEEK rushing predictions..."
    rm -rf 3-RUSHING-YARDS/predictions-week-$WEEK-*
fi

# Remove existing final reports for this week (but keep other weeks)
if [ -f "0-FINAL-REPORTS/week${WEEK}_complete_props_report.html" ]; then
    echo "Removing existing Week $WEEK final reports..."
    rm -f 0-FINAL-REPORTS/week${WEEK}_complete_props_report.html
    rm -f 0-FINAL-REPORTS/week${WEEK}_complete_props_report.txt
    rm -f 0-FINAL-REPORTS/week${WEEK}_all_props_summary.csv
fi

echo "✅ Week $WEEK cleanup complete (other weeks preserved)"

# Run Passing Yards Model (QBs only)
print_section "🎯 Running Passing Yards Model"
echo "Predicting QB passing yards..."
cd 1-PASSING-YARDS
python xgboost_passing_yards_qb.py $WEEK
if [ $? -ne 0 ]; then
    echo "❌ Error: Passing yards model failed!"
    exit 1
fi
echo "✅ Passing yards predictions complete"
cd ..

# Run Receiving Yards Model (WRs, RBs, TEs)
print_section "🎯 Running Receiving Yards Model"
echo "Predicting receiving yards for WR/RB/TE..."
cd 2-RECEIVING-YARDS
./run.sh $WEEK
if [ $? -ne 0 ]; then
    echo "❌ Error: Receiving yards model failed!"
    exit 1
fi
echo "✅ Receiving yards predictions complete"
cd ..

# Run Rushing Yards Model (QBs and RBs)
print_section "🎯 Running Rushing Yards Model"
echo "Predicting rushing yards for QB/RB..."
cd 3-RUSHING-YARDS
./run.sh $WEEK
if [ $? -ne 0 ]; then
    echo "❌ Error: Rushing yards model failed!"
    exit 1
fi
echo "✅ Rushing yards predictions complete"
cd ..

# Generate Final Combined Report
print_section "📊 Generating Final Combined Report"
echo "Creating consolidated props report..."
python create_combined_report.py $WEEK
if [ $? -ne 0 ]; then
    echo "❌ Error: Combined report generation failed!"
    exit 1
fi

# Final Summary
print_section "🎉 ALL MODELS COMPLETE"
echo "✅ Passing Yards: QB predictions generated"
echo "✅ Receiving Yards: WR/RB/TE predictions generated"
echo "✅ Rushing Yards: QB/RB predictions generated"
echo "✅ Final Reports: Combined HTML/CSV reports created"
echo ""
echo "📁 Check the 0-FINAL-REPORTS/ directory for:"
echo "   🌐 week${WEEK}_complete_props_report.html"
echo "   📄 week${WEEK}_complete_props_report.txt"
echo "   📊 week${WEEK}_all_props_summary.csv"
echo ""
echo "💡 Open 0-FINAL-REPORTS/week${WEEK}_complete_props_report.html"
echo "   in your web browser to view all props!"
echo ""
echo "🏈 Ready for Week $WEEK NFL action! 🏈"
