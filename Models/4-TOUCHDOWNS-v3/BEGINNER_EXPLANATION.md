# Touchdown Prediction Models - Beginner's Guide

## What Do These Models Do?

These models predict the probability that an NFL player will score a touchdown in an upcoming game. They use machine learning to learn from historical data.

---

## Model v1 (4-TOUCHDOWNS) - Simple Explanation

### The Big Picture
Think of v1 like a scout who watches players over different time periods:
- "How did this player do in their last 3 games?"
- "How about their last 5 games?"
- "What about their last 8 or 12 games?"

### How It Works
1. **Looks at Player History**: Creates averages over 3, 5, 8, and 12 game windows
2. **Separate Models**: Trains different models for WR, RB, TE, and QB (because they score differently)
3. **Team Context**: Considers how good the player's team is and how bad the opponent's defense is
4. **Calibration**: Adjusts probabilities to be more accurate (like tuning a scale)

### Key Settings
- **400 decision trees** - Like asking 400 different scouts for their opinion
- **Learning rate 0.05** - Very careful, conservative learning
- **4 levels deep** - Each tree can ask 4 questions before making a decision
- **Platt scaling** - Adjusts probabilities to match reality better

### Strengths
- ✅ Separate models learn position-specific patterns
- ✅ Multiple time windows capture different trends
- ✅ Calibrated probabilities are more accurate

