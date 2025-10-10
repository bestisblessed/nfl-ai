# Betting Edge Analysis - 5 Advanced NFL Analytics
# 1. First Half vs Second Half Team Performance Trends
# 2. Home Field Advantage by Team and Stadium Type
# 3. Weather Impact on Scoring (Temperature, Wind, Dome vs Outdoor)
# 4. Rest Days Impact on Team Performance
# 5. Divisional Rivalry Performance Patterns

import sqlite3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

conn = sqlite3.connect("data/nfl.db")
games = pd.read_sql("""
    SELECT game_id, season, CAST(week AS INT) as week, date, home_team, away_team, 
           home_score, away_score, roof, surface, temp, wind, away_rest, home_rest,
           stadium, game_type, pfr
    FROM Games 
    WHERE season >= 2020 AND home_score IS NOT NULL AND away_score IS NOT NULL
""", conn)
conn.close()

print("=== BETTING EDGE ANALYSIS ===")
print(f"Analyzing {len(games)} games from 2020-2025")
print("=" * 60)
print("\n1. FIRST HALF vs SECOND HALF TEAM PERFORMANCE")
print("=" * 50)
box_scores = pd.read_csv("data/all_box_scores.csv")
box_scores['first_half'] = box_scores['1'].fillna(0) + box_scores['2'].fillna(0)
box_scores['second_half'] = box_scores['3'].fillna(0) + box_scores['4'].fillna(0)
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
games_with_halves = games.merge(box_scores[['pfr_id', 'team_code', 'first_half', 'second_half']], 
                               left_on='pfr', right_on='pfr_id', how='inner')
if len(games_with_halves) > 0:
    home_first_half = games_with_halves[games_with_halves['home_team'] == games_with_halves['team_code']].copy()
    away_first_half = games_with_halves[games_with_halves['away_team'] == games_with_halves['team_code']].copy()
    home_first_half['team'] = home_first_half['home_team']
    home_first_half['first_half_pts'] = home_first_half['first_half']
    home_first_half['second_half_pts'] = home_first_half['second_half']
    away_first_half['team'] = away_first_half['away_team']
    away_first_half['first_half_pts'] = away_first_half['first_half']
    away_first_half['second_half_pts'] = away_first_half['second_half']
    halves_analysis = pd.concat([
        home_first_half[['team', 'first_half_pts', 'second_half_pts', 'season']],
        away_first_half[['team', 'first_half_pts', 'second_half_pts', 'season']]
    ], ignore_index=True)
    team_halves = halves_analysis.groupby('team').agg({
        'first_half_pts': ['mean', 'std', 'count'],
        'second_half_pts': ['mean', 'std', 'count']
    }).round(2)
    team_halves.columns = ['fh_avg', 'fh_std', 'fh_games', 'sh_avg', 'sh_std', 'sh_games']
    team_halves['fh_vs_sh_diff'] = team_halves['fh_avg'] - team_halves['sh_avg']
    team_halves['halves_ratio'] = team_halves['fh_avg'] / team_halves['sh_avg']
    team_halves = team_halves.sort_values('fh_vs_sh_diff', ascending=False)
    print("Teams with strongest FIRST HALF performance:")
    print(team_halves.head(10)[['fh_avg', 'sh_avg', 'fh_vs_sh_diff', 'halves_ratio']].to_string())
    print("\nTeams with strongest SECOND HALF performance:")
    print(team_halves.sort_values('fh_vs_sh_diff', ascending=True).head(10)[['fh_avg', 'sh_avg', 'fh_vs_sh_diff', 'halves_ratio']].to_string())
else:
    print("No box score data available for first half analysis")
    team_halves = pd.DataFrame()
