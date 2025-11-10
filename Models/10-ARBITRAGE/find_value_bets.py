"""
Compare week 10 predictions to sportsbook props and compute value edges.

Inputs:
- Predictions: 0-FINAL-REPORTS/week10_all_props_summary.csv
- Props: Arbitrage/data/week10_props_2025-11-09.csv

Rules (per user):
- Use best available line per side (Over/Under) across all books
  • Over: minimum point; tie-break by highest American odds (max price)
  • Under: maximum point; tie-break by highest American odds (max price)
- Use all books in the props CSV
- Restrict to the six supported props via position ↔ market mapping
- Align player by normalized name and ensure prediction team matches props home/away

Outputs:
- Arbitrage/data/week10_value_opportunities.csv
  Columns: player, position, team, opp, prop_type, market, predicted_yards,
           side, best_point, best_price, bookmaker, edge_yards, home_team, away_team
- Arbitrage/data/week10_top_edges_by_prop.csv
  Top 25 per (prop_type, position) by edge_yards (positive only)
"""

import os
import re
import pandas as pd


def get_file_paths(week):
    from datetime import datetime
    current_date = datetime.now().strftime("%Y-%m-%d")
    # Try filtered file first (games not yet started), then fallback
    import os
    props_filtered = f"data/week{week}_props_{current_date}_filtered.csv"
    props_original = f"data/week{week}_props_{current_date}.csv"
    # Check previous day's file as well
    from datetime import timedelta
    prev_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    props_prev_filtered = f"data/week{week}_props_{prev_date}_filtered.csv"
    props_prev_original = f"data/week{week}_props_{prev_date}.csv"
    
    if os.path.exists(props_filtered):
        props_file = props_filtered
        print(f"Using filtered props (games not yet started): {props_filtered}")
    elif os.path.exists(props_prev_filtered):
        props_file = props_prev_filtered
        print(f"Using filtered props (games not yet started): {props_prev_filtered}")
    elif os.path.exists(props_original):
        props_file = props_original
        print(f"WARNING: Using unfiltered props - may include started games: {props_original}")
    else:
        props_file = props_prev_original
        print(f"WARNING: Using unfiltered props - may include started games: {props_prev_original}")
    
    return {
        "predictions_primary": f"0-FINAL-REPORTS/week{week}_all_props_summary.csv",
        "predictions_fallback": f"../0-FINAL-REPORTS/week{week}_all_props_summary.csv",
        "props": props_file,
        "output_full": f"data/week{week}_value_opportunities.csv",
        "output_top": f"data/week{week}_top_edges_by_prop.csv"
    }

TEAM_ABBREV_TO_FULL = {
    "ARI": "Arizona Cardinals", "ATL": "Atlanta Falcons", "BAL": "Baltimore Ravens",
    "BUF": "Buffalo Bills", "CAR": "Carolina Panthers", "CHI": "Chicago Bears",
    "CIN": "Cincinnati Bengals", "CLE": "Cleveland Browns", "DAL": "Dallas Cowboys",
    "DEN": "Denver Broncos", "DET": "Detroit Lions", "GB": "Green Bay Packers",
    "HOU": "Houston Texans", "IND": "Indianapolis Colts", "JAX": "Jacksonville Jaguars",
    "KC": "Kansas City Chiefs", "LVR": "Las Vegas Raiders", "LAC": "Los Angeles Chargers",
    "LAR": "Los Angeles Rams", "MIA": "Miami Dolphins", "MIN": "Minnesota Vikings",
    "NE": "New England Patriots", "NO": "New Orleans Saints", "NYG": "New York Giants",
    "NYJ": "New York Jets", "PHI": "Philadelphia Eagles", "PIT": "Pittsburgh Steelers",
    "SF": "San Francisco 49ers", "SEA": "Seattle Seahawks", "TB": "Tampa Bay Buccaneers",
    "TEN": "Tennessee Titans", "WAS": "Washington Commanders",
}


def load_predictions(paths) -> pd.DataFrame:
    csv_path = paths["predictions_primary"] if os.path.exists(paths["predictions_primary"]) else paths["predictions_fallback"]
    df = pd.read_csv(csv_path)
    return df


def load_props(paths) -> pd.DataFrame:
    return pd.read_csv(paths["props"])


