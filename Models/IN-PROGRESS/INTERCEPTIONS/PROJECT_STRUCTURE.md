# Project Structure

## Directory Layout

```
INTERCEPTIONS/
│
├── 📋 Documentation
│   ├── README.md              # Project overview (Quick start)
│   ├── QUICK_START.md         # 30-second reference guide
│   ├── STEPS.md               # Complete step-by-step guide
│   ├── REFACTOR_SUMMARY.md    # Refactoring changes log
│   ├── EV_VIG_KELLY.md        # Mathematical theory
│   └── PROJECT_STRUCTURE.md   # This file
│
├── ⚙️ Configuration
│   └── config.py              # All settings and paths (1.7KB)
│
├── 🔧 Main Scripts
│   ├── run_all.sh                          # Master script ⭐ START HERE
│   ├── 1_scrape_odds.py                    # Step 1: Scrape DK odds (2.5KB)
│   ├── 2_calculate_edges.py                # Step 2: Calculate edges (5.8KB)
│   ├── train_qb_interceptions_model.py     # Train ML models (8.2KB)
│   ├── predict_qb_interceptions.py         # Generate predictions (8.1KB)
│   └── generate_final_report.py            # Create HTML report (19KB)
│
├── 📦 Utility Modules
│   └── utils/
│       ├── __init__.py        # Package marker
│       ├── api.py             # DraftKings API calls (1.6KB)
│       ├── odds.py            # Probability & odds math (1.6KB)
│       ├── matching.py        # Player name fuzzy matching (2.8KB)
│       ├── parser.py          # Parse API responses (3.9KB)
│       └── io.py              # File operations (1.0KB)
│
├── 📊 Data Directories
│   ├── data/                  # Scraped odds
│   │   ├── odds_interceptions_dk_latest.csv
│   │   └── odds_interceptions_dk_YYYYMMDD_HHMM.csv (snapshots)
│   │
│   ├── predictions/           # Model outputs
│   │   ├── upcoming_qb_interception_*_week_N.csv
│   │   ├── betting_edges_latest.csv
│   │   └── week_N_qb_interception_report.html
│   │
│   └── models/                # Trained ML models
│       ├── logistic_regression_model.pkl
│       ├── random_forest_model.pkl
│       └── xgboost_model.pkl
│
├── 🗄️ Backup
│   └── old_scripts/           # Original monolithic files
│       ├── scrape_qb_interceptions_odds.py (418 lines)
│       ├── calc_edges.py (382 lines)
│       └── run.sh
│
└── 📓 Analysis
    └── Interceptions.ipynb    # Jupyter notebook for exploration
```

## File Sizes

### Main Scripts
```
1_scrape_odds.py              2.5 KB  ✓ Small & focused
2_calculate_edges.py          5.8 KB  ✓ Small & focused
train_qb_interceptions_model  8.2 KB
predict_qb_interceptions      8.1 KB
generate_final_report         19 KB
run_all.sh                    4.2 KB
```

### Utils (Reusable Modules)
```
utils/api.py                  1.6 KB
utils/odds.py                 1.6 KB
utils/matching.py             2.8 KB
utils/parser.py               3.9 KB
utils/io.py                   1.0 KB
───────────────────────────────────
Total utils:                  10.9 KB
```

### Documentation
```
README.md                     4.5 KB
QUICK_START.md                3.7 KB
STEPS.md                      7.4 KB
REFACTOR_SUMMARY.md           5.7 KB
EV_VIG_KELLY.md              7.6 KB
PROJECT_STRUCTURE.md          3.5 KB
───────────────────────────────────
Total docs:                   32.4 KB
```

## Code Metrics

### Before Refactoring
```
scrape_qb_interceptions_odds.py    418 lines
calc_edges.py                      382 lines
───────────────────────────────────────────
Total main scripts:                800 lines
```

