#!/usr/bin/env python3
"""
Value Opportunities Report Generator
Creates:
- HTML full report grouped by game and prop, with edges and best lines
- PDF leader tables (top 25 edges) per (position, prop_type)

Inputs:
- 10-ARBITRAGE/data/week{WEEK}_value_opportunities.csv

Outputs:
- 10-ARBITRAGE/data/week{WEEK}_value_full_report.html
- 10-ARBITRAGE/data/week{WEEK}_value_leader_tables.pdf
"""

import os
import sys
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages


def load_value_csv(week: int, models_dir: str) -> pd.DataFrame:
    # Use absolute paths based on models_dir
    input_path = os.path.join(models_dir, f"10-ARBITRAGE/data/week{week}_value_opportunities.csv")
    if os.path.exists(input_path):
        df = pd.read_csv(input_path)
    else:
        raise FileNotFoundError(f"Could not find value opportunities CSV for week {week} at {input_path}")
    
    # Load and merge commence_time from events CSV if not already present
    if "commence_time" not in df.columns or df["commence_time"].isna().all():
        events_path = os.path.join(models_dir, f"10-ARBITRAGE/data/week{week}_events.csv")
        if os.path.exists(events_path):
            events_df = pd.read_csv(events_path)
            # Ensure commence_time is datetime
            if "commence_time" in events_df.columns:
                events_df["commence_time"] = pd.to_datetime(events_df["commence_time"], utc=True)
            # Merge on home_team and away_team
            df = pd.merge(df, events_df, on=["home_team", "away_team"], how="left", suffixes=("", "_events"))
            # If merge failed, try swapping home/away
            if "commence_time" in df.columns and df["commence_time"].isna().any():
                events_swapped = events_df.rename(columns={"home_team": "away_team", "away_team": "home_team"})
                missing_mask = df["commence_time"].isna()
                missing_rows = df[missing_mask][["home_team", "away_team"]].copy()
                missing_merged = pd.merge(missing_rows, events_swapped, on=["home_team", "away_team"], how="left")
                if "commence_time" in missing_merged.columns:
                    missing_merged["commence_time"] = pd.to_datetime(missing_merged["commence_time"], utc=True)
                    df.loc[missing_mask, "commence_time"] = missing_merged["commence_time"].values
            # Clean up any extra columns
            df = df.drop(columns=[col for col in df.columns if col.endswith("_events")], errors="ignore")
    
    return df