def normalize_player_name(name: str) -> str:
    """
    Normalize player names for fuzzy matching:
    - lowercase
    - strip punctuation
    - remove common suffixes (jr, sr, ii, iii, iv)
    - collapse whitespace
    """
    if not isinstance(name, str):
        return ""
    s = name.lower().strip()
    # remove punctuation
    s = re.sub(r"[\\.'’`-]", " ", s)
    # remove suffixes
    s = re.sub(r"\\b(jr|sr|ii|iii|iv)\\b", " ", s)
    # dedupe whitespace
    s = re.sub(r"\\s+", " ", s)
    return s.strip()


def map_market(position: str, prop_type: str) -> str:
    """
    Map prediction row (position, prop_type) to props market key.
    Supported:
    - QB Passing Yards -> player_pass_yds
    - WR/TE/RB Receiving Yards -> player_reception_yds
    - RB/QB Rushing Yards -> player_rush_yds
    """
    if not isinstance(position, str) or not isinstance(prop_type, str):
        return ""
    p = position.strip().upper()
    t = prop_type.strip().lower()
    if p == "QB" and t == "passing yards":
        return "player_pass_yds"
    if t == "receiving yards" and p in {"WR", "TE", "RB"}:
        return "player_reception_yds"
    if t == "rushing yards" and p in {"RB", "QB"}:
        return "player_rush_yds"
    return ""


def coerce_numeric(series: pd.Series) -> pd.Series:
    s = pd.to_numeric(series, errors="coerce")
    return s


def select_best_lines(df_props_filtered: pd.DataFrame) -> pd.DataFrame:
    """
    From props rows (per player/market/game), select best Over and best Under per rules.
    Returns one row per (player_norm, market, home_team, away_team) with columns:
      over_point, over_price, over_bookmaker, under_point, under_price, under_bookmaker
    """
    # Only keep numeric points
    dfp = df_props_filtered.copy()
    dfp["point"] = coerce_numeric(dfp["point"])
    dfp = dfp.dropna(subset=["point"])

    # Sort to apply tie-breakers (price descending favors higher American odds)
    over_sorted = dfp[dfp["outcome"].str.lower() == "over"].sort_values(
        by=["player_norm", "market", "home_team", "away_team", "point", "price"],
        ascending=[True, True, True, True, True, False],
    )
    under_sorted = dfp[dfp["outcome"].str.lower() == "under"].sort_values(
        by=["player_norm", "market", "home_team", "away_team", "point", "price"],
        ascending=[True, True, True, True, False, False],
    )

    # Pick first per group after sorting
    over_best = over_sorted.groupby(["player_norm", "market", "home_team", "away_team"], as_index=False).first()
    under_best = under_sorted.groupby(["player_norm", "market", "home_team", "away_team"], as_index=False).first()

    over_best = over_best.rename(columns={
        "point": "over_point",
        "price": "over_price",
        "bookmaker": "over_bookmaker",
    })[["player_norm", "market", "home_team", "away_team", "over_point", "over_price", "over_bookmaker"]]

    under_best = under_best.rename(columns={
        "point": "under_point",
        "price": "under_price",
        "bookmaker": "under_bookmaker",
    })[["player_norm", "market", "home_team", "away_team", "under_point", "under_price", "under_bookmaker"]]

    best = pd.merge(over_best, under_best, on=["player_norm", "market", "home_team", "away_team"], how="outer")
    return best


