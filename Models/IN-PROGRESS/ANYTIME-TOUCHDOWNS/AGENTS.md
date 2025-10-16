# NFL Touchdown Prediction Script

## Overview
This script predicts the probability of NFL players scoring touchdowns in upcoming games using machine learning models trained on historical player statistics and opponent defensive strength.

## Files Generated
- `touchdown_scorers_script.py` - Main executable Python script
- `defense_strength.csv` - Calculated defensive strength for all NFL teams
- `PlayerStats.csv`, `Teams.csv`, `Games.csv`, `Rosters.csv` - Processed data files

## Key Features

### 1. Data Processing
- Loads data from CSV files in the `data/` directory
- Uses `data/all_passing_rushing_receiving.csv` for player statistics
- Processes 45,316 player game records across 27 statistical categories

### 2. Defense Strength Calculation
- Calculates opponent defensive strength based on touchdowns and yards allowed
- Uses weighted composite scoring (50% touchdowns, 50% yards)
- Normalizes and inverts scores (lower = stronger defense)

### 3. Machine Learning Models
- **XGBoost**: 77.78% accuracy (primary model)
- **Random Forest**: 75.62% accuracy 
- **Logistic Regression**: 78.47% accuracy
- Ensemble averaging for final predictions

### 4. Feature Engineering
- Target variable: Binary touchdown scoring (rush_td OR rec_td > 0)
- Features: `rush_att`, `rush_yds`, `rec`, `targets`, `rec_yds`, `opponent_defense_strength`
- Handles 21,040 skill position players (RB, WR, TE)
- 24.1% baseline touchdown rate

### 5. 2025 Game Predictions
- Predicts touchdown probabilities for upcoming games
- Takes estimated player stats and opponent defense strength as inputs
- Provides predictions from all three models plus ensemble average

## Usage

### Running the Script
```bash
python touchdown_scorers_script.py
```

### Making Custom Predictions
```python
from touchdown_scorers_script import predict_2025_touchdown

# After training models in main()
predict_2025_touchdown(
    xgb_model, rf_model, logreg_model,
    "Player Name", "OPP", 0.5,  # opponent_defense_strength
    estimated_carries=10,
    estimated_rushing_yards=50,
    estimated_receptions=4,
    estimated_targets=6,
    estimated_receiving_yards=35
)
```

## Model Performance

### Feature Importance (XGBoost)
1. `rush_att` (29.3%) - Rushing attempts
2. `rec_yds` (24.9%) - Receiving yards  
3. `rush_yds` (21.7%) - Rushing yards
4. `rec` (14.6%) - Receptions
5. `opponent_defense_strength` (5.0%)
6. `targets` (4.6%) - Target share

### Sample Predictions
- **Travis Kelce vs BUF**: 23.7% (TE receiving focus)
- **Christian McCaffrey vs SF**: 53.9% (RB dual-threat)  
- **Tyreek Hill vs MIA**: 31.6% (WR big-play potential)

## Data Requirements
The script expects the following files in the `data/` directory:
- `Teams_OCT_10_2025.csv`
- `Games_OCT_10_2025.csv` 
- `all_passing_rushing_receiving.csv`
- `Rosters_OCT_10_2025.csv`

## Technical Notes
- Uses scikit-learn 1.3+ and XGBoost
- Handles missing values with zero-filling
- Reproducible results with random_state=42
- Warning messages about numerical precision are expected and don't affect results

## Model Validation
- 80/20 train-test split
- Confusion matrix analysis included
- Classification report with precision/recall metrics
- Cross-validation ready architecture
