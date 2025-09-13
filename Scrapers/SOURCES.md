## nflverse github:
- data/games.csv: https://raw.githubusercontent.com/nflverse/nfldata/master/data/games.csv
- data/player-stats/player_stats_YYYY.csv: https://github.com/nflverse/nflverse-data/releases/download/player_stats/player_stats_YYYY.csv
- data/rosters/roster_YYYY.csv: https://github.com/nflverse/nflverse-data/releases/download/rosters/roster_YYYY.csv

## pro-football-reference.com:
- data/SR-game-logs/all_teams_game_logs_YYYY.csv: https://www.pro-football-reference.com/teams/{abbr}/{YYYY}/gamelog/
- data/SR-opponent-game-logs/all_teams_opponent_game_logs_YYYY.csv: https://www.pro-football-reference.com/teams/{abbr}/{YYYY}/gamelog/
- data/SR-team-stats/all_teams_stats_YYYY.csv: https://www.pro-football-reference.com/teams/{abbr}/{YYYY}.htm (team_stats)
- data/SR-team-conversions/{abbr}_YYYY_team_conversions.csv: https://www.pro-football-reference.com/teams/{abbr}/{YYYY}.htm (team_conversions)
- data/SR-box-scores/all_box_scores_YYYY.csv → data/all_box_scores.csv: https://www.pro-football-reference.com/boxscores/{pfr}.htm (linescore)
- data/SR-scoring-tables/all_nfl_scoring_tables_YYYY.csv → data/all_scoring_tables.csv: https://www.pro-football-reference.com/boxscores/{pfr}.htm (scoring)
- data/SR-passing-rushing-receiving-game-logs/all_passing_rushing_receiving_YYYY.csv → data/all_passing_rushing_receiving.csv: https://www.pro-football-reference.com/boxscores/{pfr}.htm (player_offense) + NFLverse position data
- data/SR-passing-rushing-receiving-game-logs/all_passing_rushing_receiving_YYYY.csv → data/all_passing_rushing_receiving_pfr_clean.csv: https://www.pro-football-reference.com/boxscores/{pfr}.htm (player_offense) - PURE PFR DATA
- data/SR-defense-game-logs/all_defense_YYYY.csv → data/all_defense-game-logs.csv: https://www.pro-football-reference.com/boxscores/{pfr}.htm (player_defense in comments)

## FINAL FILES:
- data/all_team_game_logs.csv: built from data/SR-game-logs/*.csv with home/away IDs, aggregated per game
- data/all_team_stats.csv: merged from data/SR-team-stats/*.csv
- data/all_team_conversions.csv: merged from data/SR-team-conversions/*.csv
- data/rosters.csv: merged rosters with PFR player URLs added
- data/player_stats.csv: cleaned/merged player stats with game_id mapping to data/games.csv
- final_data/*.csv: exports of SQLite tables (Teams, Games, PlayerStats, Rosters) with date stamp
- nfl.db (Mixed NFLverse + PFR data):
  - Teams: created from hardcoded team list in `ScraperFinal.py` (no external file)
  - Games: populated from `data/games.csv` (nflverse); additional columns: home_spread, away_spread, team_favorite, team_covered
  - PlayerStats: populated from `data/player_stats.csv` (built from yearly `data/player-stats/player_stats_YYYY.csv` and joined to `data/games.csv` for game_id mapping)
  - Rosters: populated from `data/rosters.csv` (merged from yearly `data/rosters/roster_YYYY.csv` with PFR player URL)

- nfl-db-pfr.db (PURE PFR data only):
  - Teams: created from hardcoded team list in `ScraperFinal-PFR.py` (no external file)
  - Games: populated from `data/SR-game-logs/all_teams_game_logs_YYYY.csv` (PFR team game logs)
  - PlayerStats: populated from `data/all_passing_rushing_receiving_pfr_clean.csv` (PFR player stats WITHOUT NFLverse position data)
  - BoxScores: populated from `data/all_box_scores.csv` (PFR box scores)
  - ScoringTables: populated from `data/all_scoring_tables.csv` (PFR scoring tables)
  - TeamGameLogs: populated from `data/all_team_game_logs.csv` (PFR team game logs)
  - TeamStats: populated from `data/all_team_stats.csv` (PFR team stats)
  - TeamConversions: populated from `data/all_team_conversions.csv` (PFR team conversions)
  - PassingRushingReceiving: populated from `data/all_passing_rushing_receiving_pfr_clean.csv` (PFR player stats)
  - DefenseGameLogs: populated from `data/all_defense-game-logs.csv` (PFR defense stats)
  - ScheduleGameResults: populated from `data/SR-schedule-and-game-results/all_teams_schedule_and_game_results_merged.csv` (PFR schedule data)