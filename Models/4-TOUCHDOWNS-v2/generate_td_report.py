#!/usr/bin/env python3
"""
Generate TD predictions report formatted by game, similar to 4-TOUCHDOWNS format.
"""

import pandas as pd
import os
from datetime import datetime
from typing import Dict, Tuple


def format_probability(prob):
    """Format probability as percentage."""
    return f"{prob * 100:.1f}%"


def format_odds(odds):
    """Format odds with + for positive values."""
    if odds > 0:
        return f"+{odds:.0f}"
    return f"{odds:.0f}"


def load_rosters(rosters_path: str, target_season: int) -> Dict[Tuple[str, str], str]:
    """Return a mapping from (player_name, team) to position for a given season.

    The roster file should contain at least the columns ``season``, ``team`` and
    ``full_name``.  Player names are cleaned for better matching.
    """
    def clean_name(name):
        """Clean player name for better matching."""
        import re
        name = str(name).strip().lower()
        # Remove periods and normalize suffixes
        name = re.sub(r'\.', '', name)
        name = re.sub(r'\s+(ii|iii|iv|jr|sr)$', '', name)
        return name

    rosters = pd.read_csv(rosters_path)
    season_rosters = rosters[rosters["season"] == target_season].copy()
    position_map: Dict[Tuple[str, str], str] = {}

    for _, row in season_rosters.iterrows():
        # Store both original and cleaned versions for better matching
        original_name = str(row["full_name"]).strip().lower()
        cleaned_name = clean_name(row["full_name"])

        # Store both versions in the map
        position_map[(original_name, row["team"])] = row["position"]
        if cleaned_name != original_name:
            position_map[(cleaned_name, row["team"])] = row["position"]

    return position_map


def assign_positions(player_data: pd.DataFrame, position_map: Dict[Tuple[str, str], str]) -> pd.DataFrame:
    """Annotate the player_data DataFrame with a ``position`` column using a mapping.

    Players whose names and teams are not present in the mapping will have an
    empty string as their position.
    """
    def clean_name(name):
        """Clean player name for better matching."""
        import re
        name = str(name).strip().lower()
        # Remove periods and normalize suffixes
        name = re.sub(r'\.', '', name)
        name = re.sub(r'\s+(ii|iii|iv|jr|sr)$', '', name)
        return name

    def get_position(row):
        player_name = str(row["player"])
        team = row["team"]

        # Try multiple variations of the name
        name_variations = [
            player_name.strip().lower(),  # Original
            clean_name(player_name),      # Cleaned
        ]

        # Try each name variation
        for name_var in name_variations:
            key = (name_var, team)
            if key in position_map:
                return position_map[key]

        return ""

    player_data = player_data.copy()
    player_data["position"] = player_data.apply(get_position, axis=1)
    return player_data


def create_game_report(game_key, game_info, game_num, week_num=10):
    """Create individual game report in ASCII table format."""
    players = game_info['players']
    if not players:
        return ""

    # Sort players by TD probability (highest first)
    sorted_players = sorted(players, key=lambda x: x['pred_prob'], reverse=True)

    lines = []
    lines.append("=" * 80)
    lines.append(f"{game_key} | Week {week_num} 2025 | Anytime TD Probabilities")
    lines.append("=" * 80)
    lines.append("")

    # Create table header
    lines.append("+--------+-------------------+--------+-------+-----------+--------+")
    lines.append("|   Rank | Player            | Team   | Pos   | TD Prob   |   Odds |")
    lines.append("+========+===================+========+=======+===========+=======+")

    # Add player rows (show all players)
    for i, player in enumerate(sorted_players, 1):
        player_name = player['player'][:18].ljust(18)  # Truncate long names
        team = player['team'][:6].ljust(6)
        pos = player.get('position', 'UNK')[:5].ljust(5)  # Use actual position if available
        prob = format_probability(player['pred_prob']).rjust(9)
        odds = format_odds(player['implied_odds']).rjust(6)

        lines.append(f"| {i:6d} | {player_name} | {team} | {pos} | {prob} | {odds} |")

    lines.append("+--------+-------------------+--------+-------+-----------+--------+")

    return "\n".join(lines)


def create_individual_game_files(games, week_num):
    """Create individual text files for each game."""
    predictions_dir = f"predictions-week-{week_num}-TD"
    os.makedirs(predictions_dir, exist_ok=True)

    for game_num, (game_key, game_info) in enumerate(games.items(), 1):
        if game_info['players']:
            game_report = create_game_report(game_key, game_info, game_num, week_num)

            # Create filename like game_01_DEN_vs_LVR_td_predictions.txt
            away_team, home_team = game_key.split(' vs ')
            filename = f"game_{game_num:02d}_{away_team}_vs_{home_team}_td_predictions.txt"
            filepath = os.path.join(predictions_dir, filename)

            with open(filepath, 'w') as f:
                f.write(game_report)

            print(f"Created: {filepath}")


