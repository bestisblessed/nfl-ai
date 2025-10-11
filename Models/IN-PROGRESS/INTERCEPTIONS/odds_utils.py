"""
Utility functions for working with American odds, implied probabilities, and
robust player name matching to align sportsbook markets with model outputs.

This module is intentionally dependency-light. If RapidFuzz is available, we
use it for higher-quality fuzzy matching; otherwise we fall back to simple
exact/startswith/contains strategies.
"""

from __future__ import annotations

from typing import Iterable, Optional, Tuple


def american_to_prob(american_odds: int | str) -> float:
    """Convert American odds to implied probability in [0, 1].

    Args:
        american_odds: American odds as int or str (e.g., -120, "+115").

    Returns:
        float implied probability between 0 and 1.
    """
    if american_odds is None:
        return 0.0
    s = str(american_odds).strip()
    # Normalize Unicode minus to ASCII hyphen
    s = s.replace("\u2212", "-")
    if not s:
        return 0.0
    # Remove any leading plus sign for uniform parsing
    if s[0] == '+':
        s = s[1:]
    try:
        val = int(s)
    except ValueError:
        # Not a valid odds string
        return 0.0

    if val < 0:
        # Favorite: -N => N/(N+100)
        n = abs(val)
        return n / (n + 100.0)
    else:
        # Underdog: +P => 100/(P+100)
        return 100.0 / (val + 100.0)


def prob_to_american(probability: float) -> int:
    """Convert probability (0-1) to American odds.

    Mirrors the logic used elsewhere in the project (see
    predict_upcoming_starting_qbs.py) but clamps for stability.
    """
    epsilon = 1e-9
    p = float(max(min(probability, 1.0 - epsilon), epsilon))
    if p >= 0.5:
        # Favorite => negative odds
        return -int(round((p / (1.0 - p)) * 100))
    else:
        # Underdog => positive odds
        return int(round(((1.0 - p) / p) * 100))


def normalize_player_name(name: str) -> str:
    """Normalize player names for resilient matching.

    Lowercases, strips whitespace, squashes internal whitespace, and converts
    common punctuation variants to spaces.
    """
    if name is None:
        return ""
    s = str(name).strip().lower()
    for ch in ["\u2019", "'", ".", ",", "-", "\u2013", "\u2014"]:
        s = s.replace(ch, " ")
    parts = [p for p in s.split() if p]
    return " ".join(parts)


def best_fuzzy_match(
    target: str,
    candidates: Iterable[str],
    min_ratio: int = 90,
) -> Tuple[Optional[str], int]:
    """Find best fuzzy match for target among candidates.

    Returns (best_candidate, score). If no candidate meets min_ratio, returns
    (None, 0). Uses RapidFuzz when available; otherwise falls back to simple
    heuristics (exact, startswith, contains).
    """
    normalized_target = normalize_player_name(target)
    normalized_map = {c: normalize_player_name(c) for c in candidates}

    # Fast exact match
    for orig, norm in normalized_map.items():
        if norm == normalized_target:
            return orig, 100

    # Try simple startswith/contains heuristics
    for orig, norm in normalized_map.items():
        if norm.startswith(normalized_target) or normalized_target.startswith(norm):
            return orig, 95
        if norm.find(normalized_target) >= 0 or normalized_target.find(norm) >= 0:
            return orig, 92

    # RapidFuzz if available
    try:
        from rapidfuzz import fuzz  # type: ignore

        best_name: Optional[str] = None
        best_score = 0
        for orig, norm in normalized_map.items():
            score = int(fuzz.token_sort_ratio(normalized_target, norm))
            if score > best_score:
                best_score = score
                best_name = orig
        if best_name is not None and best_score >= min_ratio:
            return best_name, best_score
        return None, 0
    except Exception:
        # RapidFuzz not installed or failed; no good match
        return None, 0


def american_pair_to_probs(over_american: int | str, under_american: int | str) -> Tuple[float, float]:
    """Deprecated: prefer calling american_to_prob on each leg directly."""
    p_over = american_to_prob(over_american)
    p_under = american_to_prob(under_american)
    return p_over, p_under


