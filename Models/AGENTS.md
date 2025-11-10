## Knowledge Base Overview

### `box_scores_pfr.csv` (636 rows)
- **Columns**: URL, Team, 1, 2, 3, 4, OT1, OT2, OT3, OT4, Final
- **Content**: Quarter-by-quarter scores with overtime periods and final scores linked to Pro Football Reference boxscore URLs.

### `team_conversions_pfr.csv` (896 rows)
- **Columns**: Player, 3DAtt, 3DConv, 4DAtt, 4DConv, 4D%, RZAtt, RZTD, RZPct, Team, Year
- **Content**: Team conversion statistics - third down attempts/conversions, fourth down attempts/conversions/percentages, red zone attempts/touchdowns/percentages by season.

### `teams_pfr.csv` (32 rows)
- **Columns**: TeamID, Team, Division
- **Content**: NFL team reference table with 3-letter codes, full names, and divisional assignments.

### `team_stats_pfr.csv` (896 rows)
- **Columns**: Player, PF, Yds, Ply, Y/P, TO, FL, 1stD, Cmp, Att, Yds.1, TD, Int, NY/A, 1stD.1, Att.1, Yds.2, TD.1, Y/A, 1stD.2, Pen, Yds.3, 1stPy, #Dr, Sc%, TO%, Start, Time, Plays, Yds.4, Pts, Team, Year
- **Content**: Comprehensive team offense statistics including points scored, total yards, plays, turnovers, passing stats (completions, attempts, yards, TDs, interceptions), rushing stats, penalties, drives, and scoring efficiency by season.

### `game_logs_pfr.csv` (1,632 rows)
- **Columns**: game_id, home_pts_off, away_pts_off, home_pass_cmp, away_pass_cmp, home_pass_att, away_pass_att, home_pass_yds, away_pass_yds, home_pass_td, away_pass_td, home_pass_int, away_pass_int, home_pass_sacked, away_pass_sacked, home_pass_yds_per_att, away_pass_yds_per_att, home_pass_net_yds_per_att, away_pass_net_yds_per_att, home_pass_cmp_perc, away_pass_cmp_perc, home_pass_rating, away_pass_rating, home_rush_att, away_rush_att, home_rush_yds, away_rush_yds, home_rush_yds_per_att, away_rush_yds_per_att, home_rush_td, away_rush_td
- **Content**: Game-level team statistics with separate home/away columns for points, passing metrics (completions, attempts, yards, TDs, interceptions, sacks, efficiency), and rushing metrics.

### `scoring_tables_pfr.csv` (14,536 rows)
- **Columns**: Quarter, Time, Team, Detail, Team_1, Team_2, Game_ID
- **Content**: Play-by-play scoring events with quarter, time remaining, scoring team, play description, and running score totals for both teams.

### `schedule_game_results_pfr.csv` (3,722 rows)
- **Columns**: Week, Day, Date, Time, Boxscore, Outcome, OT, Rec, Home/Away, Opp, Tm, OppPts, 1stD, TotYd, PassY, RushY, TO_lost, Opp1stD, OppTotYd, OppPassY, OppRushY, TO_won, Offense, Defense, Sp. Tms, Team, Season
- **Content**: Game schedule and results with team performance metrics including yards, turnovers, first downs, and efficiency ratings for offense, defense, and special teams.

### `defense_game_logs_pfr.csv` (67,060 rows)
- **Columns**: player, team, def_int, def_int_yds, def_int_td, def_int_long, pass_defended, sacks, tackles_combined, tackles_solo, tackles_assists, tackles_loss, qb_hits, fumbles_rec, fumbles_rec_yds, fumbles_rec_td, fumbles_forced, game_id
- **Content**: Individual player defensive statistics per game including interceptions, tackles, sacks, fumbles, and pass breakups.

### `player_stats_pfr.csv` (195,827 rows)
- **Columns**: player, player_id, team, pass_cmp, pass_att, pass_yds, pass_td, pass_int, pass_sacked, pass_sacked_yds, pass_long, pass_rating, rush_att, rush_yds, rush_td, rush_long, targets, rec, rec_yds, rec_td, rec_long, fumbles, fumbles_lost, game_id, opponent_team, home, position, season, week, headshot_url, fantasy_points_ppr, home_team, away_team
- **Content**: Individual player offensive statistics per game covering passing, rushing, and receiving with fantasy points and game context data.

