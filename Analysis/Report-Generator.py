import pandas as pd
import sqlite3
import os
import shutil
os.system('rm -rf data')
shutil.copytree('../Scrapers/data', 'data')
os.system('rm data/games.csv')
os.system('rm data/player_stats.csv')
os.system('rm data/rosters.csv')
shutil.copy('../Scrapers/nfl.db', 'data/')
shutil.copy('../Scrapers/PlayerStats.csv', 'data/')
shutil.copy('../Scrapers/Rosters.csv', 'data/')
shutil.copy('../Scrapers/Games.csv', 'data/')
shutil.copy('../Scrapers/Teams.csv', 'data/')
file_path = 'data/PlayerStats.csv'
data = pd.read_csv(file_path)
filtered_data = data[data['season'].between(2020, 2024)]
filtered_file_path = 'data/PlayerStats.csv'
filtered_data.to_csv(filtered_file_path, index=False)
print("Filtered data saved to:", filtered_file_path)
file_path_rosters = 'data/Rosters.csv'
rosters_data = pd.read_csv(file_path_rosters)
filtered_rosters_data = rosters_data[rosters_data['season'].between(2020, 2024)]
filtered_rosters_file_path_new = 'data/Rosters.csv'
filtered_rosters_data.to_csv(filtered_rosters_file_path_new, index=False)
print("Filtered rosters data saved to:", filtered_rosters_file_path_new)
team1 = 'NYJ'  
team2 = 'MIN'
# team1 = 'CHI'  # Chicago Bears
# team2 = 'CAR'  # Carolina Panthers
# team1 = 'BAL'  # Baltimore Ravens
# team2 = 'CIN'  # Cincinnati Bengals
# team1 = 'BUF'  # Buffalo Bills
# team2 = 'HOU'  # Houston Texans
# team1 = 'IND'  # Indianapolis Colts
# team2 = 'JAX'  # Jacksonville Jaguars
# team1 = 'MIA'  # Miami Dolphins
# team2 = 'NE'   # New England Patriots
# team1 = 'CLE'  # Cleveland Browns
# team2 = 'WAS'  # Washington Commanders
# team1 = 'LVR'   # Las Vegas Raiders
# team2 = 'DEN'  # Denver Broncos
# team1 = 'SF'   # San Francisco 49ers
# team2 = 'ARI'  # Arizona Cardinals
# team1 = 'GB'   # Green Bay Packers
# team2 = 'LAR'  # Los Angeles Rams
# team1 = 'NYG'  # New York Giants
# team2 = 'SEA'  # Seattle Seahawks
# team1 = 'DAL'  # Dallas Cowboys
# team2 = 'PIT'  # Pittsburgh Steelers
import sqlite3
db_path = 'data/nfl.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
records = {}
teams = [team1, team2]
season = 2024
for team in teams:
    query = f"""
    SELECT game_id, week, home_team, away_team, home_score, away_score, home_spread, away_spread
    FROM Games
    WHERE (home_team = '{team}' OR away_team = '{team}') 
      AND season = {season} 
      AND game_type = 'REG';
    """
    cursor.execute(query)
    games = cursor.fetchall()
    ats_wins = 0
    ats_losses = 0
    ats_pushes = 0
    wins = 0
    losses = 0
    for game in games:
        game_id, week, home_team, away_team, home_score, away_score, home_spread, away_spread = game
        if home_score is None and away_score is None:
            continue
        if home_score is not None and away_score is not None:
            spread_diff = home_score - away_score
            try:
                home_spread_float = float(home_spread)
                spread_result = spread_diff + home_spread_float
                if spread_result > 0:
                    if team == home_team:
                        ats_wins += 1
                    else:
                        ats_losses += 1
                elif spread_result < 0:
                    if team == home_team:
                        ats_losses += 1
                    else:
                        ats_wins += 1
                else:
                    ats_pushes += 1
            except (ValueError, TypeError):
                pass
            if home_score > away_score:
                if team == home_team:
                    wins += 1
                else:  
                    losses += 1
            elif home_score < away_score:
                if team == home_team:
                    losses += 1
                else:  
                    wins += 1
    records[team] = {
        'ATS Wins': ats_wins, 
        'ATS Losses': ats_losses,
        'ATS Pushes': ats_pushes,
        'Wins': wins,
        'Losses': losses
    }
