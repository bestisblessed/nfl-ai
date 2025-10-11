"""
Scrape DraftKings NFL Interceptions O/U odds and emit a merge-ready CSV.

Primary source: DraftKings sportscontent JSON for league subcategory markets.
Observed endpoint (Interceptions O/U):
  https://sportsbook-nash.draftkings.com/sites/US-SB/api/sportscontent/controldata/league/leagueSubcategory/v1/markets

This script avoids DOM scraping by using the JSON feed that powers the UI.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import os
from typing import Any, Dict, List, Optional, Tuple

import requests

from odds_utils import normalize_player_name


NFL_LEAGUE_ID = "88808"
INTERCEPTIONS_OU_SUBCATEGORY_ID = "15937"

ENDPOINT = (
    "https://sportsbook-nash.draftkings.com/sites/US-SB/api/sportscontent/"
    "controldata/league/leagueSubcategory/v1/markets"
)


def build_params(entity: str = "events") -> Dict[str, str]:
    return {
        "isBatchable": "false",
        "templateVars": f"{NFL_LEAGUE_ID},{INTERCEPTIONS_OU_SUBCATEGORY_ID}",
        "eventsQuery": (
            f"$filter=leagueId eq '{NFL_LEAGUE_ID}' AND "
            f"clientMetadata/Subcategories/any(s: s/Id eq '{INTERCEPTIONS_OU_SUBCATEGORY_ID}')"
        ),
        "marketsQuery": (
            f"$filter=clientMetadata/subCategoryId eq '{INTERCEPTIONS_OU_SUBCATEGORY_ID}' "
            "AND tags/all(t: t ne 'SportcastBetBuilder')"
        ),
        "include": "Events",
        "entity": entity,
    }


def default_headers() -> Dict[str, str]:
    return {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36"
        ),
        "Referer": (
            "https://sportsbook.draftkings.com/leagues/football/nfl?"
            "category=passing-props-&subcategory=interceptions-o-u"
        ),
        "Accept": "application/json, text/plain, */*",
    }


def fetch_json(session: Optional[requests.Session] = None) -> Dict[str, Any]:
    sess = session or requests.Session()
    # Try entity=events first, then entity=markets as fallback
    for ent in ("events", "markets"):
        r = sess.get(ENDPOINT, params=build_params(ent), headers=default_headers(), timeout=30)
        if r.status_code >= 400:
            continue
        try:
            return r.json()
        except Exception:
            continue
    raise RuntimeError("Failed to fetch DraftKings markets payload")


def extract_events_markets_selections(payload: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Return (events, markets, selections) lists from payload.

    The DraftKings schema can evolve; we defensive-parse common shapes.
    """
    # Typical structure: { "events": [...], "markets": [...] } or nested under "entity" key
    events = payload.get("events") or payload.get("Events") or []
    markets = payload.get("markets") or payload.get("Markets") or []
    selections = payload.get("selections") or payload.get("Selections") or []

    # Some responses wrap under "data" or "result"
    if not events or not markets or not selections:
        for key in ("data", "result", "payload"):
            maybe = payload.get(key)
            if isinstance(maybe, dict):
                events = events or maybe.get("events") or maybe.get("Events") or []
                markets = markets or maybe.get("markets") or maybe.get("Markets") or []
                selections = selections or maybe.get("selections") or maybe.get("Selections") or []
    if not isinstance(events, list):
        events = []
    if not isinstance(markets, list):
        markets = []
    if not isinstance(selections, list):
        selections = []

    # Robust fallback: search recursively for lists containing typical keys
    if not events or not markets or not selections:
        found_events: List[Dict[str, Any]] = []
        found_markets: List[Dict[str, Any]] = []
        found_selections: List[Dict[str, Any]] = []

        def walk(obj: Any) -> None:
            if isinstance(obj, list):
                if obj and isinstance(obj[0], dict):
                    # Identify markets by presence of outcomes
                    if any("outcomes" in d or "Outcomes" in d for d in obj):
                        found_markets.extend([d for d in obj if isinstance(d, dict)])
                    # Identify events by presence of eventId/participants
                    if any(("eventId" in d or "participants" in d or "Participants" in d) for d in obj):
                        found_events.extend([d for d in obj if isinstance(d, dict)])
                    # Identify selections by presence of marketId and label
                    if any(("marketId" in d and "label" in d) for d in obj):
                        found_selections.extend([d for d in obj if isinstance(d, dict)])
                for it in obj:
                    walk(it)
            elif isinstance(obj, dict):
                for v in obj.values():
                    walk(v)

        walk(payload)
        if not events and found_events:
            events = found_events
        if not markets and found_markets:
            markets = found_markets
        if not selections and found_selections:
            selections = found_selections

    return events, markets, selections


