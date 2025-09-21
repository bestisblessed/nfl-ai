# Knowledge Base Overview:

## **box_scores_pfr.csv** (636 rows)
**Columns:** URL, Team, 1, 2, 3, 4, OT1, OT2, OT3, OT4, Final  
**Content:** Quarter-by-quarter scores with overtime periods and final scores linked to Pro Football Reference boxscore URLs.

## **team_conversions_pfr.csv** (896 rows)  
**Columns:** Player, 3DAtt, 3DConv, 4DAtt, 4DConv, 4D%, RZAtt, RZTD, RZPct, Team, Year  
**Content:** Team conversion statistics - third down attempts/conversions, fourth down attempts/conversions/percentages, red zone attempts/touchdowns/percentages by season.

## **teams_pfr.csv** (32 rows)
**Columns:** TeamID, Team, Division  
**Content:** NFL team reference table with 3-letter codes, full names, and divisional assignments.

## **team_stats_pfr.csv** (896 rows)
**Columns:** Player, PF, Yds, Ply, Y/P, TO, FL, 1stD, Cmp, Att, Yds.1, TD, Int, NY/A, 1stD.1, Att.1, Yds.2, TD.1, Y/A, 1stD.2, Pen, Yds.3, 1stPy, #Dr, Sc%, TO%, Start, Time, Plays, Yds.4, Pts, Team, Year  
**Content:** Comprehensive team offense statistics including points scored, total yards, plays, turnovers, passing stats (completions, attempts, yards, TDs, interceptions), rushing stats, penalties, drives, and scoring efficiency by season.

## **game_logs_pfr.csv** (1,632 rows)
**Columns:** game_id, home_pts_off, away_pts_off, home_pass_cmp, away_pass_cmp, home_pass_att, away_pass_att, home_pass_yds, away_pass_yds, home_pass_td, away_pass_td, home_pass_int, away_pass_int, home_pass_sacked, away_pass_sacked, home_pass_yds_per_att, away_pass_yds_per_att, home_pass_net_yds_per_att, away_pass_net_yds_per_att, home_pass_cmp_perc, away_pass_cmp_perc, home_pass_rating, away_pass_rating, home_rush_att, away_rush_att, home_rush_yds, away_rush_yds, home_rush_yds_per_att, away_rush_yds_per_att, home_rush_td, away_rush_td  
**Content:** Game-level team statistics with separate home/away columns for points, passing metrics (completions, attempts, yards, TDs, interceptions, sacks, efficiency), and rushing metrics.

## **scoring_tables_pfr.csv** (14,536 rows)
**Columns:** Quarter, Time, Team, Detail, Team_1, Team_2, Game_ID  
**Content:** Play-by-play scoring events with quarter, time remaining, scoring team, play description, and running score totals for both teams.

## **schedule_game_results_pfr.csv** (3,722 rows)
**Columns:** Week, Day, Date, Time, Boxscore, Outcome, OT, Rec, Home/Away, Opp, Tm, OppPts, 1stD, TotYd, PassY, RushY, TO_lost, Opp1stD, OppTotYd, OppPassY, OppRushY, TO_won, Offense, Defense, Sp. Tms, Team, Season  
**Content:** Game schedule and results with team performance metrics including yards, turnovers, first downs, and efficiency ratings for offense, defense, and special teams.

## **defense_game_logs_pfr.csv** (67,060 rows)
**Columns:** player, team, def_int, def_int_yds, def_int_td, def_int_long, pass_defended, sacks, tackles_combined, tackles_solo, tackles_assists, tackles_loss, qb_hits, fumbles_rec, fumbles_rec_yds, fumbles_rec_td, fumbles_forced, game_id  
**Content:** Individual player defensive statistics per game including interceptions, tackles, sacks, fumbles, and pass breakups.

## **player_stats_pfr.csv** (195,827 rows)
**Columns:** player, player_id, team, pass_cmp, pass_att, pass_yds, pass_td, pass_int, pass_sacked, pass_sacked_yds, pass_long, pass_rating, rush_att, rush_yds, rush_td, rush_long, targets, rec, rec_yds, rec_td, rec_long, fumbles, fumbles_lost, game_id, opponent_team, home, position, season, week, headshot_url, fantasy_points_ppr, home_team, away_team  
**Content:** Individual player offensive statistics per game covering passing, rushing, and receiving with fantasy points and game context data.