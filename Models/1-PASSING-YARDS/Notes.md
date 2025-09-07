# NFL Passing Yards Prediction Model (QB)

## Model Overview
This model predicts weekly passing yards for NFL Quarterbacks using historical performance data and current roster assignments.

## Model Type
**XGBoost Regressor** - Gradient boosting decision tree ensemble model

## Target Variable
- **pass_yards**: Weekly passing yards per player-game

## Features Used

### Feature Engineering Approach
- **Trailing Averages**: Uses historical performance metrics over multiple time windows
- **No Lookahead Bias**: All features use `.shift(1)` to ensure only past data is available for prediction
- **Window Sizes**: 3, 5, and 8 game rolling averages

### Feature Set (9 total features)
**Attempts Features:**
- `pass_att_l3`: Trailing 3-game average of pass attempts
- `pass_att_l5`: Trailing 5-game average of pass attempts  
- `pass_att_l8`: Trailing 8-game average of pass attempts

**Completions Features:**
- `pass_cmp_l3`: Trailing 3-game average of completions
- `pass_cmp_l5`: Trailing 5-game average of completions
- `pass_cmp_l8`: Trailing 8-game average of completions

**Passing Yards Features:**
- `pass_yds_l3`: Trailing 3-game average of passing yards
- `pass_yds_l5`: Trailing 5-game average of passing yards
- `pass_yds_l8`: Trailing 8-game average of passing yards

## Model Parameters

```python
XGBRegressor(
    n_estimators=500,        # Number of boosting rounds
    learning_rate=0.05,      # Learning rate (eta)
    max_depth=5,            # Maximum tree depth
    subsample=0.9,          # Fraction of samples per tree
    colsample_bytree=0.9,   # Fraction of features per tree
    objective="reg:squarederror",  # Loss function
    random_state=42,        # Reproducibility
    tree_method="hist"      # Tree construction algorithm
)
```

## Data Pipeline

### Training Data
- **Source**: `data/model_train.csv` (processed historical player-game data)
- **Scope**: Historical NFL player game logs for QB position
- **Preprocessing**: 
  - Numeric conversion and missing data handling
  - Player-level sorting by season/week for rolling calculations
  - Minimum 3 games requirement for historical features

### Current Roster Integration
- **Source**: `data/rosters_2025.csv` (nflverse current roster data)
- **Purpose**: Ensures predictions use up-to-date player-team assignments
- **Key**: Player matching via PFR ID (`player_id` with `.htm` extension)

### Prediction Process
1. **Feature Calculation**: Extract most recent trailing averages for each player
2. **Roster Mapping**: Assign players to current 2025 teams
3. **Missing Data Handling**: Fill missing trailing features with 0.0 for new/limited-data players
4. **Game Assignment**: Map players to upcoming game schedule

## Scripts Architecture

### Position-Specific Scripts
1. **`xgboost_passing_yards_qb.py`**: Quarterback predictions

### Shared Components
- **Model Architecture**: Script uses XGBoost parameters and feature engineering
- **Data Pipeline**: Training data, roster integration, and prediction logic
- **Visualization Functions**: Adaptations of table generation code

## Output Formats

### Generated Directories (per week/position)
- **`predictions-week-{week_num}-QB/`**: Quarterback predictions

### File Types per Game (in each directory)
1. **Full PNG**: Complete statistical table with all trailing features
2. **Cleaned PNG**: Simplified table (player name + predicted yards only)
3. **Text Table**: Terminal-friendly side-by-side tabulated format

### Summary Files (per position)
- `prop_projections_passing.csv`: All player predictions with full feature data for that position

## Model Strengths
- **Temporal Awareness**: Multiple time windows capture both recent and sustained performance
- **Realistic Features**: Only uses information available pre-game
- **Current Rosters**: Accounts for mid-season trades and roster changes
- **Robust to Missing Data**: Handles new players and limited historical data

## Model Limitations
- **Feature Scope**: Limited to passing-specific metrics (no team context, matchup data, etc.)
- **Position Coverage**: Covers QB only
- **Historical Dependency**: Performance limited by quality of trailing averages
- **No Game Context**: Doesn't account for game script, weather, or opponent strength

## Execution

### Running QB Predictions
```bash
./run.sh
```
This executes the complete pipeline:
1. Data preparation and roster download
2. QB predictions

### Running Individual Position
```bash
python prepare_data.py  # Run once to prepare data
python xgboost_passing_yards_qb.py  # QB only
```

## Usage Notes
- **Best For**: Week-to-week passing yards predictions for established QBs
- **Caution With**: New players, players returning from injury, or unusual game contexts
- **Update Frequency**: Requires current roster data and recent historical performance updates
- **Position Coverage**: Predictions for QB passing production
