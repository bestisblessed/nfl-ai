# NFL Team Abbreviations
This list contains the standard 3-letter team abbreviations used by Pro-Football-Reference.com and throughout the NFL data scraping system and files. These abbreviations are consistent across all game data, box scores, and statistics; and in parentheses the full team names spelled out:

1. `atl` (Atlanta Falcons)
2. `buf` (Buffalo Bills)
3. `car` (Carolina Panthers)
4. `chi` (Chicago Bears)
5. `cin` (Cincinnati Bengals)
6. `cle` (Cleveland Browns)
7. `clt` (Indianapolis Colts)
8. `crd` (Arizona Cardinals)
9. `dal` (Dallas Cowboys)
10. `den` (Denver Broncos)
11. `det` (Detroit Lions)
12. `gnb` (Green Bay Packers)
13. `htx` (Houston Texans)
14. `jax` (Jacksonville Jaguars)
15. `kan` (Kansas City Chiefs)
16. `mia` (Miami Dolphins)
17. `min` (Minnesota Vikings)
18. `nor` (New Orleans Saints)
19. `nwe` (New England Patriots)
20. `nyg` (New York Giants)
21. `nyj` (New York Jets)
22. `oti` (Tennessee Titans)
23. `phi` (Philadelphia Eagles)
24. `pit` (Pittsburgh Steelers)
25. `rai` (Las Vegas Raiders)
26. `ram` (Los Angeles Rams)
27. `rav` (Baltimore Ravens)
28. `sdg` (Los Angeles Chargers)
29. `sea` (Seattle Seahawks)
30. `sfo` (San Francisco 49ers)
31. `tam` (Tampa Bay Buccaneers)
32. `was` (Washington Commanders)




# Games Data Overview
The `games.csv` file has 13 columns:

1. `game_id` - Unique game identifier (format: YYYY_WW_AWAY_HOME)
2. `pfr_boxscore_id` - Pro-Football-Reference boxscore identifier
3. `season` - Season year
4. `week` - Week number (01-18 for regular season, 19-22 for playoffs)
5. `away_team` - Away team abbreviation
6. `home_team` - Home team abbreviation
7. `winning_team` - Winning team abbreviation
8. `PtsW` - Points scored by winning team
9. `PtsL` - Points scored by losing team
10. `YdsW` - Yards gained by winning team
11. `TOW` - Turnovers by winning team
12. `YdsL` - Yards gained by losing team
13. `TOL` - Turnovers by losing team




# Player Stats Data Overview
The `player_stats.csv` file has 36 columns:

1. `ranker` - Player ranking
2. `player_name` - Player's name
3. `player_url` - Link to player's PFR page
4. `team` - Team abbreviation
5. `team_url` - Link to team's PFR page
6. `fantasy_pos` - Fantasy position (QB, RB, WR, TE)
7. `age` - Player's age
8. `g` - Games played
9. `gs` - Games started
10. `pass_cmp` - Pass completions
11. `pass_att` - Pass attempts
12. `pass_yds` - Passing yards
13. `pass_td` - Passing touchdowns
14. `pass_int` - Interceptions thrown
15. `rush_att` - Rushing attempts
16. `rush_yds` - Rushing yards
17. `rush_yds_per_att` - Rushing yards per attempt
18. `rush_td` - Rushing touchdowns
19. `targets` - Receiving targets
20. `rec` - Receptions
21. `rec_yds` - Receiving yards
22. `rec_yds_per_rec` - Receiving yards per reception
23. `rec_td` - Receiving touchdowns
24. `fumbles` - Total fumbles
25. `fumbles_lost` - Fumbles lost
26. `all_td` - Total touchdowns
27. `two_pt_md` - Two-point conversions made
28. `two_pt_pass` - Two-point conversion passes
29. `fantasy_points` - Standard fantasy points
30. `fantasy_points_ppr` - PPR fantasy points
31. `draftkings_points` - DraftKings scoring
32. `fanduel_points` - FanDuel scoring
33. `vbd` - Value Based Drafting metric
34. `fantasy_rank_pos` - Position ranking
35. `fantasy_rank_overall` - Overall fantasy ranking
36. `season` - Season year
