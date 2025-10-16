#!/bin/bash

echo "Copying data directory and nfl.db to data/.."
rm -rf data
rm -rf final_data_pfr
mkdir -p data/final_data_pfr
# cp -r /Users/td/Code/nfl-ai/Scrapers/data . # Copy data directory from Scrapers
# cp -f /Users/td/Code/nfl-ai/Scrapers/nfl.db data/ # Copy nfl.db from Scrapers
# cp /Users/td/Code/nfl-ai/Scrapers/final_data/* data/
cp /Users/td/Code/nfl-ai/Scrapers/final_data_pfr/* data/final_data_pfr/
cp /Users/td/Code/nfl-ai/Scrapers/data/rosters.csv data/

echo ""
echo "Which model would you like to run?"
echo "1) XGBoost"
echo "2) LightGBM" 
echo "3) Random Forest"
echo "4) Logistic Regression"
echo "5) Monte Carlo"
echo "6) Run all models"
echo ""
read -p "Enter your choice (1-6): " choice
case $choice in
    1)
        echo "Running XGBoost model..."
        python xgboost_model.py
        ;;
    2)
        echo "Running LightGBM model..."
        python lightgbm_model.py
        ;;
    3)
        echo "Running Random Forest model..."
        python random_forest.py
        ;;
    4)
        echo "Running Logistic Regression model..."
        python logistic_regression.py
        ;;
    5)
        echo "Running Monte Carlo model..."
        python monte_carlo.py
        ;;
    6)
        echo "Running all models..."
        echo "Running XGBoost..."
        python xgboost_model.py
        echo "Running LightGBM..."
        python lightgbm_model.py
        echo "Running Random Forest..."
        python random_forest.py
        echo "Running Logistic Regression..."
        python logistic_regression.py
        echo "Running Monte Carlo..."
        python monte_carlo.py
        ;;
    *)
        echo "Invalid choice. Please run the script again and select 1-6."
        exit 1
        ;;
esac