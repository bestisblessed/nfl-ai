# Rushing Props API Data Issue

## Problem Discovered
Week 10 analysis revealed that most sportsbooks in the-odds-api.com are **mislabeling Rush+Receiving combined props as "player_rush_yds"**.

## Evidence

### De'Von Achane (MIA)
- **Predicted Rushing**: 71.64 yards
- **Predicted Receiving**: 22.41 yards
- **Combined**: ~94 yards
- **API Lines**:
  - Most books (DraftKings, ESPN, FanDuel, etc.): 95.5-100.5 yards ← **Rush+Rec combined!**
  - Pinnacle: 65.5 yards ← Actual rushing only ✓

### D'Andre Swift (CHI)
- **Predicted Rushing**: 52.06 yards
- **Predicted Receiving**: 31.74 yards
- **Combined**: ~83.8 yards
- **API Lines**:
  - Most books: 78.5-81.5 yards ← **Rush+Rec combined!**
  - Pinnacle: 50.5 yards ← Actual rushing only ✓

### James Cook (BUF)
- **Predicted Rushing**: 93.73 yards
- **API Lines**:
  - Most books: 44.5-49.5 yards ← Actual rushing ✓
  - Pinnacle: 85.5 yards ← Actual rushing ✓

## Solution Implemented

**Filter rushing props to only use Pinnacle's data**, as they are the only book consistently providing accurate rushing-only lines.

### Files Modified:
1. `fix_rushing_props.py` - Script to filter mislabeled rushing props
2. `find_value_bets.py` - Updated to use fixed props file

### Results:
- **Before**: 4,310 total props
- **After**: 3,193 total props  
- **Filtered**: 1,117 mislabeled rushing props

## Impact on Week 10 Report

### Before Fix (INCORRECT):
```
Rank Player                Side   Line   Odds   Book        Edge
1    James Cook (BUF)      Over   44.5   -110   ESPN        49.2 yds
2    Chuba Hubbard (CAR)   Over   12.5   -110   DK          38.0 yds
3    D'Andre Swift (CHI)   Under  81.5   -115   Fliff       29.4 yds
4    De'Von Achane (MIA)   Under  100.5  -115   Hard Rock   28.9 yds
```

### After Fix (CORRECT):
```
Rank Player                Side   Line   Odds   Book      Edge
1    Chuba Hubbard (CAR)   Over   20.5   -128   Pinnacle  30.0 yds
2    James Cook (BUF)      Over   85.5   +109   Pinnacle   8.2 yds
3    De'Von Achane (MIA)   Over   65.5   -111   Pinnacle   6.1 yds
```

## Status of Other Prop Types
- ✓ **Passing Yards**: Multiple books, data looks correct
- ✓ **Receiving Yards**: Multiple books, data looks correct
- ⚠️ **Rushing Yards**: **Only Pinnacle data used** due to API mislabeling

## Recommendations
1. Always use the fixed props file for rushing yards analysis
2. Consider contacting the-odds-api.com about this data quality issue
3. Monitor future weeks for similar issues
4. Consider adding validation checks for all prop types
