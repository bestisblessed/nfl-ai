# QB Interception Odds Analysis

A clean, modular system for analyzing NFL QB interception betting odds and finding value bets.

## Quick Start

```bash
# Run complete pipeline
./run_all.sh
```

## What This Does

1. **Scrapes** DraftKings QB interception odds
2. **Predicts** interception probabilities using ML models
3. **Calculates** betting edges by comparing model vs market
4. **Identifies** value betting opportunities

## Installation

```bash
pip install pandas scikit-learn xgboost numpy requests
```

## Project Structure

```
INTERCEPTIONS/
├── config.py                    # All settings and paths
├── STEPS.md                     # Detailed execution guide
├── run_all.sh                   # Master script (runs everything)
│
├── utils/                       # Modular utility functions
│   ├── api.py                   # DraftKings API calls
│   ├── odds.py                  # Probability & odds conversions
│   ├── matching.py              # Player name matching
│   ├── parser.py                # Parse API responses
│   └── io.py                    # File operations
│
├── 1_scrape_odds.py            # Scrape DraftKings odds
├── 2_calculate_edges.py        # Find betting value
├── train_qb_interceptions_model.py      # Train ML models
├── predict_qb_interceptions.py          # Generate predictions
│
├── data/                        # Scraped odds
├── predictions/                 # Model outputs
└── models/                      # Trained ML models
```

## Basic Usage

### Option 1: Run Everything (Recommended)
```bash
./run_all.sh
# Enter week number when prompted
```

### Option 2: Step-by-Step

```bash
# Step 1: Train models (once per season)
python train_qb_interceptions_model.py

# Step 2: Scrape current odds
python 1_scrape_odds.py

# Step 3: Generate predictions for Week 7
python predict_qb_interceptions.py --week 7

# Step 4: Calculate betting edges
python 2_calculate_edges.py
```

## Understanding the Output

The edge analysis shows where your model disagrees with the bookmaker:

```
Player          Model    Book     Fair     Model %  Book %   Edge
-----------------------------------------------------------------
Patrick Mahomes  -180    -160     -164     64.3%    62.1%    +2.2%
```

- **Model** = Your model's odds (no vig)
- **Book** = Actual DraftKings odds (includes vig)
- **Fair** = DraftKings true odds (vig removed)
- **Edge** = Your advantage (+2.2% means model thinks it's more likely)

**Positive Edge** = Bet the OVER (interception more likely than market thinks)

**Negative Edge** = Bet the UNDER (interception less likely than market thinks)

## Configuration

Edit `config.py` to customize:
- Data paths
- Model parameters
- Scraping settings
- Edge thresholds

## Key Features

✓ **Modular Design** - Clean separation of concerns  
✓ **Fixed Paths** - Uses relative paths, no hardcoded absolute paths  
✓ **Smart Caching** - Avoids unnecessary API calls (5min cache)  
✓ **VIG Handling** - Properly removes bookmaker margins  
✓ **Fuzzy Matching** - Handles name variations between sources  
✓ **Multiple Models** - Logistic Regression, Random Forest, XGBoost  

## Documentation

- **STEPS.md** - Complete step-by-step guide
- **EV_VIG_KELLY.md** - Mathematical theory
- **config.py** - All configurable settings

## Troubleshooting

**"Odds file not found"**  
→ Run: `python 1_scrape_odds.py`

**"Predictions file not found"**  
→ Run: `python predict_qb_interceptions.py --week WEEK_NUM`

**Empty odds data**  
→ DraftKings posts props 2-3 days before games

**No matching players**  
→ Check fuzzy matching threshold in `utils/matching.py`

## Advanced

### Force Re-scrape
```bash
python 1_scrape_odds.py --force
```

### Use Different Model
```bash
python predict_qb_interceptions.py --week 7 --model random_forest
python predict_qb_interceptions.py --week 7 --model xgboost
```

### Custom Data Path
```bash
export NFL_DATA_PATH="/path/to/your/data.csv"
python train_qb_interceptions_model.py
```

### Compare Specific Files
```bash
python 2_calculate_edges.py \
  --odds data/odds_interceptions_dk_20251016.csv \
  --pred predictions/upcoming_qb_interception_lr_week_7.csv
```

## Notes

- Run steps 2-4 close to game time for best results
- Models are calibrated on 2020-2025 data
- Edge calculations account for bookmaker vig
- Re-train models when new season data is available

## License

MIT

---

*For detailed documentation, see STEPS.md*
