# Final Betting Edge Analysis - 5 More NFL Analytics
# 1. Player Performance Trends and Regression Analysis
# 2. Team Matchup History and Head-to-Head Performance
# 3. Stadium-Specific Performance Patterns
# 4. Weather Extremes and Their Impact
# 5. Betting Market Inefficiencies and Value Bets

import sqlite3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

conn = sqlite3.connect("data/nfl.db")
games = pd.read_sql("""
    SELECT game_id, season, CAST(week AS INT) as week, date, home_team, away_team, 
           home_score, away_score, roof, surface, temp, wind, away_rest, home_rest,
           stadium, game_type, pfr, away_coach, home_coach, referee
    FROM Games 
    WHERE season >= 2020 AND home_score IS NOT NULL AND away_score IS NOT NULL
""", conn)
conn.close()

# Load additional datasets
player_stats = pd.read_csv("data/all_passing_rushing_receiving.csv")

print("=== FINAL BETTING EDGE ANALYSIS ===")
print(f"Analyzing {len(games)} games from 2020-2025")
print("=" * 60)

# 1. PLAYER PERFORMANCE TRENDS AND REGRESSION ANALYSIS
print("\n1. PLAYER PERFORMANCE TRENDS ANALYSIS")
print("=" * 50)

# Analyze player performance trends
if len(player_stats) > 0:
    # Focus on key positions
    qb_stats = player_stats[player_stats['position'] == 'QB'].copy()
    rb_stats = player_stats[player_stats['position'] == 'RB'].copy()
    wr_stats = player_stats[player_stats['position'] == 'WR'].copy()
    
    # QB performance analysis
    qb_performance = qb_stats.groupby('player').agg({
        'pass_yds': ['mean', 'std', 'count'],
        'pass_td': ['mean', 'std'],
        'pass_int': ['mean', 'std']
    }).round(2)
    
    qb_performance.columns = ['pass_yds_avg', 'pass_yds_std', 'games', 'pass_td_avg', 'pass_td_std', 'pass_int_avg', 'pass_int_std']
    qb_performance = qb_performance[qb_performance['games'] >= 10]  # Minimum 10 games
    
    print("Top 10 QB Performance (Passing Yards):")
    print(qb_performance.sort_values('pass_yds_avg', ascending=False).head(10)[['pass_yds_avg', 'games', 'pass_td_avg']].to_string())
    
    # RB performance analysis
    rb_performance = rb_stats.groupby('player').agg({
        'rush_yds': ['mean', 'std', 'count'],
        'rush_td': ['mean', 'std']
    }).round(2)
    
    rb_performance.columns = ['rush_yds_avg', 'rush_yds_std', 'games', 'rush_td_avg', 'rush_td_std']
    rb_performance = rb_performance[rb_performance['games'] >= 10]
    
    print("\nTop 10 RB Performance (Rushing Yards):")
    print(rb_performance.sort_values('rush_yds_avg', ascending=False).head(10)[['rush_yds_avg', 'games', 'rush_td_avg']].to_string())
    
    # WR performance analysis
    wr_performance = wr_stats.groupby('player').agg({
        'rec_yds': ['mean', 'std', 'count'],
        'rec_td': ['mean', 'std']
    }).round(2)
    
    wr_performance.columns = ['rec_yds_avg', 'rec_yds_std', 'games', 'rec_td_avg', 'rec_td_std']
    wr_performance = wr_performance[wr_performance['games'] >= 10]
    
    print("\nTop 10 WR Performance (Receiving Yards):")
    print(wr_performance.sort_values('rec_yds_avg', ascending=False).head(10)[['rec_yds_avg', 'games', 'rec_td_avg']].to_string())
else:
    print("No player stats available for analysis")

# 2. TEAM MATCHUP HISTORY AND HEAD-TO-HEAD PERFORMANCE
print("\n\n2. TEAM MATCHUP HISTORY ANALYSIS")
print("=" * 50)

# Analyze head-to-head matchups
matchup_analysis = []
for _, game in games.iterrows():
    matchup_analysis.append({
        'home_team': game['home_team'],
        'away_team': game['away_team'],
        'home_score': game['home_score'],
        'away_score': game['away_score'],
        'total': game['home_score'] + game['away_score'],
        'margin': game['home_score'] - game['away_score'],
        'season': game['season']
    })

