# Advanced Betting Edge Analysis - 5 More NFL Analytics
# 1. Quarter-by-Quarter Scoring Patterns and Momentum Shifts
# 2. Red Zone Efficiency and Goal Line Performance
# 3. Turnover Margin Impact on Game Outcomes
# 4. Time of Possession and Pace of Play Analysis
# 5. Coaching Changes and Team Performance Trends

import sqlite3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

conn = sqlite3.connect("data/nfl.db")
games = pd.read_sql("""
    SELECT game_id, season, CAST(week AS INT) as week, date, home_team, away_team, 
           home_score, away_score, roof, surface, temp, wind, away_rest, home_rest,
           stadium, game_type, pfr, away_coach, home_coach
    FROM Games 
    WHERE season >= 2020 AND home_score IS NOT NULL AND away_score IS NOT NULL
""", conn)
conn.close()

# Load additional datasets
box_scores = pd.read_csv("data/all_box_scores.csv")
team_game_logs = pd.read_csv("data/all_team_game_logs.csv")
player_stats = pd.read_csv("data/all_passing_rushing_receiving.csv")

print("=== ADVANCED BETTING EDGE ANALYSIS ===")
print(f"Analyzing {len(games)} games from 2020-2025")
print("=" * 60)

# 1. QUARTER-BY-QUARTER SCORING PATTERNS AND MOMENTUM SHIFTS
print("\n1. QUARTER-BY-QUARTER SCORING PATTERNS")
print("=" * 50)

# Process box scores for quarter analysis
box_scores['pfr_id'] = box_scores['URL'].str.extract(r'/([^/]+)\.htm$')[0]
team_mapping = {
    'Arizona Cardinals': 'ARI', 'Atlanta Falcons': 'ATL', 'Baltimore Ravens': 'BAL',
    'Buffalo Bills': 'BUF', 'Carolina Panthers': 'CAR', 'Chicago Bears': 'CHI',
    'Cincinnati Bengals': 'CIN', 'Cleveland Browns': 'CLE', 'Dallas Cowboys': 'DAL',
    'Denver Broncos': 'DEN', 'Detroit Lions': 'DET', 'Green Bay Packers': 'GB',
    'Houston Texans': 'HOU', 'Indianapolis Colts': 'IND', 'Jacksonville Jaguars': 'JAX',
    'Kansas City Chiefs': 'KC', 'Los Angeles Chargers': 'LAC', 'Los Angeles Rams': 'LAR',
    'Las Vegas Raiders': 'LVR', 'Miami Dolphins': 'MIA', 'Minnesota Vikings': 'MIN',
    'New England Patriots': 'NE', 'New Orleans Saints': 'NO', 'New York Giants': 'NYG',
    'New York Jets': 'NYJ', 'Philadelphia Eagles': 'PHI', 'Pittsburgh Steelers': 'PIT',
    'Seattle Seahawks': 'SEA', 'San Francisco 49ers': 'SF', 'Tampa Bay Buccaneers': 'TB',
    'Tennessee Titans': 'TEN', 'Washington Commanders': 'WAS', 'Washington Football Team': 'WAS'
}
box_scores['team_code'] = box_scores['Team'].map(team_mapping)

# Merge with games data
games_with_quarters = games.merge(box_scores[['pfr_id', 'team_code', '1', '2', '3', '4']], 
                                 left_on='pfr', right_on='pfr_id', how='inner')

