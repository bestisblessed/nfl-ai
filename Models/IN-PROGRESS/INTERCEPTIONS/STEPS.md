# QB Interception Odds Analysis - Execution Steps

This guide explains the complete workflow for analyzing QB interception betting odds.

## Overview

The analysis consists of 4 main steps:
1. **Train Models** - Build ML models from historical data
2. **Scrape Odds** - Get current betting lines from DraftKings
3. **Make Predictions** - Generate probabilities for upcoming games
4. **Calculate Edges** - Find value bets by comparing model vs market

---

## Prerequisites

### Install Dependencies
```bash
pip install pandas scikit-learn xgboost numpy requests
```

### Set Data Path (Optional)
If your data is not in the default location, set an environment variable:
```bash
export NFL_DATA_PATH="/path/to/player_stats_pfr.csv"
```

---

## Quick Start - Run Everything

Use the master script to run the complete pipeline:

```bash
./run_all.sh
```

This will prompt for the NFL week number and execute all steps automatically.

---

## Step-by-Step Execution

### Step 1: Train ML Models

Train Logistic Regression, Random Forest, and XGBoost models on historical data:

```bash
python train_qb_interceptions_model.py
```

**Output:**
- `models/logistic_regression_model.pkl`
- `models/random_forest_model.pkl`
- `models/xgboost_model.pkl`
- Performance metrics printed to console

**When to run:** Once per season, or when new historical data is added.

---

### Step 2: Scrape DraftKings Odds

Fetch current QB interception O/U odds:

```bash
python 1_scrape_odds.py
```

**Options:**
- `--force` - Bypass 5-minute cache and force re-fetch

**Output:**
- `data/odds_interceptions_dk_latest.csv` - Most recent odds
- `data/odds_interceptions_dk_YYYYMMDD_HHMM.csv` - Timestamped snapshot

**When to run:** Before each analysis, or whenever odds change significantly.

**Caching:** Script automatically skips re-fetching if data is less than 5 minutes old.

---

### Step 3: Generate Predictions

Create interception probability predictions for upcoming games:

```bash
python predict_qb_interceptions.py --week 7
```

**Options:**
- `--week WEEK_NUM` - NFL week number (required)
- `--model MODEL_TYPE` - Choose model: `logistic_regression` (default), `random_forest`, or `xgboost`

**Output:**
- `predictions/upcoming_qb_interception_MODELTYPE_week_N.csv`

**When to run:** Once per week, after Step 1 and before Step 4.

---

### Step 4: Calculate Betting Edges

Compare model predictions against bookmaker odds:

```bash
python 2_calculate_edges.py
```

**Options:**
- `--odds FILE` - Specify odds CSV (default: latest from Step 2)
- `--pred FILE` - Specify predictions CSV (default: latest from Step 3)

**Output:**
- Console display showing top betting opportunities
- `predictions/betting_edges_latest.csv` - Detailed results

**When to run:** After Steps 2 and 3, whenever you want to find value bets.

---

## Complete Workflow Example

Here's a typical weekly workflow:

```bash
# Week 7 analysis
export WEEK=7

# 1. Train models (if not done recently)
python train_qb_interceptions_model.py

# 2. Scrape latest odds from DraftKings
python 1_scrape_odds.py --force

# 3. Generate predictions for Week 7
python predict_qb_interceptions.py --week $WEEK

# 4. Calculate edges to find value bets
python 2_calculate_edges.py

# Optional: Generate visual HTML report
python generate_final_report.py --week $WEEK
```

---

## File Structure

```
INTERCEPTIONS/
├── config.py                          # Configuration (paths, settings)
├── STEPS.md                           # This file
├── README.md                          # Project documentation
│
├── utils/                             # Utility modules
│   ├── api.py                         # DraftKings API calls
│   ├── odds.py                        # Odds conversion & calculations
│   ├── matching.py                    # Player name matching
│   ├── parser.py                      # Parse API responses
│   └── io.py                          # File I/O operations
│
├── 1_scrape_odds.py                   # Step 2: Scrape DK odds
├── 2_calculate_edges.py               # Step 4: Calculate edges
├── train_qb_interceptions_model.py    # Step 1: Train models
├── predict_qb_interceptions.py        # Step 3: Make predictions
├── generate_final_report.py           # Optional: HTML report
├── run_all.sh                         # Master script (all steps)
│
├── data/                              # Scraped odds data
│   ├── odds_interceptions_dk_latest.csv
│   └── odds_interceptions_dk_*.csv
│
├── predictions/                       # Model outputs & edges
│   ├── upcoming_qb_interception_*_week_*.csv
│   ├── betting_edges_latest.csv
│   └── week_*_qb_interception_report.html
│
└── models/                            # Trained ML models
    ├── logistic_regression_model.pkl
    ├── random_forest_model.pkl
    └── xgboost_model.pkl
```

---

## Understanding the Output

### Edge Analysis Display

```
Player          Model    Book     Fair     Model %  Book %   Edge
-----------------------------------------------------------------
Patrick Mahomes  -180    -160     -164     64.3%    62.1%    +2.2%
Joe Burrow       -140    -110     -113     58.3%    53.1%    +5.2%
```

**Columns:**
- **Model** - Your model's predicted odds (no vig)
- **Book** - Actual DraftKings odds (includes vig)
- **Fair** - DraftKings fair odds (vig removed)
- **Model %** - Model's probability estimate
- **Book %** - Bookmaker's fair probability
- **Edge** - Your advantage over the fair line

**Positive Edge** = Model thinks interception is MORE likely than bookmaker

**Negative Edge** = Model thinks interception is LESS likely than bookmaker

---

## Troubleshooting

### "Odds file not found"
Run Step 2: `python 1_scrape_odds.py`

### "Predictions file not found"
Run Step 3: `python predict_qb_interceptions.py --week WEEK_NUM`

### "No module named 'requests'"
Install dependencies: `pip install requests pandas scikit-learn xgboost`

### "No matching players found"
Player names may differ between model and sportsbook. Check the fuzzy matching threshold in `utils/matching.py`.

### Empty odds data
No games may be available. DraftKings typically posts props 2-3 days before games.

---

## Advanced Usage

### Custom Data Path
```bash
export NFL_DATA_PATH="/custom/path/to/data.csv"
python train_qb_interceptions_model.py
```

### Force Re-scrape Odds
```bash
python 1_scrape_odds.py --force
```

### Use Different Models
```bash
# Random Forest
python predict_qb_interceptions.py --week 7 --model random_forest

# XGBoost
python predict_qb_interceptions.py --week 7 --model xgboost
```

### Compare Specific Files
```bash
python 2_calculate_edges.py \
  --odds data/odds_interceptions_dk_20251016_0038.csv \
  --pred predictions/upcoming_qb_interception_logistic_regression_week_7.csv
```

---

## Notes

- **Timing**: Run steps 2-4 close to game time for most accurate odds
- **Caching**: Step 2 caches for 5 minutes to avoid excessive API calls
- **Models**: Logistic Regression recommended for probability calibration
- **VIG**: All edge calculations properly account for bookmaker margins
- **Updates**: Re-run when odds move significantly or new information emerges

---

## Support

For issues or questions, refer to:
- `README.md` - Detailed project documentation
- `EV_VIG_KELLY.md` - Mathematical explanation of VIG and Kelly criterion
- `config.py` - All configurable settings
