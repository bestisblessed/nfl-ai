# 4-TOUCHDOWNS-v3: Improved Touchdown Prediction Model

## Overview

This is version 3 of the touchdown prediction model, combining the best aspects of v1 and v2 while adding new improvements.

## Documentation

- **BEGINNER_EXPLANATION.md** - Start here! Simple explanations of all three models
- **MODEL_EXPLANATION.md** - Detailed technical explanation of how each model works
- **PARAMETER_COMPARISON.md** - Side-by-side comparison of all parameters and features

## Quick Start

```bash
bash 4-TOUCHDOWNS-v3/run.sh <week_number>
```

## What's New in v3

### Key Improvements
1. **More Trees (500)** - Better learning capacity
2. **Deeper Trees (5 levels)** - Can capture more complex patterns
3. **Lower Learning Rate (0.03)** - More conservative, prevents overfitting
4. **Better Regularization** - Both L1 and L2 with stronger L2
5. **Additional Features** - TD rate, consecutive TD streak, touches
6. **Dual Team Features** - Both static ratings AND dynamic rolling stats
7. **Better Calibration** - Isotonic regression instead of Platt scaling
8. **Time-Series Aware** - Respects temporal order in training
9. **Early Stopping** - Prevents overfitting
10. **More Windows** - Adds 2-game window for recent trends

### Features
- Position-specific models (WR, RB, TE, QB)
- Multiple rolling windows (2, 3, 5, 8, 12 games)
- Calibrated probabilities
- Class imbalance handling
- Dynamic team features
- Static team ratings
- TD rate and streak features

## Files

- `prepare_data_v3.py` - Data preparation and feature engineering
- `xgboost_anytime_td_v3.py` - Model training and prediction
- `generate_html_reports.py` - HTML report generation
- `run.sh` - Main execution script

## Output

Predictions are saved to `predictions-week-{WEEK}-TD/`:
- `final_week{WEEK}_anytime_td_report.csv` - All predictions
- `final_week{WEEK}_{POS}_td_report.csv` - Per-position predictions
- `game_XX_{TEAM1}_vs_{TEAM2}_td_predictions.txt` - Per-game summaries
- `final_week{WEEK}_TD_report.html` - Combined HTML report
- `metrics_{POS}.csv` - Model performance metrics

## Requirements

- pandas
- numpy
- xgboost
- scikit-learn
- tabulate

## Model Comparison Summary

| Feature | v1 | v2 | v3 |
|---------|----|----|----|
| Position-specific models | ✅ | ❌ | ✅ |
| Multiple rolling windows | ✅ | ❌ | ✅ |
| Calibration | ✅ (Platt) | ❌ | ✅ (Isotonic) |
| Dynamic team features | ❌ | ✅ | ✅ |
| Static team features | ✅ | ❌ | ✅ |
| Class imbalance handling | ❌ | ✅ | ✅ |
| Number of trees | 400 | 150 | 500 |
| Learning rate | 0.05 | 0.1 | 0.03 |
| Max depth | 4 | 4 | 5 |
| Early stopping | ❌ | ❌ | ✅ |
| Time-series aware | ❌ | ❌ | ✅ |