conn.close()
for team, record in records.items():
    print(f"{team} 2024 REG Season:")
    print(f"  W/L: {record['Wins']}W - {record['Losses']}L")
    print(f"  ATS: {record['ATS Wins']}W - {record['ATS Losses']}L - {record['ATS Pushes']}P")
    print()
team1 = 'MIN'  
team2 = 'NYJ'  
file_path = "data/Games.csv"  
games_df = pd.read_csv(file_path)
vikings_df = games_df[(games_df['home_team'] == team1) | (games_df['away_team'] == team1)]
jets_df = games_df[(games_df['home_team'] == team2) | (games_df['away_team'] == team2)]
vikings_2024_df = vikings_df[vikings_df['season'] == 2024]
jets_2024_df = jets_df[jets_df['season'] == 2024]
vikings_2024_played_df = vikings_2024_df[(vikings_2024_df['home_score'].notnull()) & (vikings_2024_df['away_score'].notnull())]
jets_2024_played_df = jets_2024_df[(jets_2024_df['home_score'].notnull()) & (jets_2024_df['away_score'].notnull())]
vikings_home_points = vikings_2024_played_df[vikings_2024_played_df['home_team'] == team1]['home_score'].sum()
vikings_away_points = vikings_2024_played_df[vikings_2024_played_df['away_team'] == team1]['away_score'].sum()
vikings_total_games = vikings_2024_played_df[(vikings_2024_played_df['home_team'] == team1) | (vikings_2024_played_df['away_team'] == team1)].shape[0]
vikings_points_per_game = (vikings_home_points + vikings_away_points) / vikings_total_games if vikings_total_games > 0 else 0
jets_home_points = jets_2024_played_df[jets_2024_played_df['home_team'] == team2]['home_score'].sum()
jets_away_points = jets_2024_played_df[jets_2024_played_df['away_team'] == team2]['away_score'].sum()
jets_total_games = jets_2024_played_df[(jets_2024_played_df['home_team'] == team2) | (jets_2024_played_df['away_team'] == team2)].shape[0]
jets_points_per_game = (jets_home_points + jets_away_points) / jets_total_games if jets_total_games > 0 else 0
vikings_home_allowed = vikings_2024_played_df[vikings_2024_played_df['home_team'] == team1]['away_score'].sum()
vikings_away_allowed = vikings_2024_played_df[vikings_2024_played_df['away_team'] == team1]['home_score'].sum()
vikings_points_allowed_per_game = (vikings_home_allowed + vikings_away_allowed) / vikings_total_games if vikings_total_games > 0 else 0
jets_home_allowed = jets_2024_played_df[jets_2024_played_df['home_team'] == team2]['away_score'].sum()
jets_away_allowed = jets_2024_played_df[jets_2024_played_df['away_team'] == team2]['home_score'].sum()
jets_points_allowed_per_game = (jets_home_allowed + jets_away_allowed) / jets_total_games if jets_total_games > 0 else 0
result_2024_corrected_final = {
    f"{team1} (2024)": {
        "Points Per Game": round(vikings_points_per_game, 2),
        "Defensive Points Allowed": round(vikings_points_allowed_per_game, 2)
    },
    f"{team2} (2024)": {
        "Points Per Game": round(jets_points_per_game, 2),
        "Defensive Points Allowed": round(jets_points_allowed_per_game, 2)
    }
}
result_df = pd.DataFrame(result_2024_corrected_final)
print(result_df)
team1 = 'NYJ'  
team2 = 'MIN'  
games_df = pd.read_csv('data/Games.csv')
player_stats_df = pd.read_csv('data/PlayerStats.csv')
def analyze_2024_players(team1, team2, games_df, player_stats_df):
    positions = ['WR', 'TE', 'RB', 'QB']  
    current_players_team1 = player_stats_df[(player_stats_df['player_current_team'] == team1) & 
                                            (player_stats_df['season'] == 2024)]
    current_players_team2 = player_stats_df[(player_stats_df['player_current_team'] == team2) & 
                                            (player_stats_df['season'] == 2024)]
    players_team1_names = current_players_team1['player_display_name'].unique()
    players_team2_names = current_players_team2['player_display_name'].unique()
    print(f"\nCurrent 2024 Players for {team1}:")
    print(players_team1_names)
    print(f"\nCurrent 2024 Players for {team2}:")
    print(players_team2_names)
    print()
    for player in players_team1_names:
        player_stats = current_players_team1[current_players_team1['player_display_name'] == player]
        if player_stats['position'].isin(['WR', 'TE', 'RB']).all() and player_stats['receptions'].sum() > 0:
            average_yards_per_reception = player_stats['receiving_yards'].sum() / player_stats['receptions'].sum()
            print(f"Average yards per reception for {player}: {average_yards_per_reception}")
    for player in players_team2_names:
        player_stats = current_players_team2[current_players_team2['player_display_name'] == player]
        if player_stats['position'].isin(['WR', 'TE', 'RB']).all() and player_stats['receptions'].sum() > 0:
            average_yards_per_reception = player_stats['receiving_yards'].sum() / player_stats['receptions'].sum()
            print(f"Average yards per reception for {player}: {average_yards_per_reception}")
    for player in players_team1_names:
        player_stats = current_players_team1[current_players_team1['player_display_name'] == player]
        if player_stats['position'].isin(['WR', 'TE', 'RB']).all() and player_stats['game_id'].nunique() > 0:
            average_receptions_per_game = player_stats['receptions'].sum() / player_stats['game_id'].nunique()
            print(f"Average receptions per game for {player}: {average_receptions_per_game}")
    for player in players_team2_names:
        player_stats = current_players_team2[current_players_team2['player_display_name'] == player]
        if player_stats['position'].isin(['WR', 'TE', 'RB']).all() and player_stats['game_id'].nunique() > 0:
            average_receptions_per_game = player_stats['receptions'].sum() / player_stats['game_id'].nunique()
            print(f"Average receptions per game for {player}: {average_receptions_per_game}")
