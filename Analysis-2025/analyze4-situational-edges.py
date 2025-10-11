# Situational Betting Edge Analysis - 5 More NFL Analytics
# 1. Day of Week and Time Slot Performance Patterns
# 2. Travel Distance and Time Zone Impact
# 3. Injury Report Impact on Team Performance
# 4. Playoff vs Regular Season Performance Differences
# 5. Spread and Total Line Movement Analysis

import sqlite3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

conn = sqlite3.connect("data/nfl.db")
games = pd.read_sql("""
    SELECT game_id, season, CAST(week AS INT) as week, date, home_team, away_team, 
           home_score, away_score, roof, surface, temp, wind, away_rest, home_rest,
           stadium, game_type, pfr, weekday, gametime, spread_line, total_line
    FROM Games 
    WHERE season >= 2020 AND home_score IS NOT NULL AND away_score IS NOT NULL
""", conn)
conn.close()

print("=== SITUATIONAL BETTING EDGE ANALYSIS ===")
print(f"Analyzing {len(games)} games from 2020-2025")
print("=" * 60)

# 1. DAY OF WEEK AND TIME SLOT PERFORMANCE PATTERNS
print("\n1. DAY OF WEEK AND TIME SLOT ANALYSIS")
print("=" * 50)

# Analyze by day of week
games['total'] = games['home_score'] + games['away_score']
games['home_advantage'] = games['home_score'] - games['away_score']

day_analysis = games.groupby('weekday').agg({
    'total': ['mean', 'std', 'count'],
    'home_advantage': ['mean', 'std']
}).round(2)

day_analysis.columns = ['avg_total', 'std_total', 'games', 'avg_home_adv', 'std_home_adv']
print("Performance by Day of Week:")
print(day_analysis.to_string())

# Analyze by time slot
time_analysis = games.groupby('gametime').agg({
    'total': ['mean', 'std', 'count'],
    'home_advantage': ['mean', 'std']
}).round(2)

time_analysis.columns = ['avg_total', 'std_total', 'games', 'avg_home_adv', 'std_home_adv']
print("\nPerformance by Time Slot:")
print(time_analysis.to_string())

# 2. TRAVEL DISTANCE AND TIME ZONE IMPACT
print("\n\n2. TRAVEL DISTANCE AND TIME ZONE ANALYSIS")
print("=" * 50)

# Define time zones for teams
time_zones = {
    'ARI': 'MST', 'ATL': 'EST', 'BAL': 'EST', 'BUF': 'EST', 'CAR': 'EST', 'CHI': 'CST',
    'CIN': 'EST', 'CLE': 'EST', 'DAL': 'CST', 'DEN': 'MST', 'DET': 'EST', 'GB': 'CST',
    'HOU': 'CST', 'IND': 'EST', 'JAX': 'EST', 'KC': 'CST', 'LAC': 'PST', 'LAR': 'PST',
    'LVR': 'PST', 'MIA': 'EST', 'MIN': 'CST', 'NE': 'EST', 'NO': 'CST', 'NYG': 'EST',
    'NYJ': 'EST', 'PHI': 'EST', 'PIT': 'EST', 'SEA': 'PST', 'SF': 'PST', 'TB': 'EST',
    'TEN': 'CST', 'WAS': 'EST'
}

# Calculate time zone differences
games['home_tz'] = games['home_team'].map(time_zones)
games['away_tz'] = games['away_team'].map(time_zones)

# Define time zone differences
tz_differences = {
    'EST': {'CST': 1, 'MST': 2, 'PST': 3},
    'CST': {'EST': -1, 'MST': 1, 'PST': 2},
    'MST': {'EST': -2, 'CST': -1, 'PST': 1},
    'PST': {'EST': -3, 'CST': -2, 'MST': -1}
}

def get_tz_diff(home_tz, away_tz):
    if home_tz == away_tz:
        return 0
    return tz_differences.get(home_tz, {}).get(away_tz, 0)

games['tz_diff'] = games.apply(lambda x: get_tz_diff(x['home_tz'], x['away_tz']), axis=1)

# Analyze time zone impact
tz_analysis = games.groupby('tz_diff').agg({
    'total': ['mean', 'std', 'count'],
    'home_advantage': ['mean', 'std']
}).round(2)

tz_analysis.columns = ['avg_total', 'std_total', 'games', 'avg_home_adv', 'std_home_adv']
print("Performance by Time Zone Difference:")
print(tz_analysis.to_string())

# 3. INJURY REPORT IMPACT ON TEAM PERFORMANCE
print("\n\n3. INJURY REPORT IMPACT ANALYSIS")
print("=" * 50)

