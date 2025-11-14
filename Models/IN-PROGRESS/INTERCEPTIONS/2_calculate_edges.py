#!/usr/bin/env python3
"""
Step 2: Calculate Betting Edges

Compares model predictions against DraftKings odds to find value bets.

Usage:
    python 2_calculate_edges.py [--odds ODDS_FILE] [--pred PRED_FILE]
"""
import argparse
import os
import pandas as pd
from utils.odds import american_to_probability, probability_to_american, remove_vig, calculate_edge
from utils.matching import normalize_player_name, build_player_mapping
from config import ODDS_LATEST, PREDICTIONS_DIR


def find_latest_prediction_file():
    """Find the most recent prediction file"""
    import glob
    
    pattern = os.path.join(PREDICTIONS_DIR, "upcoming_qb_interception_logistic_regression_week_*.csv")
    files = glob.glob(pattern)
    
    if not files:
        return None
    
    # Sort by modification time, most recent first
    files.sort(key=lambda f: os.path.getmtime(f), reverse=True)
    return files[0]


def format_american_odds(value):
    """Format American odds for display"""
    if pd.isna(value) or str(value).strip().lower() == 'nan':
        return '-'
    
    s = str(value).strip().replace('\u2212', '-')
    
    if s.startswith('+') or s.startswith('-'):
        return s
    
    try:
        val = int(s)
        return f"{val:+d}"
    except:
        return s


def main():
    parser = argparse.ArgumentParser(description="Calculate betting edges")
    parser.add_argument("--odds", type=str, default="", help="Odds CSV file")
    parser.add_argument("--pred", type=str, default="", help="Predictions CSV file")
    args = parser.parse_args()
    
    # Load odds
    odds_path = args.odds or ODDS_LATEST
    if not os.path.exists(odds_path):
        print(f"❌ Odds file not found: {odds_path}")
        print("   Run: python 1_scrape_odds.py")
        return
    
    # Load predictions
    pred_path = args.pred or find_latest_prediction_file()
    if not pred_path or not os.path.exists(pred_path):
        print(f"❌ Predictions file not found")
        print("   Run: python predict_qb_interceptions.py")
        return
    
    print(f"Loading odds: {odds_path}")
    print(f"Loading predictions: {pred_path}")
    
    odds_df = pd.read_csv(odds_path)
    pred_df = pd.read_csv(pred_path)
    
    # Calculate implied probabilities from odds
    odds_df['dk_prob_over'] = odds_df['over_american_odds'].apply(american_to_probability)
    odds_df['dk_prob_under'] = odds_df['under_american_odds'].apply(american_to_probability)
    
    # Extract model probabilities
    if 'interception_american_odds' in pred_df.columns:
        pred_df['model_prob_int'] = pred_df['interception_american_odds'].apply(american_to_probability)
    elif 'interception_prob' in pred_df.columns:
        pred_df['model_prob_int'] = pd.to_numeric(pred_df['interception_prob'], errors='coerce')
    else:
        print("❌ No interception probability found in predictions")
        return
    
    # Build player name mapping
    mapping = build_player_mapping(
        pred_df['player'].tolist() if 'player' in pred_df.columns else pred_df['QB'].tolist(),
        odds_df['player'].tolist()
    )
    
    pred_df['player_odds_name'] = pred_df['player'].map(mapping) if 'player' in pred_df.columns else pred_df['QB'].map(mapping)
    
    # Merge data
    merged = pred_df.merge(
        odds_df,
        left_on='player_odds_name',
        right_on='player',
        how='left',
        suffixes=('_model', '_dk')
    )
    
    # Calculate fair odds (remove vig)
    merged['book_total_prob'] = merged['dk_prob_over'] + merged['dk_prob_under']
    merged['vig_factor'] = 1.0 / merged['book_total_prob']
    merged['dk_prob_over_fair'] = merged['dk_prob_over'] * merged['vig_factor']
    merged['dk_prob_under_fair'] = merged['dk_prob_under'] * merged['vig_factor']
    
    # Calculate edges
    merged['edge_int'] = merged['model_prob_int'] - merged['dk_prob_over_fair']
    merged['edge_no_int'] = (1 - merged['model_prob_int']) - merged['dk_prob_under_fair']
    merged['abs_edge'] = merged['edge_int'].abs().fillna(0.0)
    
    # Sort by edge
    merged = merged.sort_values('abs_edge', ascending=False)
    
    # Display results
    print("\n" + "="*80)
    print("BETTING EDGES - QB INTERCEPTIONS")
    print("="*80 + "\n")
    
    # Show only rows with valid odds data
    display_df = merged.dropna(subset=['over_american_odds', 'dk_prob_over']).copy()
    
    if display_df.empty:
        print("⚠️  No matching players found between predictions and odds")
        return
    
    # Create display columns
    display_df['Model Line'] = display_df['interception_american_odds'].apply(format_american_odds)
    display_df['Book Line'] = display_df['over_american_odds'].apply(format_american_odds)
    display_df['Book Fair'] = display_df['dk_prob_over_fair'].apply(lambda x: probability_to_american(x) if pd.notnull(x) else '-')
    display_df['Model %'] = (display_df['model_prob_int'] * 100).round(1).astype(str) + '%'
    display_df['Book %'] = (display_df['dk_prob_over_fair'] * 100).round(1).astype(str) + '%'
    display_df['Edge %'] = (display_df['edge_int'] * 100).round(1).astype(str) + '%'
    
    # Select columns for display
    cols = ['player_model', 'Model Line', 'Book Line', 'Book Fair', 'Model %', 'Book %', 'Edge %']
    result = display_df[cols].head(20)
    result.columns = ['Player', 'Model', 'Book', 'Fair', 'Model %', 'Book %', 'Edge']
    
    print(result.to_string(index=False))
    
    print("\n" + "="*80)
    print(f"Analyzed {len(display_df)} players")
    print("Note: 'Book' = actual DraftKings odds, 'Fair' = vig removed")
    print("="*80 + "\n")
    
    # Save detailed results
    output_path = os.path.join(PREDICTIONS_DIR, "betting_edges_latest.csv")
    merged.to_csv(output_path, index=False)
    print(f"✓ Saved detailed results to: {output_path}")


if __name__ == "__main__":
    main()
