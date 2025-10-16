#!/usr/bin/env python3
"""
Generate Final QB Interception Report
Creates a visual HTML report with tables and charts from model predictions
"""

import pandas as pd
import os
from datetime import datetime
import argparse
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
import base64

def load_model_predictions(week_num, model_name):
    """Load predictions for a specific model and week"""
    filename = f"predictions/upcoming_qb_interception_{model_name}_week_{week_num}.csv"
    if os.path.exists(filename):
        return pd.read_csv(filename)
    return None

def load_edge_analysis(week_num):
    """Load edge analysis for the specified week"""
    filename = f"predictions/upcoming_qb_interception_edges_week_{week_num}.csv"
    if os.path.exists(filename):
        return pd.read_csv(filename)
    return None

def create_probability_chart(df, model_name, week_num):
    """Create a probability chart for interception likelihood"""
    if df is None or len(df) == 0:
        return None

    # Convert American odds to probabilities for visualization
    def american_to_prob(odds):
        if pd.isna(odds):
            return 0.5
        odds = float(odds)
        if odds > 0:
            return 100 / (odds + 100)
        else:
            return abs(odds) / (abs(odds) + 100)

    # Show all players for complete analysis
    all_players = df.copy()
    all_players['interception_prob'] = all_players['interception_american_odds'].apply(american_to_prob)

    # Create horizontal bar chart with larger size for all players
    plt.figure(figsize=(12, len(all_players) * 0.4))  # Dynamic height based on number of players
    bars = plt.barh(range(len(all_players)), all_players['interception_prob'] * 100)

    # Color bars based on probability
    for i, (bar, prob) in enumerate(zip(bars, all_players['interception_prob'])):
        if prob > 0.5:
            bar.set_color('#ff6b6b')  # Red for high probability
        elif prob > 0.4:
            bar.set_color('#ffa726')  # Orange for medium
        else:
            bar.set_color('#66bb6a')  # Green for low

    plt.yticks(range(len(all_players)), [f"{row['player']}\n({row['team']}@{row['opponent']})"
                                        for _, row in all_players.iterrows()], fontsize=8)
    plt.xlabel('Interception Probability (%)')
    plt.title(f'{model_name.replace("_", " ").title()} - All QB Interception Probabilities (Week {week_num})')
    plt.grid(axis='x', alpha=0.3)
    plt.tight_layout()

    # Convert to base64 for embedding in HTML
    buffer = BytesIO()
    plt.savefig(buffer, format='png', bbox_inches='tight', dpi=150)
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    plt.close()

    return image_base64

def create_edge_chart(edge_df, week_num):
    """Create a chart showing betting edges"""
    if edge_df is None or len(edge_df) == 0:
        return None

    # Filter to positive edges only
    positive_edges = edge_df[edge_df['Edge %'].str.rstrip('%').astype(float) > 0]

    if len(positive_edges) == 0:
        return None

    plt.figure(figsize=(10, 6))
    edges = positive_edges['Edge %'].str.rstrip('%').astype(float)
    players = [f"{row['Player']}\n({row['Tm']}@{row['Opp']})" for _, row in positive_edges.iterrows()]

    bars = plt.bar(range(len(edges)), edges)
    plt.xticks(range(len(players)), players, rotation=45, ha='right')
    plt.ylabel('Edge Advantage (%)')
    plt.title(f'Betting Edges - Model vs DraftKings (Week {week_num})')
    plt.grid(axis='y', alpha=0.3)

    # Color bars by edge size
    for bar, edge in zip(bars, edges):
        if edge > 10:
            bar.set_color('#4caf50')  # Green for strong edges
        elif edge > 5:
            bar.set_color('#ff9800')  # Orange for moderate
        else:
            bar.set_color('#2196f3')  # Blue for small

    plt.tight_layout()

    # Convert to base64
    buffer = BytesIO()
    plt.savefig(buffer, format='png', bbox_inches='tight', dpi=150)
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    plt.close()

    return image_base64

