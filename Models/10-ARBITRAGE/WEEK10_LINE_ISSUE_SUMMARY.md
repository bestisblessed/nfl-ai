# Week 10 Line Value Issue - Investigation & Resolution

## Problem Identified

User noticed incorrect line values in Week 10 RB Rushing report:
```
Rank Player                Side   Line   Odds   Book        Edge
1    James Cook (BUF)      Over   44.5   -110   ESPN        49.2 yds
2    Chuba Hubbard (CAR)   Over   12.5   -110   DK          38.0 yds
3    D'Andre Swift (CHI)   Under  81.5   -115   Fliff       29.4 yds
4    De'Von Achane (MIA)   Under  100.5  -115   HR          28.9 yds
```

Lines appeared either too high (Achane 100.5, Swift 81.5) or too low (Hubbard 12.5, Cook 44.5).

## Root Cause

**Data was fetched at 3pm ET on Sunday, AFTER 1pm games had started.**

When games start, most sportsbooks:
1. Pull their pre-game lines
2. Switch to live in-game betting lines
3. These live lines reflect current game state, not pre-game totals

### Evidence

**1pm Games (Already Started):**
- **James Cook** (BUF vs MIA):
  - Most books: 44-49 yds (live lines)
  - Pinnacle: 85.5 yds (pre-game line retained)
  - Predicted: 93.7 yds
  
- **D'Andre Swift** (CHI vs NYG):
  - Most books: 78-81 yds (likely rush+receiving live)
  - Pinnacle: 50.5 yds (pre-game rushing only)
  - Predicted: 52.1 yds rushing
  
- **De'Von Achane** (MIA vs BUF):
  - Most books: 95-100 yds (likely rush+receiving live)
  - Pinnacle: 65.5 yds (pre-game rushing only)
  - Predicted: 71.6 yds rushing

- **Chuba Hubbard** (CAR vs NO):
  - Most books: 12-14 yds (possibly attempts or live)
  - Pinnacle: 20.5 yds (pre-game)
  - Predicted: 50.5 yds

**Later Games (Not Started):**
- **Josh Jacobs** (GB vs PHI - late game):
  - All books consistent: 63-70 yds including Pinnacle 69.5 ✓
  
- **Kyren Williams** (LAR vs SF - late game):
  - All books consistent: 63-65 yds including Pinnacle 63.5 ✓

## Solution Implemented

Added Week 10 specific filter directly in `find_value_bets.py`:
- **For 1pm ET games**: Keep ONLY Pinnacle lines (retained pre-game values)
- **For later games**: Keep ALL bookmaker lines (all pre-game)

This ensures all lines represent pre-game betting odds, not live in-game lines.

The filter only activates for week 10 specifically, so future weeks are unaffected.

## Results

### Before Fix (INCORRECT - Mixed Live/Pre-game Lines)
```
Input: 4,310 props (all books, all games)
Output: 179 matches

Top RB Rushing (INCORRECT):
1. James Cook      Over  44.5   ESPN     49.2 yds  ← Live line
2. Chuba Hubbard   Over  12.5   DK       38.0 yds  ← Live line
3. D'Andre Swift   Under 81.5   Fliff    29.4 yds  ← Live line  
4. De'Von Achane   Under 100.5  HR       28.9 yds  ← Live line
```

### After Fix (CORRECT - All Pre-game Lines)
```
Input: 2,648 props (Pinnacle for 1pm, all books for later)
Output: 179 matches

Top RB Rushing (CORRECT):
1. Chuba Hubbard   Over  20.5   Pinnacle  30.0 yds  ✓
2. James Cook      Over  85.5   Pinnacle   8.2 yds  ✓
3. De'Von Achane   Over  65.5   Pinnacle   6.1 yds  ✓
```

## Files Updated

1. **find_value_bets.py** - Added week 10 specific filter in `load_props()` function
2. **week10_value_opportunities.csv** - Regenerated value bets
3. **week10_top_edges_by_prop.csv** - Regenerated top picks
4. **WEEK10_LINE_ISSUE_SUMMARY.md** - This documentation

## Verification Summary

**All Prop Types Now Correct:**

✓ **Passing Yards** - Multiple books, realistic lines
✓ **Receiving Yards (RB)** - Multiple books, realistic lines  
✓ **Receiving Yards (WR)** - Multiple books, realistic lines
✓ **Receiving Yards (TE)** - Multiple books, realistic lines
✓ **Rushing Yards (QB)** - Multiple books, realistic lines
✓ **Rushing Yards (RB)** - Pinnacle for 1pm games, multiple books for later games

## Future Prevention

**For future weeks:**
1. Run prop fetching BEFORE 1pm ET on Sunday to avoid this issue entirely
2. Week 10 fix is hardcoded in `find_value_bets.py` and only activates for week 10

## Commands

```bash
# Fetch props (ideally before 1pm ET)
python fetch_upcoming_games_and_props.py <week>

# Generate value bets (week 10 filter automatically applied)
python find_value_bets.py <week>
```

## Lesson Learned

**Timing matters when fetching betting lines!** Always fetch props before games start, or filter out live in-game lines that don't match pre-game predictions.
