"""API utilities for scraping sportsbook odds"""
import requests
from typing import Dict, Any


def fetch_draftkings_interceptions():
    """Fetch QB Interceptions O/U odds from DraftKings API"""
    
    NFL_LEAGUE_ID = "88808"
    INTERCEPTIONS_SUBCATEGORY_ID = "15937"
    
    endpoint = (
        "https://sportsbook-nash.draftkings.com/sites/US-SB/api/sportscontent/"
        "controldata/league/leagueSubcategory/v1/markets"
    )
    
    params = {
        "isBatchable": "false",
        "templateVars": f"{NFL_LEAGUE_ID},{INTERCEPTIONS_SUBCATEGORY_ID}",
        "eventsQuery": (
            f"$filter=leagueId eq '{NFL_LEAGUE_ID}' AND "
            f"clientMetadata/Subcategories/any(s: s/Id eq '{INTERCEPTIONS_SUBCATEGORY_ID}')"
        ),
        "marketsQuery": (
            f"$filter=clientMetadata/subCategoryId eq '{INTERCEPTIONS_SUBCATEGORY_ID}' "
            "AND tags/all(t: t ne 'SportcastBetBuilder')"
        ),
        "include": "Events",
        "entity": "events",
    }
    
    headers = {
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
    
    response = requests.get(endpoint, params=params, headers=headers, timeout=30)
    response.raise_for_status()
    return response.json()