def generate_html_report(week_num):
    """Generate the complete HTML report"""

    # Load all data
    lr_df = load_model_predictions(week_num, 'logistic_regression')
    rf_df = load_model_predictions(week_num, 'random_forest')
    xgb_df = load_model_predictions(week_num, 'xgboost')
    edge_df = load_edge_analysis(week_num)

    # Set up matplotlib style
    plt.style.use('default')
    sns.set_palette("husl")

    # Generate charts
    lr_chart = create_probability_chart(lr_df, 'Logistic Regression', week_num)
    rf_chart = create_probability_chart(rf_df, 'Random Forest', week_num)
    xgb_chart = create_probability_chart(xgb_df, 'XGBoost', week_num)
    edge_chart = create_edge_chart(edge_df, week_num)

    # HTML Template
    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>QB Interception Report - Week {week_num}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f8f9fa;
        }}
        .header {{
            text-align: center;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .header h1 {{
            margin: 0;
            font-size: 2.5em;
        }}
        .header p {{
            margin: 10px 0 0 0;
            opacity: 0.9;
        }}
        .section {{
            background: white;
            margin-bottom: 30px;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .section h2 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
            margin-top: 0;
        }}
        .model-comparison {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        .model-card {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            border-left: 4px solid #3498db;
        }}
        .model-card h3 {{
            margin: 0 0 10px 0;
            color: #2c3e50;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            background: white;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background-color: #f8f9fa;
            font-weight: 600;
            color: #2c3e50;
        }}
        tr:hover {{
            background-color: #f5f5f5;
        }}
        .edge-positive {{
            background-color: #d4edda;
            border-left: 4px solid #28a745;
        }}
        .edge-negative {{
            background-color: #f8d7da;
            border-left: 4px solid #dc3545;
        }}
        .chart-container {{
            text-align: center;
            margin: 20px 0;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 8px;
        }}
        .chart-container img {{
            max-width: 100%;
            height: auto;
            border-radius: 5px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .interpretation {{
            background: #e3f2fd;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
        }}
        .interpretation h3 {{
            color: #1976d2;
            margin-top: 0;
        }}
        .betting-tips {{
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            padding: 15px;
            border-radius: 8px;
            margin: 20px 0;
        }}
        .footer {{
            text-align: center;
            margin-top: 40px;
            padding: 20px;
            color: #666;
            font-size: 0.9em;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }}
        .stat-card {{
            background: white;
            padding: 15px;
            border-radius: 8px;
            text-align: center;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .stat-value {{
            font-size: 2em;
            font-weight: bold;
            color: #3498db;
        }}
        .stat-label {{
            color: #666;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🏈 QB Interception Prediction Report</h1>
        <p>Week {week_num} | Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>

    <div class="section">
        <h2>📊 Overview & Statistics</h2>
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">{len(lr_df) if lr_df is not None else 0}</div>
                <div class="stat-label">QBs Analyzed</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{len(edge_df) if edge_df is not None else 0}</div>
                <div class="stat-label">Betting Opportunities</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{len(edge_df[edge_df['Edge %'].str.rstrip('%').astype(float) > 0]) if edge_df is not None else 0}</div>
                <div class="stat-label">Positive Edges Found</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">3</div>
                <div class="stat-label">ML Models Used</div>
            </div>
        </div>
    </div>
"""

    # Add model predictions sections
    if lr_df is not None:
        html_content += f"""
    <div class="section">
        <h2>🤖 Logistic Regression Model</h2>
        <p>All QBs ranked by interception probability</p>
        <table>
            <thead>
                <tr>
                    <th>Rank</th>
                    <th>Player</th>
                    <th>Team</th>
                    <th>Opponent</th>
                    <th>Home/Away</th>
                    <th>Int Odds</th>
                    <th>No Int Odds</th>
                </tr>
            </thead>
            <tbody>
"""

        for i, (_, row) in enumerate(lr_df.iterrows()):
            html_content += f"""
                <tr>
                    <td>{i+1}</td>
                    <td>{row['player']}</td>
                    <td>{row['team']}</td>
                    <td>{row['opponent']}</td>
                    <td>{row['home_away']}</td>
                    <td>{row['interception_american_odds']}</td>
                    <td>{row['no_interception_american_odds']}</td>
                </tr>
"""

        html_content += """
            </tbody>
        </table>
"""

        if lr_chart:
            html_content += f"""
        <div class="chart-container">
            <h3>Complete Interception Probability Analysis</h3>
            <img src="data:image/png;base64,{lr_chart}" alt="Logistic Regression All Probabilities">
        </div>
"""

        html_content += "</div>"

    if rf_df is not None:
        html_content += f"""
    <div class="section">
        <h2>🌳 Random Forest Model</h2>
        <p>All QBs ranked by interception probability</p>
        <table>
            <thead>
                <tr>
                    <th>Rank</th>
                    <th>Player</th>
                    <th>Team</th>
                    <th>Opponent</th>
                    <th>Home/Away</th>
                    <th>Int Odds</th>
                    <th>No Int Odds</th>
                </tr>
            </thead>
            <tbody>
"""

        for i, (_, row) in enumerate(rf_df.iterrows()):
            html_content += f"""
                <tr>
                    <td>{i+1}</td>
                    <td>{row['player']}</td>
                    <td>{row['team']}</td>
                    <td>{row['opponent']}</td>
                    <td>{row['home_away']}</td>
                    <td>{row['interception_american_odds']}</td>
                    <td>{row['no_interception_american_odds']}</td>
                </tr>
"""

        html_content += """
            </tbody>
        </table>
"""

        if rf_chart:
            html_content += f"""
        <div class="chart-container">
            <h3>Complete Interception Probability Analysis</h3>
            <img src="data:image/png;base64,{rf_chart}" alt="Random Forest All Probabilities">
        </div>
"""

        html_content += "</div>"

    if xgb_df is not None:
        html_content += f"""
    <div class="section">
        <h2>🚀 XGBoost Model</h2>
        <p>All QBs ranked by interception probability</p>
        <table>
            <thead>
                <tr>
                    <th>Rank</th>
                    <th>Player</th>
                    <th>Team</th>
                    <th>Opponent</th>
                    <th>Home/Away</th>
                    <th>Int Odds</th>
                    <th>No Int Odds</th>
                </tr>
            </thead>
            <tbody>
"""

        for i, (_, row) in enumerate(xgb_df.iterrows()):
            html_content += f"""
                <tr>
                    <td>{i+1}</td>
                    <td>{row['player']}</td>
                    <td>{row['team']}</td>
                    <td>{row['opponent']}</td>
                    <td>{row['home_away']}</td>
                    <td>{row['interception_american_odds']}</td>
                    <td>{row['no_interception_american_odds']}</td>
                </tr>
"""

        html_content += """
            </tbody>
        </table>
"""

        if xgb_chart:
            html_content += f"""
        <div class="chart-container">
            <h3>Complete Interception Probability Analysis</h3>
            <img src="data:image/png;base64,{xgb_chart}" alt="XGBoost All Probabilities">
        </div>
"""

        html_content += "</div>"

    # Add edge analysis
    if edge_df is not None and len(edge_df) > 0:
        html_content += f"""
    <div class="section">
        <h2>🎯 Betting Edge Analysis</h2>
        <p>Model advantage over DraftKings odds (sorted by edge percentage)</p>
        <table>
            <thead>
                <tr>
                    <th>Rank</th>
                    <th>Player</th>
                    <th>Edge %</th>
                    <th>Book Odds</th>
                    <th>Model Odds</th>
                    <th>True Model %</th>
                    <th>True Book %</th>
                    <th>Team</th>
                    <th>Opp</th>
                    <th>Time</th>
                </tr>
            </thead>
            <tbody>
"""

        for _, row in edge_df.iterrows():
            edge_pct = float(str(row['Edge %']).rstrip('%'))
            css_class = "edge-positive" if edge_pct > 0 else "edge-negative"
            html_content += f"""
                <tr class="{css_class}">
                    <td>{int(row['Rank'])}</td>
                    <td>{row['Player']}</td>
                    <td>{row['Edge %']}</td>
                    <td>{row['Book Line']}</td>
                    <td>{row['Model Line (True)']}</td>
                    <td>{row['Model % Prob (True)']}</td>
                    <td>{row['Book % Prob (True)']}</td>
                    <td>{row['Tm']}</td>
                    <td>{row['Opp']}</td>
                    <td>{row['Time']}</td>
                </tr>
"""

        html_content += """
            </tbody>
        </table>
"""

        if edge_chart:
            html_content += f"""
        <div class="chart-container">
            <h3>Positive Edge Opportunities</h3>
            <img src="data:image/png;base64,{edge_chart}" alt="Betting Edges Chart">
        </div>
"""

        html_content += "</div>"

    # Add interpretation section
    html_content += """
    <div class="section interpretation">
        <h2>📋 How to Interpret Results</h2>

        <h3>Model Predictions</h3>
        <ul>
            <li><strong>Int Odds</strong>: American odds for QB throwing an interception</li>
            <li><strong>No Int Odds</strong>: American odds for QB NOT throwing an interception</li>
            <li><strong>Negative odds (-)</strong> = Favorite (e.g., -150 means bet $150 to win $100)</li>
            <li><strong>Positive odds (+)</strong> = Underdog (e.g., +150 means bet $100 to win $150)</li>
        </ul>

        <h3>Edge Analysis</h3>
        <ul>
            <li><strong>Edge %</strong>: Positive values indicate model advantage over sportsbook</li>
            <li><strong>Book Odds</strong>: Current DraftKings betting line</li>
            <li><strong>Model Odds</strong>: What the model thinks the true odds should be</li>
            <li><strong>True %</strong>: Probabilities with bookmaker profit margin (vig) removed</li>
        </ul>
    </div>

    <div class="betting-tips">
        <h3>🎲 Betting Strategy</h3>
        <ul>
            <li>Focus on plays with <strong>positive Edge %</strong> (model has advantage)</li>
            <li>Higher edge percentages indicate better betting opportunities</li>
            <li>Always gamble responsibly and within your means</li>
            <li>Use multiple models for consensus before placing bets</li>
        </ul>
    </div>

    <div class="footer">
        <p>Report generated automatically by QB Interception Prediction Pipeline</p>
        <p>Week {week_num} | {datetime.now().strftime('%Y-%m-%d')}</p>
    </div>
</body>
</html>
"""

    return html_content

def main():
    parser = argparse.ArgumentParser(description="Generate final QB interception report")
    parser.add_argument("--week", type=int, required=True, help="Week number for the report")
    parser.add_argument("--output", type=str, help="Output filename (default: week_[week]_report.html)")

    args = parser.parse_args()

    if args.output:
        output_file = args.output
    else:
        output_file = f"predictions/week_{args.week}_qb_interception_report.html"

    print(f"📋 Generating final report for Week {args.week}...")

    # Generate HTML content
    html_content = generate_html_report(args.week)

    # Save to file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"✅ Report saved to: {output_file}")
    print("📱 Open in your browser to view the interactive report with charts and tables!")

if __name__ == "__main__":
    main()
