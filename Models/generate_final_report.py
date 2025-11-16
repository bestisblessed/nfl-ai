#!/usr/bin/env python3
"""
Combined NFL Props Report Generator
Creates a single consolidated report with all props (passing, rushing, receiving) for each game.
"""

import pandas as pd
import os
import sys
from datetime import datetime

def load_predictions(week_num):
    """Load all prediction data from the three model folders."""
    
    # Load passing yards (QBs only)
    passing_file = f"1-PASSING-YARDS/predictions-week-{week_num}-QB/final_week{week_num}_QB_pass_yards_report.csv"
    if os.path.exists(passing_file):
        passing_df = pd.read_csv(passing_file)
        passing_df['prop_type'] = 'Passing Yards'
        passing_df['position'] = 'QB'
        passing_df['pred_yards'] = passing_df['pred_pass_yards']
        print(f"Loaded {len(passing_df)} passing predictions")
    else:
        print(f"Warning: {passing_file} not found")
        passing_df = pd.DataFrame()
    
    # Load rushing yards (QBs and RBs)
    rushing_qb_file = f"3-RUSHING-YARDS/predictions-week-{week_num}-QB/final_week{week_num}_QB_rush_yards_report.csv"
    rushing_rb_file = f"3-RUSHING-YARDS/predictions-week-{week_num}-RB/final_week{week_num}_RB_rush_yards_report.csv"
    
    rushing_dfs = []
    if os.path.exists(rushing_qb_file):
        rushing_qb = pd.read_csv(rushing_qb_file)
        rushing_qb['prop_type'] = 'Rushing Yards'
        rushing_qb['position'] = 'QB'
        rushing_qb['pred_yards'] = rushing_qb['pred_rush_yards']
        rushing_dfs.append(rushing_qb)
        print(f"Loaded {len(rushing_qb)} QB rushing predictions")
    
    if os.path.exists(rushing_rb_file):
        rushing_rb = pd.read_csv(rushing_rb_file)
        rushing_rb['prop_type'] = 'Rushing Yards'
        rushing_rb['position'] = 'RB'
        rushing_rb['pred_yards'] = rushing_rb['pred_rush_yards']
        rushing_dfs.append(rushing_rb)
        print(f"Loaded {len(rushing_rb)} RB rushing predictions")
    
    rushing_df = pd.concat(rushing_dfs, ignore_index=True) if rushing_dfs else pd.DataFrame()
    
    # Load receiving yards (WRs, RBs, TEs)
    receiving_wr_file = f"2-RECEIVING-YARDS/predictions-week-{week_num}-WR/final_week{week_num}_WR_rec_yards_report.csv"
    receiving_rb_file = f"2-RECEIVING-YARDS/predictions-week-{week_num}-RB/final_week{week_num}_RB_rec_yards_report.csv"
    receiving_te_file = f"2-RECEIVING-YARDS/predictions-week-{week_num}-TE/final_week{week_num}_TE_rec_yards_report.csv"
    
    receiving_dfs = []
    for file, pos in [(receiving_wr_file, 'WR'), (receiving_rb_file, 'RB'), (receiving_te_file, 'TE')]:
        if os.path.exists(file):
            df = pd.read_csv(file)
            df['prop_type'] = 'Receiving Yards'
            df['position'] = pos
            df['pred_yards'] = df['pred_rec_yards']
            receiving_dfs.append(df)
            print(f"Loaded {len(df)} {pos} receiving predictions")
    
    receiving_df = pd.concat(receiving_dfs, ignore_index=True) if receiving_dfs else pd.DataFrame()
    
    # Combine all predictions
    all_dfs = [df for df in [passing_df, rushing_df, receiving_df] if not df.empty]
    if all_dfs:
        combined_df = pd.concat(all_dfs, ignore_index=True)
        print(f"Total combined predictions: {len(combined_df)}")

        injured_players = set()
        for injured_path in [
            "injured_players.csv",
            "data/injured_players.csv",
            "../injured_players.csv",
            "../data/injured_players.csv",
        ]:
            if os.path.exists(injured_path):
                try:
                    loaded = (
                        pd.read_csv(injured_path)["full_name"]
                        .dropna()
                        .astype(str)
                        .str.strip()
                    )
                    if not loaded.empty:
                        injured_players = set(loaded.tolist())
                        print(
                            f"Loaded {len(injured_players)} injured players from {injured_path}"
                        )
                    break
                except Exception as exc:
                    print(
                        f"Warning: failed to load injured players from {injured_path}: {exc}"
                    )

        if injured_players and not combined_df.empty:
            pre_filter = len(combined_df)
            mask = ~(
                combined_df["full_name"].isin(injured_players)
                & combined_df["prop_type"].isin(["Receiving Yards", "Rushing Yards"])
            )
            combined_df = combined_df[mask].reset_index(drop=True)
            removed = pre_filter - len(combined_df)
            if removed:
                print(
                    f"Removed {removed} injured receiving/rushing props from combined report"
                )

        return combined_df
    else:
        print("No prediction data found!")
        return pd.DataFrame()

