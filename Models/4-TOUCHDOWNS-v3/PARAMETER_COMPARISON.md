# Parameter Comparison: v1 vs v2 vs v3

## XGBoost Model Parameters

### v1 Parameters
```python
XGBClassifier(
    objective="binary:logistic",
    eval_metric="logloss",
    n_estimators=400,           # 400 trees
    max_depth=4,                # Tree depth: 4
    learning_rate=0.05,         # Conservative learning rate
    subsample=0.9,              # 90% of data per tree
    colsample_bytree=0.9,       # 90% of features per tree
    random_state=42,
    reg_alpha=0.0,              # No L1 regularization
    reg_lambda=1.0,             # L2 regularization
)
```

### v2 Parameters
```python
XGBClassifier(
    objective="binary:logistic",
    eval_metric="logloss",
    n_estimators=150,           # 150 trees (fewer)
    learning_rate=0.1,          # Higher learning rate
    max_depth=4,                 # Same depth
    subsample=0.8,              # 80% of data (more aggressive)
    colsample_bytree=0.8,       # 80% of features
    n_jobs=4,                   # Parallel processing
    scale_pos_weight=auto,      # Handles class imbalance
)
```

### v3 Parameters
```python
XGBClassifier(
    objective="binary:logistic",
    eval_metric="logloss",
    n_estimators=500,           # More trees than v1
    max_depth=5,                 # Deeper trees (was 4)
    learning_rate=0.03,          # Most conservative
    subsample=0.85,             # Between v1 and v2
    colsample_bytree=0.85,      # Between v1 and v2
    random_state=42,
    reg_alpha=0.1,              # L1 regularization added
    reg_lambda=1.5,             # Stronger L2 regularization
    scale_pos_weight=auto,      # Class imbalance handling
    min_child_weight=3,          # Minimum samples per leaf
    gamma=0.1,                   # Minimum loss reduction for splits
)
```

## Feature Engineering Comparison

### v1 Features
- **Rolling Windows**: 3, 5, 8, 12 games
- **Base Stats**: rush_att, rush_yds, targets, rec, rec_yds, scoring_tds
- **Total Features**: ~24 rolling features + 7 context features = ~31 features
- **Team Features**: Static ratings (Offense, Defense), red zone stats
- **Opponent Features**: opp_offense, opp_defense, opp_td_rate_pos/qb_rush

### v2 Features
- **Rolling Windows**: 3 games only
- **Base Stats**: rush_att, rush_yds, rush_long, targets, rec, rec_yds, rec_long, fantasy_points_ppr
- **Derived**: touches, total_tds
- **Total Features**: ~10 rolling features + 8 team features + 2 context = ~20 features
- **Team Features**: Dynamic rolling TD/points scored/allowed (3-game window)
- **Opponent Features**: Same dynamic features for opponent

### v3 Features
- **Rolling Windows**: 2, 3, 5, 8, 12 games (adds 2-game for recent trends)
- **Base Stats**: rush_att, rush_yds, targets, rec, rec_yds, scoring_tds
- **Derived**: touches, td_rate (TDs per touch), consecutive_td (streak)
- **Total Features**: ~30 rolling features + 7 context + 4 dynamic team + 1 streak = ~42 features
- **Team Features**: BOTH static ratings (v1) AND dynamic rolling (v2)
- **Opponent Features**: Same dual approach

## Calibration Comparison

### v1 Calibration
- **Method**: Platt Scaling (LogisticRegression)
- **Parameters**: C=10.0, solver='liblinear', max_iter=1000
- **Clip Range**: 0.01-0.99
- **Fallback**: Identity mapping if scaling fails

### v2 Calibration
- **Method**: None (raw probabilities)
- **Impact**: Probabilities may not be well-calibrated

### v3 Calibration
- **Method**: Isotonic Regression (more flexible than Platt)
- **Parameters**: Uses CalibratedClassifierCV with 'isotonic' method
- **Clip Range**: 0.01-0.99
- **Fallback**: Base model probabilities if calibration fails
- **Advantage**: Better handles non-linear probability distributions

## Training Strategy Comparison

### v1 Training
- **Split**: 80/20 random split (stratified)
- **Validation**: Single validation set
- **Early Stopping**: No

### v2 Training
- **Split**: All historical data (no explicit validation)
- **Validation**: None
- **Early Stopping**: No

### v3 Training
- **Split**: Time-series aware (respects temporal order)
- **Validation**: Per-season 80/20 splits, then combined
- **Early Stopping**: Yes (50 rounds)
- **Advantage**: Prevents data leakage from future to past

## Filtering Comparison

### v1 Filtering
- Usage threshold: <1.0 touches over last 3 games
- Position-specific season totals:
  - WR/TE: 2+ receptions
  - RB: 3+ rush attempts

### v2 Filtering
- Usage threshold: 2+ meaningful touches per game
- Active players: 10+ pass attempts OR 3+ targets OR 3+ rush attempts
- Requires: 1+ prior games

### v3 Filtering
- Usage threshold: <1.5 touches over last 3 games (slightly higher)
- Position-specific season totals:
  - WR: 3+ receptions (higher than v1)
  - TE: 2+ receptions (same as v1)
  - RB: 4+ rush attempts (higher than v1)
- **Rationale**: More conservative filtering to focus on truly active players

## Key Improvements in v3

1. **More Trees (500)**: Better learning capacity
2. **Deeper Trees (5)**: Can capture more complex patterns
3. **Lower Learning Rate (0.03)**: More conservative, prevents overfitting
4. **Regularization**: Both L1 and L2 with stronger L2
5. **Additional Features**: TD rate, consecutive TD streak, touches
6. **Dual Team Features**: Both static and dynamic team metrics
7. **Better Calibration**: Isotonic regression instead of Platt scaling
8. **Time-Series Aware**: Respects temporal order in training
9. **Early Stopping**: Prevents overfitting
10. **More Windows**: Adds 2-game window for recent trends

## Expected Performance

- **v1**: Good calibration, position-specific learning, but simpler features
- **v2**: Faster training, dynamic team features, but no calibration and unified model
- **v3**: Best of both worlds - position-specific, calibrated, richer features, better regularization