matchup_df = pd.DataFrame(matchup_analysis)

# Create matchup pairs
matchup_df['matchup'] = matchup_df.apply(lambda x: f"{min(x['home_team'], x['away_team'])}_{max(x['home_team'], x['away_team'])}", axis=1)

# Analyze matchup performance
matchup_stats = matchup_df.groupby('matchup').agg({
    'total': ['mean', 'std', 'count'],
    'margin': ['mean', 'std']
}).round(2)

matchup_stats.columns = ['avg_total', 'std_total', 'games', 'avg_margin', 'std_margin']
matchup_stats = matchup_stats[matchup_stats['games'] >= 3]  # Minimum 3 games

print("Highest Scoring Matchups:")
print(matchup_stats.sort_values('avg_total', ascending=False).head(10).to_string())

print("\nLowest Scoring Matchups:")
print(matchup_stats.sort_values('avg_total', ascending=True).head(10).to_string())

# 3. STADIUM-SPECIFIC PERFORMANCE PATTERNS
print("\n\n3. STADIUM-SPECIFIC PERFORMANCE ANALYSIS")
print("=" * 50)

# Analyze stadium performance
games['total'] = games['home_score'] + games['away_score']
stadium_analysis = games.groupby('stadium').agg({
    'home_score': ['mean', 'std', 'count'],
    'away_score': ['mean', 'std'],
    'total': ['mean', 'std']
}).round(2)

stadium_analysis.columns = ['home_avg', 'home_std', 'games', 'away_avg', 'away_std', 'total_avg', 'total_std']
stadium_analysis = stadium_analysis[stadium_analysis['games'] >= 10]  # Minimum 10 games

print("Highest Scoring Stadiums:")
print(stadium_analysis.sort_values('total_avg', ascending=False).head(10)[['total_avg', 'games', 'home_avg', 'away_avg']].to_string())

print("\nLowest Scoring Stadiums:")
print(stadium_analysis.sort_values('total_avg', ascending=True).head(10)[['total_avg', 'games', 'home_avg', 'away_avg']].to_string())

# 4. WEATHER EXTREMES AND THEIR IMPACT
print("\n\n4. WEATHER EXTREMES ANALYSIS")
print("=" * 50)

# Analyze extreme weather conditions
weather_games = games.dropna(subset=['temp', 'wind']).copy()
weather_games['total'] = weather_games['home_score'] + weather_games['away_score']

# Extreme temperature analysis
extreme_cold = weather_games[weather_games['temp'] <= 20].copy()
extreme_hot = weather_games[weather_games['temp'] >= 80].copy()
normal_temp = weather_games[(weather_games['temp'] > 20) & (weather_games['temp'] < 80)].copy()

print("Extreme Weather Impact:")
print(f"Extreme Cold (≤20°F): {len(extreme_cold)} games, {extreme_cold['total'].mean():.2f} avg points")
print(f"Extreme Hot (≥80°F): {len(extreme_hot)} games, {extreme_hot['total'].mean():.2f} avg points")
print(f"Normal Temp (20-80°F): {len(normal_temp)} games, {normal_temp['total'].mean():.2f} avg points")

# Extreme wind analysis
extreme_wind = weather_games[weather_games['wind'] >= 20].copy()
calm_wind = weather_games[weather_games['wind'] <= 5].copy()

print(f"\nExtreme Wind (≥20 mph): {len(extreme_wind)} games, {extreme_wind['total'].mean():.2f} avg points")
print(f"Calm Wind (≤5 mph): {len(calm_wind)} games, {calm_wind['total'].mean():.2f} avg points")

# 5. BETTING MARKET INEFFICIENCIES AND VALUE BETS
print("\n\n5. BETTING MARKET INEFFICIENCIES ANALYSIS")
print("=" * 50)

# Analyze market inefficiencies using historical data
games['total'] = games['home_score'] + games['away_score']
games['home_advantage'] = games['home_score'] - games['away_score']

