#!/usr/bin/env python3
"""
Generate HTML report for v3 touchdown predictions
"""

import os
import sys
import glob
from datetime import datetime


def main():
    week_num = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    predictions_dir = f"predictions-week-{week_num}-TD"
    
    if not os.path.exists(predictions_dir):
        print(f"Error: Directory {predictions_dir} not found!")
        return
    
    txt_files = glob.glob(f"{predictions_dir}/game_*.txt")
    txt_files.sort(key=lambda x: int(x.split('game_')[1].split('_')[0]))
    
    if not txt_files:
        print(f"No game reports found in {predictions_dir}")
        return
    
    html_file = f"{predictions_dir}/final_week{week_num}_TD_report.html"
    
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Week {week_num} Touchdown Predictions (v3)</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }}
        .container {{
            background: white;
            border-radius: 10px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0 0 10px 0;
            font-size: 2.5em;
        }}
        .header .subtitle {{
            font-size: 1.2em;
            opacity: 0.9;
        }}
        .header .timestamp {{
            margin-top: 10px;
            font-size: 0.9em;
            opacity: 0.7;
        }}
        .info-box {{
            background: #3498db;
            color: white;
            padding: 15px;
            margin: 20px;
            border-radius: 5px;
            text-align: center;
        }}
        .game-section {{
            background: #f8f9fa;
            margin: 20px;
            padding: 20px;
            border-radius: 8px;
            border-left: 5px solid #3498db;
        }}
        .game-section:hover {{
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            transform: translateY(-2px);
            transition: all 0.3s ease;
        }}
        pre {{
            font-family: 'Courier New', Courier, monospace;
            white-space: pre-wrap;
            word-wrap: break-word;
            background: white;
            padding: 15px;
            border-radius: 5px;
            overflow-x: auto;
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
    <div class="container">
        <div class="header">
            <h1>🏈 Week {week_num} Touchdown Predictions</h1>
            <div class="subtitle">Model Version 3 (Hybrid Enhanced)</div>
            <div class="timestamp">Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
        </div>
        
        <div class="info-box">
            <strong>Model v3 Features:</strong> Position-Specific Models | Multi-Window Rolling Stats (3/5/8 games) | 
            Isotonic Calibration | Enhanced Team Context | Target Share Analysis | TD Trend Tracking
        </div>
"""
    
    for txt_file in txt_files:
        with open(txt_file, 'r') as f:
            game_content = f.read()
        
        html_content += f"""        <div class="game-section">
            <pre>{game_content}</pre>
        </div>
"""
    
    html_content += f"""        <div class="footer">
            <p>Model v3 combines position-specific training with enhanced features from v1 and v2</p>
            <p>Predictions are for entertainment purposes only</p>
        </div>
    </div>
</body>
</html>"""
    
    with open(html_file, 'w') as f:
        f.write(html_content)
    
    print(f"HTML report created: {html_file}")


if __name__ == "__main__":
    main()