def get_game_matchups():
    """Get unique game matchups from upcoming games."""
    upcoming_file = "upcoming_games.csv"
    if os.path.exists(upcoming_file):
        upcoming = pd.read_csv(upcoming_file)
        # Extract unique games
        games = []
        for _, row in upcoming.iterrows():
            game = tuple(sorted([row['home_team'], row['away_team']]))
            if game not in games:
                games.append(game)
        return [(game[0], game[1]) for game in games]
    else:
        print(f"Warning: {upcoming_file} not found, using team pairs from predictions")
        return []

def format_prediction(row, questionable_players):
    """Format a single prediction row."""
    player_name = row['full_name']
    # Check if player is questionable and append marker if so
    if player_name in questionable_players:
        player_name += " (Questionable)"

    if pd.isna(row['pred_yards']):
        return f"  {player_name} ({row['position']}): No Data"
    else:
        return f"  {player_name} ({row['position']}): {row['pred_yards']:.1f} yards"

def create_game_report(team1, team2, predictions_df, week_num, questionable_players):
    """Create a text report for a single game with all props."""
    
    # Get all predictions for this game
    game_preds = predictions_df[
        ((predictions_df['team'] == team1) & (predictions_df['opp'] == team2)) |
        ((predictions_df['team'] == team2) & (predictions_df['opp'] == team1))
    ].copy()
    
    if game_preds.empty:
        return f"No predictions found for {team1} vs {team2}"
    
    # Sort by predicted yards (descending, with NaN values last)
    game_preds = game_preds.sort_values('pred_yards', ascending=False, na_position='last')
    
    report = []
    report.append("=" * 80)
    report.append(f"{team1} vs {team2} | Week {week_num} 2025 | ALL PROPS")
    report.append("=" * 80)
    report.append("")
    
    # Group by prop type
    for prop_type in ['Passing Yards', 'Rushing Yards', 'Receiving Yards']:
        prop_preds = game_preds[game_preds['prop_type'] == prop_type]
        if not prop_preds.empty:
            report.append(f"🏈 {prop_type.upper()}")
            report.append("-" * 40)
            
            # Separate by team
            team1_preds = prop_preds[prop_preds['team'] == team1].sort_values('pred_yards', ascending=False, na_position='last')
            team2_preds = prop_preds[prop_preds['team'] == team2].sort_values('pred_yards', ascending=False, na_position='last')
            
            if not team1_preds.empty:
                report.append(f"{team1}:")
                for _, row in team1_preds.iterrows():
                    report.append(format_prediction(row, questionable_players))
                report.append("")
            
            if not team2_preds.empty:
                report.append(f"{team2}:")
                for _, row in team2_preds.iterrows():
                    report.append(format_prediction(row, questionable_players))
                report.append("")
            
            report.append("")
    
    # Summary
    total_props = len(game_preds)
    props_with_data = len(game_preds.dropna(subset=['pred_yards']))
    props_no_data = total_props - props_with_data
    
    report.append("📊 GAME SUMMARY")
    report.append("-" * 20)
    report.append(f"Total Props: {total_props}")
    report.append(f"With Predictions: {props_with_data}")
    report.append(f"No Data (Rookies): {props_no_data}")
    
    if props_with_data > 0:
        top_prop = game_preds.dropna(subset=['pred_yards']).iloc[0]
        report.append(f"Top Projection: {top_prop['full_name']} ({top_prop['position']}) - {top_prop['pred_yards']:.1f} {top_prop['prop_type'].lower()}")
    
    report.append("=" * 80)
    report.append("")
    
    return "\n".join(report)