def main():
    import sys
    if len(sys.argv) < 2:
        print("Usage: python find_value_bets.py <week_number>")
        sys.exit(1)
    week = sys.argv[1]
    
    paths = get_file_paths(week)
    
    # 1) Load data
    preds = load_predictions(paths)
    props = load_props(paths)

    # 2) Prepare predictions: map market and normalize names
    preds = preds.copy()
    preds["market"] = preds.apply(lambda r: map_market(r["position"], r["prop_type"]), axis=1)
    preds = preds[preds["market"] != ""].copy()
    preds["player_norm"] = preds["full_name"].apply(normalize_player_name)
    preds["team_full"] = preds["team"].map(TEAM_ABBREV_TO_FULL)
    preds["opp_full"] = preds["opp"].map(TEAM_ABBREV_TO_FULL)

    # 3) Prepare props: filter to supported markets and normalize names
    props = props.copy()
    props = props[props["market"].isin({"player_pass_yds", "player_reception_yds", "player_rush_yds"})]
    props["player_norm"] = props["player"].apply(normalize_player_name)
    # Ensure numeric price (American odds); if missing, drop
    props["price"] = coerce_numeric(props["price"])
    props = props.dropna(subset=["price", "player_norm", "home_team", "away_team"])

    # 4) Select best Over/Under lines per player/market/game
    best_lines = select_best_lines(props)

    # 5) Join predictions to props best-lines on player+market, then ensure team alignment
    merged = pd.merge(
        preds,
        best_lines,
        on=["player_norm", "market"],
        how="left",
        suffixes=("", "_props"),
    )
    # Keep rows where prediction team is in the game teams
    team_match_mask = (
        (merged["team_full"] == merged["home_team"]) |
        (merged["team_full"] == merged["away_team"]) |
        (merged["opp_full"] == merged["home_team"]) |
        (merged["opp_full"] == merged["away_team"])
    )
    merged = merged[team_match_mask].copy()

    # 6) Compute edges
    merged["over_edge"] = merged["pred_yards"] - merged["over_point"]
    merged["under_edge"] = merged["under_point"] - merged["pred_yards"]

    def choose_side(row):
        over = row["over_edge"]
        under = row["under_edge"]
        # Handle NaNs
        over_val = over if pd.notna(over) else float("-inf")
        under_val = under if pd.notna(under) else float("-inf")
        if over_val <= 0 and under_val <= 0:
            # No positive edge; still report the larger (could be negative)
            if over_val >= under_val:
                return "Over", row["over_point"], row["over_price"], row.get("over_bookmaker", None), over
            else:
                return "Under", row["under_point"], row["under_price"], row.get("under_bookmaker", None), under
        # Choose positive max
        if over_val >= under_val:
            return "Over", row["over_point"], row["over_price"], row.get("over_bookmaker", None), over
        else:
            return "Under", row["under_point"], row["under_price"], row.get("under_bookmaker", None), under

    choice = merged.apply(choose_side, axis=1, result_type="expand")
    choice.columns = ["side", "best_point", "best_price", "bookmaker", "edge_yards"]
    out = pd.concat([merged, choice], axis=1)

    # 7) Select output columns
    out_cols = [
        "full_name", "position", "team", "opp", "prop_type", "market", "pred_yards",
        "side", "best_point", "best_price", "bookmaker", "edge_yards",
        "home_team", "away_team"
    ]
    out = out[out_cols].copy()
    out = out.rename(columns={
        "full_name": "player",
        "pred_yards": "predicted_yards",
    })

    # Ensure output dir
    os.makedirs(os.path.dirname(paths["output_full"]), exist_ok=True)
    out.to_csv(paths["output_full"], index=False)

    # 8) Top picks by (prop_type, position), positive edges only
    pos_edges = out[pd.to_numeric(out["edge_yards"], errors="coerce") > 0].copy()
    pos_edges["edge_yards"] = pd.to_numeric(pos_edges["edge_yards"], errors="coerce")
    top_rows = []
    for (ptype, pos), group in pos_edges.groupby(["prop_type", "position"]):
        top = group.sort_values("edge_yards", ascending=False).head(25)
        top_rows.append(top)
    top_df = pd.concat(top_rows, ignore_index=True) if top_rows else pd.DataFrame(columns=out.columns)
    top_df.to_csv(paths["output_top"], index=False)

    # 9) Summary logs
    total_preds = len(preds)
    total_out = len(out)
    matched_players = out["player"].nunique()
    print(f"Pred rows considered (six props only): {total_preds}")
    print(f"Output rows (matched): {total_out}  | Unique players matched: {matched_players}")
    if not out.empty:
        print("Top categories counts (positive-edge only):")
        print(pos_edges.groupby(["prop_type", "position"]).size().rename("count").to_string())
        print(f"Saved full results to: {paths['output_full']}")
        print(f"Saved top picks to:    {paths['output_top']}")
    else:
        print("No matches produced output. Check name/team alignment.")


if __name__ == "__main__":
    main()