analyze_2024_players(team1, team2, games_df, player_stats_df)
team1, team2 = 'NYJ', 'MIN'
games_df = pd.read_csv('data/Games.csv')
player_stats_df = pd.read_csv('data/PlayerStats.csv')
all_stats_df = pd.read_csv('data/all_passing_rushing_receiving.csv')
current_players_team1 = player_stats_df[(player_stats_df['player_current_team'] == team1) & (player_stats_df['season'] == 2024) & (player_stats_df['position'].isin(['WR', 'TE']))]
current_players_team2 = player_stats_df[(player_stats_df['player_current_team'] == team2) & (player_stats_df['season'] == 2024) & (player_stats_df['position'].isin(['WR', 'TE']))]
players_team1_names = current_players_team1['player_display_name'].unique()
players_team2_names = current_players_team2['player_display_name'].unique()
print(f"\nCurrent 2024 Wide Receivers and Tight Ends for {team1}:")
print(players_team1_names)
print(f"\nCurrent 2024 Wide Receivers and Tight Ends for {team2}:")
print(players_team2_names)
print()
def get_player_longest_reception_stats(player_name, opponent_team=None):
    player_data = all_stats_df[all_stats_df['player'] == player_name]
    if 'rec_long' not in player_data.columns:
        return f"No reception data available for {player_name}"
    longest_reception = player_data['rec_long'].max()  
    total_games = player_data.shape[0]
    opponent_insights = None
    opponent_data = None
    if opponent_team:
        opponent_data = player_data[player_data['opponent_team'] == opponent_team].drop_duplicates(subset=['game_id', 'rec_yds'])
        if opponent_data.empty:
            opponent_insights = f"No data available for {player_name} against {opponent_team}"
        else:
            opponent_insights = {
                "Opponent": opponent_team,
                "Longest Reception vs Opponent": opponent_data['rec_long'].max(),
                "Average Longest Reception vs Opponent": opponent_data['rec_long'].mean(),
                "Total Games vs Opponent": opponent_data.shape[0],
                "Games with 30+ Yard Reception vs Opponent": opponent_data[opponent_data['rec_long'] >= 30].shape[0],
                "Average Receptions per Game vs Opponent": opponent_data['rec'].mean(),
                "Average Receiving Yards per Game vs Opponent": opponent_data['rec_yds'].mean(),
                "Receiving Touchdowns vs Opponent": opponent_data['rec_td'].sum(),
                "Average Targets per Game vs Opponent": opponent_data['targets'].mean() if 'targets' in opponent_data.columns else "N/A",
            }
    else:
        opponent_insights = "No opponent provided."
    career_insights = {
        "Player": player_name,
        "Career Longest Reception": longest_reception,
        "Total Games Played": total_games,
    }
    return career_insights, opponent_insights, opponent_data
