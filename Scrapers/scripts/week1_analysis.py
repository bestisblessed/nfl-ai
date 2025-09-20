#!/usr/bin/env python3
"""
Week 1 2025 NFL Data Analysis and Visualization
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# Set up plotting style
plt.style.use('default')
sns.set_palette("husl")

def load_data():
    """Load the NFL data"""
    games = pd.read_csv('data/games.csv')
    passing_rushing_receiving = pd.read_csv('data/all_passing_rushing_receiving.csv')
    return games, passing_rushing_receiving

def analyze_week1_2025():
    """Analyze Week 1 2025 data"""
    games, passing_rushing_receiving = load_data()
    
    # Filter for Week 1 2025
    week1_games = games[games['game_id'].str.startswith('2025_01')]
    week1_stats = passing_rushing_receiving[passing_rushing_receiving['game_id'].str.startswith('2025_01')]
    
    print("=== WEEK 1 2025 NFL DATA ANALYSIS ===")
    print(f"Total games: {len(week1_games)}")
    print(f"Total player records: {len(week1_stats)}")
    
    # Top Receivers by Yards
    print("\n=== TOP 10 RECEIVERS BY YARDS (Week 1 2025) ===")
    receivers = week1_stats[week1_stats['rec_yds'] > 0]
    top_receivers = receivers.nlargest(10, 'rec_yds')
    for i, (idx, row) in enumerate(top_receivers.iterrows(), 1):
        print(f"{i:2d}. {row['player']:<25} ({row['team']}): {row['rec_yds']:3.0f} yards, {row['rec']:2.0f} rec, {row['rec_td']:1.0f} TD")
    
    # Top Rushers by Yards
    print("\n=== TOP 10 RUSHERS BY YARDS (Week 1 2025) ===")
    rushers = week1_stats[week1_stats['rush_yds'] > 0]
    top_rushers = rushers.nlargest(10, 'rush_yds')
    for i, (idx, row) in enumerate(top_rushers.iterrows(), 1):
        print(f"{i:2d}. {row['player']:<25} ({row['team']}): {row['rush_yds']:3.0f} yards, {row['rush_att']:2.0f} att, {row['rush_td']:1.0f} TD")
    
    # Top Passers by Yards
    print("\n=== TOP 10 PASSERS BY YARDS (Week 1 2025) ===")
    passers = week1_stats[week1_stats['pass_yds'] > 0]
    top_passers = passers.nlargest(10, 'pass_yds')
    for i, (idx, row) in enumerate(top_passers.iterrows(), 1):
        print(f"{i:2d}. {row['player']:<25} ({row['team']}): {row['pass_yds']:3.0f} yards, {row['pass_cmp']:2.0f}/{row['pass_att']:2.0f}, {row['pass_td']:1.0f} TD, {row['pass_int']:1.0f} INT")
    
    # Create visualizations
    create_charts(week1_games, week1_stats)
    
    return week1_games, week1_stats

def create_charts(week1_games, week1_stats):
    """Create visualization charts"""
    
    # 1. Top Receivers Chart
    plt.figure(figsize=(12, 8))
    receivers = week1_stats[week1_stats['rec_yds'] > 0]
    top_receivers = receivers.nlargest(10, 'rec_yds')
    
    plt.subplot(2, 2, 1)
    plt.barh(range(len(top_receivers)), top_receivers['rec_yds'])
    plt.yticks(range(len(top_receivers)), [f"{row['player']} ({row['team']})" for _, row in top_receivers.iterrows()])
    plt.xlabel('Receiving Yards')
    plt.title('Top 10 Receivers by Yards (Week 1 2025)')
    plt.gca().invert_yaxis()
    
    # 2. Top Rushers Chart
    plt.subplot(2, 2, 2)
    rushers = week1_stats[week1_stats['rush_yds'] > 0]
    top_rushers = rushers.nlargest(10, 'rush_yds')
    
    plt.barh(range(len(top_rushers)), top_rushers['rush_yds'])
    plt.yticks(range(len(top_rushers)), [f"{row['player']} ({row['team']})" for _, row in top_rushers.iterrows()])
    plt.xlabel('Rushing Yards')
    plt.title('Top 10 Rushers by Yards (Week 1 2025)')
    plt.gca().invert_yaxis()
    
    # 3. Top Passers Chart
    plt.subplot(2, 2, 3)
    passers = week1_stats[week1_stats['pass_yds'] > 0]
    top_passers = passers.nlargest(10, 'pass_yds')
    
    plt.barh(range(len(top_passers)), top_passers['pass_yds'])
    plt.yticks(range(len(top_passers)), [f"{row['player']} ({row['team']})" for _, row in top_passers.iterrows()])
    plt.xlabel('Passing Yards')
    plt.title('Top 10 Passers by Yards (Week 1 2025)')
    plt.gca().invert_yaxis()
    
    # 4. Top Passers by Completion Percentage
    plt.subplot(2, 2, 4)
    passers = week1_stats[week1_stats['pass_att'] > 0]
    passers = passers.copy()  # Avoid SettingWithCopyWarning
    passers['comp_pct'] = (passers['pass_cmp'] / passers['pass_att']) * 100
    top_comp_pct = passers.nlargest(10, 'comp_pct')
    
    plt.barh(range(len(top_comp_pct)), top_comp_pct['comp_pct'])
    plt.yticks(range(len(top_comp_pct)), [f"{row['player']} ({row['team']})" for _, row in top_comp_pct.iterrows()])
    plt.xlabel('Completion Percentage')
    plt.title('Top 10 Passers by Completion % (Week 1 2025)')
    plt.gca().invert_yaxis()
    
    plt.tight_layout()
    plt.savefig('week1_2025_analysis.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    # Additional charts
    create_additional_charts(week1_stats)

def create_additional_charts(week1_stats):
    """Create additional analysis charts"""
    
    # 1. Position Distribution
    plt.figure(figsize=(15, 10))
    
    plt.subplot(2, 3, 1)
    position_counts = week1_stats['position'].value_counts()
    plt.pie(position_counts.values, labels=position_counts.index, autopct='%1.1f%%')
    plt.title('Player Position Distribution (Week 1 2025)')
    
    # 2. Team Performance - Total Yards
    plt.subplot(2, 3, 2)
    team_stats = week1_stats.groupby('team').agg({
        'pass_yds': 'sum',
        'rush_yds': 'sum',
        'rec_yds': 'sum'
    }).reset_index()
    team_stats['total_yds'] = team_stats['pass_yds'] + team_stats['rush_yds'] + team_stats['rec_yds']
    top_teams = team_stats.nlargest(10, 'total_yds')
    
    plt.barh(range(len(top_teams)), top_teams['total_yds'])
    plt.yticks(range(len(top_teams)), top_teams['team'])
    plt.xlabel('Total Yards')
    plt.title('Top 10 Teams by Total Yards (Week 1 2025)')
    plt.gca().invert_yaxis()
    
    # 3. Touchdown Distribution
    plt.subplot(2, 3, 3)
    td_stats = week1_stats.groupby('team').agg({
        'pass_td': 'sum',
        'rush_td': 'sum',
        'rec_td': 'sum'
    }).reset_index()
    td_stats['total_td'] = td_stats['pass_td'] + td_stats['rush_td'] + td_stats['rec_td']
    top_td_teams = td_stats.nlargest(10, 'total_td')
    
    plt.barh(range(len(top_td_teams)), top_td_teams['total_td'])
    plt.yticks(range(len(top_td_teams)), top_td_teams['team'])
    plt.xlabel('Total Touchdowns')
    plt.title('Top 10 Teams by Touchdowns (Week 1 2025)')
    plt.gca().invert_yaxis()
    
    # 4. Yards Per Carry
    plt.subplot(2, 3, 4)
    rushers = week1_stats[week1_stats['rush_att'] > 0]
    rushers = rushers.copy()  # Avoid SettingWithCopyWarning
    rushers['ypc'] = rushers['rush_yds'] / rushers['rush_att']
    top_ypc = rushers.nlargest(10, 'ypc')
    
    plt.barh(range(len(top_ypc)), top_ypc['ypc'])
    plt.yticks(range(len(top_ypc)), [f"{row['player']} ({row['team']})" for _, row in top_ypc.iterrows()])
    plt.xlabel('Yards Per Carry')
    plt.title('Top 10 Rushers by YPC (Week 1 2025)')
    plt.gca().invert_yaxis()
    
    # 5. Yards Per Reception
    plt.subplot(2, 3, 5)
    receivers = week1_stats[week1_stats['rec'] > 0]
    receivers = receivers.copy()  # Avoid SettingWithCopyWarning
    receivers['ypr'] = receivers['rec_yds'] / receivers['rec']
    top_ypr = receivers.nlargest(10, 'ypr')
    
    plt.barh(range(len(top_ypr)), top_ypr['ypr'])
    plt.yticks(range(len(top_ypr)), [f"{row['player']} ({row['team']})" for _, row in top_ypr.iterrows()])
    plt.xlabel('Yards Per Reception')
    plt.title('Top 10 Receivers by YPR (Week 1 2025)')
    plt.gca().invert_yaxis()
    
    plt.tight_layout()
    plt.savefig('week1_2025_additional_analysis.png', dpi=300, bbox_inches='tight')
    plt.show()

if __name__ == "__main__":
    week1_games, week1_stats = analyze_week1_2025()
    print("\nAnalysis complete! Charts saved as 'week1_2025_analysis.png' and 'week1_2025_additional_analysis.png'")
