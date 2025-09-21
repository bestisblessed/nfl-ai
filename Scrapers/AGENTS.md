# NFL Data Scraper Output Files Overview:
This document lists all the final files created by the `ScraperFinal.py` script, along with their full column names. The script scrapes and processes various NFL data sources to generate these files for analysis.

## 1. Teams Data
- **File**: `final_data/Teams_<DATE>.csv`
- **Description**: Contains information about NFL teams.
- **Columns**:
  - `TeamID`: Unique identifier for the team (e.g., 'ARI')
  - `Team`: Full team name (e.g., 'Arizona Cardinals')
  - `Division`: Division the team belongs to (e.g., 'NFC West')

## 2. Games Data
- **File**: `final_data/Games_<DATE>.csv`
- **Description**: Contains detailed information about NFL games from 2010 onwards.
- **Columns**:
  - `game_id`: Unique identifier for the game
  - `season`: Year of the season
  - `week`: Week number of the season
  - `game_type`: Type of game (e.g., regular season, playoff)
  - `date`: Date of the game
  - `weekday`: Day of the week the game was played
  - `gametime`: Start time of the game
  - `away_team`: Away team ID
  - `away_score`: Away team score
  - `home_team`: Home team ID
  - `home_score`: Home team score
  - `location`: Game location
  - `result`: Game result
  - `total`: Total points scored
  - `overtime`: Whether the game went to overtime
  - `spread_line`: Betting spread line
  - `total_line`: Betting total line
  - `away_rest`: Days of rest for away team
  - `home_rest`: Days of rest for home team
  - `roof`: Stadium roof type
  - `surface`: Playing surface
  - `temp`: Temperature during the game
  - `wind`: Wind conditions
  - `away_qb_id`: Away team quarterback ID
  - `home_qb_id`: Home team quarterback ID
  - `away_qb_name`: Away team quarterback name
  - `home_qb_name`: Home team quarterback name
  - `away_coach`: Away team coach
  - `home_coach`: Home team coach
  - `referee`: Game referee
  - `stadium_id`: Stadium ID
  - `stadium`: Stadium name
  - `game_id_simple`: Simplified game ID (season_week)
  - `game_id_team1`: Game ID with home team
  - `game_id_team2`: Game ID with away team
  - `pfr`: Pro-Football-Reference ID
  - `home_spread`: Home team spread
  - `away_spread`: Away team spread
  - `team_favorite`: Team favored to win
  - `team_covered`: Team that covered the spread

## 3. Player Statistics
- **File**: `final_data/PlayerStats_<DATE>.csv`
- **Description**: Contains player statistics from 2010 to 2024.
- **Columns**:
  - `player_display_name`: Player's full name
  - `game_id`: Unique identifier for the game
  - `season`: Year of the season
  - `week`: Week number of the season
  - `position`: Player's position
  - `headshot_url`: URL to player's headshot
  - `completions`: Pass completions
  - `attempts`: Pass attempts
  - `passing_yards`: Passing yards
  - `passing_tds`: Passing touchdowns
  - `interceptions`: Interceptions thrown
  - `sacks`: Sacks taken
  - `carries`: Rushing attempts
  - `rushing_yards`: Rushing yards
  - `rushing_tds`: Rushing touchdowns
  - `rushing_fumbles`: Rushing fumbles
  - `receptions`: Receptions
  - `targets`: Receiving targets
  - `receiving_yards`: Receiving yards
  - `receiving_tds`: Receiving touchdowns
  - `receiving_fumbles`: Receiving fumbles
  - `fantasy_points_ppr`: Fantasy points (PPR scoring)
  - `home_team`: Home team ID
  - `away_team`: Away team ID
  - `player_current_team`: Player's current team ID

## 4. Rosters Data
- **File**: `final_data/Rosters_<DATE>.csv`
- **Description**: Contains NFL roster information for the 2024 season.
- **Columns**:
  - `season`: Year of the season
  - `team`: Team ID
  - `position`: Player position
  - `depth_chart_position`: Depth chart position
  - `status`: Player status
  - `full_name`: Player's full name
  - `first_name`: Player's first name
  - `last_name`: Player's last name
  - `birth_date`: Player's birth date
  - `height`: Player's height
  - `weight`: Player's weight
  - `college`: Player's college
  - `pfr_id`: Pro-Football-Reference player ID
  - `years_exp`: Years of experience
  - `headshot_url`: URL to player's headshot
  - `week`: Week number
  - `game_type`: Type of game
  - `entry_year`: Year player entered league
  - `rookie_year`: Rookie year
  - `draft_club`: Drafting team
  - `draft_number`: Draft pick number
  - `url`: Pro-Football-Reference player page URL