if len(games_with_quarters) > 0:
    # Analyze quarter-by-quarter patterns
    quarter_analysis = []
    for _, game in games_with_quarters.iterrows():
        # Home team quarters
        quarter_analysis.append({
            'team': game['home_team'],
            'q1': game['1'] if game['home_team'] == game['team_code'] else 0,
            'q2': game['2'] if game['home_team'] == game['team_code'] else 0,
            'q3': game['3'] if game['home_team'] == game['team_code'] else 0,
            'q4': game['4'] if game['home_team'] == game['team_code'] else 0,
            'season': game['season']
        })
        # Away team quarters
        quarter_analysis.append({
            'team': game['away_team'],
            'q1': game['1'] if game['away_team'] == game['team_code'] else 0,
            'q2': game['2'] if game['away_team'] == game['team_code'] else 0,
            'q3': game['3'] if game['away_team'] == game['team_code'] else 0,
            'q4': game['4'] if game['away_team'] == game['team_code'] else 0,
            'season': game['season']
        })
    
    quarter_df = pd.DataFrame(quarter_analysis)
    quarter_avg = quarter_df.groupby('team')[['q1', 'q2', 'q3', 'q4']].mean().round(2)
    
    # Find teams with strong quarter patterns
    quarter_avg['first_half'] = quarter_avg['q1'] + quarter_avg['q2']
    quarter_avg['second_half'] = quarter_avg['q3'] + quarter_avg['q4']
    quarter_avg['halves_diff'] = quarter_avg['first_half'] - quarter_avg['second_half']
    
    print("Teams with strongest FIRST HALF quarter performance:")
    print(quarter_avg.sort_values('first_half', ascending=False).head(10)[['q1', 'q2', 'first_half']].to_string())
    
    print("\nTeams with strongest SECOND HALF quarter performance:")
    print(quarter_avg.sort_values('second_half', ascending=False).head(10)[['q3', 'q4', 'second_half']].to_string())
    
    print("\nTeams with biggest HALF-to-HALF differences:")
    print(quarter_avg.sort_values('halves_diff', ascending=False).head(10)[['first_half', 'second_half', 'halves_diff']].to_string())
else:
    print("No quarter data available for analysis")
    quarter_avg = pd.DataFrame()

# 2. RED ZONE EFFICIENCY AND GOAL LINE PERFORMANCE
print("\n\n2. RED ZONE EFFICIENCY ANALYSIS")
print("=" * 50)

# Load red zone data if available
try:
    redzone_data = pd.read_csv("data/all_redzone.csv")
    print("Red zone data found!")
    print(f"Red zone records: {len(redzone_data)}")
    print("Sample red zone data:")
    print(redzone_data.head())
except FileNotFoundError:
    print("No red zone data available")
    redzone_data = pd.DataFrame()

# 3. TURNOVER MARGIN IMPACT ON GAME OUTCOMES
print("\n\n3. TURNOVER MARGIN IMPACT ANALYSIS")
print("=" * 50)

# Analyze turnover impact using team game logs
if len(team_game_logs) > 0:
    # Merge team game logs with games data
    home_logs = team_game_logs.merge(games[['game_id', 'home_team', 'away_team', 'home_score', 'away_score']], 
                                    on='game_id', how='inner')
    
    # Calculate turnover margins
    turnover_analysis = []
    for _, game in home_logs.iterrows():
        # Home team perspective
        turnover_analysis.append({
            'team': game['home_team'],
            'turnovers_forced': game.get('away_pass_int', 0) + game.get('away_fumbles', 0),
            'turnovers_lost': game.get('home_pass_int', 0) + game.get('home_fumbles', 0),
            'score_diff': game['home_score'] - game['away_score'],
            'game_id': game['game_id']
        })
        # Away team perspective
        turnover_analysis.append({
            'team': game['away_team'],
            'turnovers_forced': game.get('home_pass_int', 0) + game.get('home_fumbles', 0),
            'turnovers_lost': game.get('away_pass_int', 0) + game.get('away_fumbles', 0),
            'score_diff': game['away_score'] - game['home_score'],
            'game_id': game['game_id']
        })
    
    turnover_df = pd.DataFrame(turnover_analysis)
    turnover_df['turnover_margin'] = turnover_df['turnovers_forced'] - turnover_df['turnovers_lost']
    
    # Analyze turnover impact
    turnover_impact = turnover_df.groupby('turnover_margin')['score_diff'].agg(['mean', 'std', 'count']).round(2)
    print("Turnover Margin Impact on Score Differential:")
    print(turnover_impact.to_string())
    
    # Team turnover efficiency
    team_turnover = turnover_df.groupby('team')['turnover_margin'].agg(['mean', 'std', 'count']).round(2)
    team_turnover = team_turnover.sort_values('mean', ascending=False)
    print("\nTeams with best turnover margins:")
    print(team_turnover.head(10).to_string())
    
    print("\nTeams with worst turnover margins:")
    print(team_turnover.tail(10).to_string())