print("\n\n2. HOME FIELD ADVANTAGE BY TEAM AND STADIUM TYPE")
print("=" * 50)
home_games = games[['home_team', 'home_score', 'away_score', 'roof', 'stadium']].copy()
home_games['home_advantage'] = home_games['home_score'] - home_games['away_score']
home_games['team'] = home_games['home_team']
home_advantage_by_team = home_games.groupby('team')['home_advantage'].agg(['mean', 'std', 'count']).round(2)
home_advantage_by_team = home_advantage_by_team.sort_values('mean', ascending=False)
print("Teams with strongest HOME FIELD ADVANTAGE:")
print(home_advantage_by_team.head(10).to_string())
home_advantage_by_roof = home_games.groupby('roof')['home_advantage'].agg(['mean', 'std', 'count']).round(2)
print("\nHome Field Advantage by Stadium Type:")
print(home_advantage_by_roof.to_string())
print("\n\n3. WEATHER IMPACT ON SCORING")
print("=" * 50)
weather_games = games.dropna(subset=['temp', 'wind']).copy()
weather_games['total'] = weather_games['home_score'] + weather_games['away_score']
temp_bins = pd.cut(weather_games['temp'], bins=5, labels=['Very Cold', 'Cold', 'Moderate', 'Warm', 'Hot'])
weather_games['temp_category'] = temp_bins
temp_scoring = weather_games.groupby('temp_category')['total'].agg(['mean', 'std', 'count']).round(2)
print("Scoring by Temperature:")
print(temp_scoring.to_string())
wind_bins = pd.cut(weather_games['wind'], bins=4, labels=['Calm', 'Light', 'Moderate', 'Strong'])
weather_games['wind_category'] = wind_bins
wind_scoring = weather_games.groupby('wind_category')['total'].agg(['mean', 'std', 'count']).round(2)
print("\nScoring by Wind Conditions:")
print(wind_scoring.to_string())
dome_games = games[games['roof'] == 'dome'].copy()
outdoor_games = games[games['roof'] == 'outdoors'].copy()
dome_games['total'] = dome_games['home_score'] + dome_games['away_score']
outdoor_games['total'] = outdoor_games['home_score'] + outdoor_games['away_score']
print(f"\nDome vs Outdoor Scoring:")
print(f"Dome games: {dome_games['total'].mean():.2f} avg points ({len(dome_games)} games)")
print(f"Outdoor games: {outdoor_games['total'].mean():.2f} avg points ({len(outdoor_games)} games)")
print(f"Difference: {dome_games['total'].mean() - outdoor_games['total'].mean():.2f} points")
print("\n\n4. REST DAYS IMPACT ON TEAM PERFORMANCE")
print("=" * 50)
rest_analysis = games[['home_team', 'away_team', 'home_score', 'away_score', 'home_rest', 'away_rest']].copy()
rest_analysis['home_advantage'] = rest_analysis['home_score'] - rest_analysis['away_score']
rest_analysis['rest_difference'] = rest_analysis['home_rest'] - rest_analysis['away_rest']
rest_bins = pd.cut(rest_analysis['rest_difference'], bins=7, labels=['-3+ days', '-2 days', '-1 day', 'Equal', '+1 day', '+2 days', '+3+ days'])
rest_analysis['rest_category'] = rest_bins
rest_impact = rest_analysis.groupby('rest_category')['home_advantage'].agg(['mean', 'std', 'count']).round(2)
print("Home Field Advantage by Rest Day Difference:")
print(rest_impact.to_string())
print("\n\n5. DIVISIONAL RIVALRY PERFORMANCE PATTERNS")
print("=" * 50)
divisions = {
    'AFC East': ['BUF', 'MIA', 'NE', 'NYJ'],
    'AFC North': ['BAL', 'CIN', 'CLE', 'PIT'],
    'AFC South': ['HOU', 'IND', 'JAX', 'TEN'],
    'AFC West': ['DEN', 'KC', 'LAC', 'LVR'],
    'NFC East': ['DAL', 'NYG', 'PHI', 'WAS'],
    'NFC North': ['CHI', 'DET', 'GB', 'MIN'],
    'NFC South': ['ATL', 'CAR', 'NO', 'TB'],
    'NFC West': ['ARI', 'LAR', 'SF', 'SEA']
}
team_to_division = {}
for div, teams in divisions.items():
    for team in teams:
        team_to_division[team] = div
games['home_division'] = games['home_team'].map(team_to_division)
games['away_division'] = games['away_team'].map(team_to_division)
games['is_divisional'] = games['home_division'] == games['away_division']
divisional_games = games[games['is_divisional'] == True].copy()
non_divisional_games = games[games['is_divisional'] == False].copy()
divisional_games['total'] = divisional_games['home_score'] + divisional_games['away_score']
non_divisional_games['total'] = non_divisional_games['home_score'] + non_divisional_games['away_score']
print(f"Divisional vs Non-Divisional Scoring:")
print(f"Divisional games: {divisional_games['total'].mean():.2f} avg points ({len(divisional_games)} games)")
print(f"Non-divisional games: {non_divisional_games['total'].mean():.2f} avg points ({len(non_divisional_games)} games)")
print(f"Difference: {divisional_games['total'].mean() - non_divisional_games['total'].mean():.2f} points")
divisional_games['home_advantage'] = divisional_games['home_score'] - divisional_games['away_score']
non_divisional_games['home_advantage'] = non_divisional_games['home_score'] - non_divisional_games['away_score']
print(f"\nHome Field Advantage:")
print(f"Divisional games: {divisional_games['home_advantage'].mean():.2f} points")
print(f"Non-divisional games: {non_divisional_games['home_advantage'].mean():.2f} points")
print("\n\n=== BETTING EDGE RECOMMENDATIONS ===")
print("=" * 60)
print("\n🎯 FIRST HALF BETTING EDGES:")
if len(team_halves) > 0:
    fh_strong = team_halves.head(5)
    sh_strong = team_halves.sort_values('fh_vs_sh_diff', ascending=True).head(5)
    print("Teams to BET FIRST HALF OVER with:")
    for team in fh_strong.index:
        print(f"  {team}: {fh_strong.loc[team, 'fh_avg']:.1f} avg first half points")
    print("\nTeams to BET SECOND HALF OVER with:")
    for team in sh_strong.index:
        print(f"  {team}: {sh_strong.loc[team, 'sh_avg']:.1f} avg second half points")