def create_game_html_report(team1, team2, predictions_df, week_num, questionable_players):
    """Create an HTML report for a single game with all props."""
    
    # Get all predictions for this game
    game_preds = predictions_df[
        ((predictions_df['team'] == team1) & (predictions_df['opp'] == team2)) |
        ((predictions_df['team'] == team2) & (predictions_df['opp'] == team1))
    ].copy()
    
    if game_preds.empty:
        return f"<p>No predictions found for {team1} vs {team2}</p>"
    
    # Sort by predicted yards (descending, with NaN values last)
    game_preds = game_preds.sort_values('pred_yards', ascending=False, na_position='last')
    
    html = []
    html.append(f'<div class="game-container">')
    html.append(f'<h2 class="game-header">{team1} vs {team2} | Week {week_num} 2025 | ALL PROPS</h2>')
    
    # Group by prop type
    for prop_type in ['Passing Yards', 'Rushing Yards', 'Receiving Yards']:
        prop_preds = game_preds[game_preds['prop_type'] == prop_type]
        if not prop_preds.empty:
            html.append(f'<div class="prop-section">')
            html.append(f'<h3 class="prop-header">🏈 {prop_type.upper()}</h3>')
            html.append(f'<div class="teams-container">')
            
            # Create side-by-side team tables
            team1_preds = prop_preds[prop_preds['team'] == team1].sort_values('pred_yards', ascending=False, na_position='last')
            team2_preds = prop_preds[prop_preds['team'] == team2].sort_values('pred_yards', ascending=False, na_position='last')
            
            html.append(f'<div class="team-column">')
            if not team1_preds.empty:
                html.append(f'<h4 class="team-name">{team1}</h4>')
                html.append(f'<table class="props-table">')
                html.append(f'<thead><tr><th>Player</th><th>Position</th><th>Prediction</th></tr></thead>')
                html.append(f'<tbody>')
                for _, row in team1_preds.iterrows():
                    if pd.isna(row['pred_yards']):
                        pred_text = "No Data"
                        pred_class = "no-data"
                    else:
                        pred_text = f"{row['pred_yards']:.1f}"
                        pred_class = "prediction"
                    player_name = row["full_name"]
                    if player_name in questionable_players:
                        player_name += " (Questionable)"
                    html.append(f'<tr><td>{player_name}</td><td>{row["position"]}</td><td class="{pred_class}">{pred_text}</td></tr>')
                html.append(f'</tbody></table>')
            html.append(f'</div>')
            
            html.append(f'<div class="team-column">')
            if not team2_preds.empty:
                html.append(f'<h4 class="team-name">{team2}</h4>')
                html.append(f'<table class="props-table">')
                html.append(f'<thead><tr><th>Player</th><th>Position</th><th>Prediction</th></tr></thead>')
                html.append(f'<tbody>')
                for _, row in team2_preds.iterrows():
                    if pd.isna(row['pred_yards']):
                        pred_text = "No Data"
                        pred_class = "no-data"
                    else:
                        pred_text = f"{row['pred_yards']:.1f}"
                        pred_class = "prediction"
                    player_name = row["full_name"]
                    if player_name in questionable_players:
                        player_name += " (Questionable)"
                    html.append(f'<tr><td>{player_name}</td><td>{row["position"]}</td><td class="{pred_class}">{pred_text}</td></tr>')
                html.append(f'</tbody></table>')
            html.append(f'</div>')
            
            html.append(f'</div>') # teams-container
            html.append(f'</div>') # prop-section
    
    # Summary
    total_props = len(game_preds)
    props_with_data = len(game_preds.dropna(subset=['pred_yards']))
    props_no_data = total_props - props_with_data
    
    html.append(f'<div class="game-summary">')
    html.append(f'<h4>📊 Game Summary</h4>')
    html.append(f'<p><strong>Total Props:</strong> {total_props}</p>')
    html.append(f'<p><strong>With Predictions:</strong> {props_with_data}</p>')
    html.append(f'<p><strong>No Data (Rookies):</strong> {props_no_data}</p>')
    
    if props_with_data > 0:
        top_prop = game_preds.dropna(subset=['pred_yards']).iloc[0]
        html.append(f'<p><strong>Top Projection:</strong> {top_prop["full_name"]} ({top_prop["position"]}) - {top_prop["pred_yards"]:.1f} {top_prop["prop_type"].lower()}</p>')
    
    html.append(f'</div>') # game-summary
    html.append(f'</div>') # game-container
    
    return "\n".join(html)