for team, players in [(team1, players_team1_names), (team2, players_team2_names)]:
    print(f"\nAnalyzing players for {team}:")
    for player_name in players:
        career_insights, opponent_insights, opponent_data = get_player_longest_reception_stats(player_name, team2 if team == team1 else team1)
        print(f"\n{player_name}:")
        print("CAREER INSIGHTS:")
        for key, value in career_insights.items():
            print(f"{key}: {value}")
        print("OPPONENT INSIGHTS:")
        if isinstance(opponent_insights, dict):
            for key, value in opponent_insights.items():
                print(f"{key}: {value}")
        else:
            print(opponent_insights)
        if opponent_data is not None and not opponent_data.empty:
            print("GAMES AGAINST OPPONENT:")
            for index, row in opponent_data.iterrows():
                print(f"{index + 1}. Game ID: {row['game_id']}, Rec Yards: {row['rec_yds']}")
        print("-" * 50)
team1, team2 = 'NYJ', 'MIN'
games_df = pd.read_csv('data/Games.csv')
player_stats_df = pd.read_csv('data/PlayerStats.csv')
all_stats_df = pd.read_csv('data/all_passing_rushing_receiving.csv')
current_players_team1 = player_stats_df[(player_stats_df['player_current_team'] == team1) & (player_stats_df['season'] == 2024) & (player_stats_df['position'].isin(['RB', 'QB']))]
current_players_team2 = player_stats_df[(player_stats_df['player_current_team'] == team2) & (player_stats_df['season'] == 2024) & (player_stats_df['position'].isin(['RB', 'QB']))]
players_team1_names = current_players_team1['player_display_name'].unique()
players_team2_names = current_players_team2['player_display_name'].unique()
print(f"\nCurrent 2024 Running Backs and Quarterbacks for {team1}:")
print(players_team1_names)
print(f"\nCurrent 2024 Running Backs and Quarterbacks for {team2}:")
print(players_team2_names)
print()
def get_player_stats(player_name, opponent_team=None):
    player_data = all_stats_df[all_stats_df['player'] == player_name]
    if player_data.empty:
        return f"No data available for {player_name}"
    total_games = player_data.shape[0]
    opponent_insights = None
    opponent_data = None
    if opponent_team:
        opponent_data = player_data[player_data['opponent_team'] == opponent_team].drop_duplicates(subset=['game_id'])
        if opponent_data.empty:
            opponent_insights = f"No data available for {player_name} against {opponent_team}"
        else:
            opponent_insights = {
                "Opponent": opponent_team,
                "Total Games vs Opponent": opponent_data.shape[0],
                "Average Rush Yards per Game vs Opponent": opponent_data['rush_yds'].mean(),
                "Rushing Touchdowns vs Opponent": opponent_data['rush_td'].sum(),
                "Average Yards per Carry vs Opponent": opponent_data['rush_yds'].sum() / opponent_data['rush_att'].sum() if opponent_data['rush_att'].sum() > 0 else 0,
            }
    else:
        opponent_insights = "No opponent provided."
    career_insights = {
        "Player": player_name,
        "Total Games Played": total_games,
        "Career Rush Yards": player_data['rush_yds'].sum(),
        "Career Rush TDs": player_data['rush_td'].sum(),
    }
    return career_insights, opponent_insights, opponent_data