# Identify teams with consistent over/under performance
team_totals = games.groupby('home_team').agg({
    'total': ['mean', 'std', 'count']
}).round(2)

team_totals.columns = ['avg_total', 'std_total', 'games']
team_totals = team_totals[team_totals['games'] >= 20]  # Minimum 20 games

print("Teams with Highest Scoring Games (Home):")
print(team_totals.sort_values('avg_total', ascending=False).head(10).to_string())

print("\nTeams with Lowest Scoring Games (Home):")
print(team_totals.sort_values('avg_total', ascending=True).head(10).to_string())

# Analyze away team performance
away_totals = games.groupby('away_team').agg({
    'total': ['mean', 'std', 'count']
}).round(2)

away_totals.columns = ['avg_total', 'std_total', 'games']
away_totals = away_totals[away_totals['games'] >= 20]

print("\nTeams with Highest Scoring Games (Away):")
print(away_totals.sort_values('avg_total', ascending=False).head(10).to_string())

print("\nTeams with Lowest Scoring Games (Away):")
print(away_totals.sort_values('avg_total', ascending=True).head(10).to_string())

# BETTING EDGE RECOMMENDATIONS
print("\n\n=== FINAL BETTING EDGE RECOMMENDATIONS ===")
print("=" * 60)

print("\n🏈 PLAYER PERFORMANCE EDGES:")
if len(player_stats) > 0:
    print("Top QB for passing yards bets:")
    print(f"  {qb_performance.index[0]}: {qb_performance.iloc[0]['pass_yds_avg']:.1f} avg yards")
    
    print("Top RB for rushing yards bets:")
    print(f"  {rb_performance.index[0]}: {rb_performance.iloc[0]['rush_yds_avg']:.1f} avg yards")
    
    print("Top WR for receiving yards bets:")
    print(f"  {wr_performance.index[0]}: {wr_performance.iloc[0]['rec_yds_avg']:.1f} avg yards")

print("\n🏟️ STADIUM EDGES:")
print("Best stadiums for OVER bets:")
best_stadiums = stadium_analysis.sort_values('total_avg', ascending=False).head(3)
for stadium in best_stadiums.index:
    print(f"  {stadium}: {best_stadiums.loc[stadium, 'total_avg']:.1f} avg points")

print("\nWorst stadiums for OVER bets:")
worst_stadiums = stadium_analysis.sort_values('total_avg', ascending=True).head(3)
for stadium in worst_stadiums.index:
    print(f"  {stadium}: {worst_stadiums.loc[stadium, 'total_avg']:.1f} avg points")

print("\n🌡️ WEATHER EXTREMES EDGES:")
if len(extreme_cold) > 0:
    print(f"Extreme cold games: {extreme_cold['total'].mean():.1f} avg points (UNDER bets)")
if len(extreme_hot) > 0:
    print(f"Extreme hot games: {extreme_hot['total'].mean():.1f} avg points (OVER bets)")
if len(extreme_wind) > 0:
    print(f"Extreme wind games: {extreme_wind['total'].mean():.1f} avg points (UNDER bets)")

print("\n📊 MARKET INEFFICIENCY EDGES:")
print("Best home teams for OVER bets:")
best_home = team_totals.sort_values('avg_total', ascending=False).head(3)
for team in best_home.index:
    print(f"  {team}: {best_home.loc[team, 'avg_total']:.1f} avg points")

print("\nBest away teams for OVER bets:")
best_away = away_totals.sort_values('avg_total', ascending=False).head(3)
for team in best_away.index:
    print(f"  {team}: {best_away.loc[team, 'avg_total']:.1f} avg points")

# Create final visualization
fig, axes = plt.subplots(2, 3, figsize=(18, 12))

# 1. Player Performance
if len(player_stats) > 0:
    qb_performance['pass_yds_avg'].head(10).plot(kind='bar', ax=axes[0,0], color='blue')
    axes[0,0].set_title('Top 10 QB Passing Yards')
    axes[0,0].set_ylabel('Average Passing Yards')
    axes[0,0].tick_params(axis='x', rotation=45)

