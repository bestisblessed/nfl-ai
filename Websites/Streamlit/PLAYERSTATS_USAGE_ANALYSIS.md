# PlayerStats.csv Usage Analysis

## Pages That Load PlayerStats.csv

### 1. **Matchup Generator (00_⚔️_Matchup_Generator.py)** ✅ ACTUALLY USES IT
**Usage:** Lines 1805-1823 - Filters historical player stats vs opponents
- Uses columns: `player_display_name`, `home_team`, `away_team`, `player_current_team`, `position`, `receiving_yards`, `passing_yards`, `rushing_yards`, `receiving_tds`, `passing_tds`, `rushing_tds`, `fantasy_points_ppr`, `game_id`
- **Can be replaced with:** `all_passing_rushing_receiving.csv` (has 2010-2025)
- **Replacement notes:** Need to map column names and derive `home_team`/`away_team` from `home` boolean + `team` + `opponent_team`

### 2. **Home.py** ⚠️ MINOR USAGE
**Usage:** Line 375 - Added to `player_sources` list as fallback
- Only used as fallback for collecting player names
- Primary sources are `player_stats_pfr.csv` and `all_passing_rushing_receiving.csv`
- **Can be removed** - not critical

### 3. **Player Dashboard (05_🥇_Player_Dashboard.py)** ❌ NOT USED
**Usage:** Loaded but never referenced
- Page uses `all_passing_rushing_receiving.csv` (as `df_player_data`) instead
- **Can be removed**

### 4. **Player Trends (06_📈_Player_Trends.py)** ❌ NOT USED
**Usage:** Loaded but never referenced
- Page uses `all_passing_rushing_receiving.csv` (as `df_all_passing_rushing_receiving`) instead
- **Can be removed**

### 5. **Team Trends (07_📉_Team_Trends.py)** ❌ NOT USED
**Usage:** Added to `dataframes` list (line 84) but list is never used
- **Can be removed**

### 6. **Betting Trends (08_💰_Betting_Trends.py)** ❌ NOT USED
**Usage:** Loaded but never referenced
- Page only uses `Games.csv` for ATS/O/U analysis
- **Can be removed**

### 7. **Standings (12_💍_Standings.py)** ❌ NOT USED
**Usage:** Loaded but never referenced
- Page only uses `Games.csv` for standings calculation
- **Can be removed**

## Column Mapping for Replacement

### PlayerStats.csv → all_passing_rushing_receiving.csv

| PlayerStats.csv | all_passing_rushing_receiving.csv | Notes |
|----------------|-----------------------------------|-------|
| `player_display_name` | `player` | Direct mapping |
| `home_team` | Derived from `game_id` or `home` + `team` | Need to extract from game_id format: `YYYY_WW_AWAY_HOME` |
| `away_team` | Derived from `game_id` or `home` + `team` | Need to extract from game_id format: `YYYY_WW_AWAY_HOME` |
| `player_current_team` | `team` | Current team in that game |
| `position` | `position` | Direct mapping |
| `passing_yards` | `pass_yds` | Direct mapping |
| `rushing_yards` | `rush_yds` | Direct mapping |
| `receiving_yards` | `rec_yds` | Direct mapping |
| `passing_tds` | `pass_td` | Direct mapping |
| `rushing_tds` | `rush_td` | Direct mapping |
| `receiving_tds` | `rec_td` | Direct mapping |
| `fantasy_points_ppr` | **MISSING** | Need to calculate or add column |
| `game_id` | `game_id` | Direct mapping |
| `season` | `season` | Direct mapping (2010-2025!) |

## Recommendation

**Replace PlayerStats.csv with all_passing_rushing_receiving.csv** in Matchup Generator:
1. Only one page actually uses it (Matchup Generator)
2. `all_passing_rushing_receiving.csv` has full 2010-2025 coverage
3. Column mapping is straightforward
4. Need to:
   - Map column names
   - Derive `home_team`/`away_team` from `game_id` (format: `YYYY_WW_AWAY_HOME`)
   - Calculate `fantasy_points_ppr` if needed (or make it optional)
   - Use `team` as `player_current_team`

**Remove PlayerStats.csv from all other pages** - they don't use it.
