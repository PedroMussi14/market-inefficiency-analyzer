# =============================================================================
# components.py
# Presentation helpers: formatting, bookmaker links, and the HTML pieces the
# views are built from (tiles, the headline money figure, the order ticket,
# list rows). Any text that comes from a data provider is HTML-escaped
# before it is placed inside unsafe_allow_html markup.
# =============================================================================

import zlib
from datetime import UTC, datetime
from html import escape
from urllib.parse import quote_plus

import pandas as pd
import streamlit as st

from .config import BOOK_LINKS, MARKET_OPTIONS, NEAR_ARB_THRESHOLD
from .theme import TILE_TONES

# Stake-split tones: the accent at falling strengths, one per leg
SPLIT_TONES = ["#1d5fd6", "#6f9be6", "#a9c5f1", "#d3e2f8"]

# Short marks for well-known sportsbooks; others use their initials
BOOK_MARKS = {
    "Bet365": "365", "Betfair": "BF", "Betsson": "BS", "Pinnacle": "PN", "Betway": "BW",
    "Marathon Bet": "MB", "DraftKings": "DK", "FanDuel": "FD", "BetMGM": "MGM", "Caesars": "CZ",
    "William Hill": "WH", "888sport": "888", "Unibet": "UB", "Betano": "BT", "Sportingbet": "SB",
}


# ── Formatting ───────────────────────────────────────────────────────────────

def is_live_event(commence_time_str: str) -> bool:
    """Return True if the event start time is in the past (game is underway)."""
    if not commence_time_str:
        return False
    try:
        event_time = datetime.fromisoformat(commence_time_str.replace("Z", "+00:00"))
        return event_time <= datetime.now(UTC)
    except ValueError:
        return False


def format_start(commence_time) -> str:
    """'2026-10-27T23:30:00Z' → 'Tue 27 Oct, 23:30 UTC' (falls back to the raw text)."""
    text = str(commence_time or "")
    try:
        t = datetime.fromisoformat(text.replace("Z", "+00:00")).astimezone(UTC)
    except ValueError:
        return text
    return f"{t:%a} {t.day} {t:%b}, {t:%H:%M} UTC"


def format_outcome(name, point=None) -> str:
    """Label an outcome, including its line for spreads/totals.

    format_outcome("Lakers")           → "Lakers"
    format_outcome("Lakers", -3.5)     → "Lakers -3.5"
    format_outcome("Over", 220.5)      → "Over 220.5"
    """
    if point is None or pd.isna(point):
        return str(name)
    if name in ("Over", "Under"):
        return f"{name} {point:g}"
    return f"{name} {point:+g}"


def format_market_label(market_key: str) -> str:
    """Convert an API market key back to a human-readable label for display."""
    return {v: k for k, v in MARKET_OPTIONS.items()}.get(market_key, market_key)


def split_teams(game: str) -> list:
    for sep in (" vs ", " @ "):
        if sep in game:
            return game.split(sep)
    return [game]


def short_game(name: str, limit: int = 28) -> str:
    """Shorten 'Boston Celtics vs Chicago Bulls' → 'Celtics vs Bulls'."""
    teams = split_teams(name)
    if len(teams) == 2:
        name = " vs ".join(t.split()[-1] if len(t) > 12 else t for t in teams)
    return name if len(name) <= limit else name[: limit - 1] + "…"


def money(value, signed: bool = False) -> str:
    """$1,234.50 with an optional sign; a dash when missing."""
    if value is None or pd.isna(value):
        return "—"
    sign = ("+" if value > 0 else "−" if value < 0 else "") if signed else ("−" if value < 0 else "")
    return f"{sign}${abs(value):,.2f}"


def percent(value, signed: bool = True, digits: int = 2) -> str:
    """+0.46% with its sign; a dash when missing."""
    if value is None or pd.isna(value):
        return "—"
    sign = ("+" if value > 0 else "−" if value < 0 else "") if signed else ""
    return f"{sign}{abs(value):.{digits}f}%"


def american(odds) -> str:
    try:
        odds = int(odds)
    except (TypeError, ValueError):
        return "—"
    return f"+{odds}" if odds > 0 else f"−{abs(odds)}"


def locked_in_return(implied_sum):
    """Return (%) from backing every outcome at the best prices, staked to pay the same.

    1 / implied_sum − 1: positive is a guaranteed profit (the arbitrage ROI),
    negative is the margin the bookmakers keep.
    """
    return (1 / implied_sum - 1) * 100


# ── Bookmaker links ──────────────────────────────────────────────────────────

def clean_bookmaker_link(raw_link: str, book_title: str) -> str:
    """Sanitise a bookmaker link before rendering it.

    Handles known issues such as BetMGM's {state} placeholder which appears
    when no geo-specific link is available.

    Returns None if the link is unusable.
    """
    if not raw_link or not str(raw_link).startswith("http"):
        return None

    link_str = str(raw_link).strip()

    # BetMGM returns {state} in the URL when a geo-specific link isn't available
    if "betmgm.com" in link_str.lower():
        if "{state}" in link_str:
            link_str = link_str.replace("{state}", "www")
        if "sports.www.betmgm.com" in link_str or "{state}" in link_str:
            return None

    return link_str