else:
    print("No team game logs available for turnover analysis")
    turnover_df = pd.DataFrame()

# 4. TIME OF POSSESSION AND PACE OF PLAY ANALYSIS
print("\n\n4. TIME OF POSSESSION AND PACE ANALYSIS")
print("=" * 50)

# Analyze pace of play using scoring patterns
games['total'] = games['home_score'] + games['away_score']
games['margin'] = abs(games['home_score'] - games['away_score'])

# Pace analysis by game type
pace_analysis = games.groupby(['season', 'week']).agg({
    'total': ['mean', 'std', 'count'],
    'margin': ['mean', 'std']
}).round(2)

pace_analysis.columns = ['avg_total', 'std_total', 'games', 'avg_margin', 'std_margin']
print("Pace of Play by Season and Week:")
print(pace_analysis.head(10).to_string())

# High-scoring vs low-scoring game analysis
high_scoring = games[games['total'] >= 50].copy()
low_scoring = games[games['total'] <= 35].copy()

print(f"\nHigh-scoring games (50+ points): {len(high_scoring)} games")
print(f"Low-scoring games (35- points): {len(low_scoring)} games")

if len(high_scoring) > 0 and len(low_scoring) > 0:
    print(f"High-scoring avg margin: {high_scoring['margin'].mean():.2f}")
    print(f"Low-scoring avg margin: {low_scoring['margin'].mean():.2f}")

# 5. COACHING CHANGES AND TEAM PERFORMANCE TRENDS
print("\n\n5. COACHING CHANGES AND PERFORMANCE TRENDS")
print("=" * 50)

# Analyze coaching impact
coaching_analysis = games.groupby(['home_coach', 'season']).agg({
    'home_score': ['mean', 'count'],
    'away_score': ['mean']
}).round(2)

coaching_analysis.columns = ['home_avg', 'games', 'away_avg']
coaching_analysis['home_advantage'] = coaching_analysis['home_avg'] - coaching_analysis['away_avg']
coaching_analysis = coaching_analysis.sort_values('home_advantage', ascending=False)

print("Coaches with strongest home field advantage:")
print(coaching_analysis.head(10).to_string())

# Team performance trends by season
team_trends = games.groupby(['home_team', 'season']).agg({
    'home_score': ['mean', 'count'],
    'away_score': ['mean']
}).round(2)

team_trends.columns = ['home_avg', 'games', 'away_avg']
team_trends['home_advantage'] = team_trends['home_avg'] - team_trends['away_avg']

# Find teams with improving/declining trends
team_season_trends = []
for team in team_trends.index.get_level_values(0).unique():
    team_data = team_trends.loc[team]
    if len(team_data) >= 3:  # At least 3 seasons of data
        trend = team_data['home_advantage'].values
        if len(trend) >= 3:
            recent_avg = trend[-2:].mean()  # Last 2 seasons
            early_avg = trend[:2].mean()   # First 2 seasons
            improvement = recent_avg - early_avg
            team_season_trends.append({
                'team': team,
                'improvement': improvement,
                'recent_advantage': recent_avg,
                'early_advantage': early_avg
            })

trend_df = pd.DataFrame(team_season_trends).sort_values('improvement', ascending=False)
print("\nTeams with biggest home field advantage improvement:")
print(trend_df.head(10).to_string())

print("\nTeams with biggest home field advantage decline:")
print(trend_df.tail(10).to_string())

# BETTING EDGE RECOMMENDATIONS
print("\n\n=== ADVANCED BETTING EDGE RECOMMENDATIONS ===")
print("=" * 60)

print("\n🎯 QUARTER-BY-QUARTER EDGES:")
if len(quarter_avg) > 0:
    first_half_strong = quarter_avg.sort_values('first_half', ascending=False).head(5)
    second_half_strong = quarter_avg.sort_values('second_half', ascending=False).head(5)
    
    print("Teams to BET FIRST HALF OVER with:")
    for team in first_half_strong.index:
        print(f"  {team}: {first_half_strong.loc[team, 'first_half']:.1f} avg first half points")
    
    print("\nTeams to BET SECOND HALF OVER with:")
    for team in second_half_strong.index:
        print(f"  {team}: {second_half_strong.loc[team, 'second_half']:.1f} avg second half points")

