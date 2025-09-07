#!/usr/bin/env python3
"""
Merge all WR prediction reports into a single comprehensive report.
Combines text outputs and references to cleaned images.
"""

import os
import sys
import glob
from datetime import datetime

def merge_position_reports(week_num, position):
    """Merge all prediction reports for a given week and position."""
    
    # Define the predictions directory
    predictions_dir = f"predictions-week-{week_num}-{position}"
    
    if not os.path.exists(predictions_dir):
        print(f"Error: Directory {predictions_dir} not found!")
        return
    
    # Get all text files and sort them by game number
    txt_files = glob.glob(f"{predictions_dir}/game_*_{position}_predictions.txt")
    txt_files.sort(key=lambda x: int(x.split('game_')[1].split('_')[0]))
    
    if not txt_files:
        print(f"No text files found in {predictions_dir}")
        return
    
    # Create the merged report
    output_file = f"{predictions_dir}/final_week{week_num}_{position}_rush_yards_report.txt"
    
    with open(output_file, 'w') as outfile:
        # Write header
        position_name = {"QB": "QB RUSHING YARDS", "RB": "RB RUSHING YARDS"}
        outfile.write(f"WEEK {week_num} 2025 - COMPLETE {position_name.get(position, position)} PREDICTIONS\n")
        outfile.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        outfile.write(f"Total Games: {len(txt_files)}\n")
        outfile.write("=" * 80 + "\n\n")
        

        
        # Write each game's predictions
        for i, txt_file in enumerate(txt_files, 1):
            # Extract game info from filename
            filename = os.path.basename(txt_file)
            game_info = filename.replace(f'_{position}_predictions.txt', '')
            game_num = game_info.split('_')[0]
            teams = '_'.join(game_info.split('_')[1:])
            
            # Clean up team names (remove game number prefix and fix formatting)
            team_parts = teams.split('_vs_')
            if len(team_parts) == 2:
                team1, team2 = team_parts[0], team_parts[1]
                # Remove game number prefix (e.g., "01_PHI" -> "PHI")
                team1 = team1.split('_', 1)[-1] if '_' in team1 else team1
                team2 = team2.split('_', 1)[-1] if '_' in team2 else team2
                clean_teams = f"{team1} vs {team2}"
            else:
                # Fallback: remove all game number prefixes
                clean_teams = teams.replace('_', ' vs ')
                # Remove leading numbers (e.g., "01 PHI" -> "PHI")
                import re
                clean_teams = re.sub(r'\b\d+\s+', '', clean_teams)
            
            # Read the text file content
            try:
                with open(txt_file, 'r') as infile:
                    content = infile.read()
                
                # Write game header with clean title format
                outfile.write(f"GAME {i} | {clean_teams} | Week {week_num} 2025\n")
                
                # Process content to remove redundant title lines and game summary
                lines = content.split('\n')
                
                # Find table start
                content_start = 0
                for j, line in enumerate(lines):
                    if line.startswith('+') or line.startswith('|'):
                        content_start = j
                        break
                
                # Find table end (before game summary)
                content_end = len(lines)
                for j in range(content_start, len(lines)):
                    if 'GAME SUMMARY' in lines[j] or lines[j].startswith('=') and j > content_start + 5:
                        content_end = j
                        break
                
                # Write only the table content (no title, no summary)
                table_content = '\n'.join(lines[content_start:content_end]).strip()
                outfile.write(table_content)
                outfile.write("\n\n" + "=" * 60 + "\n\n")
                
            except Exception as e:
                outfile.write(f"Error reading {txt_file}: {e}\n\n")
        
        # Write footer with instructions
        outfile.write("\n" + "=" * 80 + "\n")
        outfile.write("REPORT COMPLETE\n")
        outfile.write("=" * 80 + "\n")
        outfile.write(f"This report contains all {position} rushing yards predictions for Week " + str(week_num) + ".\n")
        outfile.write("Each game includes:\n")
        outfile.write("• Text summary of predictions\n")
        outfile.write("• Full detailed image\n")
        outfile.write("• Cleaned/condensed image\n")
        outfile.write("\nFor the complete dataset, see: prop_projections_rushing.csv\n")
        outfile.write("=" * 80 + "\n")
    
    print(f"✅ Merged {position} report created: {output_file}")
    print(f"📊 Combined {len(txt_files)} games into single report")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python merge_reports.py <week_number>")
        print("Example: python merge_reports.py 1")
        sys.exit(1)
    
    try:
        week_num = int(sys.argv[1])
        if week_num < 1 or week_num > 18:
            print("Error: Week number must be between 1 and 18")
            sys.exit(1)
    except ValueError:
        print("Error: Week number must be a valid integer")
        sys.exit(1)
    
    # Merge reports for all positions
    positions = ["QB", "RB"]
    for position in positions:
        merge_position_reports(week_num, position)