else:
    print("No first half data available for analysis")
print("\n🏠 HOME FIELD ADVANTAGE EDGES:")
hfa_strong = home_advantage_by_team.head(5)
print("Teams with strongest home field advantage:")
for team in hfa_strong.index:
    print(f"  {team}: +{hfa_strong.loc[team, 'mean']:.1f} point advantage")
print("\n🌤️ WEATHER EDGES:")
print(f"Dome games score {dome_games['total'].mean() - outdoor_games['total'].mean():.1f} more points than outdoor games")
print("Consider OVER bets in dome games, UNDER bets in extreme weather")
print("\n😴 REST DAY EDGES:")
rest_strong = rest_impact.sort_values('mean', ascending=False).head(3)
print("Rest day advantages:")
for rest_cat in rest_strong.index:
    print(f"  {rest_cat}: +{rest_strong.loc[rest_cat, 'mean']:.1f} point advantage")
print("\n🏆 DIVISIONAL RIVALRY EDGES:")
print(f"Divisional games score {divisional_games['total'].mean() - non_divisional_games['total'].mean():.1f} more points")
print("Consider OVER bets in divisional matchups")
fig, axes = plt.subplots(2, 3, figsize=(18, 12))
if len(team_halves) > 0:
    team_halves['fh_vs_sh_diff'].head(10).plot(kind='bar', ax=axes[0,0], color='skyblue')
    axes[0,0].set_title('First Half vs Second Half Performance')
    axes[0,0].set_ylabel('Points Difference (FH - SH)')
    axes[0,0].tick_params(axis='x', rotation=45)
else:
    axes[0,0].text(0.5, 0.5, 'No First Half Data Available', ha='center', va='center', transform=axes[0,0].transAxes)
    axes[0,0].set_title('First Half vs Second Half Performance')
home_advantage_by_team['mean'].head(10).plot(kind='bar', ax=axes[0,1], color='lightgreen')
axes[0,1].set_title('Home Field Advantage by Team')
axes[0,1].set_ylabel('Average Point Advantage')
axes[0,1].tick_params(axis='x', rotation=45)
temp_scoring['mean'].plot(kind='bar', ax=axes[0,2], color='orange')
axes[0,2].set_title('Scoring by Temperature')
axes[0,2].set_ylabel('Average Total Points')
axes[0,2].tick_params(axis='x', rotation=45)
rest_impact['mean'].plot(kind='bar', ax=axes[1,0], color='purple')
axes[1,0].set_title('Home Advantage by Rest Days')
axes[1,0].set_ylabel('Average Point Advantage')
axes[1,0].tick_params(axis='x', rotation=45)
dome_vs_outdoor = pd.DataFrame({
    'Dome': [dome_games['total'].mean()],
    'Outdoor': [outdoor_games['total'].mean()]
})
dome_vs_outdoor.T.plot(kind='bar', ax=axes[1,1], color=['red', 'blue'])
axes[1,1].set_title('Dome vs Outdoor Scoring')
axes[1,1].set_ylabel('Average Total Points')
axes[1,1].legend().remove()
div_vs_non_div = pd.DataFrame({
    'Divisional': [divisional_games['total'].mean()],
    'Non-Divisional': [non_divisional_games['total'].mean()]
})
div_vs_non_div.T.plot(kind='bar', ax=axes[1,2], color=['green', 'gray'])
axes[1,2].set_title('Divisional vs Non-Divisional')
axes[1,2].set_ylabel('Average Total Points')
axes[1,2].legend().remove()
plt.tight_layout()
plt.savefig('betting_edges_analysis.png', dpi=300, bbox_inches='tight')
plt.show()
print(f"\n📊 Analysis complete! Visualization saved as 'betting_edges_analysis.png'")
print(f"📈 Key insights generated for {len(games)} games from 2020-2025")
