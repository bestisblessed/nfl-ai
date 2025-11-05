#!/usr/bin/env python3
"""
Step 1: Scrape DraftKings QB Interception Odds

Usage:
    python 1_scrape_odds.py [--force]
"""
import argparse
import os
import datetime as dt
from utils.api import fetch_draftkings_interceptions
from utils.parser import (
    extract_events_markets_selections,
    make_event_maps,
    parse_interception_markets
)
from utils.io import write_odds_csv
from config import ODDS_LATEST, ODDS_SNAPSHOT_DIR, SCRAPE_CACHE_MINUTES


def should_skip_fetch(output_path: str, force: bool):
    """Check if we should skip fetching based on cache age"""
    if force:
        return False
    
    if not os.path.exists(output_path):
        return False
    
    mtime = os.path.getmtime(output_path)
    age_seconds = dt.datetime.now().timestamp() - mtime
    
    if age_seconds < SCRAPE_CACHE_MINUTES * 60:
        print(f"✓ Using cached odds (age: {age_seconds/60:.1f} minutes)")
        return True
    
    return False


def main():
    parser = argparse.ArgumentParser(description="Scrape DraftKings QB Interception odds")
    parser.add_argument("--force", action="store_true", help="Force re-fetch even if cached")
    args = parser.parse_args()
    
    print("Scraping DraftKings QB Interception Odds...")
    print(f"Output: {ODDS_LATEST}")
    
    if should_skip_fetch(ODDS_LATEST, args.force):
        print(f"Skipping fetch. Use --force to override.")
        return
    
    # Fetch data from DraftKings API
    print("Fetching from DraftKings API...")
    payload = fetch_draftkings_interceptions()
    
    # Parse the response
    events, markets, selections = extract_events_markets_selections(payload)
    print(f"  Found {len(events)} events, {len(markets)} markets, {len(selections)} selections")
    
    event_team_map, event_time_map = make_event_maps(events)
    
    # Parse interception markets
    odds_data = parse_interception_markets(markets, selections, event_team_map, event_time_map)
    
    if not odds_data:
        print("⚠️  No odds data found. Check if games are available.")
        return
    
    # Save to latest file
    write_odds_csv(odds_data, ODDS_LATEST)
    
    # Save timestamped snapshot
    timestamp = dt.datetime.now().strftime("%Y%m%d_%H%M")
    snapshot_path = os.path.join(ODDS_SNAPSHOT_DIR, f"odds_interceptions_dk_{timestamp}.csv")
    write_odds_csv(odds_data, snapshot_path)
    
    print(f"✓ Scraped {len(odds_data)} QB interception odds")
    print(f"  Latest: {ODDS_LATEST}")
    print(f"  Snapshot: {snapshot_path}")


if __name__ == "__main__":
    main()
