# Touchdown Prediction Models: v1, v2, and v3 Explained

## Overview
Both models predict the probability that a player will score a touchdown in an upcoming game. They use machine learning (XGBoost) to learn patterns from historical NFL data.

---

## Model v1 (4-TOUCHDOWNS) - Detailed Explanation

### How It Works (Beginner Terms)
1. **Data Preparation**: Takes historical player stats (rushing attempts, receiving yards, touchdowns, etc.) and creates "rolling averages" - like looking at a player's last 3, 5, 8, or 12 games to see their recent performance.

2. **Feature Engineering**: Creates features like:
   - Rolling averages of rushing attempts, receiving yards, touchdowns over different time windows
   - Team offensive/defensive ratings
   - Opponent's historical tendency to allow touchdowns
   - Red zone statistics (how often teams score when close to the end zone)
   - Home/away flag

3. **Training**: Trains separate models for each position (WR, RB, TE, QB):
   - WR/RB/TE: Predicts "anytime TD" (rushing OR receiving)
   - QB: Predicts rushing TD only
   - Uses XGBoost classifier (a type of decision tree ensemble)
   - Applies "Platt scaling" to calibrate probabilities (makes predictions more accurate)

4. **Filtering**: Removes players with low usage (bench players) before making predictions

### Model Parameters (v1)

**XGBoost Parameters:**
- `objective="binary:logistic"` - Binary classification (TD or no TD)
- `eval_metric="logloss"` - Uses log loss to evaluate model quality
- `n_estimators=400` - Uses 400 decision trees
- `max_depth=4` - Each tree can be 4 levels deep (prevents overfitting)
- `learning_rate=0.05` - Small learning rate (more conservative, requires more trees)
- `subsample=0.9` - Uses 90% of training data for each tree (reduces overfitting)
- `colsample_bytree=0.9` - Uses 90% of features for each tree
- `random_state=42` - For reproducibility
- `reg_alpha=0.0` - L1 regularization (not used)
- `reg_lambda=1.0` - L2 regularization (prevents overfitting)

**Calibration (Platt Scaling):**
- Uses LogisticRegression with `C=10.0` (moderate regularization)
- `solver='liblinear'` - Fast solver for small datasets
- `max_iter=1000` - Maximum iterations
- Clips probabilities to 0.01-0.99 range for stability

**Features Used:**
- Rolling windows: 3, 5, 8, 12 games
- Base stats: rush_att, rush_yds, targets, rec, rec_yds, scoring_tds
- Context: home_flag, Offense, Defense, opp_offense, opp_defense, rz_td_pct, rz_att_pg, opp_td_rate_pos/opp_td_rate_qb_rush

**Training:**
- 80/20 train/validation split
- Stratified split (maintains class balance)

**Filtering:**
- Removes players with <1.0 average touches over last 3 games
- Position-specific season totals: WR/TE need 2+ receptions, RB needs 3+ rush attempts

---

## Model v2 (4-TOUCHDOWNS-v2) - Detailed Explanation

### How It Works (Beginner Terms)
1. **Data Preparation**: Similar to v1 but uses a different approach:
   - Creates "placeholder" rows for upcoming games
   - Computes rolling team features (TDs scored/allowed, points scored/allowed)
   - Uses expanding season averages as fallback

2. **Feature Engineering**: 
   - Rolling averages over 3-game window (single window, not multiple)
   - Season averages (expanding window)
   - Team-level features (TDs scored/allowed, points scored/allowed)
   - Opponent team features
   - Games played prior count
   - Home/away flag

3. **Training**: 
   - Single model for all positions (not separate per position)
   - Uses class imbalance handling (`scale_pos_weight`)
   - No Platt scaling calibration

4. **Filtering**: 
   - Requires 2+ meaningful touches per game
   - Filters to active 2025 players (10+ pass attempts OR 3+ targets OR 3+ rush attempts)
   - Requires at least 1 prior game

### Model Parameters (v2)

