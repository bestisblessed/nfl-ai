# Touchdown Prediction Models - Complete Comparison & v3 Improvements

## Overview in Beginner Terms

These models predict whether NFL players will score touchdowns in upcoming games. They use historical player stats, team performance, and opponent data to calculate probability scores.

Think of it like this: The model looks at how often a player has gotten the ball recently, how many yards they gained, how good their team is at scoring, and how good the opposing defense is at preventing touchdowns. It then combines all this information to estimate "What's the chance this player scores a TD this week?"

---

## 4-TOUCHDOWNS (v1) - The Position-Specific Approach

### How It Works
V1 trains **4 separate models** (one for each position: QB, RB, WR, TE). Each position gets its own specialized model because QBs score differently than RBs, etc. It uses a technique called "Platt Scaling" to make sure the probabilities are well-calibrated (not overconfident or underconfident).

### Key Features (What the model looks at):

**Rolling Window Stats** - Looks at multiple time windows (3, 5, 8, 12 games) to understand both recent form and longer trends:
- `rush_att_rm3/rm5/rm8/rm12` - How many rushing attempts in last 3/5/8/12 games
- `rush_yds_rm3/rm5/rm8/rm12` - Rushing yards in those windows
- `targets_rm3/rm5/rm8/rm12` - How many times targeted for passes
- `rec_rm3/rm5/rm8/rm12` - Receptions (catches)
- `rec_yds_rm3/rm5/rm8/rm12` - Receiving yards
- `scoring_tds_rm3/rm5/rm8/rm12` - Total TDs scored in those windows

**Team Context Features:**
- `Offense` - Team's offensive rating (how good they are at offense overall)
- `Defense` - Team's defensive rating
- `opp_offense` - Opponent's offensive rating
- `opp_defense` - Opponent's defensive rating
- `rz_td_pct` - Red zone TD percentage (how often team scores TDs when close to goal)
- `rz_att_pg` - Red zone attempts per game

**Situational Features:**
- `home_flag` - Is the player playing at home? (1=yes, 0=no)
- `opp_td_rate_pos` - How often opponent allows TDs to this position
- `opp_td_rate_qb_rush` - How often opponent allows rushing TDs to QBs

### XGBoost Model Parameters (v1):

| Parameter | Value | What It Does | Why This Value |
|-----------|-------|--------------|----------------|
| `objective` | "binary:logistic" | Tells model this is yes/no prediction (TD or no TD) | Standard for binary classification |
| `n_estimators` | 400 | Number of decision trees to build | More trees = more learning, but 400 is balanced |
| `max_depth` | 4 | How deep each decision tree can go | Shallow trees prevent overfitting (learning noise) |
| `learning_rate` | 0.05 | How much each tree contributes to final answer | Small value = slower but more stable learning |
| `subsample` | 0.9 | Uses 90% of data for each tree | Adds randomness to prevent overfitting |
| `colsample_bytree` | 0.9 | Uses 90% of features for each tree | More randomness for robustness |
| `reg_alpha` | 0.0 | L1 regularization (penalty for complexity) | No penalty here |
| `reg_lambda` | 1.0 | L2 regularization | Small penalty to prevent overfitting |
| `eval_metric` | "logloss" | How to measure model quality | Standard for probability predictions |

### Calibration (Platt Scaling):

| Parameter | Value | What It Does |
|-----------|-------|--------------|
| `max_iter` | 1000 | Maximum iterations for calibration | Ensures convergence |
| `C` | 10.0 | Regularization strength | Moderate regularization |
| `solver` | 'liblinear' | Algorithm for logistic regression | More stable for small datasets |

### Player Filtering:
- Must have at least 1 touch (rush attempt/target) in last 3 games
- Position-specific season minimums:
  - WRs: 2+ receptions
  - TEs: 2+ receptions  
  - RBs: 3+ rush attempts
- Removes injured/questionable players

---

## 4-TOUCHDOWNS-v2 - The Unified Team-Context Approach

### How It Works
V2 trains **1 single model** for all positions together. It focuses heavily on team-level offensive/defensive metrics and uses simpler rolling windows. No Platt scaling - relies on XGBoost's built-in probability calibration.

### Key Features (What the model looks at):

**Player Rolling Stats** (3-game window only):
- `rush_att_rolling` - Recent rushing attempts
- `rush_yds_rolling` - Recent rushing yards
- `rush_long_rolling` - Longest recent rush
- `targets_rolling` - Recent targets
- `rec_rolling` - Recent receptions
- `rec_yds_rolling` - Recent receiving yards
- `rec_long_rolling` - Longest recent reception
- `fantasy_points_ppr_rolling` - Recent fantasy points (PPR scoring)
- `touches_rolling` - Total touches (rushes + targets + receptions)
- `total_tds_rolling` - Recent TDs scored

**Season Average Stats:**
- `total_tds_season_avg` - Expanding average of TDs this season

