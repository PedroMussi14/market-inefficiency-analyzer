# =============================================================================
# odds.py
# Odds-format conversions and implied-probability maths.
#
# Bookmakers quote prices in different formats. Everything in the analyzer is
# computed in decimal odds, where a price of 2.50 returns 2.50 per 1.00 staked
# (stake included). The implied probability of a price is simply 1 / decimal.
# =============================================================================

from collections.abc import Iterable


def american_to_decimal(american_odds: int) -> float:
    """Convert American odds to decimal format.

    Positive odds (e.g. +150):  decimal = 1 + (odds / 100)
    Negative odds (e.g. -110):  decimal = 1 + (100 / |odds|)
    """
    if american_odds > 0:
        return 1 + (american_odds / 100)
    return 1 + (100 / abs(american_odds))


def decimal_to_american(decimal_odds: float) -> int:
    """Convert decimal odds to American format, rounded to the nearest integer.

    Raises ValueError for prices at or below 1.0, which have no American form.
    """
    if decimal_odds <= 1:
        raise ValueError(f"Decimal odds must be greater than 1.0, got {decimal_odds}")
    if decimal_odds >= 2:
        return round((decimal_odds - 1) * 100)
    return round(-100 / (decimal_odds - 1))


def implied_probability(decimal_odds: float) -> float:
    """Return the probability implied by a single decimal price."""
    return 1 / decimal_odds


def implied_probability_sum(decimal_odds: Iterable[float]) -> float:
    """Return the sum of implied probabilities across all outcomes of a market.

    Bookmakers price above 1.0 (the excess is their margin, or "vig").
    A sum below 1.0 across the best available prices means an arbitrage exists.
    """
    return sum(implied_probability(odd) for odd in decimal_odds)