def create_html_report(week_num):
    """Create an HTML report with all touchdown predictions."""
    import glob

    predictions_dir = f"predictions-week-{week_num}-TD"

    if not os.path.exists(predictions_dir):
        print(f"Error: Directory {predictions_dir} not found!")
        return

    txt_files = glob.glob(f"{predictions_dir}/game_*.txt")
    txt_files.sort(key=lambda x: int(x.split('game_')[1].split('_')[0]))

    if not txt_files:
        print(f"No text files found in {predictions_dir}")
        return

    html_file = f"{predictions_dir}/final_week{week_num}_TD_report.html"

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Week {week_num} Touchdown Predictions</title>
    <style>
        body {{ font-family: 'Courier New', Courier, monospace; max-width: 1000px; margin: auto; padding: 20px; background-color: #f0f0f0; }}
        .header {{ background-color: #333; color: white; padding: 20px; text-align: center; margin-bottom: 20px; }}
        .game-section {{ background: white; margin-bottom: 20px; padding: 15px; border: 1px solid #ddd; }}
        pre {{ white-space: pre-wrap; word-wrap: break-word; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Week {week_num} Touchdown Predictions</h1>
        <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
"""

    for txt_file in txt_files:
        with open(txt_file, 'r') as f:
            game_content = f.read()

        html_content += f"""    <div class="game-section">
        <pre>{game_content}</pre>
    </div>
"""

    html_content += """</body>
</html>"""

    with open(html_file, 'w') as f:
        f.write(html_content)

    print(f"HTML report created: {html_file}")


def main(week_num=10):
    # Load data
    td_predictions = pd.read_csv('td_predictions.csv')
    upcoming_games = pd.read_csv('../upcoming_games.csv')

    # Load rosters and assign positions
    position_map = load_rosters('../data/rosters.csv', 2025)
    td_predictions = assign_positions(td_predictions, position_map)

    # Sort predictions by probability (highest first)
    td_predictions = td_predictions.sort_values('pred_prob', ascending=False)

    # Create game lookup
    games = {}
    for _, game in upcoming_games.iterrows():
        home_team = game['home_team']
        away_team = game['away_team']
        game_key = f"{away_team} vs {home_team}"
        games[game_key] = {
            'home_team': home_team,
            'away_team': away_team,
            'players': []
        }

    # Group players by game
    for _, player in td_predictions.iterrows():
        team = player['team']
        opponent = player['opponent_team']

        # Find which game this player belongs to
        for game_key, game_info in games.items():
            if (team == game_info['home_team'] and opponent == game_info['away_team']) or \
               (team == game_info['away_team'] and opponent == game_info['home_team']):
                game_info['players'].append(player)
                break

    # Create individual game files
    create_individual_game_files(games, week_num)

    # Create HTML report
    create_html_report(week_num)

    # Move the raw predictions data to the predictions folder
    predictions_dir = f"predictions-week-{week_num}-TD"
    import shutil
    shutil.move('td_predictions.csv', f'{predictions_dir}/td_predictions.csv')
    print(f"Moved raw predictions data to {predictions_dir}/td_predictions.csv")

    # Generate overall leaderboard text file
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    total_props = sum(len(game_info['players']) for game_info in games.values())

    leaderboard_lines = []
    leaderboard_lines.append("=" * 80)
    leaderboard_lines.append(f"NFL WEEK {week_num} 2025 - ALL ANYTIME TD SCORERS")
    leaderboard_lines.append("=" * 80)
    leaderboard_lines.append(f"Generated: {timestamp}")
    leaderboard_lines.append("")
    leaderboard_lines.append("+--------+-------------------+--------+-------+-----------+--------+")
    leaderboard_lines.append("|   Rank | Player            | Team   | Pos   | TD Prob   |   Odds |")
    leaderboard_lines.append("+========+===================+========+=======+===========+=======+")

    # Show all players, not just top 20
    for i, (_, player) in enumerate(td_predictions.iterrows(), 1):
        player_name = player['player'][:18].ljust(18)
        team = player['team'][:6].ljust(6)
        pos = player.get('position', 'UNK')[:5].ljust(5)
        prob = format_probability(player['pred_prob']).rjust(9)
        odds = format_odds(player['implied_odds']).rjust(6)
        leaderboard_lines.append(f"| {i:6d} | {player_name} | {team} | {pos} | {prob} | {odds} |")

    leaderboard_lines.append("+--------+-------------------+--------+-------+-----------+--------+")
    leaderboard_lines.append("")
    leaderboard_lines.append(f"Total TD Projections Across All Games: {total_props}")

    # Write leaderboard
    predictions_dir = f"predictions-week-{week_num}-TD"
    with open(f'{predictions_dir}/final_week{week_num}_anytime_td_report.csv', 'w') as f:
        f.write('\n'.join(leaderboard_lines))

    print(f"Generated final leaderboard report with {total_props} total projections")


if __name__ == "__main__":
    import sys
    week_num = 10  # Default week
    if len(sys.argv) > 1:
        try:
            week_num = int(sys.argv[1])
        except ValueError:
            print("Error: Week number must be a valid integer")
            sys.exit(1)

    main(week_num)