---

## Models & Code Overview

### Purpose
- **Scope**: Three XGBoost-based props model families (Passing, Receiving, Rushing) produce per-game PNG/TXT assets and CSVs. A master script compiles all into final TXT/HTML/CSV.
- **Inputs**: `Scrapers/data/all_passing_rushing_receiving.csv`, `Scrapers/data/rosters/roster_2025.csv`, repo files `starting_qbs_2025.csv`, `upcoming_games.csv`.
- **One-shot run**: `bash gen_final_report.sh WEEK` (W=1–18).

### 1-PASSING-YARDS (QB passing yards)
- **Runners**: `prepare_data.py`, `xgboost_passing_yards_qb.py`, `generate_txt_reports.py`, `generate_html_reports.py`.
- **Model**: XGBRegressor on rolling means of attempts/completions/yards (windows 3/5/8); restricted to starting QBs.
- **Outputs**: `1-PASSING-YARDS/predictions-week-W-QB/`
  - `final_weekW_QB_pass_yards_report.csv`
  - Per-game PNGs (full and cleaned), TXT; merged TXT/HTML

### 2-RECEIVING-YARDS (WR, RB, TE)
- **Runners**: `xgboost_receiving_yards_wr.py`, `xgboost_receiving_yards_rb.py`, `xgboost_receiving_yards_te.py`, then TXT/HTML generators.
- **Model(s)**: XGB on rolling means of targets/receptions/rec_yards (3/5/8/12) + rolling medians + baseline features (last-3 avg, prior-season avg, career median). Uses `reg:absoluteerror` objective. No placeholders for players without history.
- **Outputs**: `2-RECEIVING-YARDS/predictions-week-W-{WR|RB|TE}/`
  - `final_weekW_{POS}_rec_yards_report.csv`
  - Per-game PNGs (full and cleaned), TXT; merged TXT/HTML

### 3-RUSHING-YARDS (QB, RB)
- **Runners**: `xgboost_rushing_yards_qb.py`, `xgboost_rushing_yards_rb.py`, then TXT/HTML generators.
- **Model(s)**: XGB on rolling means of rush_attempts/rush_yds (3/5/8/12) + rolling medians + baseline features (last-3 avg, prior-season avg, career median). Uses `reg:absoluteerror` objective. QB variant: only starting QBs; rookies flagged "No Data".
- **Outputs**: `3-RUSHING-YARDS/predictions-week-W-{QB|RB}/`
  - `final_weekW_{POS}_rush_yards_report.csv`
  - Per-game PNGs (full and cleaned), TXT; merged TXT/HTML

### 10-ARBITRAGE (Value Betting Analysis)
- **Runners**: `fetch_upcoming_games_and_props.py`, `find_value_bets.py`, `render_value_reports.py`.
- **Purpose**: Fetches betting props from the-odds-api.com, compares model predictions to sportsbook lines, identifies value opportunities.
- **Inputs**: `0-FINAL-REPORTS/weekW_all_props_summary.csv` (model predictions).
- **Process**:
  1. Fetches props for 6 markets: QB Passing Yards, WR/TE/RB Receiving Yards, QB/RB Rushing Yards.
  2. Compares predictions vs. best available lines across all books (best Over = min point + max odds; best Under = max point + max odds).
  3. Calculates edge (predicted yards vs. line) and ranks opportunities.
- **Outputs**: `10-ARBITRAGE/data/weekW_value_opportunities.csv`, `weekW_top_edges_by_prop.csv`, `weekW_value_full_report.html`, `weekW_value_leader_tables.pdf`.

### 999-POWER-RANKINGS (Team Elo Ratings)
- **Runner**: `power_rankings.py`.
- **Model**: Elo-based team power rankings using historical game results from `Scrapers/nfl.db`.
- **Parameters**: K-factor=20, home field advantage=2.5, vig=1.04.
- **Inputs**: SQLite database `Scrapers/nfl.db` (Games table with home_team, away_team, scores, season, week).
- **Outputs**: `999-POWER-RANKINGS/output/` with CSV rankings and PNG visualizations.