def normalize_book_name(name: str) -> str:
    """Map a raw bookmaker name (from the API) to its canonical display name."""
    name_lower = name.lower()
    mapping = {
        "draftkings":  "DraftKings",
        "fanduel":     "FanDuel",
        "betmgm":      "BetMGM",
        "caesars":     "Caesars",
        "betrivers":   "BetRivers",
        "pointsbet":   "PointsBet",
        "barstool":    "Barstool",
        "hard rock":   "Hard Rock Bet",
        "espn":        "ESPN BET",
        "fanatics":    "Fanatics",
        "bet365":      "Bet365",
        "william hill":"William Hill",
        "888":         "888sport",
        "unibet":      "Unibet",
        "pinnacle":    "Pinnacle",
        "betway":      "Betway",
        "leovegas":    "LeoVegas",
        "coral":       "Coral",
        "ladbrokes":   "Ladbrokes",
        "bovada":      "Bovada",
        "mybookie":    "MyBookie.ag",
        "lowvig":      "LowVig.ag",
        "betus":       "BetUS",
        "betonline":   "BetOnline",
    }
    for key, display in mapping.items():
        if key in name_lower:
            return display
    return name


def book_url(book: str, raw_link=None) -> str | None:
    """The best URL for a bookmaker: the provider's deep link, else its homepage."""
    name = normalize_book_name(book)
    return clean_bookmaker_link(raw_link, name) or BOOK_LINKS.get(name)


def build_game_info_link(game_name: str) -> str:
    """Build a Google search URL for ESPN match coverage of the given game."""
    return f"https://www.google.com/search?q={quote_plus(game_name + ' ESPN')}"


def build_general_odds_info_link(game_name: str) -> str:
    """Build a Google search URL for odds info on the given game."""
    return f"https://www.google.com/search?q={quote_plus(game_name + ' odds')}"


def open_link(url: str | None, label: str = "Open", primary: bool = False) -> str:
    """A pill-shaped link that opens in a new tab ('' when there is no URL)."""
    if not url:
        return ""
    cls = "open primary" if primary else "open"
    return (f'<a class="{cls}" href="{escape(url)}" target="_blank" rel="noopener noreferrer">'
            f'{escape(label)} ↗</a>')


# ── Tiles: a stable pale colour and a short mark for each team and book ──────

def _tone(name: str) -> tuple:
    return TILE_TONES[zlib.crc32(name.encode("utf-8")) % len(TILE_TONES)]


def _initials(name: str) -> str:
    words = [w for w in name.replace(".", " ").split() if w[:1].isalnum()]
    if not words:
        return "?"
    if len(words) == 1:
        return words[0][:2].upper()
    return (words[0][0] + words[-1][0]).upper()


def tile(name: str, mark: str | None = None, small: bool = False) -> str:
    bg, ink = _tone(name)
    cls = "tile sm" if small else "tile"
    return (f'<span class="{cls}" style="background:{bg};color:{ink}" '
            f'aria-hidden="true">{escape(mark or _initials(name))}</span>')


def book_tile(book: str, small: bool = False) -> str:
    name = normalize_book_name(book)
    return tile(name, BOOK_MARKS.get(name), small)


def team_pair(game: str) -> str:
    """Two overlapping team tiles (or one for a game name that does not split)."""
    teams = split_teams(game)
    return '<span class="pair">' + "".join(tile(t.strip()) for t in teams[:2]) + "</span>"


# ── Page pieces ──────────────────────────────────────────────────────────────

def pill(text: str, kind: str = "neutral") -> str:
    return f'<span class="pill {kind}">{escape(text)}</span>'


def live_badge(commence_time) -> str:
    """A 'Live' pill if the event has started, else ''."""
    return pill("Live", "accent") if is_live_event(str(commence_time or "")) else ""


def status_pill(implied_sum: float) -> str:
    """'Guaranteed profit' under 1.000, 'Near break-even' under NEAR_ARB_THRESHOLD, else nothing."""
    if implied_sum < 1.0:
        return pill("Guaranteed profit", "positive")
    if implied_sum < NEAR_ARB_THRESHOLD:
        return pill("Near break-even", "warning")
    return ""


def render_page_header(title: str, sub: str = "", provider_name: str = "") -> None:
    """The page title, one line about the data under it, and where the data comes from."""
    source = ""
    if provider_name:
        live = provider_name != "demo"
        source = (f'<div class="source"><span class="dot{" live" if live else ""}"></span>'
                  f'{"Live odds" if live else "Demo data"}</div>')
    st.markdown(
        f'<div class="page-head"><div><h1>{escape(title)}</h1>'
        f'<div class="page-sub">{sub}</div></div>{source}</div>',
        unsafe_allow_html=True,
    )