print("\n🔄 TURNOVER EDGES:")
if len(turnover_df) > 0:
    turnover_strong = team_turnover.head(5)
    print("Teams with best turnover margins:")
    for team in turnover_strong.index:
        print(f"  {team}: +{turnover_strong.loc[team, 'mean']:.1f} turnover margin")

print("\n⚡ PACE OF PLAY EDGES:")
print(f"High-scoring games (50+): {len(high_scoring)} games")
print(f"Low-scoring games (35-): {len(low_scoring)} games")
if len(high_scoring) > 0 and len(low_scoring) > 0:
    print(f"High-scoring games have {high_scoring['margin'].mean() - low_scoring['margin'].mean():.1f} point larger margins")

print("\n👨‍💼 COACHING EDGES:")
coaching_strong = coaching_analysis.head(5)
print("Coaches with strongest home field advantage:")
for coach in coaching_strong.index:
    print(f"  {coach[0]}: +{coaching_strong.loc[coach, 'home_advantage']:.1f} point advantage")

print("\n📈 TREND EDGES:")
if len(trend_df) > 0:
    improving_teams = trend_df.head(5)
    print("Teams with improving home field advantage:")
    for _, team in improving_teams.iterrows():
        print(f"  {team['team']}: +{team['improvement']:.1f} point improvement")

# Create advanced visualization
fig, axes = plt.subplots(2, 3, figsize=(18, 12))

# 1. Quarter Performance
if len(quarter_avg) > 0:
    quarter_avg[['q1', 'q2', 'q3', 'q4']].head(10).plot(kind='bar', ax=axes[0,0], stacked=True)
    axes[0,0].set_title('Quarter-by-Quarter Scoring by Team')
    axes[0,0].set_ylabel('Average Points per Quarter')
    axes[0,0].tick_params(axis='x', rotation=45)

# 2. Turnover Impact
if len(turnover_df) > 0:
    turnover_impact['mean'].plot(kind='bar', ax=axes[0,1], color='red')
    axes[0,1].set_title('Turnover Margin Impact on Score Differential')
    axes[0,1].set_ylabel('Average Score Differential')
    axes[0,1].tick_params(axis='x', rotation=45)

# 3. Pace of Play
pace_analysis['avg_total'].plot(kind='line', ax=axes[0,2], marker='o')
axes[0,2].set_title('Pace of Play Trends by Season')
axes[0,2].set_ylabel('Average Total Points')
axes[0,2].tick_params(axis='x', rotation=45)

# 4. Team Turnover Margins
if len(turnover_df) > 0:
    team_turnover['mean'].head(10).plot(kind='bar', ax=axes[1,0], color='green')
    axes[1,0].set_title('Team Turnover Margins')
    axes[1,0].set_ylabel('Average Turnover Margin')
    axes[1,0].tick_params(axis='x', rotation=45)

# 5. Coaching Impact
coaching_analysis['home_advantage'].head(10).plot(kind='bar', ax=axes[1,1], color='purple')
axes[1,1].set_title('Coaching Home Field Advantage')
axes[1,1].set_ylabel('Average Point Advantage')
axes[1,1].tick_params(axis='x', rotation=45)

# 6. Team Trends
if len(trend_df) > 0:
    trend_df['improvement'].head(10).plot(kind='bar', ax=axes[1,2], color='orange')
    axes[1,2].set_title('Team Home Field Advantage Trends')
    axes[1,2].set_ylabel('Improvement in Point Advantage')
    axes[1,2].tick_params(axis='x', rotation=45)

plt.tight_layout()
plt.savefig('advanced_betting_edges_analysis.png', dpi=300, bbox_inches='tight')
plt.show()

print(f"\n📊 Advanced analysis complete! Visualization saved as 'advanced_betting_edges_analysis.png'")
print(f"📈 Advanced insights generated for {len(games)} games from 2020-2025")
