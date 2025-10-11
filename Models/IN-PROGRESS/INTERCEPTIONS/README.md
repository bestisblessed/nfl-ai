# QB Interception Prediction Model

A complete machine learning pipeline for predicting NFL quarterback interception probabilities and identifying betting edges against sportsbooks. Includes model training, live predictions, odds scraping, and sophisticated edge analysis with proper VIG handling.

## Overview

This QB Interception Prediction Model uses machine learning to predict quarterback interception probabilities and identify betting edges. The system includes:

- **ML Model Training**: Compares Logistic Regression, Random Forest, and XGBoost algorithms
- **Live Predictions**: Generates interception probabilities for upcoming NFL games
- **Odds Scraping**: Collects real-time DraftKings betting lines
- **Edge Analysis**: Calculates betting advantages by comparing model predictions vs. bookmaker odds
- **VIG Handling**: Properly accounts for bookmaker profit margins in edge calculations

The complete pipeline provides actionable insights for identifying undervalued QB interception props.

## Features Used

The model uses the following quarterback statistics as features:
- `pass_att`: Number of pass attempts
- `pass_cmp`: Number of completed passes
- `pass_yds`: Total passing yards
- `pass_td`: Passing touchdowns
- `pass_sacked`: Number of times sacked

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

#### Training Script Output:
- Model performance metrics (accuracy, precision, recall, F1-score)
- Confusion matrices for each algorithm
- Cross-validation results
- Saved model files (*.pkl)

#### Prediction Script Output:
- Individual model prediction files in `predictions/` directory
- American odds and probabilities for each QB

#### Edge Analysis Output:
- Comprehensive comparison table showing:
  - Model predictions vs bookmaker odds
  - True probabilities (vig removed) vs implied probabilities (vig included)
  - Edge percentages for each player
- Terminal display ranked by model confidence

## Data Requirements

The script expects a CSV file at `/Users/td/Code/nfl-ai/Models/IN-PROGRESS/final_data_pfr/player_stats_pfr.csv` with the following characteristics:
- Contains NFL player statistics from seasons 2020-2025
- Includes quarterback position data
- Has the feature columns listed above
- Contains a `pass_int` column for the target variable (interceptions thrown)

## Model Performance

The system trains and compares three different machine learning algorithms on historical NFL data (seasons 2020-2025). Performance metrics are evaluated using cross-validation:

- **Logistic Regression**: Primary model, optimized for probability predictions
- **Random Forest**: Ensemble method for robustness
- **XGBoost**: Gradient boosting for complex patterns

All three models are saved as `.pkl` files and can be used for predictions. The Logistic Regression model is used by default for edge analysis due to its strong probability calibration.

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

### Prediction Files
Individual model predictions are saved as CSV files in the `predictions/` directory:
- `upcoming_qb_interception_logistic_regression_week_1.csv`
- `upcoming_qb_interception_random_forest_week_1.csv`
- `upcoming_qb_interception_xgboost_week_1.csv`

Each contains:
- Player name and team information
- American odds for interception/no-interception
- Probabilities for both outcomes

### Edge Analysis Display
The comparison script (`compare_odds_to_model.py`) generates a comprehensive analysis table with:

| Column | Description |
|--------|-------------|
| **Rank** | Position sorted by model prediction (favorite to underdog) |
| **Player** | Quarterback name |
| **Model Line (True)** | Algorithm's unbiased prediction (no vig) |
| **Book Line (True)** | Bookmaker's fair odds (vig removed) |
| **Book Line (Implied)** | Actual betting odds users see (with vig) |
| **Model % Prob (True)** | Model's probability estimate |
| **Book % Prob (True)** | Bookmaker's fair probability |
| **Edge %** | Advantage over bookmaker's fair assessment |
| **Tm/Opp/Time** | Team, opponent, and game time |

### Key Concepts in Output:
- **True**: Fair probabilities without bookmaker margin
- **Implied**: Probabilities that include vig (what users see)
- **Edge**: How much your model outperforms the bookmaker's fair assessment

## Usage

### Complete Workflow (Recommended)
Run the full pipeline in one command:
```bash
./run.sh
```
This will:
1. Train all three ML models
2. Generate predictions for upcoming games
3. Scrape latest DraftKings odds
4. Compare model predictions vs. bookmaker lines
5. Display results with edge analysis

### Individual Steps

#### Training Models
```bash
python train_interception_model.py
```
Trains Logistic Regression, Random Forest, and XGBoost models on historical data.

#### Generating Predictions
```bash
# Logistic Regression (default)
python predict_upcoming_starting_qbs.py

# Random Forest
python predict_upcoming_starting_qbs.py --model random_forest

# XGBoost
python predict_upcoming_starting_qbs.py --model xgboost
```

#### Scraping Odds (Optional)
```bash
# Scrape DraftKings QB interception odds
python scrape_interception_odds.py

# Alternative scraper for Action Network
python scrape_interception_odds_action_network.py
```

#### Edge Analysis
Compare model predictions against bookmaker odds:
```bash
# Use actual per-market vig (recommended)
python compare_odds_to_model.py

# Use fixed vig percentage across all markets
python compare_odds_to_model.py --fixed-vig 0.05
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
├── compare_odds_to_model.py                         # Edge analysis vs bookmaker odds
├── scrape_interception_odds.py                      # DraftKings odds scraper
├── scrape_interception_odds_action_network.py       # Action Network odds scraper
├── config.py                                        # Configuration settings
├── run.sh                                           # Complete pipeline script (train + predict + scrape + analyze)
├── Interceptions.ipynb                              # Jupyter notebook for analysis
├── *_model.pkl                                      # Trained models (3 files, temp)
├── data/                                            # Scraped odds data
│   └── odds_interceptions_dk_latest.csv            # Latest DraftKings odds
├── predictions/                                     # Output directory
│   ├── upcoming_qb_interception_*_week_*.csv        # Individual model predictions
│   └── upcoming_qb_interception_edges_week_*.csv    # Edge analysis results
├── bak/                                             # Backup files
└── README.md                                        # This documentation
```