### Weaknesses
- ❌ Uses static team ratings (doesn't change much)
- ❌ No explicit handling of rare events (TDs are uncommon)
- ❌ Simpler features

---

## Model v2 (4-TOUCHDOWNS-v2) - Simple Explanation

### The Big Picture
v2 is like a scout who focuses on recent performance and team dynamics:
- "How has this player done in the last 3 games?"
- "How many touchdowns has their team scored recently?"
- "How many touchdowns has the opponent allowed recently?"

### How It Works
1. **Single Window**: Only looks at last 3 games (simpler than v1)
2. **One Model**: Uses the same model for all positions (simpler)
3. **Dynamic Team Stats**: Calculates team performance on-the-fly
4. **Class Imbalance**: Explicitly handles that TDs are rare events

### Key Settings
- **150 decision trees** - Fewer scouts, but faster
- **Learning rate 0.1** - Learns faster (less careful)
- **4 levels deep** - Same depth as v1
- **No calibration** - Uses raw probabilities

### Strengths
- ✅ Dynamic team features (changes with recent games)
- ✅ Handles class imbalance (TDs are rare)
- ✅ Faster to train
- ✅ Simpler approach

### Weaknesses
- ❌ Single model for all positions (can't specialize)
- ❌ Only 3-game window (misses longer trends)
- ❌ No calibration (probabilities may be off)
- ❌ Fewer features overall

---

## Model v3 (4-TOUCHDOWNS-v3) - The Best of Both Worlds

### The Big Picture
v3 combines the best ideas from v1 and v2, plus adds new improvements:
- Uses multiple time windows (like v1) PLUS dynamic team stats (like v2)
- Separate models per position (like v1) PLUS better calibration
- More features and smarter learning

### How It Works
1. **Multiple Windows**: Looks at 2, 3, 5, 8, and 12 game averages
2. **Position-Specific**: Separate models for each position (like v1)
3. **Dual Team Features**: Uses BOTH static ratings AND dynamic recent stats
4. **Better Calibration**: Uses isotonic regression (more flexible than v1)
5. **Smarter Learning**: More trees, deeper trees, but slower learning rate
6. **New Features**: 
   - TD rate (touchdowns per touch)
   - Consecutive TD streak
   - Total touches

### Key Settings
- **500 decision trees** - More opinions than v1
- **Learning rate 0.03** - Most careful learning (prevents mistakes)
- **5 levels deep** - Can ask more questions (deeper than v1/v2)
- **Isotonic calibration** - Better probability adjustment
- **Early stopping** - Stops learning when it's not improving

### Improvements Over v1 and v2

**From v1:**
- ✅ Keeps position-specific models
- ✅ Keeps multiple time windows
- ✅ Keeps calibration (but improved)
- ✅ Adds dynamic team features
- ✅ Adds class imbalance handling
- ✅ More trees, deeper trees

**From v2:**
- ✅ Keeps dynamic team features
- ✅ Keeps class imbalance handling
- ✅ Adds position-specific models
- ✅ Adds multiple time windows
- ✅ Adds calibration
- ✅ More sophisticated features

**New in v3:**
- ✅ TD rate feature (efficiency metric)
- ✅ Consecutive TD streak (momentum)
- ✅ 2-game window (very recent trends)
- ✅ Time-series aware training (respects game order)
- ✅ Early stopping (prevents overfitting)
- ✅ Better regularization (prevents overfitting)

---

## What Each Parameter Does

### n_estimators (Number of Trees)
- **What it is**: How many decision trees the model uses
- **v1**: 400 trees
- **v2**: 150 trees
- **v3**: 500 trees
- **More trees** = More opinions, but slower and can overfit

### learning_rate
- **What it is**: How quickly the model learns from mistakes
- **v1**: 0.05 (careful)
- **v2**: 0.1 (faster)
- **v3**: 0.03 (most careful)
- **Lower rate** = More careful, needs more trees, less likely to overfit

### max_depth
- **What it is**: How many questions each tree can ask
- **v1**: 4 levels
- **v2**: 4 levels
- **v3**: 5 levels
- **Deeper** = Can learn more complex patterns, but can overfit

### subsample
- **What it is**: What percentage of training data each tree sees
- **v1**: 90%
- **v2**: 80%
- **v3**: 85%
- **Lower** = More randomness, prevents overfitting

### colsample_bytree
- **What it is**: What percentage of features each tree can use
- **v1**: 90%
- **v2**: 80%
- **v3**: 85%
- **Lower** = More randomness, prevents overfitting

### scale_pos_weight
- **What it is**: How much to weight positive examples (TDs) vs negative (no TD)
- **v1**: Not used
- **v2**: Auto-calculated
- **v3**: Auto-calculated
- **Why**: TDs are rare, so we need to tell the model they're important

### Calibration
- **What it is**: Adjusting probabilities to match reality
- **v1**: Platt scaling (linear adjustment)
- **v2**: None (raw probabilities)
- **v3**: Isotonic regression (non-linear adjustment)
- **Why**: Raw probabilities might say "50% chance" when it's really 30%

---

## Feature Comparison

### Rolling Windows
- **v1**: 3, 5, 8, 12 games (4 windows)
- **v2**: 3 games only (1 window)
- **v3**: 2, 3, 5, 8, 12 games (5 windows)
- **Why multiple windows**: Short-term trends (2-3 games) vs long-term trends (8-12 games)

### Base Statistics
- **v1**: rush_att, rush_yds, targets, rec, rec_yds, scoring_tds
- **v2**: rush_att, rush_yds, rush_long, targets, rec, rec_yds, rec_long, fantasy_points_ppr
- **v3**: rush_att, rush_yds, targets, rec, rec_yds, scoring_tds + touches, td_rate, consecutive_td
- **v3 adds**: Efficiency metrics (TD rate) and momentum (streak)

### Team Features
- **v1**: Static ratings (Offense, Defense) + red zone stats
- **v2**: Dynamic rolling TD/points scored/allowed (3-game window)
- **v3**: BOTH static ratings AND dynamic rolling stats
- **v3 advantage**: Captures both overall team strength and recent form

---

## Why v3 Should Be Better

1. **More Information**: More features, more time windows, more context
2. **Smarter Learning**: More trees, deeper trees, but careful learning rate
3. **Better Calibration**: Isotonic regression adjusts probabilities better
4. **Position Specialization**: Separate models learn position-specific patterns
5. **Prevents Overfitting**: Early stopping, regularization, time-series aware training
6. **Handles Rare Events**: Explicit class imbalance handling
7. **Dual Team Context**: Both overall strength and recent form

---

## Expected Results

- **v1**: Good calibrated probabilities, position-specific, but simpler features
- **v2**: Fast, dynamic team features, but no calibration and unified model
- **v3**: Best of both - calibrated, position-specific, rich features, better learning

The main improvement in v3 is combining the strengths of both approaches while adding new features and better learning strategies.
