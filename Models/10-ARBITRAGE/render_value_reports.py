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


def load_value_csv(week: int) -> pd.DataFrame:
    input_path = f"10-ARBITRAGE/data/week{week}_value_opportunities.csv"
    alt_path = f"data/week{week}_value_opportunities.csv"
    if os.path.exists(input_path):
        return pd.read_csv(input_path)
    if os.path.exists(alt_path):
        return pd.read_csv(alt_path)
    raise FileNotFoundError(f"Could not find value opportunities CSV for week {week} at {input_path} or {alt_path}")


def build_html_report(df: pd.DataFrame, week: int) -> str:
    css = """
    <style>
      body { font-family: -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Helvetica, Arial, sans-serif; margin: 0; background: #f8f9fa; color: #222; }
      .container { max-width: 1100px; margin: 0 auto; padding: 24px; }
      .header { background: linear-gradient(135deg, #0f172a, #1e293b); color: #fff; padding: 24px; border-radius: 12px; margin-bottom: 24px; }
      .header h1 { margin: 0 0 8px 0; font-weight: 700; font-size: 24px; }
      .header p { margin: 0; opacity: .9; }
      .game { background: #fff; border-radius: 12px; padding: 16px; margin: 16px 0; box-shadow: 0 1px 3px rgba(0,0,0,0.06); }
      .game h2 { margin: 0 0 8px 0; font-size: 18px; color: #0f172a; }
      .section { margin-top: 8px; }
      .section h3 { margin: 12px 0 6px 0; font-size: 14px; color: #334155; text-transform: uppercase; letter-spacing: .03em; }
      table { width: 100%; border-collapse: collapse; }
      th, td { text-align: left; padding: 8px 10px; font-size: 13px; border-bottom: 1px solid #e5e7eb; }
      th { background: #0f172a; color: #fff; position: sticky; top: 0; }
      tr:hover td { background: #f9fafb; }
      .num { text-align: right; font-variant-numeric: tabular-nums; }
      .pill { display: inline-block; padding: 2px 8px; border-radius: 999px; font-size: 12px; }
      .over { background: #dcfce7; color: #166534; }
      .under { background: #fee2e2; color: #991b1b; }
      .footer { text-align: center; color: #64748b; margin: 24px 0 8px 0; font-size: 12px; }
    </style>
    """
    head = f"""<!doctype html><html><head><meta charset="utf-8"><title>Week {week} Value Opportunities</title>{css}</head><body>"""
    header = f"""
    <div class="container">
      <div class="header">
        <h1>NFL Week {week} - Value Opportunities</h1>
        <p>Best-line comparison vs model predictions (edge in yards)</p>
        <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
      </div>
    """
    # Order games by kickoff if available, else by name
    # We only have home_team/away_team; sort lexicographically for determinism
    df_local = df.copy()
    df_local["game_key"] = df_local.apply(lambda r: f"{r['home_team']} vs {r['away_team']}", axis=1)
    games = df_local["game_key"].dropna().unique().tolist()
    games.sort()

    body_parts = []
    for game in games:
        gdf = df_local[df_local["game_key"] == game].copy()
        if gdf.empty:
            continue
        body_parts.append(f'<div class="game"><h2>{game}</h2>')
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

    df = load_value_csv(week)
    # Ensure numeric types
    for c in ["predicted_yards","best_point","best_price","edge_yards"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    # Save reports to 0-FINAL-REPORTS to match existing final report outputs
    os.makedirs("0-FINAL-REPORTS", exist_ok=True)
    html_out = f"0-FINAL-REPORTS/week{week}_value_complete_props_report.html"
    pdf_out = f"0-FINAL-REPORTS/week{week}_value_leader_tables.pdf"

    html = build_html_report(df, week)
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