**XGBoost Parameters:**
- `objective="binary:logistic"` - Binary classification
- `eval_metric="logloss"` - Log loss evaluation
- `n_estimators=150` - Only 150 trees (fewer than v1)
- `learning_rate=0.1` - Higher learning rate (faster learning, less conservative)
- `max_depth=4` - Same depth as v1
- `subsample=0.8` - Uses 80% of data (more aggressive than v1)
- `colsample_bytree=0.8` - Uses 80% of features
- `n_jobs=4` - Uses 4 CPU cores
- `scale_pos_weight` - Automatically calculated to handle class imbalance (negative examples / positive examples)

**No Calibration**: Raw probabilities from XGBoost are used directly

**Features Used:**
- Rolling window: 3 games only (single window)
- Base stats: rush_att, rush_yds, rush_long, targets, rec, rec_yds, rec_long, fantasy_points_ppr
- Derived: touches, total_tds
- Team features: td_scored_feature, td_allowed_feature, pts_scored_feature, pts_allowed_feature (for both team and opponent)
- Context: games_played_prior, is_home

**Training:**
- Trains on all historical data before the upcoming week
- No explicit validation split (uses all data for training)

**Filtering:**
- Requires 2+ meaningful touches per game
- Active players only (season totals)
- Requires 1+ prior games

---

## Key Differences Between v1 and v2

### 1. **Position-Specific vs. Unified Model**
- **v1**: Separate models for WR, RB, TE, QB (4 models total)
- **v2**: Single unified model for all positions
- **Impact**: v1 can learn position-specific patterns better, but v2 is simpler

### 2. **Feature Windows**
- **v1**: Multiple rolling windows (3, 5, 8, 12 games) - 24 rolling features
- **v2**: Single rolling window (3 games) + season averages - fewer features
- **Impact**: v1 captures more temporal patterns, v2 is simpler

### 3. **Calibration**
- **v1**: Uses Platt scaling to calibrate probabilities
- **v2**: No calibration, uses raw XGBoost probabilities
- **Impact**: v1 probabilities should be more calibrated (better match actual frequencies)

### 4. **Model Complexity**
- **v1**: 400 trees, learning_rate=0.05 (more conservative, deeper)
- **v2**: 150 trees, learning_rate=0.1 (faster, simpler)
- **Impact**: v1 might overfit less, v2 trains faster

### 5. **Team Features**
- **v1**: Uses pre-computed team ratings (Offense, Defense) and red zone stats
- **v2**: Computes rolling team TD/points features dynamically
- **Impact**: v2 team features are more recent/game-specific

### 6. **Class Imbalance Handling**
- **v1**: Relies on stratified train/test split
- **v2**: Uses `scale_pos_weight` to handle imbalance
- **Impact**: v2 explicitly handles the fact that TDs are rare events

### 7. **Data Structure**
- **v1**: Pre-processes data into model_train.csv with all features ready
- **v2**: Computes features on-the-fly with placeholder rows
- **Impact**: v1 is more explicit, v2 is more flexible

---

## Model v3 - Improvements

### Design Philosophy
Combine the best aspects of both models while addressing their weaknesses:

1. **Position-Specific Models** (from v1) - Different positions have different TD patterns
2. **Multiple Rolling Windows** (from v1) - Capture short-term and long-term trends
3. **Calibration** (from v1) - Important for accurate probability estimates
4. **Better Team Features** (from v2) - More dynamic, game-specific
5. **Class Imbalance Handling** (from v2) - Explicit handling of rare events
6. **More Features** - Add additional predictive signals
7. **Better Filtering** - More sophisticated player filtering

### v3 Improvements

**Model Architecture:**
- Position-specific models (like v1) for better specialization
- Increased model complexity: 500 trees, learning_rate=0.03 (more conservative than v1)
- Both Platt scaling AND class imbalance handling

**Features:**
- Multiple rolling windows: 2, 3, 5, 8, 12 games (adds 2-game window for recent trends)
- Team features: Both static ratings (v1) AND dynamic rolling features (v2)
- Additional features:
  - Touchdown rate (TDs per touch)
  - Target share (targets relative to team)
  - Red zone target rate
  - Recent TD streak (consecutive games with TD)
  - Opponent strength vs position

**Calibration:**
- Platt scaling with isotonic regression fallback
- Cross-validation for better calibration

**Filtering:**
- More sophisticated usage filters
- Position-specific thresholds
- Recent form consideration

**Training:**
- Time-series cross-validation (respects temporal order)
- Early stopping to prevent overfitting
- Feature importance analysis
