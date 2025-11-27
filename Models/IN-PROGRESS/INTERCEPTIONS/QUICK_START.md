# Quick Start Guide

## 30-Second Start

```bash
./run_all.sh
```

That's it! Follow the prompts.

---

## What Each Script Does

### Main Scripts (Run These)

| Script | What It Does | When to Run |
|--------|-------------|-------------|
| `1_scrape_odds.py` | Fetches DraftKings odds | Before analysis |
| `2_calculate_edges.py` | Finds value bets | After predictions |
| `train_qb_interceptions_model.py` | Trains ML models | Once per season |
| `predict_qb_interceptions.py` | Makes predictions | Weekly |
| `run_all.sh` | Runs everything | Weekly |

### Utility Modules (Don't Run These)

| Module | Purpose |
|--------|---------|
| `utils/api.py` | DraftKings API calls |
| `utils/odds.py` | Probability math |
| `utils/matching.py` | Match player names |
| `utils/parser.py` | Parse responses |
| `utils/io.py` | Read/write files |

---

## Common Commands

### Full Analysis
```bash
./run_all.sh
# Enter: 7 (for Week 7)
# Train models: n
# Generate report: y
```

### Just Update Odds
```bash
python 1_scrape_odds.py --force
python 2_calculate_edges.py
```

### New Season
```bash
python train_qb_interceptions_model.py
```

---

## Output Files

| File | What It Contains |
|------|-----------------|
| `data/odds_interceptions_dk_latest.csv` | Latest DK odds |
| `predictions/upcoming_qb_interception_*_week_N.csv` | Model predictions |
| `predictions/betting_edges_latest.csv` | Value bets |
| `predictions/week_N_qb_interception_report.html` | Visual report |

---

## Understanding the Output

```
Player          Model    Book     Fair     Model %  Book %   Edge
-----------------------------------------------------------------
Patrick Mahomes  -180    -160     -164     64.3%    62.1%    +2.2%
Joe Burrow       -140    -110     -113     58.3%    53.1%    +5.2%
```

### What This Means

**Patrick Mahomes:**
- Model says 64.3% chance of interception
- Book says 62.1% (after removing vig)
- +2.2% edge = Model thinks it's MORE likely
- **Action:** Consider betting OVER 0.5 interceptions

**Positive Edge** → Bet OVER (interception more likely)  
**Negative Edge** → Bet UNDER (interception less likely)

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "Odds file not found" | Run: `python 1_scrape_odds.py` |
| "Predictions file not found" | Run: `python predict_qb_interceptions.py --week N` |
| "No module named 'requests'" | Run: `pip install requests pandas scikit-learn xgboost` |
| Empty odds data | Wait - DK posts props 2-3 days before games |

---

## File Structure

```
INTERCEPTIONS/
├── run_all.sh          # ⭐ START HERE
├── 1_scrape_odds.py    # Step 1
├── 2_calculate_edges.py # Step 2
├── config.py           # Settings
├── utils/              # Helper functions
├── data/               # Scraped odds
├── predictions/        # Results
└── models/             # Trained models
```

---

## Documentation

- **This file** - Quick reference
- **STEPS.md** - Detailed guide
- **README.md** - Project overview
- **config.py** - All settings

---

## Advanced Options

### Force Re-scrape
```bash
python 1_scrape_odds.py --force
```

### Different Models
```bash
python predict_qb_interceptions.py --week 7 --model random_forest
python predict_qb_interceptions.py --week 7 --model xgboost
```

### Custom Odds File
```bash
python 2_calculate_edges.py --odds data/odds_interceptions_dk_20251016.csv
```

---

## Tips

💡 Run `1_scrape_odds.py` multiple times per day to track line movement

💡 Compare edge percentages across different models

💡 Larger absolute edges (±5%+) are more significant

💡 Check both OVER and UNDER for opportunities

💡 Re-scrape odds close to game time for best accuracy

---

**Need help?** See STEPS.md for detailed instructions.
