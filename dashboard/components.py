# =============================================================================
# components.py
# Presentation helpers: formatting, pills, the title row, cards' inner HTML,
# the legs table and bookmaker link resolution. Any text that comes from a
# data provider is HTML-escaped before it is placed inside unsafe_allow_html
# markup.
# =============================================================================

from datetime import UTC, datetime
from html import escape
from urllib.parse import quote_plus

import pandas as pd
import streamlit as st

from .config import BOOK_LINKS, MARKET_OPTIONS, NEAR_ARB_THRESHOLD

# Stake-split tones: one hue (the accent) at falling strengths, one per leg
SPLIT_TONES = ["#4a8ad6", "rgba(74,138,214,.6)", "rgba(74,138,214,.32)", "rgba(74,138,214,.18)"]


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


def short_game(name: str, limit: int = 28) -> str:
    """Shorten 'Boston Celtics vs Chicago Bulls' → 'Celtics vs Bulls' for chart labels."""
    for sep in (" vs ", " @ "):
        if sep in name:
            teams = [t.split()[-1] if len(t) > 12 else t for t in name.split(sep)]
            name = sep.join(teams)
            break
    return name if len(name) <= limit else name[: limit - 1] + "…"


def money(value, signed: bool = False) -> str:
    """$1,234.50 with an optional sign; a grey dash when missing."""
    if value is None or pd.isna(value):
        return "—"
    sign = ("+" if value > 0 else "−" if value < 0 else "") if signed else ("−" if value < 0 else "")
    return f"{sign}${abs(value):,.2f}"


def percent(value, signed: bool = True, digits: int = 2) -> str:
    """+0.46% with its sign; a grey dash when missing."""
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


def link_html(label: str, url: str | None, detail: str = "") -> str:
    """A text action that opens in a new tab, or the label in grey if there is no URL.

    `detail` is appended to the label on wider screens only ("Open" + " Betsson").
    """
    text = escape(label) + (f'<span class="hide-sm"> {escape(detail)}</span>' if detail else "")
    if not url:
        return f'<span style="color:var(--muted)">{text}</span>'
    return (f'<a class="go" href="{escape(url)}" target="_blank" rel="noopener noreferrer">'
            f'{text} ↗</a>')


# ── Pills ────────────────────────────────────────────────────────────────────

def pill(text: str, kind: str = "neutral") -> str:
    return f'<span class="pill {kind}">{escape(text)}</span>'


def live_badge(commence_time) -> str:
    """A 'Live' pill if the event has started, else ''."""
    return pill("Live", "negative") if is_live_event(str(commence_time or "")) else ""


def status_pill(implied_sum: float) -> str:
    """'Arbitrage' under 1.000, 'Near break-even' under NEAR_ARB_THRESHOLD, else nothing."""
    if implied_sum < 1.0:
        return pill("Arbitrage", "positive")
    if implied_sum < NEAR_ARB_THRESHOLD:
        return pill("Near break-even", "warning")
    return ""


# ── Page structure ───────────────────────────────────────────────────────────

def render_page_header(title: str, finding_html: str = "", stamp_html: str = "") -> None:
    """The title row: an h1, the screen's finding under it, a freshness stamp on the right.

    `finding_html` and `stamp_html` are trusted markup; escape provider text before passing it.
    """
    st.markdown(
        f'<div class="title-row"><div><h1>{escape(title)}</h1>'
        f'<div class="finding">{finding_html}</div></div>'
        f'<div class="stamp">{stamp_html}</div></div>',
        unsafe_allow_html=True,
    )


def source_stamp(provider_name: str, cache_seconds: int) -> str:
    source = "Demo data" if provider_name == "demo" else "Live odds"
    return f'{pill(source)}<span>Cached for {cache_seconds} s</span>'


def section(title: str) -> None:
    st.markdown(f'<h2 class="section">{escape(title)}</h2>', unsafe_allow_html=True)


def card_title(title: str, sub: str = "") -> str:
    sub_html = f'<div class="card-sub">{escape(sub)}</div>' if sub else ""
    return f'<div><h3 class="card-title">{escape(title)}</h3>{sub_html}</div>'


def empty_state(html: str) -> None:
    """One sentence in a dashed frame, used wherever a block has nothing to show."""
    st.markdown(f'<div class="empty">{html}</div>', unsafe_allow_html=True)


def figures_html(figures: list) -> str:
    """A row of label-over-value figures: [(label, value, css_class, is_lead), ...]."""
    cells = "".join(
        f'<div class="figure{" lead" if lead else ""}"><div class="label">{escape(label)}</div>'
        f'<div class="value {cls}">{value}</div></div>'
        for label, value, cls, lead in figures
    )
    return f'<div class="figure-row">{cells}</div>'


def game_head_html(name: str, meta: str, pills_html: str = "") -> str:
    name_html = f'<div class="game-name">{escape(name)}</div>' if name else ""
    return (
        f'<div class="game-head"><div>{name_html}'
        f'<div class="game-meta">{escape(meta)}</div></div>'
        f'<div class="pills">{pills_html}</div></div>'
    )


# ── Legs: the best price per outcome, its stake and where to place it ────────

def legs_table_html(results: list, hide_american: bool = False) -> str:
    """Table of the best price for every outcome of one game.

    `results` are analysis result dicts (outcome, point, bookmaker, american_odds,
    decimal_odds, optional stake and link). When stakes are present, each leg's
    payout and a total row show that every outcome returns the same amount.
    """
    has_stake = any(r.get("stake") is not None for r in results)

    head = '<th>Outcome</th><th>Sportsbook</th>'
    if not hide_american:
        head += '<th class="r hide-sm">American</th>'
    head += '<th class="r">Decimal</th>'
    if has_stake:
        head += '<th class="r">Stake</th><th class="r hide-sm">Returns</th>'
    head += '<th class="r">Place bet</th>'

    rows = ""
    total_stake, payouts = 0.0, []
    for r in results:
        book = normalize_book_name(r["bookmaker"])
        cells = (f'<td>{escape(format_outcome(r["outcome"], r.get("point")))}</td>'
                 f'<td class="sub">{escape(book)}</td>')
        if not hide_american:
            cells += f'<td class="r hide-sm">{american(r.get("american_odds"))}</td>'
        cells += f'<td class="r">{r["decimal_odds"]:.3f}</td>'
        if has_stake:
            stake = r.get("stake")
            payout = stake * r["decimal_odds"] if stake is not None else None
            if stake is not None:
                total_stake += stake
                payouts.append(payout)
            cells += f'<td class="r">{money(stake)}</td><td class="r hide-sm">{money(payout)}</td>'
        cells += f'<td class="r">{link_html("Open", book_url(r["bookmaker"], r.get("link")), book)}</td>'
        rows += f"<tr>{cells}</tr>"

    if has_stake and payouts:
        # One cell per column (including the ones hidden on a phone) keeps the row aligned
        rows += (
            '<tr class="total"><td>Total</td><td></td>'
            + ('<td class="hide-sm"></td>' if not hide_american else "")
            + f'<td></td><td class="r">{money(total_stake)}</td>'
            f'<td class="r hide-sm">{money(min(payouts))}</td><td></td></tr>'
        )

    return (f'<div class="table-frame"><table class="legs"><thead><tr>{head}</tr></thead>'
            f'<tbody>{rows}</tbody></table></div>')


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
                   f'{escape(format_outcome(r["outcome"], r.get("point")))} '
                   f'<span class="num">{share:.1f}%</span></span>')
    return f'<div><div class="split">{bar}</div><div class="split-legend">{legend}</div></div>'
