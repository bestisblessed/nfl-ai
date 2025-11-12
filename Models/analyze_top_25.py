#!/usr/bin/env python3
"""
NFL Props Analysis - Top 25 Projections
Analyzes and displays the top 25 projections for each prop type from the final results.
Generates a professional HTML report and PDF.
"""

import pandas as pd
import sys
import os
from datetime import datetime
from weasyprint import HTML, CSS
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.backends.backend_pdf import PdfPages

# Check command line arguments
if len(sys.argv) != 2:
    print("Usage: python analyze_top_25.py <week_number>")
    print("Example: python analyze_top_25.py 5")
    sys.exit(1)

try:
    week_num = int(sys.argv[1])
    if week_num < 1 or week_num > 18:
        print("Error: Week number must be between 1 and 18")
        sys.exit(1)
except ValueError:
    print("Error: Week number must be a valid integer")
    sys.exit(1)

print(f"NFL Props Analysis - Week {week_num}")
print("=" * 50)
print()

# Load data
csv_file = f"0-FINAL-REPORTS/week{week_num}_all_props_summary.csv"
if not os.path.exists(csv_file):
    print(f"Error: File {csv_file} not found!")
    print("Make sure you've run the full report generation first.")
    sys.exit(1)

df = pd.read_csv(csv_file)
print(f"Loaded {len(df)} total projections from {csv_file}")
print()

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

# Define prop types
prop_types = [
    ("QB", "Passing Yards", "TOP 25 QB PASSING YARDS"),
    ("QB", "Rushing Yards", "TOP 25 QB RUSHING YARDS"),
    ("WR", "Receiving Yards", "TOP 25 WR RECEIVING YARDS"),
    ("TE", "Receiving Yards", "TOP 25 TE RECEIVING YARDS"),
    ("RB", "Rushing Yards", "TOP 25 RB RUSHING YARDS"),
    ("RB", "Receiving Yards", "TOP 25 RB RECEIVING YARDS")
]

# Generate HTML content (COMMENTED OUT)
# html_content = f"""<!DOCTYPE html>
# <html lang="en">
# <head>
#     <meta charset="UTF-8">
#     <meta name="viewport" content="width=device-width, initial-scale=1.0">
#     <title>NFL Week {week_num} - Top 25 Props Report</title>
#     <style>
#         body {{
#             font-family: 'Times New Roman', Times, serif;
#             margin: 0;
#             padding: 0;
#             background-color: #f8f9fa;
#             color: #333;
#         }}
#         .container {{
#             max-width: none;
#             margin: 0;
#             background: #f8f9fa;
#             border-radius: 0;
#             box-shadow: none;
#             overflow: hidden;
#         }}
#         .header {{
#             background: linear-gradient(135deg, #991b1b 0%, #7f1d1d 100%);
#             color: white;
#             padding: 30px;
#             text-align: center;
#         }}
#         .header h1 {{
#             margin: 0;
#             font-size: 2.5em;
#             font-weight: 300;
#         }}
#         .header p {{
#             margin: 10px 0 0 0;
#             font-size: 1.2em;
#             opacity: 0.9;
#         }}
#         .content {{
#             padding: 30px;
#             background: #f8f9fa;
#         }}
#         .table-section {{
#             margin-bottom: 40px;
#         }}
#         .table-title {{
#             font-size: 1.4em;
#             font-weight: 600;
#             color: #991b1b;
#             margin-bottom: 15px;
#             padding-bottom: 8px;
#             border-bottom: 2px solid #991b1b;
#         }}
#         table {{
#             width: 100%;
#             border-collapse: collapse;
#             margin-bottom: 20px;
#             background: white;
#             border-radius: 8px;
#             overflow: hidden;
#             box-shadow: 0 2px 4px rgba(0,0,0,0.1);
#         }}
#         th {{
#             background: #991b1b;
#             color: white;
#             padding: 15px;
#             text-align: left;
#             font-weight: 600;
#             font-size: 1.1em;
#         }}
#         td {{
#             padding: 12px 15px;
#             border-bottom: 1px solid #eee;
#         }}
#         tr:nth-child(even) {{
#             background-color: #f5f5f5;
#         }}
#         tr:hover {{
#             background-color: #fee2e2;
#         }}
#         .rank {{
#             font-weight: bold;
#             color: #991b1b;
#             width: 60px;
#         }}
#         .player {{
#             font-weight: 600;
#             width: 200px;
#         }}
#         .team {{
#             color: #666;
#             width: 80px;
#         }}
#         .yards {{
#             font-weight: bold;
#             color: #991b1b;
#             text-align: right;
#             width: 100px;
#         }}
#         .opponent {{
#             color: #666;
#             width: 80px;
#         }}
#         .footer {{
#             background: #f8f9fa;
#             padding: 20px;
#             text-align: center;
#             color: #666;
#             border-top: 1px solid #e5e5e5;
#         }}
#         .generated {{
#             font-size: 0.9em;
#             margin-top: 10px;
#         }}
#     </style>
# </head>
# <body>
#     <div class="container">
#         <div class="header">
#                     <h1>NFL Week {week_num} Props Report</h1>
#                     <p>Top 25 Projections by Position</p>
#         </div>
#         <div class="content">"""

