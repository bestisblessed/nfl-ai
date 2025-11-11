#!/usr/bin/env python3
"""
Create an HTML report that combines all touchdown prediction summaries - v3
"""

import os
import sys
import glob
from datetime import datetime

def create_html_report(week_num):
    """Create an HTML report with all touchdown predictions."""
    
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
    <title>Week {week_num} Touchdown Predictions - v3</title>
    <style>
        body {{ font-family: 'Courier New', Courier, monospace; max-width: 1000px; margin: auto; padding: 20px; background-color: #f0f0f0; }}
        .header {{ background-color: #333; color: white; padding: 20px; text-align: center; margin-bottom: 20px; }}
        .game-section {{ background: white; margin-bottom: 20px; padding: 15px; border: 1px solid #ddd; }}
        pre {{ white-space: pre-wrap; word-wrap: break-word; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Week {week_num} Touchdown Predictions - v3</h1>
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

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python generate_html_reports.py <week_number>")
        sys.exit(1)
    
    try:
        week_num = int(sys.argv[1])
    except ValueError:
        print("Error: Week number must be a valid integer")
        sys.exit(1)
    
    create_html_report(week_num)