def make_event_maps(events: List[Dict[str, Any]]):
    """Build helper maps: eventId -> (homeTeam, awayTeam, startTime).

    Team names can appear as full names or abbreviations depending on feed. We
    capture the display strings and rely on downstream matching to align.
    """
    event_team_map: Dict[str, Tuple[str, str]] = {}
    event_time_map: Dict[str, str] = {}

    for ev in events:
        event_id = str(ev.get("eventId") or ev.get("id") or "")
        start = (
            ev.get("startEventDate")
            or ev.get("startDate")
            or ev.get("startTime")
            or ev.get("start")
        )
        event_time_map[event_id] = str(start) if start is not None else ""

        # Participants may be under "teamName"/"name" with roles
        home_name = ""
        away_name = ""
        participants = ev.get("participants") or ev.get("Participants") or []
        if isinstance(participants, list):
            for p in participants:
                role = (p.get("role") or p.get("Role") or p.get("venueRole") or "").lower()
                nm = (
                    p.get("teamName")
                    or p.get("name")
                    or p.get("abbreviation")
                    or p.get("displayName")
                    or ""
                )
                if role == "home":
                    home_name = str(nm)
                elif role == "away":
                    away_name = str(nm)
        event_team_map[event_id] = (home_name, away_name)
    return event_team_map, event_time_map


def yield_interception_rows(
    markets: List[Dict[str, Any]],
    selections: List[Dict[str, Any]],
    event_team_map: Dict[str, Tuple[str, str]],
    event_time_map: Dict[str, str],
):
    """Yield normalized rows for Interceptions O/U markets.

    Each market should include: eventId, outcomes with Over/Under selections,
    and a player association.
    """
    # Index selections by marketId for fast lookup
    selections_by_market: Dict[str, List[Dict[str, Any]]] = {}
    for sel in selections:
        mid = str(sel.get("marketId") or "")
        if not mid:
            continue
        selections_by_market.setdefault(mid, []).append(sel)

    for m in markets:
        # Filter on subcategory if present
        client_meta = m.get("clientMetadata") or {}
        subcat = str(client_meta.get("subCategoryId") or m.get("subcategoryId") or "")
        if subcat and subcat != INTERCEPTIONS_OU_SUBCATEGORY_ID:
            continue

        event_id = str(m.get("eventId") or m.get("eventID") or m.get("event") or "")
        outcomes = m.get("outcomes") or m.get("Outcomes") or []
        # Player name typically on market or outcome
        player_name = (
            m.get("participantName")
            or m.get("participant")
            or m.get("playerName")
            or ""
        )

        # Try to extract player from outcomes if missing
        if not player_name and isinstance(outcomes, list):
            for o in outcomes:
                pn = (
                    o.get("participantName")
                    or o.get("participant")
                    or o.get("playerName")
                    or ""
                )
                if pn:
                    player_name = pn
                    break

        # Try to extract from selections participants
        market_id = str(m.get("id") or m.get("marketId") or "")
        sel_list = selections_by_market.get(market_id, [])
        player_venue_role = ""
        if not player_name and sel_list:
            for s in sel_list:
                parts = s.get("participants") or []
                if parts and isinstance(parts, list):
                    for p in parts:
                        if str(p.get("type") or "").lower() == "player":
                            n = p.get("name")
                            if n:
                                player_name = str(n)
                                player_venue_role = str(p.get("venueRole") or "")
                                break
                    if player_name:
                        break

        # Parse from market name if still missing: "<Player> Interceptions Thrown O/U"
        if not player_name:
            market_name = str(m.get("name") or "")
            if market_name:
                lower = market_name.lower()
                for key in (" interceptions thrown", " interceptions o/u", " interceptions"):
                    idx = lower.find(key)
                    if idx > 0:
                        player_name = market_name[:idx].strip()
                        break

        player_name = str(player_name).strip()
        if not player_name:
            # Skip anonymous markets
            continue

        # Find Over/Under odds and line (expect 0.5)
        over_odds: Optional[str] = None
        under_odds: Optional[str] = None
        line_val: Optional[str] = None

        # Prefer selections for odds extraction
        if isinstance(sel_list, list) and sel_list:
            for s in sel_list:
                sel_label = (s.get("label") or s.get("outcomeType") or "").lower()
                display_odds = s.get("displayOdds") or {}
                odds = display_odds.get("american") or s.get("oddsAmerican") or s.get("odds")
                ln = s.get("points") or s.get("line") or s.get("lineValue")
                if ln is not None:
                    line_val = str(ln)
                if "over" in sel_label:
                    over_odds = str(odds) if odds is not None else over_odds
                elif "under" in sel_label:
                    under_odds = str(odds) if odds is not None else under_odds
        else:
            # Fallback to old embedded outcomes structure if present
            if isinstance(outcomes, list):
                for o in outcomes:
                    sel = (o.get("label") or o.get("selection") or o.get("name") or "").lower()
                    odds = o.get("oddsAmerican") or o.get("priceAmerican") or o.get("odds")
                    ln = o.get("line") or o.get("lineValue") or o.get("points")
                    if ln is not None:
                        line_val = str(ln)
                    if "over" in sel:
                        over_odds = str(odds) if odds is not None else over_odds
                    elif "under" in sel:
                        under_odds = str(odds) if odds is not None else under_odds

        home, away = event_team_map.get(event_id, ("", ""))
        start_time = event_time_map.get(event_id, "")

        # Assign team/opponent/home_away heuristically by matching player name to team participants
        # If unknown, leave empty; downstream comparison uses team/opponent mapping too.
        team = ""
        opponent = ""
        home_away = ""
        pn_norm = normalize_player_name(player_name)
        # Heuristic: if player's last token matches one of the team strings (rarely reliable), skip.
        # We leave team/opponent blank to be enriched during comparison by joining on upcoming_games.

        # Prefer venueRole from selections: AwayPlayer/HomePlayer
        vr = player_venue_role.lower()
        if vr.startswith("away"):
            team = away
            opponent = home
            home_away = "AWAY"
        elif vr.startswith("home"):
            team = home
            opponent = away
            home_away = "HOME"

        yield {
            "player": player_name,
            "team": team,
            "opponent": opponent,
            "home_away": home_away,
            "line": line_val or "0.5",
            "over_american_odds": over_odds or "",
            "under_american_odds": under_odds or "",
            "event_id": event_id,
            "start_time": start_time,
            "source": "draftkings",
        }


