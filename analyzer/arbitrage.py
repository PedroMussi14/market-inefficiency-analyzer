# =============================================================================
# arbitrage.py
# Core logic for detecting arbitrage opportunities across sportsbooks.
#
# Workflow:
#   1. Extract best odds per outcome from all bookmakers for a given event
#   2. Convert American odds → Decimal
#   3. Group outcomes into complete lines (spreads/totals pair on the same line)
#   4. Compute implied probability sum per line; keep the lowest
#   5. If sum < 1.0 → arbitrage exists; calculate optimal stakes, profit, ROI
# =============================================================================

from .odds import american_to_decimal, implied_probability_sum

# -----------------------------------------------------------------------------
# Bookmaker Deep Link Configuration
# -----------------------------------------------------------------------------
# Maps bookmaker titles (as returned by the API) to their event URL templates.
# Use {sid} as the placeholder for the event SID provided by the API.
#
# To add a new bookmaker:
#   1. Open an event page on their site and inspect the URL structure
#   2. Replace the event-specific segment with {sid}
#   3. Add the entry below
# -----------------------------------------------------------------------------
BOOKMAKER_DEEP_LINK_TEMPLATES = {
    "BetUS": "https://www.betus.com.pa/sportsbook/#/event/main/{sid}",
}

# Homepage-only URLs that should be discarded in favour of SID-based deep links.
# If a bookmaker's API link resolves to just their homepage, add it here.
BOOKMAKER_HOMEPAGES = {
    "https://www.betus.com.pa",
    "http://www.betus.com.pa",
}

# Markets where the spread/total line must be included in the outcome key to
# avoid accidentally pairing incompatible lines and producing false arbitrage.
LINE_BASED_MARKETS = {"spreads", "totals"}


# =============================================================================
# Arbitrage Math
# =============================================================================

def calculate_stakes(bankroll: float, odds: list) -> list:
    """Compute optimal stake per outcome to guarantee equal payout regardless of result.

    Each stake is proportional to the inverse of its odds, normalised to the bankroll.
    """
    inv_sum = implied_probability_sum(odds)
    return [(bankroll / odd) / inv_sum for odd in odds]


def calculate_profit(bankroll: float, stakes: list, odds: list) -> float:
    """Return the guaranteed profit (worst-case payout minus bankroll)."""
    payouts = [stake * odd for stake, odd in zip(stakes, odds, strict=True)]
    return min(payouts) - bankroll


def calculate_roi(bankroll: float, profit: float) -> float:
    """Return profit as a percentage of bankroll."""
    return (profit / bankroll) * 100


# =============================================================================
# Outcome Key Helpers
# =============================================================================

def outcome_key(outcome: dict, selected_market: str) -> tuple:
    """Build a stable, unique key for a betting outcome.

    For line-based markets (spreads/totals) the point value is embedded in the
    key so that outcomes on different lines are never grouped together.

    Returns:
        (outcome_id, name, point)
    """
    name = outcome["name"]
    point = outcome.get("point")

    if selected_market in LINE_BASED_MARKETS:
        return f"{name}|{point}", name, point

    return name, name, point


# =============================================================================
# Deep Link Resolution
# =============================================================================

def build_deep_link(
    bookmaker_title: str,
    outcome: dict,
    market: dict,
    bookmaker: dict,
):
    """Resolve the best available direct link to the event page on the bookmaker's site.

    Resolution order:
        1. outcome-level  → most specific, prefer this
        2. market-level   → second preference
        3. bookmaker-level → least specific

    If the resolved link is a bare homepage (listed in BOOKMAKER_HOMEPAGES),
    it is discarded and a deep link is constructed from the event SID instead.
    If no SID or template is available, returns None.
    """
    raw_link = (
        outcome.get("link")
        or market.get("link")
        or bookmaker.get("link")
    )

    # Discard bare homepage links — they add no navigational value
    if raw_link and raw_link.rstrip("/") in BOOKMAKER_HOMEPAGES:
        raw_link = None

    if raw_link:
        return raw_link

    # Attempt SID-based deep link construction
    sid = (
        outcome.get("sid")
        or market.get("sid")
        or bookmaker.get("sid")
    )
    template = BOOKMAKER_DEEP_LINK_TEMPLATES.get(bookmaker_title)

    if template and sid:
        return template.format(sid=sid)

    return None


# =============================================================================
# Best-Price Extraction
# =============================================================================

def get_best_odds_for_event(event: dict, selected_market: str = "h2h") -> dict:
    """Scan all bookmakers for the given event and return the best (highest)
    decimal odds available per outcome.

    Returns a dict keyed by outcome_id, each value containing:
        name, point, bookmaker, american_odds, odds (decimal), link
    """
    best_odds = {}

    for bookmaker in event.get("bookmakers", []):
        book_title = bookmaker.get("title", bookmaker.get("key", "Unknown"))

        for market in bookmaker.get("markets", []):
            if market.get("key") != selected_market:
                continue

            for outcome in market.get("outcomes", []):
                outcome_id, name, point = outcome_key(outcome, selected_market)
                american_price = outcome["price"]
                decimal_price = american_to_decimal(american_price)
                link = build_deep_link(book_title, outcome, market, bookmaker)

                # Keep this bookmaker only if it offers the best price for this outcome
                if outcome_id not in best_odds or decimal_price > best_odds[outcome_id]["odds"]:
                    best_odds[outcome_id] = {
                        "outcome_id":    outcome_id,
                        "name":          name,
                        "point":         point,
                        "bookmaker":     book_title,
                        "american_odds": american_price,
                        "odds":          decimal_price,
                        "link":          link,
                    }

    return best_odds