### Orchestration
- **`gen_final_report.sh`**: Master workflow script that:
  1. Copies `Scrapers/data/` to `Models/data/`
  2. Updates `upcoming_games.csv` and `upcoming_bye_week.csv` via `update_upcoming_games.py`
  3. Updates `starting_qbs_2025.csv` based on playing vs. bye teams
  4. Scrapes injury reports via `scrape_injured_players.py` → `injured_players.csv`, `questionable_players.csv`
  5. Cleans existing week predictions
  6. Runs all three model families (Passing, Receiving, Rushing)
  7. Generates combined report via `generate_final_report.py`
  8. Generates Top 25 analysis PDF via `analyze_top_25.py`
  9. Fetches betting props via `10-ARBITRAGE/fetch_upcoming_games_and_props.py`
  10. Finds value bets via `10-ARBITRAGE/find_value_bets.py`
  11. Renders value reports via `10-ARBITRAGE/render_value_reports.py`
- **`generate_final_report.py`**: Loads per-model CSVs, tags `prop_type`/`position`, groups by game using `upcoming_games.csv` (fallback to pairs from data), and writes:
  - `0-FINAL-REPORTS/weekW_complete_props_report.txt` and `.html`
  - `0-FINAL-REPORTS/weekW_all_props_summary.csv`
- **`analyze_top_25.py`**: Generates Top 25 leader tables PDF per prop type/position from final summary CSV.

### Utility Scripts
- **`update_upcoming_games.py`**: Reads `data/games.csv`, filters unplayed games for specified week (or next upcoming), writes `upcoming_games.csv` and `upcoming_bye_week.csv`. Auto-updates QB files based on playing teams.
- **`scrape_injured_players.py`**: Uses Playwright to scrape ESPN NFL injuries page, extracts players with status "Out", "IR", "Doubtful" → `injured_players.csv`; others → `questionable_players.csv`.

### Input Files
- **`upcoming_games.csv`**: Two columns (`home_team`, `away_team`) for current week matchups. Generated by `update_upcoming_games.py` from `data/games.csv`.
- **`upcoming_bye_week.csv`**: Teams on bye for current week.
- **`starting_qbs_2025.csv`**: QB reference file with team assignments. Auto-updated based on playing teams.
- **`starting_qbs_2025_bye.csv`**: QBs for teams on bye.
- **`injured_players.csv`**: Players with "Out", "IR", "Doubtful" status (scraped from ESPN).
- **`questionable_players.csv`**: Players with other injury statuses (scraped from ESPN).
- **`data/games.csv`**: Source game schedule from Scrapers (columns: home_team, away_team, date, gametime, home_score, away_score, season, week, game_type).

### External Data Sources & APIs
- **the-odds-api.com**: Betting props API used by `10-ARBITRAGE/fetch_upcoming_games_and_props.py`. Fetches player props (passing/receiving/rushing yards) from multiple sportsbooks. API key required.
- **ESPN.com**: Injury data scraped via Playwright by `scrape_injured_players.py` from `https://www.espn.com/nfl/injuries`.
- **Pro Football Reference (PFR)**: Historical data stored in CSV files (see Knowledge Base Overview) located in `Scrapers/final_data_pfr/` and `Scrapers/data/`.
- **SQLite Database**: `Scrapers/nfl.db` contains game results (Games table) used by power rankings model.

### Quick start
1. Ensure inputs exist: `Scrapers/data/all_passing_rushing_receiving.csv`, `Scrapers/data/rosters/roster_2025.csv`; `data/games.csv` for upcoming games.
2. Run: `bash gen_final_report.sh WEEK`.
3. Outputs:
   - `0-FINAL-REPORTS/weekW_complete_props_report.html` - Combined props report
   - `0-FINAL-REPORTS/weekW_all_props_summary.csv` - All predictions summary
   - `0-FINAL-REPORTS/weekW_leader_tables.pdf` - Top 25 leader tables
   - `0-FINAL-REPORTS/weekW_value_complete_props_report.html` - Value betting report (if props fetched)
   - `0-FINAL-REPORTS/weekW_value_leader_tables.pdf` - Value opportunities PDF
   - `10-ARBITRAGE/data/weekW_value_opportunities.csv` - Value bets CSV