### After Refactoring
```
1_scrape_odds.py                    64 lines  (-354, -85%)
2_calculate_edges.py               127 lines  (-255, -67%)
───────────────────────────────────────────
Total main scripts:                191 lines  (-609, -76%)

utils/api.py                        46 lines
utils/odds.py                       47 lines
utils/matching.py                   76 lines
utils/parser.py                     97 lines
utils/io.py                         28 lines
───────────────────────────────────────────
Total utils:                       294 lines

TOTAL CODE:                        485 lines  (-315, -39% overall)
```

**Result:** 76% reduction in main scripts, 39% overall reduction while adding modularity

## Execution Flow

```
START
  │
  ├─> run_all.sh (Master Script)
  │    │
  │    ├─> train_qb_interceptions_model.py (Optional)
  │    │    └─> Creates: models/*.pkl
  │    │
  │    ├─> 1_scrape_odds.py
  │    │    ├─> Uses: utils/api.py, utils/parser.py, utils/io.py
  │    │    └─> Creates: data/odds_interceptions_dk_*.csv
  │    │
  │    ├─> predict_qb_interceptions.py
  │    │    └─> Creates: predictions/upcoming_qb_interception_*_week_N.csv
  │    │
  │    ├─> 2_calculate_edges.py
  │    │    ├─> Uses: utils/odds.py, utils/matching.py
  │    │    └─> Creates: predictions/betting_edges_latest.csv
  │    │
  │    └─> generate_final_report.py (Optional)
  │         └─> Creates: predictions/week_N_qb_interception_report.html
  │
END
```

## Module Dependencies

```
1_scrape_odds.py
├── utils.api          (fetch_draftkings_interceptions)
├── utils.parser       (extract_events_markets_selections, make_event_maps, parse_interception_markets)
├── utils.io           (write_odds_csv)
└── config             (ODDS_LATEST, ODDS_SNAPSHOT_DIR, SCRAPE_CACHE_MINUTES)

2_calculate_edges.py
├── utils.odds         (american_to_probability, probability_to_american, remove_vig, calculate_edge)
├── utils.matching     (normalize_player_name, build_player_mapping)
└── config             (ODDS_LATEST, PREDICTIONS_DIR)
```

## Data Flow

```
Input Data
    │
    ├─> player_stats_pfr.csv (Historical NFL data)
    │
    v
train_qb_interceptions_model.py
    │
    ├─> logistic_regression_model.pkl
    ├─> random_forest_model.pkl
    └─> xgboost_model.pkl
         │
         v
predict_qb_interceptions.py
         │
         └─> upcoming_qb_interception_*_week_N.csv
              │
              v
         DraftKings API
              │
              v
         1_scrape_odds.py
              │
              └─> odds_interceptions_dk_latest.csv
                   │
                   v
              2_calculate_edges.py
                   │
                   └─> betting_edges_latest.csv ⭐ FINAL OUTPUT
```

## Key Features

### ✅ Modularity
- Shared utilities in `utils/` folder
- Reusable across scripts
- Easy to extend (add new sportsbooks, models, etc.)

### ✅ Maintainability
- Small, focused scripts
- Clear separation of concerns
- Easy to locate and update functionality

### ✅ Portability
- No hardcoded paths
- Relative path configuration
- Environment variable support

### ✅ Documentation
- Multiple documentation files for different needs
- Clear execution steps
- Inline code comments

### ✅ Usability
- Interactive master script
- Smart caching
- Helpful error messages

## Quick Reference

| Task | Command |
|------|---------|
| Run everything | `./run_all.sh` |
| Just scrape odds | `python 1_scrape_odds.py` |
| Calculate edges | `python 2_calculate_edges.py` |
| Train models | `python train_qb_interceptions_model.py` |
| Make predictions | `python predict_qb_interceptions.py --week N` |

## Documentation Guide

| Document | Purpose | When to Read |
|----------|---------|--------------|
| **README.md** | Project overview | First time |
| **QUICK_START.md** | Fast reference | Every time |
| **STEPS.md** | Detailed guide | When learning |
| **REFACTOR_SUMMARY.md** | What changed | Migration |
| **EV_VIG_KELLY.md** | Math theory | Understanding |
| **PROJECT_STRUCTURE.md** | This file | Architecture |

---

**Last Updated:** 2025-11-05  
**Version:** 2.0 (Modular Refactor)