# Process each prop type (COMMENTED OUT HTML GENERATION)
for position, prop_type, title in prop_types:
    print("=" * 80)
    print(title)
    print("=" * 80)
    
    # Filter and sort data
    filtered_df = df[(df['position'] == position) & (df['prop_type'] == prop_type)]
    
    if filtered_df.empty:
        print(f"No data found for {position} {prop_type}")
        print()
        continue
    
    # Get top 25
    top_25 = filtered_df.nlargest(25, 'pred_yards')
    
    # Print terminal output only (HTML generation commented out)
    for i, (_, row) in enumerate(top_25.iterrows(), 1):
        player = row['full_name']
        if player in questionable_players:
            player += " (Questionable)"
        team = row['team']
        opp = row['opp']
        yards = round(row['pred_yards'], 1)

        print(f"{i:2d}. {player} ({team}) - {yards:6.1f} yards vs {opp}")
    
    print()

# Complete HTML (COMMENTED OUT)
# html_content += f"""
#         </div>
#         <div class="footer">
#             <p>NFL Props Analysis Report</p>
#             <p class="generated">Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
#         </div>
#     </div>
# </body>
# </html>"""

# Save HTML report (COMMENTED OUT)
# html_filename = f"0-FINAL-REPORTS/week{week_num}_leaders.html"
# with open(html_filename, 'w') as f:
#     f.write(html_content)

# Generate PDF (COMMENTED OUT)
# pdf_filename = f"0-FINAL-REPORTS/week{week_num}_leaders.pdf"
# try:
#     from weasyprint import HTML, CSS
#     
#     html_doc = HTML(filename=html_filename)
#     css = CSS(string='''
#         @page { size: A4; margin: 0.75in; }
#         body { font-size: 12px; }
#         .header h1 { font-size: 2em; }
#         .table-title { font-size: 1.5em; }
#         th, td { padding: 8px 10px; font-size: 11px; }
#     ''')
#     
#     html_doc.write_pdf(pdf_filename, stylesheets=[css])
#     pdf_generated = True
# except ImportError:
#     pdf_generated = False