**Team Features:**
- `team_td_scored_feature` - Team's recent TD production (rolling 3 games)
- `team_td_allowed_feature` - TDs team has allowed on defense
- `team_pts_scored_feature` - Team's recent point production
- `team_pts_allowed_feature` - Points allowed
- `team_games_played_prior` - How many games team has played

**Opponent Features:**
- `opp_td_scored_feature` - Opponent's TD production
- `opp_td_allowed_feature` - TDs opponent allows
- `opp_pts_scored_feature` - Opponent's scoring
- `opp_pts_allowed_feature` - Opponent's points allowed

**Situational:**
- `is_home` - Playing at home?
- `games_played_prior` - Player's games played this season

### XGBoost Model Parameters (v2):

| Parameter | Value | What It Does | Why This Value |
|-----------|-------|--------------|----------------|
| `n_estimators` | 150 | Number of decision trees | Fewer trees than v1 (faster training) |
| `learning_rate` | 0.1 | Contribution of each tree | 2x faster learning than v1 |
| `max_depth` | 4 | Tree depth | Same as v1 |
| `subsample` | 0.8 | Data sampling per tree | Slightly more aggressive sampling |
| `colsample_bytree` | 0.8 | Feature sampling per tree | More aggressive than v1 |
| `objective` | "binary:logistic" | Binary classification | Same as v1 |
| `eval_metric` | "logloss" | Quality metric | Same as v1 |
| `n_jobs` | 4 | CPU cores to use | Parallel processing for speed |
| `scale_pos_weight` | calculated | Handles class imbalance | Auto-adjusts for rare TDs |

### Player Filtering:
- Must have 2+ meaningful touches per game historically
- Must be active in target season:
  - 10+ pass attempts (QBs) OR
  - 3+ targets (pass catchers) OR
  - 3+ rush attempts (runners)

---

## KEY DIFFERENCES Between v1 and v2

| Aspect | v1 (4-TOUCHDOWNS) | v2 (4-TOUCHDOWNS-v2) |
|--------|-------------------|----------------------|
| **Model Architecture** | 4 separate position-specific models | 1 unified model for all positions |
| **Rolling Windows** | Multiple (3, 5, 8, 12 games) | Single (3 games only) |
| **Calibration** | Platt Scaling with logistic regression | XGBoost native + scale_pos_weight |
| **Trees** | 400 trees, lr=0.05 (slow/stable) | 150 trees, lr=0.1 (fast) |
| **Team Features** | Offense/Defense ratings, red zone stats | Rolling TD/points scored/allowed |
| **Complexity** | High - more features, calibration | Lower - fewer features, simpler |
| **Training Time** | Slower (4 models × 400 trees each) | Faster (1 model × 150 trees) |
| **Opponent TD Rate** | Position-specific opponent TD rates | Generic team TD allowed metrics |
| **Season Context** | No expanding averages | Includes season-to-date averages |

### Strengths of v1:
- Position-specific models can learn nuances (QB TDs very different from WR TDs)
- Multiple time windows capture both recent form and longer trends
- Platt scaling ensures probabilities are well-calibrated
- More sophisticated opponent matchup analysis

### Weaknesses of v1:
- Slower to train (4 models)
- Platt scaling can fail on small datasets
- More complex = harder to maintain
- Might overfit with so many features

### Strengths of v2:
- Faster training (1 model)
- Team-level context is rich and informative
- Season averages provide good baseline
- Simpler = more robust
- scale_pos_weight handles imbalance well

### Weaknesses of v2:
- Only 3-game window might miss longer trends
- One model for all positions might not capture position differences
- No dedicated red zone stats
- Less sophisticated opponent analysis

---

## Why You Might Be Unhappy with Current Results

**Possible Issues:**

1. **Calibration Problems** - Probabilities might be too high or too low across the board
2. **Recency Bias** - 3-game windows might overreact to recent performance
3. **Missing Context** - Neither captures game flow, weather, injuries well
4. **Class Imbalance** - TDs are rare events (maybe 5-10% of player-games)
5. **Position Differences** - v2 treating all positions same might hurt accuracy
6. **Lack of Advanced Stats** - No snap counts, target share, red zone touches

---

## v3 IMPROVEMENT STRATEGY

The v3 model will combine the best of both approaches:

1. **Hybrid Architecture**: Train position-specific models BUT with unified team features
2. **Multi-Window Features**: Use 3, 5, 8 game windows (not 12 - too far back)
3. **Better Calibration**: Use XGBoost's scale_pos_weight + post-hoc isotonic calibration
4. **Enhanced Features**:
   - Target share (% of team's targets)
   - Snap count percentage when available
   - Red zone touches specifically
   - Recent TD trend (TDs in last 3 vs previous 3)
5. **Improved Model Tuning**:
   - More trees (250) with moderate learning rate (0.075)
   - Cross-validation for hyperparameter selection
   - Early stopping to prevent overfitting
6. **Better Filtering**:
   - Remove players with <3 games played this season
   - Weight recent games more heavily
   - Separate handling for goal-line backs vs featured backs

Coming up: Full v3 implementation!