def create_full_html_page(title, content):
    """Create a complete HTML page with CSS styling."""
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
            color: #333;
        }}
        
        .game-container {{
            background: white;
            border-radius: 10px;
            padding: 25px;
            margin-bottom: 30px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }}
        
        .game-header {{
            text-align: center;
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 15px;
            margin-bottom: 25px;
            font-size: 1.8em;
            font-weight: bold;
        }}
        
        .prop-section {{
            margin-bottom: 30px;
        }}
        
        .prop-header {{
            color: #27ae60;
            font-size: 1.4em;
            margin-bottom: 15px;
            padding: 10px;
            background-color: #ecf0f1;
            border-left: 4px solid #27ae60;
            border-radius: 5px;
        }}
        
        .teams-container {{
            display: flex;
            gap: 20px;
            justify-content: space-between;
        }}
        
        .team-column {{
            flex: 1;
        }}
        
        .team-name {{
            color: #34495e;
            font-size: 1.2em;
            margin-bottom: 10px;
            padding: 8px;
            background-color: #3498db;
            color: white;
            text-align: center;
            border-radius: 5px;
        }}
        
        .props-table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 15px;
            background: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }}
        
        .props-table th {{
            background-color: #2c3e50;
            color: white;
            padding: 12px 8px;
            text-align: left;
            font-weight: bold;
        }}
        
        .props-table td {{
            padding: 10px 8px;
            border-bottom: 1px solid #ecf0f1;
        }}
        
        .props-table tr:hover {{
            background-color: #f8f9fa;
        }}
        
        .prediction {{
            font-weight: bold;
            color: #27ae60;
        }}
        
        .no-data {{
            color: #e74c3c;
            font-style: italic;
        }}
        
        .game-summary {{
            background-color: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 8px;
            padding: 20px;
            margin-top: 25px;
        }}
        
        .game-summary h4 {{
            color: #2c3e50;
            margin-top: 0;
            margin-bottom: 15px;
        }}
        
        .game-summary p {{
            margin: 8px 0;
        }}
        
        .master-header {{
            text-align: center;
            color: #2c3e50;
            font-size: 2.2em;
            margin-bottom: 30px;
            padding: 20px;
            background: linear-gradient(135deg, #3498db, #2c3e50);
            color: white;
            border-radius: 10px;
        }}
        
        .toc {{
            background: white;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 30px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }}
        
        .toc h3 {{
            color: #2c3e50;
            margin-bottom: 15px;
        }}
        
        .toc ul {{
            list-style-type: none;
            padding: 0;
        }}
        
        .toc li {{
            padding: 8px 0;
            border-bottom: 1px solid #ecf0f1;
        }}
        
        .toc a {{
            color: #3498db;
            text-decoration: none;
            font-weight: 500;
        }}
        
        .toc a:hover {{
            text-decoration: underline;
        }}
        
        @media (max-width: 768px) {{
            .teams-container {{
                flex-direction: column;
            }}
            
            .props-table {{
                font-size: 0.9em;
            }}
            
            .props-table th, .props-table td {{
                padding: 8px 4px;
            }}
        }}
    </style>
</head>
<body>
    {content}
</body>
</html>"""
    
    return html

def create_combined_report(week_num=1):
    """Create the main combined report."""
    
    print("🏈 Creating Combined NFL Props Report...")
    print("=" * 50)
    
    # Load all predictions
    predictions_df = load_predictions(week_num)
    if predictions_df.empty:
        print("❌ No prediction data found. Make sure all models have been run.")
        return

    # Load questionable players list
    questionable_players = set()
    questionable_file = "questionable_players.csv"
    if os.path.exists(questionable_file):
        try:
            questionable_df = pd.read_csv(questionable_file)
            questionable_players = set(questionable_df['full_name'].dropna().astype(str).str.strip().tolist())
            print(f"Loaded {len(questionable_players)} questionable players")
        except Exception as e:
            print(f"Warning: Could not load questionable players: {e}")
    else:
        print("Warning: questionable_players.csv not found")
    
    # Get unique games
    games = get_game_matchups()
    if not games:
        # Fallback: extract games from predictions
        unique_matchups = set()
        for _, row in predictions_df.iterrows():
            matchup = tuple(sorted([row['team'], row['opp']]))
            unique_matchups.add(matchup)
        games = list(unique_matchups)
    
    print(f"Found {len(games)} games to process")
    
    # Create output directory
    output_dir = "0-FINAL-REPORTS"
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate individual game reports (both text and HTML)
    all_reports = []
    all_html_reports = []
    
    for i, (team1, team2) in enumerate(games, 1):
        print(f"Processing Game {i:2d}: {team1} vs {team2}")
        
        # Text report
        game_report = create_game_report(team1, team2, predictions_df, week_num, questionable_players)
        all_reports.append(game_report)
        
        # HTML report
        game_html = create_game_html_report(team1, team2, predictions_df, week_num, questionable_players)
        all_html_reports.append(game_html)
        
        # Save individual game reports
        game_filename = f"{output_dir}/game_{i:02d}_{team1}_vs_{team2}_all_props.txt"
        with open(game_filename, 'w') as f:
            f.write(game_report)
            
        game_html_filename = f"{output_dir}/game_{i:02d}_{team1}_vs_{team2}_all_props.html"
        with open(game_html_filename, 'w') as f:
            html_content = create_full_html_page(f"{team1} vs {team2} - All Props", game_html)
            f.write(html_content)
    
    # Create master combined report
    master_report = []
    master_report.append(f"🏈 NFL WEEK {week_num} 2025 - COMPLETE PROPS REPORT")
    master_report.append("=" * 80)
    master_report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    master_report.append(f"Total Games: {len(games)}")
    master_report.append(f"Total Props: {len(predictions_df)}")
    master_report.append("")
    master_report.append("This report includes ALL player props for each game:")
    master_report.append("• QB Passing Yards")
    master_report.append("• QB Rushing Yards") 
    master_report.append("• RB Rushing Yards")
    master_report.append("• WR/RB/TE Receiving Yards")
    master_report.append("")
    master_report.append("=" * 80)
    master_report.append("")
    
    # Add all game reports
    master_report.extend(all_reports)
    
    # Save master report (text)
    master_filename = f"{output_dir}/week{week_num}_complete_props_report.txt"
    with open(master_filename, 'w') as f:
        f.write("\n".join(master_report))
    
    # Create master HTML report
    master_html = []
    master_html.append(f'<div class="master-header">🏈 NFL WEEK {week_num} 2025 - COMPLETE PROPS REPORT</div>')
    
    # Table of contents
    master_html.append('<div class="toc">')
    master_html.append('<h3>📋 Table of Contents</h3>')
    master_html.append('<ul>')
    for i, (team1, team2) in enumerate(games, 1):
        master_html.append(f'<li><a href="#game{i:02d}">{team1} vs {team2}</a></li>')
    master_html.append('</ul>')
    master_html.append('</div>')
    
    # Add game anchors and content
    for i, game_html in enumerate(all_html_reports, 1):
        team1, team2 = games[i-1]
        master_html.append(f'<div id="game{i:02d}">')
        master_html.append(game_html)
        master_html.append('</div>')
    
    master_html_filename = f"{output_dir}/week{week_num}_complete_props_report.html"
    with open(master_html_filename, 'w') as f:
        html_content = create_full_html_page(f"NFL Week {week_num} 2025 - Complete Props Report", "\n".join(master_html))
        f.write(html_content)
    
    # Create summary CSV
    summary_df = predictions_df[['full_name', 'team', 'opp', 'position', 'prop_type', 'pred_yards']].copy()
    summary_df = summary_df.sort_values(['team', 'opp', 'prop_type', 'pred_yards'], ascending=[True, True, True, False], na_position='last')
    summary_filename = f"{output_dir}/week{week_num}_all_props_summary.csv"
    summary_df.to_csv(summary_filename, index=False)
    
    # Clean up individual game files - keep only master reports
    print("🧹 Cleaning up individual game files...")
    for i, (team1, team2) in enumerate(games, 1):
        # Remove individual text files
        game_txt_file = f"{output_dir}/game_{i:02d}_{team1}_vs_{team2}_all_props.txt"
        if os.path.exists(game_txt_file):
            os.remove(game_txt_file)
        
        # Remove individual HTML files
        game_html_file = f"{output_dir}/game_{i:02d}_{team1}_vs_{team2}_all_props.html"
        if os.path.exists(game_html_file):
            os.remove(game_html_file)
    
    print("=" * 50)
    print("✅ Combined Props Report Complete!")
    print(f"📁 Output Directory: {output_dir}/")
    print(f"📄 Master Text Report: {master_filename}")
    print(f"🌐 Master HTML Report: {master_html_filename}")
    print(f"📊 Summary CSV: {summary_filename}")
    print(f"🗑️  Individual game files cleaned up - only master reports kept")
    print("")
    print("🎯 Master reports contain ALL props (passing, rushing, receiving)")
    print("   for all games in a single, comprehensive format!")
    print(f"💡 Open {master_html_filename} in your web browser to view the complete HTML report!")

if __name__ == "__main__":
    week_num = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    create_combined_report(week_num)