## 5. Box Scores
- **File**: `data/all_box_scores.csv`
- **Description**: Contains box score data for games in the 2024 season.
- **Columns**:
  - `URL`: URL of the game box score
  - `Team`: Team name
  - `1`: First quarter score
  - `2`: Second quarter score
  - `3`: Third quarter score
  - `4`: Fourth quarter score
  - `OT1`: First overtime score (if applicable)
  - `OT2`: Second overtime score (if applicable)
  - `OT3`: Third overtime score (if applicable)
  - `OT4`: Fourth overtime score (if applicable)
  - `Final`: Final score

## 6. Scoring Tables / Touchdown Logs
- **File**: `data/all_scoring_tables.csv`
- **Description**: Contains scoring play-by-play data for games in the 2024 season.
- **Columns**:
  - `Quarter`: Quarter of the scoring play
  - `Time`: Time of the scoring play
  - `Team`: Team that scored
  - `Detail`: Description of the scoring play
  - `Team_1`: Score for team 1 after play
  - `Team_2`: Score for team 2 after play
  - `Game_ID`: Unique identifier for the game

## 7. Team Game Logs
- **File**: `data/all_team_game_logs.csv`
- **Description**: Contains aggregated game log data for teams in the 2024 season.
- **Columns**:
  - `game_id`: Unique identifier for the game
  - `season`: Year of the season
  - `home_pts_off`: Home team points scored
  - `away_pts_off`: Away team points scored
  - `home_pass_cmp`: Home team pass completions
  - `away_pass_cmp`: Away team pass completions
  - `home_pass_att`: Home team pass attempts
  - `away_pass_att`: Away team pass attempts
  - `home_pass_yds`: Home team passing yards
  - `away_pass_yds`: Away team passing yards
  - `home_pass_td`: Home team passing touchdowns
  - `away_pass_td`: Away team passing touchdowns
  - `home_pass_int`: Home team interceptions thrown
  - `away_pass_int`: Away team interceptions thrown
  - `home_pass_sacked`: Home team times sacked
  - `away_pass_sacked`: Away team times sacked
  - `home_pass_yds_per_att`: Home team passing yards per attempt
  - `away_pass_yds_per_att`: Away team passing yards per attempt
  - `home_pass_net_yds_per_att`: Home team net passing yards per attempt
  - `away_pass_net_yds_per_att`: Away team net passing yards per attempt
  - `home_pass_cmp_perc`: Home team completion percentage
  - `away_pass_cmp_perc`: Away team completion percentage
  - `home_pass_rating`: Home team passer rating
  - `away_pass_rating`: Away team passer rating
  - `home_rush_att`: Home team rushing attempts
  - `away_rush_att`: Away team rushing attempts
  - `home_rush_yds`: Home team rushing yards
  - `away_rush_yds`: Away team rushing yards
  - `home_rush_yds_per_att`: Home team rushing yards per attempt
  - `away_rush_yds_per_att`: Away team rushing yards per attempt
  - `home_rush_td`: Home team rushing touchdowns
  - `away_rush_td`: Away team rushing touchdowns

## 8. Team Stats and Rankings
- **File**: `data/all_team_stats.csv`
- **Description**: Contains team statistics and rankings for the 2024 season.
- **Columns**:
  - `Player`: Team or category (e.g., 'Team', 'Opponent')
  - `PF`: Points for
  - `Yds`: Total yards
  - `Ply`: Total plays
  - `Y/P`: Yards per play
  - `TO`: Turnovers
  - `FL`: Fumbles lost
  - `1stD`: Total first downs
  - `Cmp`: Pass completions (Passing)
  - `Att`: Pass attempts (Passing)
  - `Yds`: Passing yards
  - `TD`: Passing touchdowns
  - `Int`: Interceptions thrown
  - `NY/A`: Net yards per attempt
  - `1stD`: First downs by passing
  - `Att`: Rushing attempts
  - `Yds`: Rushing yards
  - `TD`: Rushing touchdowns
  - `Y/A`: Yards per attempt (Rushing)
  - `1stD`: First downs by rushing
  - `Pen`: Penalties
  - `Yds`: Penalty yards
  - `1stPy`: First downs by penalty
  - `#Dr`: Number of drives
  - `Sc%`: Scoring percentage
  - `TO%`: Turnover percentage
  - `Start`: Average starting field position
  - `Time`: Average time per drive
  - `Plays`: Average plays per drive
  - `Yds`: Average yards per drive
  - `Pts`: Average points per drive
  - `Team`: Team abbreviation
  - `Year`: Season year