def build_html_report(df: pd.DataFrame, week: int, models_dir: str) -> str:
    css = """
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
            color: #333;
        }

        .container { max-width: 1100px; margin: 0 auto; padding: 24px; }
        .header {
            background: linear-gradient(135deg, #3498db, #2c3e50);
            color: #fff;
            padding: 24px;
            border-radius: 12px;
            margin-bottom: 24px;
            text-align: center;
        }
        .header h1 { margin: 0 0 8px 0; font-weight: 700; font-size: 24px; }
        .header p { margin: 0; opacity: .9; }
        .game {
            background: #fff;
            border-radius: 12px;
            padding: 16px;
            margin: 16px 0;
            box-shadow: 0 1px 3px rgba(0,0,0,0.06);
        }
        .game h2 {
            margin: 0 0 4px 0;
            font-size: 18px;
            color: #2c3e50;
            text-align: center;
            border-bottom: none;
            padding-bottom: 0;
        }

        .game-subtitle {
            font-size: 14px;
            color: #7f8c8d;
            text-align: center;
            margin-bottom: 12px;
            font-weight: normal;
        }
        .section { margin-top: 8px; }
        .section h3 {
            margin: 12px 0 6px 0;
            font-size: 14px;
            color: #27ae60;
            text-transform: uppercase;
            letter-spacing: .03em;
            text-align: center;
            padding: 10px;
            background-color: #ecf0f1;
            border-left: 4px solid #27ae60;
            border-radius: 5px;
        }
        table { width: 100%; border-collapse: collapse; }
        th, td { text-align: left; padding: 8px 10px; font-size: 13px; border-bottom: 1px solid #e5e7eb; }
        th { background: #2c3e50; color: #fff; position: sticky; top: 0; }
        tr:hover td { background: #f9fafb; }
        .num { text-align: right; font-variant-numeric: tabular-nums; }
        .pill { display: inline-block; padding: 2px 8px; border-radius: 999px; font-size: 12px; }
        .over { background: #dcfce7; color: #166534; }
        .under { background: #fee2e2; color: #991b1b; }
        .footer { text-align: center; color: #64748b; margin: 24px 0 8px 0; font-size: 12px; }
        .toc {
            background: white;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 30px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        .toc h3 {
            color: #2c3e50;
            margin-bottom: 15px;
        }
        .toc ul {
            list-style-type: none;
            padding: 0;
        }
        .toc li {
            padding: 8px 0;
            border-bottom: 1px solid #ecf0f1;
        }
        .toc a {
            color: #3498db;
            text-decoration: none;
            font-weight: 500;
        }
        .toc a:hover {
            text-decoration: underline;
        }
        .toc-time {
            color: #7f8c8d;
            font-size: 0.9em;
            font-weight: 400;
            font-style: italic;
            margin-left: 8px;
        }
    </style>
    """
    head = f"""<!doctype html><html><head><meta charset="utf-8"><title>Week {week} Value Sheet</title>{css}</head><body>"""
    header = f"""
    <div class="container">
      <div class="header">
        <h1>NFL Week {week} - Value Sheet</h1>
      </div>
    """
    # Order games using upcoming_games.csv order (same as regular props report)
    df_local = df.copy()
    df_local["game_key"] = df_local.apply(lambda r: f"{r['home_team']} vs {r['away_team']}", axis=1)

    # Read game order from upcoming_games.csv (same as regular props report)
    upcoming_file = os.path.join(models_dir, "upcoming_games.csv")
    if os.path.exists(upcoming_file):
        upcoming_df = pd.read_csv(upcoming_file)
        games = []
        for _, row in upcoming_df.iterrows():
            home_team = row['home_team']
            away_team = row['away_team']
            # Check both possible game key formats (home vs away and away vs home)
            game_key1 = f"{home_team} vs {away_team}"
            game_key2 = f"{away_team} vs {home_team}"
            if game_key1 in df_local["game_key"].values:
                games.append(game_key1)
            elif game_key2 in df_local["game_key"].values:
                games.append(game_key2)
        # Remove duplicates while preserving order
        games = list(dict.fromkeys(games))
        # If no matches (e.g., upcoming uses abbreviations but df has full names),
        # fall back to using all games present in the data
        if not games:
            games = df_local["game_key"].dropna().unique().tolist()
            games.sort()
    else:
        # Fallback to lexicographic sorting if upcoming_games.csv not found
        games = df_local["game_key"].dropna().unique().tolist()
        games.sort()

    # Create a mapping of game to commence time and date in EST, and sort games chronologically
    game_times = {}
    game_times_for_sorting = {}
    if "commence_time" in df_local.columns:
        for game in games:
            gdf = df_local[df_local["game_key"] == game]
            if not gdf.empty and pd.notna(gdf["commence_time"].iloc[0]):
                # Convert UTC to Eastern time
                utc_time = pd.to_datetime(gdf["commence_time"].iloc[0], utc=True)
                # Ensure timezone-aware
                if utc_time.tz is None:
                    utc_time = utc_time.tz_localize('UTC')
                
                # Use UTC-5 for 1 PM games (18:00 UTC), UTC-4 for later games (EDT)
                utc_hour = utc_time.hour
                if utc_hour == 18:
                    # 1 PM EST games
                    eastern_time = utc_time - pd.Timedelta(hours=5)
                    tz_label = "EST"
                else:
                    # Later games use EDT
                    eastern_time = utc_time - pd.Timedelta(hours=4)
                    tz_label = "EDT"
                
                # Format as date and time
                date_str = eastern_time.strftime('%m/%d')
                time_str = eastern_time.strftime('%I:%M %p ' + tz_label).lstrip('0')
                game_times[game] = f"{date_str} - {time_str}"
                game_times_for_sorting[game] = utc_time
    
    # Sort games by commence time (chronologically)
    if game_times_for_sorting:
        games_with_time = [g for g in games if g in game_times_for_sorting]
        games_without_time = [g for g in games if g not in game_times_for_sorting]
        # Convert to timestamp for comparison to avoid timezone issues
        games_with_time.sort(key=lambda g: game_times_for_sorting[g].timestamp())
        games = games_with_time + games_without_time

    # Create table of contents
    toc_parts = []
    toc_parts.append('<div class="toc">')
    toc_parts.append('<h3>📋 Game Schedule</h3>')
    toc_parts.append('<ul>')

    # Create mapping of game to display info for TOC
    game_info = {}
    game_display_names = {}
    
    # Parse all games to create display names
    for game in games:
        # Parse game key to extract teams (format: "Home Team vs Away Team")
        if " vs " in game:
            parts = game.split(" vs ", 1)
            home_team = parts[0]
            away_team = parts[1]
            game_display_names[game] = f"{away_team} @ {home_team}"
        else:
            game_display_names[game] = game
    
    # Add time information if available
    if "commence_time" in df_local.columns:
        for game in games:
            gdf = df_local[df_local["game_key"] == game]
            if not gdf.empty and pd.notna(gdf["commence_time"].iloc[0]):
                utc_time = pd.to_datetime(gdf["commence_time"].iloc[0], utc=True)
                # Ensure timezone-aware
                if utc_time.tz is None:
                    utc_time = utc_time.tz_localize('UTC')
                
                # Use UTC-5 for 1 PM games (18:00 UTC), UTC-4 for later games (EDT)
                utc_hour = utc_time.hour
                if utc_hour == 18:
                    # 1 PM EST games
                    eastern_time = utc_time - pd.Timedelta(hours=5)
                    tz_label = "EST"
                else:
                    # Later games use EDT
                    eastern_time = utc_time - pd.Timedelta(hours=4)
                    tz_label = "EDT"
                
                date_str = eastern_time.strftime('%m/%d')
                time_str = eastern_time.strftime('%I:%M %p ' + tz_label).lstrip('0')
                game_info[game] = f"<span class='toc-time'>{date_str} - {time_str}</span>"
            else:
                game_info[game] = "<span class='toc-time'>Time TBA</span>"
    else:
        # No commence_time column, set all to TBA
        for game in games:
            game_info[game] = "<span class='toc-time'>Time TBA</span>"

    for i, game in enumerate(games, 1):
        display_name = game_display_names.get(game, game)
        time_info = game_info.get(game, "<span class='toc-time'>Time TBA</span>")
        toc_parts.append(f'<li><a href="#game{i:02d}">{display_name}</a> {time_info}</li>')

    toc_parts.append('</ul>')
    toc_parts.append('</div>')

    body_parts = []
    body_parts.extend(toc_parts)

    for i, game in enumerate(games, 1):
        gdf = df_local[df_local["game_key"] == game].copy()
        if gdf.empty:
            continue

        # Create game header with title and subtitle
        game_header = f'<h2>{game}</h2>'
        if game in game_times:
            game_header += f'<div class="game-subtitle">{game_times[game]}</div>'

        body_parts.append(f'<div id="game{i:02d}" class="game">{game_header}')
        # For readability: group by prop_type then position
        for prop_type in ["Passing Yards", "Receiving Yards", "Rushing Yards"]:
            pdf = gdf[gdf["prop_type"] == prop_type].copy()
            if pdf.empty:
                continue
            body_parts.append(f'<div class="section"><h3>{prop_type}</h3>')
            # Columns to show
            cols = ["player","position","team","opp","side","best_point","best_price","bookmaker","predicted_yards","edge_yards"]
            rows = []
            for _, row in pdf.sort_values("edge_yards", ascending=False).iterrows():
                side = str(row.get("side",""))
                pill_cls = "over" if side.lower()=="over" else "under"
                rows.append(f"""
                <tr>
                  <td>{row['player']}</td>
                  <td>{row['position']}</td>
                  <td>{row['team']}</td>
                  <td>{row['opp']}</td>
                  <td><span class="pill {pill_cls}">{side}</span></td>
                  <td class="num">{row['best_point']:.1f}</td>
                  <td class="num">{row['best_price']:.0f}</td>
                  <td>{row['bookmaker']}</td>
                  <td class="num">{row['predicted_yards']:.1f}</td>
                  <td class="num">{row['edge_yards']:.1f}</td>
                </tr>
                """)
            table = f"""
            <table>
              <thead>
                <tr>
                  <th>Player</th><th>Pos</th><th>Team</th><th>Opp</th>
                  <th>Side</th><th>Line</th><th>Odds</th><th>Book</th>
                  <th>Pred</th><th>Edge</th>
                </tr>
              </thead>
              <tbody>
                {''.join(rows)}
              </tbody>
            </table>
            """
            body_parts.append(table)
            body_parts.append("</div>")
        body_parts.append("</div>")

    footer = f'<div class="footer">Value report generated from best-line selection across books</div></div></body></html>'
    return head + header + "".join(body_parts) + footer


