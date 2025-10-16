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


# Display upcoming games
echo ""
echo "Upcoming NFL Games:"
python3 -c "
import pandas as pd
import sys
try:
    games_df = pd.read_csv('/Users/td/Code/nfl-ai/Models/upcoming_games.csv')
    for i, row in games_df.iterrows():
        print(f'{i+1}) {row[\"home_team\"]} vs {row[\"away_team\"]}')
    print(f'{len(games_df)+1}) All games')
except Exception as e:
    print('Error loading games:', e)
    sys.exit(1)
"
echo ""
read -p "Select a game to predict (1-$(($(python3 -c "import pandas as pd; df=pd.read_csv('/Users/td/Code/nfl-ai/Models/upcoming_games.csv'); print(len(df))")+1))): " game_choice
if [ "$game_choice" -le "$(python3 -c "import pandas as pd; df=pd.read_csv('/Users/td/Code/nfl-ai/Models/upcoming_games.csv'); print(len(df))")" ]; then
    HOME_TEAM=$(python3 -c "import pandas as pd; df=pd.read_csv('/Users/td/Code/nfl-ai/Models/upcoming_games.csv'); print(df.iloc[$game_choice-1]['home_team'])")
    AWAY_TEAM=$(python3 -c "import pandas as pd; df=pd.read_csv('/Users/td/Code/nfl-ai/Models/upcoming_games.csv'); print(df.iloc[$game_choice-1]['away_team'])")
    MATCHUP_STR="$HOME_TEAM vs $AWAY_TEAM"
    echo "Predicting for: $MATCHUP_STR"
else
    MATCHUP_STR="All games"
    echo "Predicting for: All games"
fi


# Select Model
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
if [ "$game_choice" -le "$(python3 -c "import pandas as pd; df=pd.read_csv('/Users/td/Code/nfl-ai/Models/upcoming_games.csv'); print(len(df))")" ]; then
    case $choice in
        1)
            echo "Running XGBoost model for $MATCHUP_STR..."
            python xgboost_model.py --matchup "$HOME_TEAM" "$AWAY_TEAM"
            ;;
        2)
            echo "Running LightGBM model for $MATCHUP_STR..."
            python lightgbm_model.py --matchup "$HOME_TEAM" "$AWAY_TEAM"
            ;;
        3)
            echo "Running Random Forest model for $MATCHUP_STR..."
            python random_forest.py --matchup "$HOME_TEAM" "$AWAY_TEAM"
            ;;
        4)
            echo "Running Logistic Regression model for $MATCHUP_STR..."
            python logistic_regression.py --matchup "$HOME_TEAM" "$AWAY_TEAM"
            ;;
        5)
            echo "Running Monte Carlo model for $MATCHUP_STR..."
            python monte_carlo.py --matchup "$HOME_TEAM" "$AWAY_TEAM"
            ;;
        6)
            echo "Running all models for $MATCHUP_STR..."
            echo "Running XGBoost..."
            python xgboost_model.py --matchup "$HOME_TEAM" "$AWAY_TEAM"
            echo "Running LightGBM..."
            python lightgbm_model.py --matchup "$HOME_TEAM" "$AWAY_TEAM"
            echo "Running Random Forest..."
            python random_forest.py --matchup "$HOME_TEAM" "$AWAY_TEAM"
            echo "Running Logistic Regression..."
            python logistic_regression.py --matchup "$HOME_TEAM" "$AWAY_TEAM"
            echo "Running Monte Carlo..."
            python monte_carlo.py --matchup "$HOME_TEAM" "$AWAY_TEAM"
            ;;
    esac
else
    # All games selected
    case $choice in
        1)
            echo "Running XGBoost model for all games..."
            python xgboost_model.py
            ;;
        2)
            echo "Running LightGBM model for all games..."
            python lightgbm_model.py
            ;;
        3)
            echo "Running Random Forest model for all games..."
            python random_forest.py
            ;;
        4)
            echo "Running Logistic Regression model for all games..."
            python logistic_regression.py
            ;;
        5)
            echo "Running Monte Carlo model for all games..."
            python monte_carlo.py
            ;;
        6)
            echo "Running all models for all games..."
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
    esac
fi