# Load injury data if available
try:
    injured_players = pd.read_csv("../Models/injured_players.csv")
    questionable_players = pd.read_csv("../Models/questionable_players.csv")
    print("Injury data found!")
    print(f"Injured players: {len(injured_players)}")
    print(f"Questionable players: {len(questionable_players)}")
except FileNotFoundError:
    print("No injury data available")
    injured_players = pd.DataFrame()
    questionable_players = pd.DataFrame()

# 4. PLAYOFF VS REGULAR SEASON PERFORMANCE DIFFERENCES
print("\n\n4. PLAYOFF VS REGULAR SEASON ANALYSIS")
print("=" * 50)

# Analyze regular season vs playoffs
regular_season = games[games['game_type'] == 'REG'].copy()
playoffs = games[games['game_type'] != 'REG'].copy()

if len(playoffs) > 0:
    reg_season_stats = regular_season.groupby('season').agg({
        'total': ['mean', 'std', 'count'],
        'home_advantage': ['mean', 'std']
    }).round(2)
    
    playoff_stats = playoffs.groupby('season').agg({
        'total': ['mean', 'std', 'count'],
        'home_advantage': ['mean', 'std']
    }).round(2)
    
    print("Regular Season Performance:")
    print(reg_season_stats.head().to_string())
    
    print("\nPlayoff Performance:")
    print(playoff_stats.head().to_string())
    
    print(f"\nRegular Season vs Playoffs:")
    print(f"Regular Season: {regular_season['total'].mean():.2f} avg points ({len(regular_season)} games)")
    print(f"Playoffs: {playoffs['total'].mean():.2f} avg points ({len(playoffs)} games)")
    print(f"Difference: {playoffs['total'].mean() - regular_season['total'].mean():.2f} points")
    
    print(f"\nHome Field Advantage:")
    print(f"Regular Season: {regular_season['home_advantage'].mean():.2f} points")
    print(f"Playoffs: {playoffs['home_advantage'].mean():.2f} points")
    print(f"Difference: {playoffs['home_advantage'].mean() - regular_season['home_advantage'].mean():.2f} points")
else:
    print("No playoff data available")

# 5. SPREAD AND TOTAL LINE MOVEMENT ANALYSIS
print("\n\n5. SPREAD AND TOTAL LINE MOVEMENT ANALYSIS")
print("=" * 50)

# Analyze spread and total line performance
games_with_lines = games.dropna(subset=['spread_line', 'total_line']).copy()

if len(games_with_lines) > 0:
    # Spread analysis
    games_with_lines['spread_result'] = games_with_lines['home_score'] - games_with_lines['away_score']
    games_with_lines['spread_cover'] = games_with_lines['spread_result'] > games_with_lines['spread_line']
    
    spread_analysis = games_with_lines.groupby('spread_line').agg({
        'spread_cover': ['mean', 'count'],
        'total': ['mean', 'std']
    }).round(3)
    
    spread_analysis.columns = ['cover_rate', 'games', 'avg_total', 'std_total']
    print("Spread Performance by Line:")
    print(spread_analysis.head(10).to_string())
    
    # Total analysis
    games_with_lines['total_cover'] = games_with_lines['total'] > games_with_lines['total_line']
    
    total_analysis = games_with_lines.groupby('total_line').agg({
        'total_cover': ['mean', 'count'],
        'total': ['mean', 'std']
    }).round(3)
    
    total_analysis.columns = ['over_rate', 'games', 'avg_total', 'std_total']
    print("\nTotal Performance by Line:")
    print(total_analysis.head(10).to_string())
    
    # Home team spread performance
    home_spread = games_with_lines.groupby('home_team').agg({
        'spread_cover': ['mean', 'count'],
        'total': ['mean', 'std']
    }).round(3)
    
    home_spread.columns = ['cover_rate', 'games', 'avg_total', 'std_total']
    home_spread = home_spread.sort_values('cover_rate', ascending=False)
    
    print("\nHome Team Spread Performance:")
    print(home_spread.head(10).to_string())
    
    print("\nHome Team Spread Performance (Worst):")
    print(home_spread.tail(10).to_string())
else:
    print("No spread/total line data available")

# BETTING EDGE RECOMMENDATIONS
print("\n\n=== SITUATIONAL BETTING EDGE RECOMMENDATIONS ===")
print("=" * 60)

print("\n📅 DAY OF WEEK EDGES:")
best_day = day_analysis.sort_values('avg_total', ascending=False).index[0]
worst_day = day_analysis.sort_values('avg_total', ascending=True).index[0]
print(f"Best day for OVER bets: {best_day} ({day_analysis.loc[best_day, 'avg_total']:.1f} avg points)")
print(f"Worst day for OVER bets: {worst_day} ({day_analysis.loc[worst_day, 'avg_total']:.1f} avg points)")