# =============================================================================
# Event Analysis
# =============================================================================

def _build_results(best_odds: dict, outcome_ids: list) -> list:
    """Construct the per-outcome result rows from the best-odds mapping."""
    return [
        {
            "outcome":       best_odds[oid]["name"],
            "point":         best_odds[oid]["point"],
            "bookmaker":     best_odds[oid]["bookmaker"],
            "american_odds": best_odds[oid]["american_odds"],
            "decimal_odds":  best_odds[oid]["odds"],
            "link":          best_odds[oid].get("link"),
        }
        for oid in outcome_ids
    ]


def _attach_arbitrage_data(
    analysis: dict,
    results: list,
    decimal_odds: list,
    bankroll: float,
) -> None:
    """Mutate analysis and results in-place with stake, profit, and ROI data."""
    stakes = calculate_stakes(bankroll, decimal_odds)
    profit = calculate_profit(bankroll, stakes, decimal_odds)
    roi    = calculate_roi(bankroll, profit)

    for i, stake in enumerate(stakes):
        results[i]["stake"] = stake

    analysis["profit"] = profit
    analysis["roi"]    = roi


# =============================================================================
# Market Completeness & Line Grouping
# =============================================================================

def _expected_outcome_count(event: dict, selected_market: str) -> int:
    """Return how many outcomes a complete market must cover.

    Line-based markets are always two-sided (home/away or over/under).
    For h2h, the largest outcome set any single bookmaker lists is the truth:
    if one book prices a Draw, a Home+Away pair alone is not a complete hedge.
    Soccer moneylines are always 3-way, even if every remaining book omits the
    Draw (e.g. after bookmaker filtering).
    """
    if selected_market in LINE_BASED_MARKETS:
        return 2

    per_book = [
        len(market.get("outcomes", []))
        for bookmaker in event.get("bookmakers", [])
        for market in bookmaker.get("markets", [])
        if market.get("key") == selected_market
    ]
    expected = max(per_book, default=0)

    if str(event.get("sport_key", "")).startswith("soccer"):
        expected = max(expected, 3)
    return expected


def _group_into_lines(best_odds: dict, selected_market: str, home_team: str) -> dict:
    """Split best-price outcomes into independent markets ("lines").

    A spread or total is only a hedge when both sides are on the SAME line:
        spreads → Home -3.5 pairs with Away +3.5  (keyed by the home-team point)
        totals  → Over 220.5 pairs with Under 220.5 (keyed by the total)
    h2h has a single line, keyed None.

    Returns {line_key: [outcome_id, ...]}.
    """
    if selected_market not in LINE_BASED_MARKETS:
        return {None: list(best_odds)}

    lines: dict = {}
    for oid, entry in best_odds.items():
        point = entry["point"]
        if point is None:
            continue
        if selected_market == "spreads":
            key = point if entry["name"] == home_team else -point
        else:
            key = point
        lines.setdefault(key, []).append(oid)
    return lines


def analyze_event(
    event: dict,
    bankroll: float = 100,
    selected_market: str = "h2h",
):
    """Analyse a single event for arbitrage opportunities.

    Each complete line (see `_group_into_lines`) is evaluated independently and
    the one with the lowest implied probability sum is reported.

    Returns a structured analysis dict, or None when no line covers every
    outcome (an incomplete market can never be a guaranteed hedge).

    Return schema:
        event, sport, commence_time, line (float | None), implied_prob_sum,
        arbitrage, results (list), profit (float | None), roi (float | None)
    """
    best_odds = get_best_odds_for_event(event, selected_market=selected_market)
    expected  = max(_expected_outcome_count(event, selected_market), 2)

    candidates = []
    for line, outcome_ids in _group_into_lines(
        best_odds, selected_market, event.get("home_team")
    ).items():
        if len(outcome_ids) < expected:
            continue
        decimal_odds = [best_odds[oid]["odds"] for oid in outcome_ids]
        candidates.append((implied_probability_sum(decimal_odds), line, outcome_ids, decimal_odds))

    if not candidates:
        return None

    prob_sum, line, outcome_ids, decimal_odds = min(candidates, key=lambda c: c[0])
    arb_exists = prob_sum < 1

    results = _build_results(best_odds, outcome_ids)

    analysis = {
        "event":            f"{event.get('away_team')} vs {event.get('home_team')}",
        "sport":            event.get("sport_title"),
        "commence_time":    event.get("commence_time"),
        "line":             line,
        "implied_prob_sum": prob_sum,
        "arbitrage":        arb_exists,
        "results":          results,
        "profit":           None,
        "roi":              None,
    }

    if arb_exists:
        _attach_arbitrage_data(analysis, results, decimal_odds, bankroll)

    return analysis