def card_head(title: str, note: str = "") -> str:
    note_html = f'<span class="card-note">{note}</span>' if note else ""
    return f'<div class="card-head"><span class="card-title">{escape(title)}</span>{note_html}</div>'


def empty_state(html: str) -> None:
    """One sentence in a dashed frame, used wherever a block has nothing to show."""
    st.markdown(f'<div class="empty">{html}</div>', unsafe_allow_html=True)


def money_html(value: float, signed: bool = True, positive: bool = False) -> str:
    """The headline figure: '+$1' large with '.65' smaller and lighter."""
    text = money(value, signed=signed)
    whole, _, cents = text.partition(".")
    cls = "money pos" if positive else "money"
    cents_html = f'<span class="cents">.{cents}</span>' if cents else ""
    return f'<div class="{cls}">{whole}{cents_html}</div>'


def matchup_html(game: str, meta: str, pills_html: str = "") -> str:
    return (
        '<div class="card-head" style="align-items:center">'
        f'<div class="matchup">{team_pair(game)}<div><div class="matchup-name">{escape(game)}</div>'
        f'<div class="matchup-meta">{escape(meta)}</div></div></div>'
        f'<div>{pills_html}</div></div>'
    )


def facts_html(facts: list) -> str:
    """Small label-over-value facts: [(label, value), ...]."""
    cells = "".join(f'<div class="fact"><div class="label">{escape(label)}</div>'
                    f'<div class="value">{value}</div></div>' for label, value in facts)
    return f'<div class="facts">{cells}</div>'


# ── The order ticket: one row per leg, with its stake, payout and link ───────

def ticket_html(results: list, hide_american: bool = False) -> str:
    """Every outcome's best price as a ticket row.

    With stakes (an arbitrage): "Stake $44.98 · pays $101.65" per leg and a
    total showing every outcome returns the same. Without: the price alone.
    """
    has_stake = any(r.get("stake") is not None for r in results)
    rows, total, payouts = "", 0.0, []
    for r in results:
        book = normalize_book_name(r["bookmaker"])
        price = f'{r["decimal_odds"]:.2f}'
        if not hide_american:
            price += f' ({american(r.get("american_odds"))})'
        main = escape(format_outcome(r["outcome"], r.get("point")))
        if has_stake and r.get("stake") is not None:
            payout = r["stake"] * r["decimal_odds"]
            total += r["stake"]
            payouts.append(payout)
            money_cell = (f'<div class="leg-money"><div class="leg-main">{money(r["stake"])}</div>'
                          f'<div class="leg-sub">pays {money(payout)}</div></div>')
        else:
            money_cell = f'<div class="leg-money"><div class="leg-main">{price.split(" ")[0]}</div></div>'
        rows += (
            f'<div class="leg">{book_tile(book)}'
            f'<div><div class="leg-main">{main}</div>'
            f'<div class="leg-sub">{escape(book)} · {price}</div></div>'
            f'{money_cell}'
            f'<div class="leg-open">{open_link(book_url(r["bookmaker"], r.get("link")), "Open " + book)}</div>'
            '</div>'
        )
    total_html = ""
    if payouts:
        total_html = (f'<div class="ticket-total"><span>You stake <b>{money(total)}</b></span>'
                      f'<span>Every outcome pays <b>{money(min(payouts))}</b></span></div>')
    return f'<div class="ticket">{rows}</div>{total_html}'


def stake_split_html(results: list) -> str:
    """One 100% bar of the stake per leg, with its legend built from the same tones."""
    legs = [r for r in results if r.get("stake")]
    total = sum(r["stake"] for r in legs)
    if not legs or total <= 0:
        return ""
    bar, legend = "", ""
    for i, r in enumerate(legs):
        tone = SPLIT_TONES[i % len(SPLIT_TONES)]
        share = r["stake"] / total * 100
        bar += f'<span style="width:{share:.2f}%;background:{tone}"></span>'
        legend += (f'<span><i style="background:{tone}"></i>'
                   f'{escape(format_outcome(r["outcome"], r.get("point")))} {share:.0f}%</span>')
    return f'<div><div class="split">{bar}</div><div class="split-legend">{legend}</div></div>'


def row_html(lead: str, main: str, sub: str, value_html: str, value_sub: str = "", url: str | None = None) -> str:
    """A list row: tile, two lines of text, a right-aligned value and an Open link.

    `main`, `sub` and `value_sub` are escaped here; `lead` and `value_html` are trusted markup.
    """
    vsub = f'<div class="row-sub">{escape(value_sub)}</div>' if value_sub else ""
    return (
        f'<div class="row">{lead}'
        f'<div><div class="row-main">{escape(main)}</div><div class="row-sub">{escape(sub)}</div></div>'
        f'<div class="row-end">{value_html}{vsub}</div>'
        f'<div class="row-open">{open_link(url)}</div></div>'
    )
