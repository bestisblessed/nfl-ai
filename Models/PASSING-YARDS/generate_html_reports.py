#!/usr/bin/env python3
"""
Create an HTML report that combines all WR prediction images and summaries.
This creates a single HTML file that can be opened in a browser to view all results.
"""

import os
import sys
import glob
from datetime import datetime

def create_html_report_for_position(week_num, position):
    """Create an HTML report with all predictions for a specific position."""
    
    predictions_dir = f"predictions-week-{week_num}-{position}"
    
    if not os.path.exists(predictions_dir):
        print(f"Error: Directory {predictions_dir} not found!")
        return
    
    # Get all cleaned image files and sort them
    image_files = glob.glob(f"{predictions_dir}/game_*_{position}_predictions_cleaned.png")
    image_files.sort(key=lambda x: int(x.split('game_')[1].split('_')[0]))
    
    if not image_files:
        print(f"No cleaned image files found in {predictions_dir}")
        return
    
    # Create HTML file
    html_file = f"{predictions_dir}/final_week{week_num}_{position}_pass_yards_report.html"
    
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Week {week_num} {position} Passing Yards Predictions</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            text-align: center;
            margin-bottom: 30px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .header h1 {{
            margin: 0;
            font-size: 2.5em;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }}
        .header p {{
            margin: 10px 0 0 0;
            font-size: 1.2em;
            opacity: 0.9;
        }}
        .game-section {{
            background: white;
            margin-bottom: 30px;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .game-header {{
            background: #2c3e50;
            color: white;
            padding: 15px 20px;
            font-size: 1.3em;
            font-weight: bold;
        }}
        .game-content {{
            padding: 20px;
            text-align: center;
        }}
        .game-image {{
            max-width: 100%;
            height: auto;
            border-radius: 5px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .stats {{
            background: #ecf0f1;
            padding: 15px;
            margin-top: 15px;
            border-radius: 5px;
            text-align: left;
        }}
        .stats h4 {{
            margin: 0 0 10px 0;
            color: #2c3e50;
        }}
        .stats p {{
            margin: 5px 0;
            font-size: 0.9em;
        }}
        .toc {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 30px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .toc h3 {{
            margin-top: 0;
            color: #2c3e50;
        }}
        .toc ul {{
            list-style-type: none;
            padding: 0;
        }}
        .toc li {{
            padding: 8px 0;
            border-bottom: 1px solid #eee;
        }}
        .toc a {{
            text-decoration: none;
            color: #3498db;
            font-weight: bold;
        }}
        .toc a:hover {{
            color: #2980b9;
        }}
        .footer {{
            text-align: center;
            padding: 20px;
            color: #7f8c8d;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Week {week_num} {position} Passing Yards Predictions</h1>
        <p>Complete NFL Week {week_num} 2025 {position} Projections</p>
        <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
    
    <div class="toc">
        <h3>📋 Table of Contents</h3>
        <ul>
"""
    
    # Add table of contents
    for i, image_file in enumerate(image_files, 1):
        filename = os.path.basename(image_file)
        game_info = filename.replace(f'_{position}_predictions_cleaned.png', '')
        game_num = game_info.split('_')[0]
        teams = '_'.join(game_info.split('_')[1:])
        
        # Clean up team names
        team_parts = teams.split('_vs_')
        if len(team_parts) == 2:
            team1, team2 = team_parts[0], team_parts[1]
            clean_teams = f"{team1} vs {team2}"
        else:
            clean_teams = teams.replace('_', ' vs ')
        
        html_content += f'            <li><a href="#game-{i}">Game {i}: {clean_teams}</a></li>\n'
    
    html_content += """        </ul>
    </div>
"""
    
    # Add each game section
    for i, image_file in enumerate(image_files, 1):
        filename = os.path.basename(image_file)
        game_info = filename.replace(f'_{position}_predictions_cleaned.png', '')
        game_num = game_info.split('_')[0]
        teams = '_'.join(game_info.split('_')[1:])
        
        # Clean up team names
        team_parts = teams.split('_vs_')
        if len(team_parts) == 2:
            team1, team2 = team_parts[0], team_parts[1]
            clean_teams = f"{team1} vs {team2}"
        else:
            clean_teams = teams.replace('_', ' vs ')
        
        # Get relative path for image
        image_path = os.path.basename(image_file)
        
        html_content += f"""    <div class="game-section" id="game-{i}">
        <div class="game-header">
            Game {i}: {clean_teams}
        </div>
        <div class="game-content">
            <img src="{image_path}" alt="Week {week_num} {clean_teams} {position} Predictions" class="game-image">
            <div class="stats">
                <h4>📊 Game Information</h4>
                <p><strong>Week:</strong> {week_num}</p>
                <p><strong>Season:</strong> 2025</p>
            </div>
        </div>
    </div>
"""
    
    html_content += f"""    <div class="footer">
        <p>Week {week_num} {position} Passing Yards Predictions Report</p>
        <p>Generated by NFL AI Models | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
</body>
</html>"""
    
    with open(html_file, 'w') as f:
        f.write(html_content)
    
    print(f"🌐 {position} HTML report created: {html_file}")
    print(f"📊 Included {len(image_files)} games")
    print(f"💡 Open {html_file} in your web browser to view the complete report")

def create_all_html_reports(week_num):
    """Create HTML reports for all positions (WR, RB, TE)."""
    positions = ["QB"]
    for position in positions:
        create_html_report_for_position(week_num, position)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python create_html_report.py <week_number>")
        print("Example: python create_html_report.py 1")
        sys.exit(1)
    
    try:
        week_num = int(sys.argv[1])
        if week_num < 1 or week_num > 18:
            print("Error: Week number must be between 1 and 18")
            sys.exit(1)
    except ValueError:
        print("Error: Week number must be a valid integer")
        sys.exit(1)
    
    create_all_html_reports(week_num)
