# Streamlit Pages Data File Usage

## 1. Home.py
# 2010-2025
- data/all_team_game_logs.csv (2020-2025)
- data/SR-game-logs/all_teams_game_logs_2024.csv (2024)
- data/SR-game-logs/all_teams_game_logs_2025.csv (2025)
- data/odds/nfl_odds_movements.csv
- data/odds/nfl_odds_movements_circa.csv
- data/Teams.csv
- data/Games.csv (2010-2025)
- data/PlayerStats.csv (2010-2024)
- data/all_teams_schedule_and_game_results_merged.csv (2010-2025)
- data/all_passing_rushing_receiving.csv (2020-2025)
- data/player_stats_pfr.csv (2010-2025)
- data/rosters/*.csv (2010-2025)

## 2. Matchup Generator (00_⚔️_Matchup_Generator.py)
# 2010-2025
- data/Games.csv (2010-2025)
- data/PlayerStats.csv (2010-2024)
- data/rosters/roster_2025.csv (2025)
- data/all_team_game_logs.csv (2020-2025)
- data/all_defense-game-logs.csv (2020-2025)
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
# 2020-2025
- data/Teams.csv
- data/Games.csv (2010-2025)
- data/PlayerStats.csv (2010-2024)
- data/all_team_game_logs.csv (2020-2025)
- data/all_teams_schedule_and_game_results_merged.csv (2010-2025)
- data/all_passing_rushing_receiving.csv (2020-2025)
- data/Rosters.csv (2010-2025)

## 8. Player Trends (06_📈_Player_Trends.py)
# 2020-2025
- data/Teams.csv
- data/Games.csv (2010-2025)
- data/PlayerStats.csv (2010-2024)
- data/all_team_game_logs.csv (2020-2025)
- data/all_teams_schedule_and_game_results_merged.csv (2010-2025)
- data/all_passing_rushing_receiving.csv (2020-2025)

## 9. Team Trends (07_📉_Team_Trends.py)
# 2024-2025
- data/Teams.csv
- data/Games.csv (2010-2025)
- data/PlayerStats.csv (2010-2024)
- data/all_team_game_logs.csv (2020-2025)
- data/all_teams_schedule_and_game_results_merged.csv (2010-2025)
- data/all_box_scores.csv (2020-2025)
- data/SR-game-logs/all_teams_game_logs_2024.csv (2024)
- data/SR-game-logs/all_teams_game_logs_2025.csv (2025)

## 10. Betting Trends (08_💰_Betting_Trends.py)
# 2024-2025
- data/Teams.csv
- data/Games.csv (2010-2025)
- data/PlayerStats.csv (2010-2024)

## 11. Scoring Trends (09_📊_Scoring_Trends.py)
# 2020-2025
- data/player_stats_pfr.csv (2010-2025)
- data/rosters/roster_2025.csv (2025)

## 12. AI Chatbot (10_🤖_AI_Chatbot.py)
# 2020-2025
- data/player_stats_pfr.csv (2010-2025)
- data/all_team_game_logs.csv (2020-2025)
- data/Rosters.csv (2010-2025)

## 13. Standings (12_💍_Standings.py)
# 2020-2025
- data/Teams.csv
- data/Games.csv (2010-2025)
- data/PlayerStats.csv (2010-2024)
