# =============================================================================
# filters.py
# Bookmaker filtering applied to events BEFORE arbitrage / +EV analysis.
#
# Two filters, applied in this order by `prepare_events`:
#   1. Accessibility ("I bet from…"): keep only books you can actually use
#      from one location. An arbitrage is only real if every leg can be placed.
#   2. Reliability: always drop books whose API prices are known to differ from
#      what users actually see, plus any books the user excludes by name.
#
# Matching is done on a normalised form of the bookmaker's key and title
# (lowercase, letters and digits only), so the pattern "marathonbet" matches
# the title "Marathon Bet" and "888" matches "888sport".
# =============================================================================

import re

# "I bet from…" presets: substring patterns matched against bookmaker names.
# None disables the filter.
ACCESSIBILITY_PRESETS: dict[str, frozenset | None] = {
    "anywhere": None,
    "brazil": frozenset({
        # International books licensed in BR or accepting BR users
        "bet365", "betfair", "pinnacle", "1xbet", "betsson",
        "unibet", "betway", "888", "leovegas", "marathonbet",
        # BR-native operators (available through the BrOdds provider)
        "sportingbet", "betano", "kto", "pixbet", "stake",
        "estrelabet", "galera", "esportes da sorte", "superbet",
    }),
    "usa": frozenset({
        "draftkings", "fanduel", "betmgm", "caesars", "betrivers",
        "espn bet", "fanatics", "hard rock", "barstool", "pointsbet",
        "bovada", "mybookie", "betonline", "betus", "lowvig",
    }),
    "uk": frozenset({
        "bet365", "betfair", "william hill", "ladbrokes", "coral",
        "betway", "888", "unibet", "paddy power", "skybet",
        "betvictor", "marathonbet", "leovegas",
    }),
    "europe": frozenset({
        "bet365", "betfair", "pinnacle", "1xbet", "betsson",
        "unibet", "betway", "888", "marathonbet",
    }),
}

# Books whose feed prices routinely differ from what users can actually bet:
#   - 1xBet:  dozens of regional sites with independent pricing; the API serves
#             the international feed, often 2-5% off the local site → phantom arbs.
#   - Unibet: does not operate in Brazil, so its "arbs" cannot be taken there.
UNRELIABLE_PATTERNS: frozenset = frozenset({"1xbet", "unibet"})


def _normalise(text: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (text or "").lower())


def matches_any(bookmaker: dict, patterns) -> bool:
    """True if the bookmaker's key or title contains any of the patterns."""
    names = (_normalise(bookmaker.get("title", "")), _normalise(bookmaker.get("key", "")))
    return any(_normalise(p) in name for p in patterns for name in names if name)


def is_unreliable(bookmaker: dict) -> bool:
    return matches_any(bookmaker, UNRELIABLE_PATTERNS)


def _filter_bookmakers(events: list, keep) -> list:
    """Return shallow copies of `events` keeping only bookmakers where keep(book)."""
    return [
        {**event, "bookmakers": [b for b in event.get("bookmakers", []) if keep(b)]}
        for event in events
    ]


def prepare_events(
    events: list,
    bet_from: str = "anywhere",
    excluded_titles: frozenset = frozenset(),
    include_unreliable: bool = False,
) -> list:
    """Apply the accessibility, reliability and exclusion filters to events.

    Args:
        events:             canonical events from a provider
        bet_from:           key of ACCESSIBILITY_PRESETS
        excluded_titles:    exact bookmaker titles to drop
        include_unreliable: keep UNRELIABLE_PATTERNS books (off by default)
    """
    accessible = ACCESSIBILITY_PRESETS[bet_from]

    def keep(book: dict) -> bool:
        if accessible is not None and not matches_any(book, accessible):
            return False
        if not include_unreliable and is_unreliable(book):
            return False
        return book.get("title") not in excluded_titles

    return _filter_bookmakers(events, keep)
