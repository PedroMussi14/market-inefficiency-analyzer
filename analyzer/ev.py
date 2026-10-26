# =============================================================================
# ev.py
# Positive expected value (+EV) detection against a sharp reference line.
#
# Pinnacle is widely treated as the "sharpest" bookmaker: its prices are the
# best public estimate of true outcome probabilities. Removing its margin
# ("de-vigging") gives a fair probability p for each outcome. Any other book
# offering decimal odds d with  d * p > 1  is a positive-expected-value bet.
# =============================================================================

from .arbitrage import build_deep_link, outcome_key
from .odds import american_to_decimal, implied_probability_sum

SHARP_BOOK = "pinnacle"


def _is_sharp_book(bookmaker: dict) -> bool:
    return SHARP_BOOK in bookmaker.get("title", "").lower()


def fair_probabilities(event: dict, selected_market: str = "h2h") -> dict:
    """Return the sharp book's de-vigged probability per outcome key.

    Outcomes are keyed with `outcome_key`, so spread/total prices are only ever
    compared against the sharp price on the same line. Returns {} when the
    sharp book does not price this market.
    """
    sharp_prices = {}
    for bookmaker in event.get("bookmakers", []):
        if not _is_sharp_book(bookmaker):
            continue
        for market in bookmaker.get("markets", []):
            if market.get("key") != selected_market:
                continue
            for outcome in market.get("outcomes", []):
                key = outcome_key(outcome, selected_market)[0]
                sharp_prices[key] = american_to_decimal(outcome["price"])
        break

    if not sharp_prices:
        return {}

    # Normalise implied probabilities so they sum to exactly 1 (remove the vig)
    raw_sum = implied_probability_sum(sharp_prices.values())
    return {key: (1 / price) / raw_sum for key, price in sharp_prices.items()}


def find_ev_bets(event: dict, selected_market: str = "h2h") -> list:
    """Return every +EV bet in the event, best edge first.

    Each bet dict contains: event, sport, commence_time, outcome, point,
    bookmaker, american_odds, decimal_odds, true_prob (%), ev_pct (%), link.
    Returns [] if the sharp book is not present for this market.
    """
    true_probs = fair_probabilities(event, selected_market)
    if not true_probs:
        return []

    ev_bets = []
    for bookmaker in event.get("bookmakers", []):
        if _is_sharp_book(bookmaker):
            continue
        title = bookmaker.get("title", bookmaker.get("key", "Unknown"))

        for market in bookmaker.get("markets", []):
            if market.get("key") != selected_market:
                continue
            for outcome in market.get("outcomes", []):
                key, name, point = outcome_key(outcome, selected_market)
                if key not in true_probs:
                    continue

                decimal_odds = american_to_decimal(outcome["price"])
                ev = decimal_odds * true_probs[key] - 1
                if ev <= 0:
                    continue

                ev_bets.append({
                    "event":         f"{event.get('away_team')} vs {event.get('home_team')}",
                    "sport":         event.get("sport_title"),
                    "commence_time": event.get("commence_time"),
                    "outcome":       name,
                    "point":         point,
                    "bookmaker":     title,
                    "american_odds": outcome["price"],
                    "decimal_odds":  round(decimal_odds, 4),
                    "true_prob":     round(true_probs[key] * 100, 2),
                    "ev_pct":        round(ev * 100, 2),
                    "link":          build_deep_link(title, outcome, market, bookmaker),
                })

    return sorted(ev_bets, key=lambda bet: bet["ev_pct"], reverse=True)
