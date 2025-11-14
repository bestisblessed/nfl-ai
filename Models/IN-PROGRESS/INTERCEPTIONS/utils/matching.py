"""Player name matching utilities"""


def normalize_player_name(name: str) -> str:
    """Normalize player name for fuzzy matching"""
    if name is None:
        return ""
    
    s = str(name).strip().lower()
    
    # Remove common punctuation
    for ch in ["\u2019", "'", ".", ",", "-", "\u2013", "\u2014"]:
        s = s.replace(ch, " ")
    
    # Remove extra spaces
    parts = [p for p in s.split() if p]
    return " ".join(parts)


def fuzzy_match_players(target: str, candidates: list, min_ratio: int = 90):
    """Find best matching player name from candidates"""
    t = normalize_player_name(target)
    cmap = {c: normalize_player_name(c) for c in candidates}
    
    # Exact match
    for orig, norm in cmap.items():
        if norm == t:
            return orig, 100
    
    # Prefix/contains match
    for orig, norm in cmap.items():
        if norm.startswith(t) or t.startswith(norm):
            return orig, 95
        if (t in norm) or (norm in t):
            return orig, 92
    
    # Try rapidfuzz if available
    try:
        from rapidfuzz import fuzz
        best_name, best_score = None, 0
        for orig, norm in cmap.items():
            sc = int(fuzz.token_sort_ratio(t, norm))
            if sc > best_score:
                best_score, best_name = sc, orig
        
        if best_name and best_score >= min_ratio:
            return best_name, best_score
    except ImportError:
        pass
    
    return None, 0


def build_player_mapping(model_players: list, odds_players: list) -> dict:
    """Build mapping between model player names and odds player names"""
    mapping = {}
    odds_norm_map = {normalize_player_name(p): p for p in odds_players}
    
    for player in model_players:
        norm = normalize_player_name(player)
        
        # Try exact normalized match first
        if norm in odds_norm_map:
            mapping[player] = odds_norm_map[norm]
        else:
            # Try fuzzy matching
            match, score = fuzzy_match_players(player, odds_players, min_ratio=90)
            if match:
                mapping[player] = match
    
    return mapping