# Generate PNG Image Report (COMMENTED OUT)
# png_filename = f"0-FINAL-REPORTS/week{week_num}_leaders.png"
# try:
#     fig, axes = plt.subplots(len(prop_types), 1, figsize=(12, 2.5 * len(prop_types)))
#     if len(prop_types) == 1:
#         axes = [axes]
#     
#     fig.suptitle(f'NFL Week {week_num} - Top 25 Props Report', fontsize=16, fontweight='bold', y=0.98)
#     
#     for i, (position, prop_type, title) in enumerate(prop_types):
#         ax = axes[i]
#         filtered_df = df[(df['position'] == position) & (df['prop_type'] == prop_type)]
#         
#         if filtered_df.empty:
#             ax.text(0.5, 0.5, f'No data for {position} {prop_type}', ha='center', va='center', transform=ax.transAxes)
#             ax.set_title(title, fontsize=12, fontweight='bold', pad=10)
#             continue
#         
#         top_25 = filtered_df.nlargest(25, 'pred_yards')
#         
#         # Create table data
#         table_data = []
#         for j, (_, row) in enumerate(top_25.iterrows(), 1):
#             player = row['full_name']
#             team = row['team']
#             opp = row['opp']
#             yards = round(row['pred_yards'], 1)
#             table_data.append([f"{j:2d}", f"{player} ({team})", f"vs {opp}", f"{yards:6.1f} yards"])
#         
#         # Create table
#         table = ax.table(cellText=table_data,
#                         colLabels=['Rank', 'Player', 'Opponent', 'Predicted Yards'],
#                         cellLoc='left',
#                         loc='center',
#                         bbox=[0, 0, 1, 1])
#         
#         table.auto_set_font_size(False)
#         table.set_fontsize(9)
#         table.scale(1, 1.5)
#         
#         # Style the table
#         for j in range(len(table_data) + 1):
#             for k in range(4):
#                 cell = table[(j, k)]
#                 if j == 0:  # Header row
#                     cell.set_facecolor('#991b1b')
#                     cell.set_text_props(weight='bold', color='white')
#                 else:
#                     cell.set_facecolor('#f8f9fa' if j % 2 == 0 else 'white')
#                     if k == 0 or k == 3:  # Rank and yards columns
#                         cell.set_text_props(weight='bold', color='#991b1b')
#         
#         ax.set_title(title, fontsize=12, fontweight='bold', pad=10, color='#991b1b')
#         ax.axis('off')
#     
#     plt.tight_layout()
#     plt.savefig(png_filename, dpi=300, bbox_inches='tight', facecolor='white')
#     plt.close()
#     png_generated = True
# except Exception as e:
#     print(f"PNG generation failed: {e}")
#     png_generated = False

# Generate Terminal-Style PDF
terminal_pdf_filename = f"0-FINAL-REPORTS/week{week_num}_leader_tables.pdf"
try:
    with PdfPages(terminal_pdf_filename) as pdf:
        for position, prop_type, title in prop_types:
            filtered_df = df[(df['position'] == position) & (df['prop_type'] == prop_type)]
            
            if filtered_df.empty:
                continue
            
            top_25 = filtered_df.nlargest(25, 'pred_yards')
            
            fig, ax = plt.subplots(figsize=(8.5, 11))
            ax.set_xlim(0, 8.5)
            ax.set_ylim(0, 11)
            ax.axis('off')
            
            # Title
            ax.text(4.25, 10.5, title, ha='center', va='center', fontsize=14, fontweight='bold', fontfamily='monospace')
            
            # Table header
            ax.text(0.5, 10, "Rank", ha='left', va='center', fontsize=10, fontweight='bold', fontfamily='monospace')
            ax.text(2.0, 10, "Player", ha='left', va='center', fontsize=10, fontweight='bold', fontfamily='monospace')
            ax.text(5.0, 10, "Opponent", ha='left', va='center', fontsize=10, fontweight='bold', fontfamily='monospace')
            ax.text(7.0, 10, "Yards", ha='right', va='center', fontsize=10, fontweight='bold', fontfamily='monospace')
            
            # Separator line
            ax.plot([0.5, 8.0], [9.8, 9.8], 'k-', linewidth=0.5)
            
            # Data rows
            for i, (_, row) in enumerate(top_25.iterrows()):
                y_pos = 9.5 - (i * 0.3)
                player = row['full_name']
                team = row['team']
                opp = row['opp']
                yards = round(row['pred_yards'], 1)
                
                ax.text(0.5, y_pos, f"{i+1:2d}", ha='left', va='center', fontsize=9, fontfamily='monospace')
                ax.text(2.0, y_pos, f"{player} ({team})", ha='left', va='center', fontsize=9, fontfamily='monospace')
                ax.text(5.0, y_pos, f"vs {opp}", ha='left', va='center', fontsize=9, fontfamily='monospace')
                ax.text(7.0, y_pos, f"{yards:6.1f}", ha='right', va='center', fontsize=9, fontfamily='monospace')
            
            pdf.savefig(fig, bbox_inches='tight')
            plt.close(fig)
    
    terminal_pdf_generated = True
except Exception as e:
    print(f"Terminal-style PDF generation failed: {e}")
    terminal_pdf_generated = False

# Final output
if terminal_pdf_generated:
    print(f"Terminal-style PDF generated: {terminal_pdf_filename}")