print("\n🕐 TIME SLOT EDGES:")
best_time = time_analysis.sort_values('avg_total', ascending=False).index[0]
worst_time = time_analysis.sort_values('avg_total', ascending=True).index[0]
print(f"Best time for OVER bets: {best_time} ({time_analysis.loc[best_time, 'avg_total']:.1f} avg points)")
print(f"Worst time for OVER bets: {worst_time} ({time_analysis.loc[worst_time, 'avg_total']:.1f} avg points)")

print("\n🌍 TIME ZONE EDGES:")
if len(tz_analysis) > 0:
    best_tz = tz_analysis.sort_values('avg_home_adv', ascending=False).index[0]
    worst_tz = tz_analysis.sort_values('avg_home_adv', ascending=True).index[0]
    print(f"Best time zone advantage: {best_tz} hours ({tz_analysis.loc[best_tz, 'avg_home_adv']:.1f} point advantage)")
    print(f"Worst time zone advantage: {worst_tz} hours ({tz_analysis.loc[worst_tz, 'avg_home_adv']:.1f} point advantage)")

print("\n🏆 PLAYOFF EDGES:")
if len(playoffs) > 0:
    print(f"Playoffs score {playoffs['total'].mean() - regular_season['total'].mean():.1f} more points than regular season")
    print(f"Playoff home field advantage: {playoffs['home_advantage'].mean():.1f} vs regular season: {regular_season['home_advantage'].mean():.1f}")

print("\n📊 SPREAD EDGES:")
if len(games_with_lines) > 0:
    best_spread_team = home_spread.index[0]
    worst_spread_team = home_spread.index[-1]
    print(f"Best home team to bet on: {best_spread_team} ({home_spread.loc[best_spread_team, 'cover_rate']:.1%} cover rate)")
    print(f"Worst home team to bet on: {worst_spread_team} ({home_spread.loc[worst_spread_team, 'cover_rate']:.1%} cover rate)")

# Create situational visualization
fig, axes = plt.subplots(2, 3, figsize=(18, 12))

# 1. Day of Week Performance
day_analysis['avg_total'].plot(kind='bar', ax=axes[0,0], color='skyblue')
axes[0,0].set_title('Average Total Points by Day of Week')
axes[0,0].set_ylabel('Average Total Points')
axes[0,0].tick_params(axis='x', rotation=45)

# 2. Time Slot Performance
time_analysis['avg_total'].plot(kind='bar', ax=axes[0,1], color='lightgreen')
axes[0,1].set_title('Average Total Points by Time Slot')
axes[0,1].set_ylabel('Average Total Points')
axes[0,1].tick_params(axis='x', rotation=45)

# 3. Time Zone Impact
if len(tz_analysis) > 0:
    tz_analysis['avg_home_adv'].plot(kind='bar', ax=axes[0,2], color='orange')
    axes[0,2].set_title('Home Field Advantage by Time Zone Difference')
    axes[0,2].set_ylabel('Average Point Advantage')
    axes[0,2].tick_params(axis='x', rotation=45)

# 4. Regular Season vs Playoffs
if len(playoffs) > 0:
    reg_vs_playoff = pd.DataFrame({
        'Regular Season': [regular_season['total'].mean()],
        'Playoffs': [playoffs['total'].mean()]
    })
    reg_vs_playoff.T.plot(kind='bar', ax=axes[1,0], color=['blue', 'red'])
    axes[1,0].set_title('Regular Season vs Playoffs')
    axes[1,0].set_ylabel('Average Total Points')
    axes[1,0].legend().remove()

# 5. Spread Performance
if len(games_with_lines) > 0:
    home_spread['cover_rate'].head(10).plot(kind='bar', ax=axes[1,1], color='purple')
    axes[1,1].set_title('Home Team Spread Cover Rate')
    axes[1,1].set_ylabel('Cover Rate')
    axes[1,1].tick_params(axis='x', rotation=45)

# 6. Total Line Performance
if len(games_with_lines) > 0:
    total_analysis['over_rate'].head(10).plot(kind='bar', ax=axes[1,2], color='brown')
    axes[1,2].set_title('Over Rate by Total Line')
    axes[1,2].set_ylabel('Over Rate')
    axes[1,2].tick_params(axis='x', rotation=45)

plt.tight_layout()
plt.savefig('situational_betting_edges_analysis.png', dpi=300, bbox_inches='tight')
plt.show()

print(f"\n📊 Situational analysis complete! Visualization saved as 'situational_betting_edges_analysis.png'")
print(f"📈 Situational insights generated for {len(games)} games from 2020-2025")
