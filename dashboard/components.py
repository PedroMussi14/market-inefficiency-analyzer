# =============================================================================
# components.py
# Small presentation helpers: badges, cards, the best-prices table and
# bookmaker link resolution. Any text that comes from a data provider is
# HTML-escaped before it is placed inside unsafe_allow_html markup.
# =============================================================================

from datetime import UTC, datetime
from html import escape
from urllib.parse import quote_plus

import pandas as pd
import streamlit as st

from .config import BOOK_LINKS, MARKET_OPTIONS, NEAR_ARB_THRESHOLD
from .theme import COLORS


def is_live_event(commence_time_str: str) -> bool:
    """Return True if the event start time is in the past (game is underway)."""
    if not commence_time_str:
        return False
    try:
        event_time = datetime.fromisoformat(commence_time_str.replace("Z", "+00:00"))
        return event_time <= datetime.now(UTC)
    except ValueError:
        return False


LIVE_BADGE_HTML = '<span class="live-indicator"><span class="live-dot"></span>LIVE</span>'


def live_badge(commence_time) -> str:
    """Return the pulsing LIVE badge HTML if the event has started, else ''."""
    return LIVE_BADGE_HTML if is_live_event(str(commence_time or "")) else ""


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


def clean_bookmaker_link(raw_link: str, book_title: str) -> str:
    """Sanitise a bookmaker link before rendering it as a button.

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


def efficiency_badge(eff: float) -> str:
    """Return an inline HTML badge reflecting the market's efficiency level.

    - Green  "Arbitrage" : eff < 1.0
    - Yellow "Near Arb"  : eff < NEAR_ARB_THRESHOLD
    - Grey   "Normal"    : everything else
    """
    base = (
        "display:inline-block; padding:3px 12px; border-radius:20px; "
        "font-size:0.68rem; font-weight:700; letter-spacing:0.08em; text-transform:uppercase;"
    )
    if eff < 1.0:
        style = (f"{base} background:rgba(0,229,160,0.15); "
                 f"color:{COLORS['arb_green']}; border:1px solid {COLORS['arb_green']};")
        return f'<span style="{style}">&#9889; Arbitrage</span>'
    elif eff < NEAR_ARB_THRESHOLD:
        style = (f"{base} background:rgba(245,166,35,0.12); "
                 f"color:{COLORS['warning']}; border:1px solid {COLORS['warning']};")
        return f'<span style="{style}">&#9670; Near Arb</span>'
    else:
        style = (f"{base} background:rgba(107,118,148,0.15); "
                 f"color:{COLORS['text_muted']}; border:1px solid {COLORS['border']};")
        return f'<span style="{style}">&#9671; Normal</span>'


def render_page_header(title: str, tag: str, caption: str = "") -> None:
    """Render the standard page header (h1 + badge tag) plus an optional caption and divider."""
    st.markdown(
        f'<div class="header-bar"><h1>{title}</h1>'
        f'<span class="header-tag">{tag}</span></div>',
        unsafe_allow_html=True,
    )
    if caption:
        st.caption(caption)
    st.markdown("---")


def build_game_info_link(game_name: str) -> str:
    """Build a Google search URL for ESPN match coverage of the given game."""
    return f"https://www.google.com/search?q={quote_plus(game_name + ' ESPN')}"


def build_general_odds_info_link(game_name: str) -> str:
    """Build a Google search URL for odds info on the given game."""
    return f"https://www.google.com/search?q={quote_plus(game_name + ' odds')}"


def render_bookmaker_links(book_links: dict) -> None:
    """Render one button per bookmaker ({title: raw_link}).

    Preference order: the provider's deep link → the BOOK_LINKS homepage → plain text.
    """
    for book, raw_link in book_links.items():
        name = normalize_book_name(book)
        if cleaned := clean_bookmaker_link(raw_link, name):
            st.link_button(f"→ {name}", cleaned, width="stretch")
        elif homepage := BOOK_LINKS.get(name):
            st.link_button(f"{name} (Home)", homepage, width="stretch")
        else:
            st.write(name)


def game_card_html(label: str, title: str, subtitle: str, badges_html: str,
                   accent: str | None = None, right_html: str = "") -> str:
    """Return the dark summary card used at the top of each game section.

    `label`, `title` and `subtitle` are escaped; `badges_html` and `right_html`
    are trusted markup built by this module.
    """
    C = COLORS
    accent_border = f"border-left:3px solid {accent};" if accent else ""
    return (
        f'<div style="background:{C["surface"]};border:1px solid {C["border"]};{accent_border}'
        f'border-radius:10px;padding:1rem 1.2rem;margin-bottom:0.6rem;">'
        f'<div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;">'
        f'<div>'
        f'<span style="font-size:0.6rem;color:{C["text_muted"]};text-transform:uppercase;'
        f'letter-spacing:0.12em;display:block;margin-bottom:3px;">{escape(label)}</span>'
        f'<div style="font-family:Syne,sans-serif;font-size:1.05rem;font-weight:700;color:{C["text"]};">'
        f'{escape(title)}</div>'
        f'<div style="font-size:0.72rem;color:{C["text_muted"]};margin-top:3px;">{escape(subtitle)}</div>'
        f'</div>'
        f'<div style="display:flex;flex-direction:column;align-items:flex-end;gap:5px;">'
        f'{badges_html}{right_html}'
        f'</div></div></div>'
    )


def build_prices_table(event_rows: pd.DataFrame, bankroll: float,
                       hide_american: bool = False) -> str:
    """Build a styled HTML table showing the best available price per outcome.

    Columns rendered: Outcome | Sportsbook | [American Odds] | Decimal Odds
    Optional columns appended when data is present: Suggested Bet | Place Bet (link)
    `hide_american=True` omits the American Odds column (useful for Brazilian
    books which only display decimal).
    """
    has_stake = (
        "Suggested Bet ($)" in event_rows.columns
        and event_rows["Suggested Bet ($)"].notna().any()
    )
    has_link = (
        "Direct Link" in event_rows.columns
        and event_rows["Direct Link"].notna().any()
    )

    C = COLORS  # local alias for brevity inside HTML f-strings

    # Per-outcome accent colours — cycles if there are more than 4 outcomes
    outcome_colors = [C["arb_green"], C["accent2"], C["warning"], C["danger"]]

    # Reusable inline style fragments — all colours pulled from COLORS
    th = (f"padding:10px 14px;text-align:left;font-size:0.62rem;text-transform:uppercase;"
          f"letter-spacing:0.1em;color:{C['text_muted']};border-bottom:1px solid {C['border']};white-space:nowrap;")
    td  = (f"padding:11px 14px;font-size:0.82rem;color:{C['text']};"
           f"border-bottom:1px solid {C['surface2']};white-space:nowrap;")
    tn  = td + "text-align:right;font-family:'IBM Plex Mono',monospace;"
    # Slightly darker stripe for alternating rows (not in COLORS — intentional subtle variation)
    _row_bg_alt = "#13161f"

    rows_html = ""
    for i, (_, row) in enumerate(event_rows.iterrows()):
        outcome  = escape(format_outcome(row.get("Bet On", ""), row.get("Line")))
        book     = escape(str(row.get("Sportsbook", "")))
        am_odds  = row.get("American Odds", "")
        dec_odds = row.get("Decimal Odds", "")
        stake    = row.get("Suggested Bet ($)", None)
        link     = row.get("Direct Link", None)

        accent = outcome_colors[i % len(outcome_colors)]
        bg     = C["surface"] if i % 2 == 0 else _row_bg_alt

        # Positive American odds get a green colour; negative stay default
        try:
            am_int    = int(am_odds)
            am_color  = C["arb_green"] if am_int > 0 else C["text"]
            am_prefix = "+" if am_int > 0 else ""
        except (ValueError, TypeError):
            am_int, am_color, am_prefix = None, C["text"], ""

        try:
            dec_str = f"{float(dec_odds):.4f}"
        except (ValueError, TypeError):
            dec_str = str(dec_odds)

        try:
            stake_str = f"${float(stake):.2f}" if stake is not None and str(stake) != "nan" else "&#8212;"
        except (ValueError, TypeError):
            stake_str = "&#8212;"

        # Deep link renders as a styled "Bet →" button; missing link shows an em dash
        if link and str(link).startswith("http"):
            link_cell = (
                f'<a href="{escape(str(link))}" target="_blank" rel="noopener noreferrer" '
                f'style="display:inline-block;padding:3px 10px;'
                f'border-radius:5px;background:rgba(61,155,255,0.1);border:1px solid {C["accent2"]};'
                f'color:{C["accent2"]};font-size:0.7rem;text-decoration:none;text-transform:uppercase;">'
                'Bet &#8594;</a>'
            )
        else:
            link_cell = f'<span style="color:{C["text_muted"]};">&#8212;</span>'

        stake_td = f'<td style="{tn}color:{C["warning"]};">{stake_str}</td>' if has_stake else ""
        link_td  = f'<td style="{td}">{link_cell}</td>'                      if has_link  else ""
        am_td    = (f'<td style="{tn}color:{am_color};">{am_prefix}{am_odds}</td>'
                    if not hide_american else "")

        rows_html += (
            f'<tr style="background:{bg};">'
            f'<td style="{td}border-left:3px solid {accent};font-weight:600;color:{accent};">{outcome}</td>'
            f'<td style="{td}">{book}</td>'
            f'{am_td}'
            f'<td style="{tn}">{dec_str}</td>'
            f'{stake_td}{link_td}'
            f'</tr>'
        )

    # Optional column headers to match optional data columns above
    sh = f'<th style="{th}text-align:right;">Suggested Bet</th>' if has_stake else ""
    lh = f'<th style="{th}">Place Bet</th>'                      if has_link  else ""
    am_h = f'<th style="{th}text-align:right;">Amer. Odds</th>'  if not hide_american else ""

    return (
        f'<div style="border:1px solid {C["border"]};border-radius:10px;overflow:hidden;width:100%;">'
        '<table style="width:100%;border-collapse:collapse;">'
        f'<thead><tr style="background:{C["surface2"]};">'
        f'<th style="{th}">Outcome</th>'
        f'<th style="{th}">Sportsbook</th>'
        f'{am_h}'
        f'<th style="{th}text-align:right;">Dec. Odds</th>'
        f'{sh}{lh}</tr></thead>'
        f'<tbody>{rows_html}</tbody></table></div>'
    )
