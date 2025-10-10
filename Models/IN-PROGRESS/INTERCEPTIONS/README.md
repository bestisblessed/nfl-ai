# QB Interception Prediction Model

This directory contains cleaned-up Python scripts for predicting the probability that a quarterback will throw an interception in their next NFL game.

## Overview

The model uses machine learning to analyze quarterback performance statistics and predict interception likelihood. It compares three different algorithms:
- Logistic Regression
- Random Forest
- XGBoost

## Features Used

The model uses the following quarterback statistics as features:
- `attempts`: Number of pass attempts
- `completions`: Number of completed passes
- `passing_yards`: Total passing yards
- `passing_tds`: Passing touchdowns
- `sacks`: Number of times sacked
- `passing_epa`: Expected Points Added from passing
- `passing_air_yards`: Total air yards on passes

## Installation

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

Or install individual packages:
```bash
pip install pandas scikit-learn xgboost numpy
```

## Usage

### Running the Main Model

Execute the main training and prediction script:

```bash
python train_interception_model.py
```

This will:
1. Load and preprocess the player statistics data
2. Train three different machine learning models
3. Evaluate model performance on a test set
4. Generate interception probability predictions for all player-games

### Expected Output

The script will output:
- Model performance metrics (accuracy, precision, recall, F1-score)
- Confusion matrices for each model
- Sample interception probability predictions

## Data Requirements

The script expects a CSV file at `/Users/td/Code/nfl-ai/Models/IN-PROGRESS/data/PlayerStats.csv` with the following characteristics:
- Contains NFL player statistics from multiple seasons
- Includes quarterback position data
- Has the feature columns listed above
- Contains an `interceptions` column for the target variable

## Model Performance

Based on the training data (seasons 2020-2025, including current season games):
- **Logistic Regression**: ~75% accuracy
- **Random Forest**: ~73% accuracy
- **XGBoost**: ~74% accuracy

## Prediction Methodology

The script generates predictions using a two-step approach:

1. **Recent Performance**: Uses the player's most recent game statistics
2. **Historical Averages**: Falls back to career averages when recent data is unavailable

This ensures robust predictions even for players with limited recent game data.

## Output Format

Predictions are returned as probability arrays with two columns:
- Column 0: Probability of **NO** interception
- Column 1: Probability of **throwing an interception**

Example output:
```
[[0.52892704 0.47107296]  # 47.1% chance of interception
 [0.05948888 0.94051112]  # 94.1% chance of interception
 ...]
```

## Customization

You can modify the script to:
- Change the seasons used for training
- Adjust the feature selection
- Use different machine learning algorithms
- Save predictions to CSV files (uncomment the relevant lines in the main function)

## File Structure

```
INTERCEPTIONS/
├── train_interception_model.py        # Main training and prediction script
├── predict_upcoming_starting_qbs.py   # Prediction script for upcoming games
├── config.py                          # Configuration settings
├── requirements.txt                   # Python dependencies
├── run.sh                             # Convenience script for running models
├── predict_qb_ints.sh                 # Alternative shell script for predictions
├── logreg_model.pkl                   # Trained logistic regression model
├── upcoming_qb_interception_probs.csv # Latest prediction results
└── README.md                          # This documentation
```
