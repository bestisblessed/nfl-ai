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

The system trains and compares three different machine learning algorithms:
- **Logistic Regression**: ~66% accuracy (best performing)
- **Random Forest**: ~62% accuracy
- **XGBoost**: ~59% accuracy

All three models are saved and can be used for predictions.

## Prediction Methodology

The script generates predictions using a two-step approach:

1. **Recent Performance**: Uses the player's most recent game statistics
2. **Historical Averages**: Falls back to career averages when recent data is unavailable

This ensures robust predictions even for players with limited recent game data.

## Vigorish (VIG) Handling

### What is VIG?
Vigorish (VIG) is the bookmaker's profit margin built into betting odds. For QB interception props, this typically ranges from 4.5-5.5% per side (9-11% total), though it varies by market and sportsbook.

### Why VIG Matters
Comparing model probabilities (which are "fair" estimates) directly against bookmaker odds (which include vig) creates inaccurate edge calculations. Proper vig handling is essential for identifying true betting opportunities.

### VIG Calculation Methods

**Method 1 (Currently Used): Normalize Bookmaker Probabilities**
- Calculates actual vig per market: `vig_factor = 1 / (over_prob + under_prob)`
- Removes vig: `fair_book_prob = book_prob × vig_factor`
- Compares: `edge = model_prob - fair_book_prob`
- **Purpose**: Shows how much your model disagrees with the bookmaker's "true" probability assessment

**Method 2 (Alternative): Add VIG to Model Probabilities**
- Adds market vig to model: `model_vigged = model_prob × (over_prob + under_prob)`
- Compares: `edge = model_vigged - book_prob`
- **Purpose**: Shows edge against actual betting prices you'd face

### Implementation
The `compare_odds_to_model.py` script uses **Method 1** by default, calculating actual vig for each specific market. You can optionally use a fixed vig percentage:

```bash
# Use actual per-market vig (default)
python compare_odds_to_model.py

# Use fixed 5% vig across all markets
python compare_odds_to_model.py --fixed-vig 0.05
```

**Recommendation**: Use actual per-market vig (default) for maximum accuracy, as bookmakers adjust vig based on betting patterns, player performance, and market conditions.

## Output Format

Predictions are returned as probability arrays with two columns:
- Column 0: Probability of **NO** interception
- Column 1: Probability of **throwing an interception**

American betting odds are also available by running the conversion script.

## Usage

### Training All Models
```bash
python train_interception_model.py
```
This trains all three models, saves them, and generates prediction files for each.

### Predicting with Specific Model
```bash
# Logistic Regression (default)
python predict_upcoming_starting_qbs.py

# Random Forest
python predict_upcoming_starting_qbs.py --model random_forest

# XGBoost
python predict_upcoming_starting_qbs.py --model xgboost
```

### Converting to American Odds (Optional)
The main pipeline saves American odds directly. Use this script only if you need to convert existing probability files:
```bash
python convert_probabilities_to_american_odds.py --model random_forest --week 1
```

## Customization

You can modify the scripts to:
- Change the seasons used for training
- Adjust the feature selection
- Use different machine learning algorithms
- Save predictions to CSV files

## File Structure

```
INTERCEPTIONS/
├── train_interception_model.py                       # Training script (saves 3 model files)
├── predict_upcoming_starting_qbs.py                 # Prediction script for upcoming games
├── convert_probabilities_to_american_odds.py        # Convert probs to odds (optional utility)
├── config.py                                        # Configuration settings
├── run.sh                                           # Convenience script (full pipeline)
├── *_model.pkl                                      # Trained models (3 files, temp)
├── predictions/                                     # Output directory
│   └── upcoming_qb_interception_*_week_*.csv        # Weekly QB predictions (American odds)
└── README.md                                        # This documentation
```