def build_pdf_leader_tables(df: pd.DataFrame, week: int, output_pdf: str) -> None:
    categories = [
        ("QB", "Passing Yards",  "TOP 25 VALUE EDGES - QB PASSING"),
        ("QB", "Rushing Yards",  "TOP 25 VALUE EDGES - QB RUSHING"),
        ("WR", "Receiving Yards","TOP 25 VALUE EDGES - WR RECEIVING"),
        ("TE", "Receiving Yards","TOP 25 VALUE EDGES - TE RECEIVING"),
        ("RB", "Rushing Yards",  "TOP 25 VALUE EDGES - RB RUSHING"),
        ("RB", "Receiving Yards","TOP 25 VALUE EDGES - RB RECEIVING"),
    ]
    def shorten(text: str, max_chars: int) -> str:
        if not isinstance(text, str):
            return ""
        t = text.strip()
        return t if len(t) <= max_chars else t[: max_chars - 1] + "…"
    # Abbreviations for long bookmaker names to prevent overlap
    book_abbrev = {
        "DraftKings": "DK",
        "DraftKings Pick6": "DKP6",
        "FanDuel": "FD",
        "BetMGM": "MGM",
        "Pinnacle": "PIN",
        "BetOnline.ag": "BOL",
        "BetRivers": "BR",
        "betPARX": "PARX",
        "PrizePicks": "PP",
        "Underdog": "UD",
        "Hard Rock Bet": "HR",
        "Bally Bet": "Bally",
        "ESPN BET": "ESPN",
        "Bovada": "Bovada",
    }

    with PdfPages(output_pdf) as pdf:
        for position, prop_type, title in categories:
            subset = df[(df["position"] == position) & (df["prop_type"] == prop_type)].copy()
            if subset.empty:
                continue
            # Top by edge_yards descending, positive only
            subset = subset[pd.to_numeric(subset["edge_yards"], errors="coerce") > 0]
            subset = subset.sort_values("edge_yards", ascending=False).head(25)
            if subset.empty:
                continue

            fig, ax = plt.subplots(figsize=(8.5, 11))
            ax.set_xlim(0, 8.5)
            ax.set_ylim(0, 11)
            ax.axis('off')

            # Header
            ax.text(4.25, 10.6, f"Week {week} - {title}", ha='center', va='center',
                    fontsize=14, fontweight='bold', fontfamily='monospace')
            ax.text(0.5, 10.1, "Rank", ha='left', va='center',
                    fontsize=10, fontweight='bold', fontfamily='monospace')
            ax.text(1.4, 10.1, "Player", ha='left', va='center',
                    fontsize=10, fontweight='bold', fontfamily='monospace')
            ax.text(3.8, 10.1, "Side", ha='left', va='center',
                    fontsize=10, fontweight='bold', fontfamily='monospace')
            ax.text(4.6, 10.1, "Line", ha='left', va='center',
                    fontsize=10, fontweight='bold', fontfamily='monospace')
            ax.text(5.2, 10.1, "Odds", ha='left', va='center',
                    fontsize=10, fontweight='bold', fontfamily='monospace')
            ax.text(6.0, 10.1, "Book", ha='left', va='center',
                    fontsize=10, fontweight='bold', fontfamily='monospace')
            ax.text(8.0, 10.1, "Edge", ha='right', va='center',
                    fontsize=10, fontweight='bold', fontfamily='monospace')
            ax.plot([0.5, 8.2], [9.9, 9.9], 'k-', linewidth=0.5)

            for i, (_, row) in enumerate(subset.iterrows()):
                y = 9.6 - i * 0.31
                # Player without opponent (retain team)
                player_full = f"{row['player']} ({row['team']})".strip()
                # Constrain player column width by truncating long labels
                player = shorten(player_full, 30)
                side = str(row.get("side",""))
                # Abbreviate long bookmaker names
                book = str(row.get("bookmaker","")).strip()
                book_short = book_abbrev.get(book, book[:8])
                # Separate columns for line, odds, book
                line_val = f"{row['best_point']:.1f}"
                odds_val = f"{row['best_price']:.0f}"
                edge = f"{row['edge_yards']:.1f} yds"
                ax.text(0.5, y, f"{i+1:2d}", ha='left', va='center',
                        fontsize=9, fontfamily='monospace')
                ax.text(1.4, y, player, ha='left', va='center',
                        fontsize=8.5, fontfamily='monospace')
                ax.text(3.8, y, side, ha='left', va='center',
                        fontsize=9, fontfamily='monospace',
                        color=("#166534" if side.lower()=="over" else "#991b1b"))
                # Columns: line, odds, book
                ax.text(4.6, y, line_val, ha='left', va='center',
                        fontsize=8.5, fontfamily='monospace')
                ax.text(5.2, y, odds_val, ha='left', va='center',
                        fontsize=8.5, fontfamily='monospace')
                ax.text(6.0, y, book_short, ha='left', va='center',
                        fontsize=8.5, fontfamily='monospace')
                ax.text(8.0, y, edge, ha='right', va='center',
                        fontsize=9, fontfamily='monospace')

            pdf.savefig(fig, bbox_inches='tight')
            plt.close(fig)


