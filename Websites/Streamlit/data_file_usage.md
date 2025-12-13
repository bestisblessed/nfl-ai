# Streamlit Pages Data File Usage

## 1. Home.py
# 2010-2025
- data/all_team_game_logs.csv (2020-2025) ⚠️ MISSING 2010-2019
- data/SR-game-logs/all_teams_game_logs_2024.csv (2024)
- data/SR-game-logs/all_teams_game_logs_2025.csv (2025)
- data/odds/nfl_odds_movements.csv
- data/odds/nfl_odds_movements_circa.csv
- data/Teams.csv
- data/Games.csv (2010-2025)
- data/PlayerStats.csv (2010-2024) ⚠️ MISSING 2025
- data/all_teams_schedule_and_game_results_merged.csv (2010-2025)
- data/all_passing_rushing_receiving.csv (2020-2025) ⚠️ MISSING 2010-2019
- data/player_stats_pfr.csv (2010-2025)
- data/rosters/*.csv (2010-2025)

## 2. Matchup Generator (00_⚔️_Matchup_Generator.py)
# 2010-2025
- data/Games.csv (2010-2025)
- data/PlayerStats.csv (2010-2024) ⚠️ MISSING 2025
- data/rosters/roster_2025.csv (2025)
- data/all_team_game_logs.csv (2020-2025) ⚠️ MISSING 2010-2019
- data/all_defense-game-logs.csv (2020-2025) ⚠️ MISSING 2010-2019
- data/all_redzone.csv (2010-2025)

## 3. Weekly Projections (01_🔮_Weekly_Projections.py)
# 2025
- data/projections/week*_all_props_summary.csv
- data/Games.csv (2010-2025)
- upcoming_games.csv
- data/projections/week*_complete_props_report.txt (optional)
- data/projections/week*_complete_props_report.html (optional)
- data/odds/nfl_odds_*.json

## 4. Weekly Leaders (02_📋_Weekly_Leaders.py)
# 2025
- data/projections/week*_all_props_summary.csv
- data/projections/week*_leader_tables.pdf

## 5. Value Plays (03_💎_Value_Plays.py)
# 2025
- data/projections/week*_value_opportunities.csv
- data/projections/week*_top_edges_by_prop.csv
- data/Games.csv (2010-2025)
- upcoming_games.csv
- data/projections/week*_complete_props_report.txt (optional)
- data/projections/week*_complete_props_report.html (optional)
- data/projections/week*_value_complete_props_report.html
- data/projections/week*_value_leader_tables.pdf
- data/odds/nfl_odds_*.json

## 6. Odds Dashboard (04_📈_Odds_Dashboard.py)
# Current/upcoming games (no season filter - shows recent and upcoming games)
- data/odds/nfl_odds_movements.csv
- data/odds/nfl_odds_movements_circa.csv
- upcoming_games.csv
- data/odds/nfl_odds_*.json

## 7. Player Dashboard (05_🥇_Player_Dashboard.py)
# 2010-2025
- data/Teams.csv
- data/Games.csv (2010-2025)
- data/PlayerStats.csv (2010-2024) ⚠️ MISSING 2025
- data/all_team_game_logs.csv (2020-2025) ⚠️ MISSING 2010-2019
- data/all_teams_schedule_and_game_results_merged.csv (2010-2025)
- data/all_passing_rushing_receiving.csv (2020-2025) ⚠️ MISSING 2010-2019
- data/Rosters.csv (2010-2025)

**Note:** Page uses `all_passing_rushing_receiving.csv` as primary data source, which only has 2020-2025. For full 2010-2025 support, this file needs 2010-2019 data.

## 8. Player Trends (06_📈_Player_Trends.py)
# 2010-2025
- data/Teams.csv
- data/Games.csv (2010-2025)
- data/PlayerStats.csv (2010-2024) ⚠️ MISSING 2025
- data/all_team_game_logs.csv (2020-2025) ⚠️ MISSING 2010-2019
- data/all_teams_schedule_and_game_results_merged.csv (2010-2025)
- data/all_passing_rushing_receiving.csv (2020-2025) ⚠️ MISSING 2010-2019

**Note:** Page uses `all_passing_rushing_receiving.csv` as primary data source, which only has 2020-2025. For full 2010-2025 support, this file needs 2010-2019 data.

## 9. Team Trends (07_📉_Team_Trends.py)
# 2010-2025
- data/Teams.csv
- data/Games.csv (2010-2025)
- data/PlayerStats.csv (2010-2024) ⚠️ MISSING 2025
- data/all_team_game_logs.csv (2020-2025) ⚠️ MISSING 2010-2019
- data/all_teams_schedule_and_game_results_merged.csv (2010-2025)
- data/all_box_scores.csv (2020-2025) ⚠️ MISSING 2010-2019
- data/SR-game-logs/all_teams_game_logs_2024.csv (2024)
- data/SR-game-logs/all_teams_game_logs_2025.csv (2025)

**Note:** Page uses `all_box_scores.csv` for 1H/2H analysis, which only has 2020-2025. For full 2010-2025 support, this file needs 2010-2019 data. Also uses year-specific SR-game-logs files for 2024-2025 only.

## 10. Betting Trends (08_💰_Betting_Trends.py)
# 2010-2025
- data/Teams.csv
- data/Games.csv (2010-2025)
- data/PlayerStats.csv (2010-2024) ⚠️ MISSING 2025

**Note:** Page only uses Games.csv for ATS/O/U analysis, which has full 2010-2025 coverage. PlayerStats.csv is loaded but not used for season filtering.

## 11. Scoring Trends (09_📊_Scoring_Trends.py)
# 2010-2025
- data/player_stats_pfr.csv (2010-2025)
- data/rosters/roster_2025.csv (2025)

**Note:** Page uses `player_stats_pfr.csv` which has full 2010-2025 coverage. The roster_2025.csv is only used for position lookup, not season filtering.

## 12. AI Chatbot (10_🤖_AI_Chatbot.py)
# 2010-2025
- data/player_stats_pfr.csv (2010-2025)
- data/all_team_game_logs.csv (2020-2025) ⚠️ MISSING 2010-2019
- data/Rosters.csv (2010-2025)

**Note:** Page uses `all_team_game_logs.csv` which only has 2020-2025. For full 2010-2025 support, this file needs 2010-2019 data.

## 13. Standings (12_💍_Standings.py)
# 2010-2025
- data/Teams.csv
- data/Games.csv (2010-2025)
- data/PlayerStats.csv (2010-2024) ⚠️ MISSING 2025

**Note:** Page only uses Games.csv for standings calculation, which has full 2010-2025 coverage. PlayerStats.csv is loaded but not used for season filtering.

---

## Summary of Files Missing Years for 2010-2025 Standardization

### Critical Files Missing Years:
1. **data/PlayerStats.csv**: Missing 2025 (has 2010-2024)
2. **data/all_team_game_logs.csv**: Missing 2010-2019 (has 2020-2025)
3. **data/all_passing_rushing_receiving.csv**: Missing 2010-2019 (has 2020-2025)
4. **data/all_box_scores.csv**: Missing 2010-2019 (has 2020-2025)
5. **data/all_defense-game-logs.csv**: Missing 2010-2019 (has 2020-2025)

### Pages That Would Benefit from Full 2010-2025 Coverage:
- **Player Dashboard**: Uses `all_passing_rushing_receiving.csv` (primary source) - needs 2010-2019
- **Player Trends**: Uses `all_passing_rushing_receiving.csv` (primary source) - needs 2010-2019
- **Team Trends**: Uses `all_box_scores.csv` for 1H/2H analysis - needs 2010-2019
- **AI Chatbot**: Uses `all_team_game_logs.csv` - needs 2010-2019
- **Matchup Generator**: Uses `all_team_game_logs.csv` and `all_defense-game-logs.csv` - needs 2010-2019

### Pages Already Supporting 2010-2025:
- **Betting Trends**: Only uses Games.csv (has full coverage)
- **Standings**: Only uses Games.csv (has full coverage)
- **Scoring Trends**: Uses player_stats_pfr.csv (has full coverage)