def write_csv(rows: List[Dict[str, Any]], out_path: str) -> None:
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    fieldnames = [
        "player",
        "team",
        "opponent",
        "home_away",
        "line",
        "over_american_odds",
        "under_american_odds",
        "event_id",
        "start_time",
        "source",
    ]
    with open(out_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fieldnames})


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Scrape DraftKings Interceptions O/U odds")
    p.add_argument(
        "--force",
        action="store_true",
        help="Bypass time-based caching",
    )
    return p.parse_args()


def should_skip_fetch(out_path: str, force: bool, max_age_minutes: int = 5) -> bool:
    if force:
        return False
    if not os.path.exists(out_path):
        return False
    mtime = os.path.getmtime(out_path)
    age = dt.datetime.now().timestamp() - mtime
    return age < max_age_minutes * 60


def main() -> None:
    args = parse_args()
    out_path = "/Users/td/Code/nfl-ai/Models/IN-PROGRESS/INTERCEPTIONS/data/odds_interceptions_dk_latest.csv"
    if should_skip_fetch(out_path, args.force):
        print(f"Using cached odds file: {out_path}")
        return

    payload = fetch_json()
    events, markets, selections = extract_events_markets_selections(payload)
    event_team_map, event_time_map = make_event_maps(events)
    rows = list(yield_interception_rows(markets, selections, event_team_map, event_time_map))

    # If writing timestamped snapshot alongside latest
    ts = dt.datetime.now().strftime("%Y%m%d_%H%M")
    snapshot_dir = "/Users/td/Code/nfl-ai/Models/IN-PROGRESS/INTERCEPTIONS/data"
    os.makedirs(snapshot_dir, exist_ok=True)
    snapshot_path = os.path.join(snapshot_dir, f"odds_interceptions_dk_{ts}.csv")

    # Dump payload for debugging if no rows parsed
    if not rows:
        dbg_dir = os.path.join(os.path.dirname(snapshot_path), "debug")
        os.makedirs(dbg_dir, exist_ok=True)
        dbg_path = os.path.join(dbg_dir, f"raw_dk_interceptions_{ts}.json")
        try:
            with open(dbg_path, "w") as f:
                json.dump(payload, f)
            print(f"No rows parsed. Wrote raw payload to {dbg_path}")
        except Exception as e:
            print(f"No rows parsed. Failed to write debug payload: {e}")

    write_csv(rows, out_path)
    write_csv(rows, snapshot_path)
    print(f"Saved {len(rows)} rows to {out_path} and {snapshot_path}")


if __name__ == "__main__":
    main()


