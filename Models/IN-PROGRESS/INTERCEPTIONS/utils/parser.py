"""Parse DraftKings API responses"""
from typing import Dict, List, Tuple, Any


def extract_events_markets_selections(payload: Dict[str, Any]):
    """Extract events, markets, and selections from DraftKings API response"""
    events = payload.get("events") or payload.get("Events") or []
    markets = payload.get("markets") or payload.get("Markets") or []
    selections = payload.get("selections") or payload.get("Selections") or []
    
    # Check nested structures
    if not events or not markets or not selections:
        for key in ("data", "result", "payload"):
            maybe = payload.get(key)
            if isinstance(maybe, dict):
                events = events or maybe.get("events") or maybe.get("Events") or []
                markets = markets or maybe.get("markets") or maybe.get("Markets") or []
                selections = selections or maybe.get("selections") or maybe.get("Selections") or []
    
    return events, markets, selections


def make_event_maps(events: List[Dict[str, Any]]):
    """Build helper maps from events data"""
    event_team_map = {}
    event_time_map = {}
    
    for ev in events:
        event_id = str(ev.get("eventId") or ev.get("id") or "")
        start = (
            ev.get("startEventDate") or
            ev.get("startDate") or
            ev.get("startTime") or
            ev.get("start")
        )
        event_time_map[event_id] = str(start) if start else ""
        
        # Extract team names
        home_name, away_name = "", ""
        participants = ev.get("participants") or ev.get("Participants") or []
        
        if isinstance(participants, list):
            for p in participants:
                role = (p.get("role") or p.get("Role") or p.get("venueRole") or "").lower()
                name = (
                    p.get("teamName") or
                    p.get("name") or
                    p.get("abbreviation") or
                    p.get("displayName") or
                    ""
                )
                if role == "home":
                    home_name = str(name)
                elif role == "away":
                    away_name = str(name)
        
        event_team_map[event_id] = (home_name, away_name)
    
    return event_team_map, event_time_map


def parse_interception_markets(markets: List[Dict], selections: List[Dict], 
                               event_team_map: Dict, event_time_map: Dict):
    """Parse interception O/U markets from DraftKings data"""
    # Index selections by market ID
    selections_by_market = {}
    for sel in selections:
        mid = str(sel.get("marketId") or "")
        if mid:
            selections_by_market.setdefault(mid, []).append(sel)
    
    results = []
    
    for market in markets:
        market_id = str(market.get("id") or market.get("marketId") or "")
        event_id = str(market.get("eventId") or "")
        
        # Extract player name
        player_name = (
            market.get("participantName") or
            market.get("participant") or
            market.get("playerName") or
            ""
        )
        
        # Parse from market name if missing
        if not player_name:
            market_name = str(market.get("name") or "")
            for key in (" interceptions thrown", " interceptions o/u", " interceptions"):
                idx = market_name.lower().find(key)
                if idx > 0:
                    player_name = market_name[:idx].strip()
                    break
        
        if not player_name:
            continue
        
        # Extract Over/Under odds
        over_odds, under_odds, line = None, None, "0.5"
        sel_list = selections_by_market.get(market_id, [])
        
        for sel in sel_list:
            label = (sel.get("label") or sel.get("outcomeType") or "").lower()
            display_odds = sel.get("displayOdds") or {}
            odds = display_odds.get("american") or sel.get("oddsAmerican") or sel.get("odds")
            ln = sel.get("points") or sel.get("line") or sel.get("lineValue")
            
            if ln is not None:
                line = str(ln)
            
            if "over" in label and odds is not None:
                over_odds = str(odds)
            elif "under" in label and odds is not None:
                under_odds = str(odds)
        
        # Get team info
        home, away = event_team_map.get(event_id, ("", ""))
        start_time = event_time_map.get(event_id, "")
        
        results.append({
            "player": player_name,
            "team": "",
            "opponent": "",
            "home_away": "",
            "line": line,
            "over_american_odds": over_odds or "",
            "under_american_odds": under_odds or "",
            "event_id": event_id,
            "start_time": start_time,
            "source": "draftkings",
        })
    
    return results
