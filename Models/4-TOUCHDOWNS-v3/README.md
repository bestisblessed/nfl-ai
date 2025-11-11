# 4-TOUCHDOWNS-v3: Enhanced Hybrid Model

## Quick Start

```bash
cd /workspace/Models/4-TOUCHDOWNS-v3
./run.sh 10  # For week 10 predictions
```

## What's New in v3?

v3 combines the best aspects of v1 and v2 with additional enhancements:

### Key Improvements

1. **Hybrid Architecture**
   - Position-specific models (like v1) for QB, RB, WR, TE
   - Each position learns its own touchdown patterns
   - More accurate than unified model for diverse positions

2. **Enhanced Features**
   - Multi-window rolling stats (3, 5, 8 games) - captures both recent and medium-term trends
   - Target share and rush share - measures player's role in offense
   - TD trend tracking - compares last 3 games to previous 3 games
   - Season expanding averages - provides baseline expectation
   - Team offensive/defensive context from both v1 and v2

3. **Better Calibration**
   - Isotonic calibration instead of Platt scaling
   - More robust for non-linear probability corrections
   - Better handles edge cases (very high/low probabilities)

4. **Improved Model Parameters**
   - 250 trees (balanced between v1's 400 and v2's 150)
   - Deeper trees (max_depth=5) to capture position-specific patterns
   - Learning rate 0.075 (balanced)
   - Enhanced regularization (L1=0.5, L2=1.5)
   - Class imbalance handling via scale_pos_weight
   - min_child_weight=3 to prevent overfitting on rare events

5. **Enhanced Filtering**
   - Requires 3+ games played this season
   - Higher activity thresholds (2 touches/game vs 1)
   - Position-specific season minimums raised:
     - WRs: 5+ receptions (was 2)
     - TEs: 3+ receptions (was 2)
     - RBs: 8+ rush attempts (was 3)
   - Removes injured and questionable players

6. **Better Metrics**
   - Tracks both calibrated and uncalibrated performance
   - Includes Brier score (probability accuracy metric)
   - Reports class distribution per position
   - Detailed training/validation splits

## Files

- `prepare_data_v3.py` - Enhanced data preparation with new features
- `train_predict_v3.py` - Main modeling script with isotonic calibration
- `generate_html_report.py` - Beautiful HTML report generator
- `run.sh` - Complete pipeline script
- `MODEL_COMPARISON.md` - Detailed comparison of v1, v2, v3

## Output Files

In `predictions-week-{N}-TD/`:

- `final_week{N}_anytime_td_report.csv` - All predictions ranked
- `final_week{N}_{POS}_td_report.csv` - Per-position predictions
- `game_{N}_{HOME}_vs_{AWAY}_td_predictions.txt` - Per-game reports
- `final_week{N}_TD_report.html` - Interactive HTML report
- `model_metrics_v3.csv` - Model performance metrics

## Expected Improvements Over v1 and v2

**Better Calibration**: Isotonic calibration should provide more accurate probabilities, especially at extremes

**Position Nuances**: QB rushing TDs are very different from WR receiving TDs - separate models capture this

**Trend Detection**: TD trend feature identifies hot/cold players better than raw rolling averages

**Better Filtering**: Higher thresholds remove noise from bench players and practice squad call-ups

**Balanced Speed**: Faster than v1 (fewer trees) but more accurate than v2 (position-specific)

## Why v3 Should Perform Better

1. **Addresses v1 Weaknesses**:
   - Simpler than Platt scaling (more robust)
   - Fewer trees = less overfitting risk
   - Stronger regularization

2. **Addresses v2 Weaknesses**:
   - Position-specific models capture nuances
   - Multi-window features capture medium-term trends
   - Red zone stats included (v2 missed these)

3. **New Advantages**:
   - Target/rush share shows player's offensive role
   - TD trends identify momentum
   - Better filtering reduces false positives
   - Enhanced metrics help validate model quality

## Troubleshooting

**"No upcoming players" error**: Make sure `../upcoming_games.csv` exists and has week data

**Position errors**: Check that `../data/rosters.csv` has 2025 season data with positions

**Missing features**: Ensure all data files are in correct locations:
```
Models/4-TOUCHDOWNS-v3/
  data/
    schedule_game_results_pfr.csv
    team_conversions_pfr.csv
  ../upcoming_games.csv
  ../starting_qbs_2025.csv
  ../injured_players.csv
  ../questionable_players.csv
  ../data/rosters.csv
```

**Calibration warnings**: These are normal for small sample sizes. Model still works.

## Next Steps

After running v3, compare its predictions to v1 and v2:

1. Check if probabilities are more realistic (not too extreme)
2. Verify that top predictions make intuitive sense
3. Compare metrics (AUC, log loss, Brier score) across versions
4. Track actual outcomes to validate accuracy over multiple weeks

v3 should provide the most reliable touchdown predictions by combining the strengths of both previous versions!