## 9. Schedule & Game Results
- **File**: `data/SR-schedule-and-game-results/all_teams_schedule_and_game_results_merged.csv`
- **Description**: Contains schedule and game result data for teams in the 2024 season.
- **Columns**:
  - `Week`: Week number
  - `Day`: Day of the week
  - `Date`: Date of the game
  - `Time`: Start time
  - `Boxscore`: Boxscore link word
  - `Outcome`: Win/Loss outcome
  - `OT`: Overtime indicator
  - `Rec`: Team record after game
  - `Home/Away`: Home or Away game indicator
  - `Opp`: Opponent team
  - `Tm`: Team points
  - `OppPts`: Opponent points
  - `1stD`: First downs
  - `TotYd`: Total yards
  - `PassY`: Passing yards
  - `RushY`: Rushing yards
  - `TO_lost`: Turnovers lost
  - `Opp1stD`: Opponent first downs
  - `OppTotYd`: Opponent total yards
  - `OppPassY`: Opponent passing yards
  - `OppRushY`: Opponent rushing yards
  - `TO_won`: Turnovers won
  - `Offense`: Expected points - Offense
  - `Defense`: Expected points - Defense
  - `Sp. Tms`: Expected points - Special Teams
  - `Team`: Team abbreviation
  - `Season`: Season year

## 10. Team Conversions
- **File**: `data/all_team_conversions.csv`
- **Description**: Contains team conversion statistics for the 2024 season.
- **Columns**:
  - `Player`: Team or category
  - `3DAtt`: 3rd down attempts
  - `3DConv`: 3rd down conversions
  - `4DAtt`: 4th down attempts
  - `4DConv`: 4th down conversions
  - `4D%`: 4th down conversion percentage
  - `RZAtt`: Red zone attempts
  - `RZTD`: Red zone touchdowns
  - `RZPct`: Red zone touchdown percentage
  - `Team`: Team abbreviation
  - `Year`: Season year

## 11. Passing, Rushing, and Receiving Game Logs
- **File**: `data/all_passing_rushing_receiving.csv`
- **Description**: Contains individual player game logs for passing, rushing, and receiving in the 2024 season.
- **Columns**:
  - `player`: Player name
  - `player_id`: Player ID from Pro-Football-Reference
  - `team`: Player's team ID
  - `pass_cmp`: Pass completions
  - `pass_att`: Pass attempts
  - `pass_yds`: Passing yards
  - `pass_td`: Passing touchdowns
  - `pass_int`: Interceptions thrown
  - `pass_sacked`: Times sacked
  - `pass_sacked_yds`: Yards lost to sacks
  - `pass_long`: Longest pass
  - `pass_rating`: Passer rating
  - `rush_att`: Rushing attempts
  - `rush_yds`: Rushing yards
  - `rush_td`: Rushing touchdowns
  - `rush_long`: Longest rush
  - `targets`: Receiving targets
  - `rec`: Receptions
  - `rec_yds`: Receiving yards
  - `rec_td`: Receiving touchdowns
  - `rec_long`: Longest reception
  - `fumbles`: Total fumbles
  - `fumbles_lost`: Fumbles lost
  - `game_id`: Unique identifier for the game
  - `opponent_team`: Opponent team ID
  - `home`: Whether player was on home team ('y' or 'n')
  - `position`: Player position

## 12. Defense Game Logs
- **File**: `data/all_defense-game-logs.csv`
- **Description**: Contains defensive statistics for players in games during the 2024 season.
- **Columns**:
  - `player`: Player name
  - `team`: Player's team
  - `def_int`: Interceptions
  - `def_int_yds`: Interception return yards
  - `def_int_td`: Interception return touchdowns
  - `def_int_long`: Longest interception return
  - `pass_defended`: Passes defended
  - `sacks`: Sacks
  - `tackles_combined`: Total tackles
  - `tackles_solo`: Solo tackles
  - `tackles_assists`: Assisted tackles
  - `tackles_loss`: Tackles for loss
  - `qb_hits`: Quarterback hits
  - `fumbles_rec`: Fumbles recovered
  - `fumbles_rec_yds`: Fumble recovery yards
  - `fumbles_rec_td`: Fumble recovery touchdowns
  - `fumbles_forced`: Fumbles forced
  - `game_id`: Unique identifier for the game

**Note**: `<DATE>` in filenames represents the current date in the format `MMM_DD_YYYY` (e.g., `OCT_25_2023`). Files in the `final_data` directory include this timestamp to indicate when they were generated.

-----------------------------------------------------------------------------------------------------------

# DATA SOURCES:

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
  - Game Logs: `final_data_pfr/game_logs_pfr.csv` (Games + TeamGameLogs merged - COMPREHENSIVE GAME DATA)
  - BoxScores: populated from `data/all_box_scores.csv` (PFR box scores)
  - ScoringTables: populated from `data/all_scoring_tables.csv` (PFR scoring tables)
  - TeamGameLogs: populated from `data/all_team_game_logs.csv` (PFR team game logs)
  - TeamStats: populated from `data/all_team_stats.csv` (PFR team stats)
  - TeamConversions: populated from `data/all_team_conversions.csv` (PFR team conversions)
  - PassingRushingReceiving: populated from `data/all_passing_rushing_receiving_pfr_clean.csv` (PFR player stats)
  - DefenseGameLogs: populated from `data/all_defense-game-logs.csv` (PFR defense stats)
  - ScheduleGameResults: populated from `data/SR-schedule-and-game-results/all_teams_schedule_and_game_results_merged.csv` (PFR schedule data)