def main():
    if len(sys.argv) != 2:
        print("Usage: python 10-ARBITRAGE/render_value_reports.py <week_number>")
        sys.exit(1)
    try:
        week = int(sys.argv[1])
    except ValueError:
        print("Week must be an integer")
        sys.exit(1)

    # Get absolute path to Models directory (repo home)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    models_dir = os.path.dirname(script_dir)  # Go up from 10-ARBITRAGE/ to Models/

    df = load_value_csv(week, models_dir)
    # Ensure numeric types
    for c in ["predicted_yards","best_point","best_price","edge_yards"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    # Always save to Models/0-FINAL-REPORTS/ using absolute path
    final_reports_dir = os.path.join(models_dir, "0-FINAL-REPORTS")
    os.makedirs(final_reports_dir, exist_ok=True)
    html_out = os.path.join(final_reports_dir, f"week{week}_value_complete_props_report.html")
    pdf_out = os.path.join(final_reports_dir, f"week{week}_value_leader_tables.pdf")

    html = build_html_report(df, week, models_dir)
    with open(html_out, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"HTML report written: {html_out}")

    try:
        build_pdf_leader_tables(df, week, pdf_out)
        print(f"PDF leader tables written: {pdf_out}")
    except Exception as e:
        print(f"Failed to generate PDF leader tables: {e}")


if __name__ == "__main__":
    main()