for team, players in [(team1, players_team1_names), (team2, players_team2_names)]:
    print(f"\nAnalyzing players for {team}:")
    for player_name in players:
        career_insights, opponent_insights, opponent_data = get_player_stats(player_name, team2 if team == team1 else team1)
        print(f"\n{player_name}:")
        print("CAREER INSIGHTS:")
        for key, value in career_insights.items():
            print(f"{key}: {value}")
        print("OPPONENT INSIGHTS:")
        if isinstance(opponent_insights, dict):
            for key, value in opponent_insights.items():
                print(f"{key}: {value}")
        else:
            print(opponent_insights)
        if opponent_data is not None and not opponent_data.empty:
            print("GAMES AGAINST OPPONENT:")
            for index, row in opponent_data.iterrows():
                print(f"{index + 1}. Game ID: {row['game_id']}, Rush Yards: {row['rush_yds']}")
        print("-" * 50)
team1 = 'NYJ'  
team2 = 'MIN'  
games_df = pd.read_csv('data/Games.csv')
player_stats_df = pd.read_csv('data/PlayerStats.csv')
def analyze_team_matchup(team1, team2, games_df, player_stats_df):
    team_matchups = games_df[((games_df['home_team'] == team1) & (games_df['away_team'] == team2)) | 
                             ((games_df['home_team'] == team2) & (games_df['away_team'] == team1))]
    last_10_games = team_matchups.sort_values(by='date', ascending=False).head(10)
    if last_10_games.empty:
        return f"No recent games found between {team1} and {team2}."
    total_points = last_10_games['home_score'] + last_10_games['away_score']
    average_total_points = total_points.mean()
    team1_wins = sum((last_10_games['home_team'] == team1) & (last_10_games['home_score'] > last_10_games['away_score'])) + \
                 sum((last_10_games['away_team'] == team1) & (last_10_games['away_score'] > last_10_games['home_score']))
    team2_wins = sum((last_10_games['home_team'] == team2) & (last_10_games['home_score'] > last_10_games['away_score'])) + \
                 sum((last_10_games['away_team'] == team2) & (last_10_games['away_score'] > last_10_games['home_score']))
    team1_scores = last_10_games.loc[last_10_games['home_team'] == team1, 'home_score'].sum() + \
                   last_10_games.loc[last_10_games['away_team'] == team1, 'away_score'].sum()
    team2_scores = last_10_games.loc[last_10_games['home_team'] == team2, 'home_score'].sum() + \
                   last_10_games.loc[last_10_games['away_team'] == team2, 'away_score'].sum()
    team1_home_wins = sum((last_10_games['home_team'] == team1) & (last_10_games['home_score'] > last_10_games['away_score']))
    team1_home_losses = sum((last_10_games['home_team'] == team1) & (last_10_games['home_score'] < last_10_games['away_score']))
    team1_away_wins = sum((last_10_games['away_team'] == team1) & (last_10_games['away_score'] > last_10_games['home_score']))
    team1_away_losses = sum((last_10_games['away_team'] == team1) & (last_10_games['away_score'] < last_10_games['home_score']))
    team2_home_wins = sum((last_10_games['home_team'] == team2) & (last_10_games['home_score'] > last_10_games['away_score']))
    team2_home_losses = sum((last_10_games['home_team'] == team2) & (last_10_games['home_score'] < last_10_games['away_score']))
    team2_away_wins = sum((last_10_games['away_team'] == team2) & (last_10_games['away_score'] > last_10_games['home_score']))
    team2_away_losses = sum((last_10_games['away_team'] == team2) & (last_10_games['away_score'] < last_10_games['home_score']))
    over_50_points_games = sum(total_points > 50)
    print(f"Matchup: {team1} vs {team2}")
    print(f"Total games analyzed between these two teams: {len(last_10_games)}")
    print(f"{team1} Wins: {team1_wins}")
    print(f"{team2} Wins: {team2_wins}")
    print(f"Average Total Points: {average_total_points}")
    print(f"Games with more than 50 total points: {over_50_points_games}")
    print(f"Average points scored by {team1} per game: {team1_scores / len(last_10_games):.2f}")
    print(f"Average points scored by {team2} per game: {team2_scores / len(last_10_games):.2f}")
    print(f"{team1} home record: {team1_home_wins}W {team1_home_losses}L")
    print(f"{team1} away record: {team1_away_wins}W {team1_away_losses}L")
    print(f"{team2} home record: {team2_home_wins}W {team2_home_losses}L")
    print(f"{team2} away record: {team2_away_wins}W {team2_away_losses}L")
    return last_10_games
