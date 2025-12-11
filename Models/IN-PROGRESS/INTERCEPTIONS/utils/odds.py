"""Odds conversion and probability utilities"""


def american_to_probability(american_odds):
    """Convert American odds to implied probability"""
    if american_odds is None:
        return 0.0
    
    s = str(american_odds).strip().replace('\u2212', '-')
    if not s or s == '-':
        return 0.0
    
    if s[0] == '+':
        s = s[1:]
    
    try:
        value = int(s)
    except (ValueError, TypeError):
        return 0.0
    
    if value < 0:
        return abs(value) / (abs(value) + 100.0)
    else:
        return 100.0 / (value + 100.0)


def probability_to_american(probability):
    """Convert probability to American odds"""
    epsilon = 1e-9
    prob = min(max(float(probability), epsilon), 1.0 - epsilon)
    
    if prob >= 0.5:
        return -int(round((prob / (1.0 - prob)) * 100))
    else:
        return int(round(((1.0 - prob) / prob) * 100))


def remove_vig(over_prob, under_prob):
    """Remove bookmaker vig from probabilities to get fair odds"""
    total_prob = over_prob + under_prob
    vig_factor = 1.0 / total_prob
    
    fair_over = over_prob * vig_factor
    fair_under = under_prob * vig_factor
    
    return fair_over, fair_under, total_prob


def calculate_edge(model_prob, book_prob_fair):
    """Calculate betting edge: model probability vs fair bookmaker probability"""
    return model_prob - book_prob_fair