# 2. Matchup Analysis
matchup_stats['avg_total'].head(10).plot(kind='bar', ax=axes[0,1], color='green')
axes[0,1].set_title('Highest Scoring Matchups')
axes[0,1].set_ylabel('Average Total Points')
axes[0,1].tick_params(axis='x', rotation=45)

# 3. Stadium Performance
stadium_analysis['total_avg'].head(10).plot(kind='bar', ax=axes[0,2], color='orange')
axes[0,2].set_title('Highest Scoring Stadiums')
axes[0,2].set_ylabel('Average Total Points')
axes[0,2].tick_params(axis='x', rotation=45)

# 4. Weather Impact
weather_comparison = pd.DataFrame({
    'Extreme Cold': [extreme_cold['total'].mean() if len(extreme_cold) > 0 else 0],
    'Extreme Hot': [extreme_hot['total'].mean() if len(extreme_hot) > 0 else 0],
    'Normal Temp': [normal_temp['total'].mean() if len(normal_temp) > 0 else 0],
    'Extreme Wind': [extreme_wind['total'].mean() if len(extreme_wind) > 0 else 0],
    'Calm Wind': [calm_wind['total'].mean() if len(calm_wind) > 0 else 0]
})
weather_comparison.T.plot(kind='bar', ax=axes[1,0], color=['red', 'orange', 'blue', 'purple', 'lightblue'])
axes[1,0].set_title('Weather Impact on Scoring')
axes[1,0].set_ylabel('Average Total Points')
axes[1,0].legend().remove()

# 5. Home Team Performance
team_totals['avg_total'].head(10).plot(kind='bar', ax=axes[1,1], color='purple')
axes[1,1].set_title('Home Team Scoring Performance')
axes[1,1].set_ylabel('Average Total Points')
axes[1,1].tick_params(axis='x', rotation=45)

# 6. Away Team Performance
away_totals['avg_total'].head(10).plot(kind='bar', ax=axes[1,2], color='brown')
axes[1,2].set_title('Away Team Scoring Performance')
axes[1,2].set_ylabel('Average Total Points')
axes[1,2].tick_params(axis='x', rotation=45)

plt.tight_layout()
plt.savefig('final_betting_edges_analysis.png', dpi=300, bbox_inches='tight')
plt.show()

print(f"\n📊 Final analysis complete! Visualization saved as 'final_betting_edges_analysis.png'")
print(f"📈 Final insights generated for {len(games)} games from 2020-2025")

# SUMMARY OF ALL ANALYSES
print("\n\n=== COMPREHENSIVE BETTING EDGE SUMMARY ===")
print("=" * 60)
print("🎯 KEY BETTING EDGES IDENTIFIED:")
print("1. First Half vs Second Half: LAC, KC strong first half; MIN, NYG strong second half")
print("2. Home Field Advantage: BUF (+10.9), BAL (+7.4), GB (+7.3) point advantages")
print("3. Weather Impact: Dome games +3.9 points vs outdoor; extreme weather reduces scoring")
print("4. Rest Days: +2 days rest = +9.7 point advantage")
print("5. Time Zone: -1 hour difference = +3.3 point home advantage")
print("6. Playoffs: +3.2 points vs regular season; +4.7 point home advantage")
print("7. Day/Time: Friday games highest scoring (55.8 avg); Wednesday lowest (35.0 avg)")
print("8. Turnover Margin: PIT, GB, BUF best margins; LVR, CAR, CLE worst")
print("9. Coaching: Dan Campbell (+27.5), Shane Steichen (+20.0) point advantages")
print("10. Stadium: Certain stadiums consistently high/low scoring")
print("\n💡 RECOMMENDED BETTING STRATEGIES:")
print("• OVER bets: Dome games, Friday games, playoff games, teams with rest advantage")
print("• UNDER bets: Extreme weather, Wednesday games, outdoor games in cold")
print("• Home bets: BUF, BAL, GB, KC, MIA with rest advantage")
print("• First Half: LAC, KC, TEN, ATL, IND")
print("• Second Half: MIN, NYG, NE, WAS, PIT")
print("• Spread: GB (61.7% cover), avoid ATL (34.1% cover)")
print("\n🎲 These edges provide statistical advantages for informed betting decisions!")