last_10_games = analyze_team_matchup(team1, team2, games_df, player_stats_df)
team1 = 'NYJ'  
team2 = 'MIN'  
games_df = pd.read_csv('data/Games.csv')
player_stats_df = pd.read_csv('data/PlayerStats.csv')
def analyze_current_2024_players_and_their_historical_stats(team1, team2, games_df, player_stats_df):
    positions = ['WR', 'TE', 'RB', 'QB']  
    current_players_team1 = player_stats_df[(player_stats_df['player_current_team'] == team1) & 
                                            (player_stats_df['season'] == 2024)]
    current_players_team2 = player_stats_df[(player_stats_df['player_current_team'] == team2) & 
                                            (player_stats_df['season'] == 2024)]
    players_team1_names = current_players_team1['player_display_name'].unique()
    players_team2_names = current_players_team2['player_display_name'].unique()
    print(f"\nCurrent 2024 Players for {team1}:")
    print(players_team1_names)
    print(f"\nCurrent 2024 Players for {team2}:")
    print(players_team2_names)
    matchup_games = games_df[((games_df['home_team'] == team1) & (games_df['away_team'] == team2)) |
                             ((games_df['home_team'] == team2) & (games_df['away_team'] == team1))]
    print("\nHistorical Stats of Current 2024 Players for the Matchup:")
    historical_stats_team1 = player_stats_df[(player_stats_df['player_display_name'].isin(players_team1_names)) &
                                             ((player_stats_df['home_team'] == team1) & (player_stats_df['away_team'] == team2) |
                                              (player_stats_df['home_team'] == team2) & (player_stats_df['away_team'] == team1))]
    historical_stats_team2 = player_stats_df[(player_stats_df['player_display_name'].isin(players_team2_names)) &
                                             ((player_stats_df['home_team'] == team1) & (player_stats_df['away_team'] == team2) |
                                              (player_stats_df['home_team'] == team2) & (player_stats_df['away_team'] == team1))]
    def summarize_player_stats(historical_stats):
        if not historical_stats.empty:
            summary = historical_stats.groupby('player_display_name').agg({
                'receptions': 'mean',
                'targets': 'mean',
                'receiving_yards': 'mean',
                'receiving_tds': 'mean',
                'carries': 'mean',
                'rushing_yards': 'mean',
                'rushing_tds': 'mean',
                'passing_yards': 'mean',
                'passing_tds': 'mean',
                'interceptions': 'mean',
                'fantasy_points_ppr': 'mean'
            }).reset_index()
            summary['games_played'] = historical_stats.groupby('player_display_name')['game_id'].nunique().values
            return summary
        else:
            return pd.DataFrame()
    summary_team1 = summarize_player_stats(historical_stats_team1)
    summary_team2 = summarize_player_stats(historical_stats_team2)
    print(f"\nAverage Historical Stats per Game for {team1} players vs {team2}:")
    if not summary_team1.empty:
        print(summary_team1)
    else:
        print(f"No historical stats found for {team1} players vs {team2}.")
    print(f"\nAverage Historical Stats per Game for {team2} players vs {team1}:")
    if not summary_team2.empty:
        print(summary_team2)
    else:
        print(f"No historical stats found for {team2} players vs {team1}.")
analyze_current_2024_players_and_their_historical_stats(team1, team2, games_df, player_stats_df)