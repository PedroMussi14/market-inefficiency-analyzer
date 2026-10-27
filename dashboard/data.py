# =============================================================================
# data.py
# Cached data loading and DataFrame shaping for the dashboard.
#
# Every loader runs provider events through analyzer.filters.prepare_events,
# so the accessibility and reliability filters apply identically on every page.
# =============================================================================

from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd
import streamlit as st

from analyzer.arbitrage import analyze_event
from analyzer.ev import find_ev_bets
from analyzer.export import analyses_to_dataframe
from analyzer.filters import prepare_events
from analyzer.providers import get_provider

from .config import EXCLUDED_SPORT_KEYWORDS

# =============================================================================
# Loaders (cached)
# =============================================================================


@st.cache_data(ttl=300)
def load_sports(provider_name: str) -> dict:
    """Return a display-title → sport-key mapping for the provider.

    Futures/outright markets are excluded because they can't be arbitraged
    per game. Cached for 5 minutes per provider.
    """
    sports = get_provider(provider_name).get_sports()
    return {
        sport["title"]: sport["key"]
        for sport in sports
        if not any(kw in sport["key"].lower() for kw in EXCLUDED_SPORT_KEYWORDS)
    }


def _fetch_events(provider_name: str, sport_key: str, market: str, region: str,
                  bet_from: str, excluded_books: frozenset = frozenset()) -> list:
    """Fetch odds for one sport and apply the bookmaker filters."""
    events = get_provider(provider_name).get_odds(
        sport=sport_key, markets=market, regions=region,
        odds_format="american", include_links=True, include_sids=True,
    )
    return prepare_events(events, bet_from=bet_from, excluded_titles=excluded_books)


def _analyse(events: list, bankroll: float, market: str) -> list:
    return [
        analysis
        for event in events
        if (analysis := analyze_event(event, bankroll, selected_market=market)) is not None
    ]


@st.cache_data(ttl=60)
def load_data(
    provider_name: str,
    sport_key: str,
    market: str,
    region: str,
    bankroll: float,
    bet_from: str,
    excluded_books: frozenset = frozenset(),
) -> tuple:
    """Fetch one sport's odds and run the arbitrage analysis.

    Returns:
        (all_analyses, detail_df, event_df)
    """
    events = _fetch_events(provider_name, sport_key, market, region, bet_from, excluded_books)

    all_analyses = _analyse(events, bankroll, market)

    detail_df = analyses_to_dataframe(all_analyses)
    event_df  = summarize_by_event(all_analyses)
    detail_df = add_direct_links(detail_df, all_analyses)

    return all_analyses, detail_df, event_df


@st.cache_data(ttl=120)
def load_all_arbitrage(provider_name: str, market: str, region: str, bankroll: float,
                       bet_from: str) -> tuple:
    """Scan every available sport in parallel and keep only arbitrage results.

    Returns:
        (arbitrage_analyses sorted by ROI,
         sorted sport keys that failed to load,
         the first failure's message, or "" when every sport loaded)
    """
    sports = load_sports(provider_name)

    def scan(sport_key: str) -> list:
        events = _fetch_events(provider_name, sport_key, market, region, bet_from)
        return [a for a in _analyse(events, bankroll, market) if a["arbitrage"]]

    found, failed, reasons = [], [], []
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(scan, key): key for key in sports.values()}
        for future in as_completed(futures):
            try:
                found.extend(future.result())
            except Exception as e:
                failed.append(futures[future])
                reasons.append(e)

    # A spent quota explains every other failure, so report it first
    reasons.sort(key=lambda e: not getattr(e, "quota_exhausted", False))
    reason = str(reasons[0]) if reasons else ""
    return sorted(found, key=lambda a: a.get("roi") or 0, reverse=True), sorted(failed), reason


@st.cache_data(ttl=60)
def load_ev_bets(provider_name: str, sport_key: str, market: str, region: str,
                 bet_from: str) -> list:
    """Return every +EV bet for one sport versus Pinnacle's de-vigged line."""
    events = _fetch_events(provider_name, sport_key, market, region, bet_from)
    bets = [bet for event in events for bet in find_ev_bets(event, selected_market=market)]
    return sorted(bets, key=lambda b: b["ev_pct"], reverse=True)


# =============================================================================
# DataFrame helpers
# =============================================================================


def summarize_by_event(all_analyses: list) -> pd.DataFrame:
    """Build a one-row-per-event summary DataFrame from a list of analysis dicts.

    A "Line" column is included only for spreads/totals analyses.
    """
    rows = []
    for analysis in all_analyses:
        row = {
            "Game":              analysis["event"],
            "Sport":             analysis["sport"],
            "Start Time":        analysis["commence_time"],
        }
        if analysis.get("line") is not None:
            row["Line"] = analysis["line"]
        row.update({
            "Market Efficiency": round(analysis["implied_prob_sum"], 4),
            "Guaranteed Profit": "Yes" if analysis["arbitrage"] else "No",
            "Profit ($)":        round(analysis["profit"], 2) if analysis["profit"] is not None else None,
            "Return (%)":        round(analysis["roi"],    2) if analysis["roi"]    is not None else None,
        })
        rows.append(row)
    return pd.DataFrame(rows)


def add_direct_links(df: pd.DataFrame, analyses: list) -> pd.DataFrame:
    """Attach a 'Direct Link' column to the detail DataFrame by cross-referencing analyses.

    Matches each row by (event name, bookmaker) and pulls the link stored in the
    analysis results. This preserves deep links built in arbitrage.py.
    """
    df = df.copy()

    # Build a lookup: (event, bookmaker) → link  for O(1) access
    link_lookup = {
        (analysis.get("event"), res.get("bookmaker")): res.get("link")
        for analysis in analyses
        for res in analysis.get("results", [])
    }

    game_col = "event" if "event" in df.columns else "Game"
    df["Direct Link"] = df.apply(
        lambda row: link_lookup.get((row.get(game_col), row.get("bookmaker"))),
        axis=1,
    )
    return df


def format_event_detail(df: pd.DataFrame) -> pd.DataFrame:
    """Rename raw API column names to user-friendly display names and round numeric columns."""
    rename_map = {
        "event":            "Game",
        "sport":            "Sport",
        "commence_time":    "Start Time",
        "implied_prob_sum": "Market Efficiency",
        "arbitrage":        "Guaranteed Profit",
        "profit":           "Profit ($)",
        "roi":              "Return (%)",
        "outcome":          "Bet On",
        "point":            "Line",
        "bookmaker":        "Sportsbook",
        "american_odds":    "American Odds",
        "decimal_odds":     "Decimal Odds",
        "stake":            "Suggested Bet ($)",
    }
    display_df = df.rename(columns=rename_map)

    # Apply appropriate rounding: 4 decimal places for rates, 2 for currency/percent
    round_4 = {"Market Efficiency", "Decimal Odds"}
    for col in ["Market Efficiency", "Profit ($)", "Return (%)", "Decimal Odds", "Suggested Bet ($)"]:
        if col in display_df.columns:
            display_df[col] = pd.to_numeric(display_df[col], errors="coerce").round(4 if col in round_4 else 2)

    return display_df
