# =============================================================================
# views/ev_bets.py
# Bets priced above Pinnacle's de-vigged fair odds (positive expected value).
# Requires a region that includes Pinnacle (eu or uk).
# =============================================================================

from html import escape

import pandas as pd
import streamlit as st

from ..components import (
    clean_bookmaker_link,
    format_market_label,
    format_outcome,
    live_badge,
    normalize_book_name,
    render_page_header,
)
from ..config import BOOK_LINKS
from ..data import load_ev_bets
from ..sidebar import Settings
from ..theme import COLORS

EV_COLUMNS = {
    "event":         "Game",
    "sport":         "Sport",
    "commence_time": "Start Time",
    "outcome":       "Bet On",
    "point":         "Line",
    "bookmaker":     "Sportsbook",
    "american_odds": "American Odds",
    "decimal_odds":  "Decimal Odds",
    "true_prob":     "True Prob (%)",
    "ev_pct":        "EV (%)",
}


def _render_bet_card(bet: dict, s: Settings) -> None:
    ev_color = (COLORS["arb_green"] if bet["ev_pct"] >= 2 else
                COLORS["warning"]   if bet["ev_pct"] >= 1 else
                COLORS["accent2"])
    book = normalize_book_name(bet["bookmaker"])

    # BR books only display decimal odds
    if s.hide_american_odds:
        odds_display = f'{bet["decimal_odds"]:.3f}'
    else:
        odds_display = f'{"+" if bet["american_odds"] > 0 else ""}{bet["american_odds"]}'

    C = COLORS
    st.markdown(
        f'<div style="background:{C["surface"]};border:1px solid {C["border"]};'
        f'border-left:3px solid {ev_color};'
        f'border-radius:10px;padding:0.9rem 1.1rem;margin-bottom:0.4rem;">'
        f'<div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;">'
        f'<div>'
        f'<span style="font-size:0.6rem;color:{C["text_muted"]};text-transform:uppercase;letter-spacing:0.12em;'
        f'display:block;margin-bottom:3px;">{escape(str(bet["sport"]))} &middot; {format_market_label(s.market)}</span>'
        f'<div style="font-family:Syne,sans-serif;font-size:1rem;font-weight:700;color:{C["text"]};">'
        f'{escape(bet["event"])}</div>'
        f'<div style="font-size:0.75rem;color:{C["text_muted"]};margin-top:3px;">'
        f'Bet <b style="color:{C["text"]};">{escape(format_outcome(bet["outcome"], bet.get("point")))}</b> '
        f'@ <b style="color:{C["text"]};">{odds_display}</b> '
        f'on <b style="color:{C["text"]};">{escape(book)}</b></div>'
        f'</div>'
        f'<div style="display:flex;flex-direction:column;align-items:flex-end;gap:4px;">'
        f'{live_badge(bet.get("commence_time"))}'
        f'<span style="font-size:1rem;font-weight:700;color:{ev_color};">+{bet["ev_pct"]:.2f}% EV</span>'
        f'<span style="font-size:0.72rem;color:{C["text_muted"]};">True prob: {bet["true_prob"]:.1f}%</span>'
        f'</div></div></div>',
        unsafe_allow_html=True,
    )

    if cleaned := clean_bookmaker_link(bet.get("link"), book):
        st.link_button(f"→ Bet on {book}", cleaned)
    elif homepage := BOOK_LINKS.get(book):
        st.link_button(f"{book} (Home)", homepage)
    st.markdown("")


def render(s: Settings) -> None:
    render_page_header(
        "+EV Bets", "vs Pinnacle",
        "Bets where a bookmaker's odds exceed Pinnacle's de-vigged implied probability. "
        "Requires **Europe** or **UK** region to include Pinnacle's sharp line.",
    )

    if not any(r in s.region for r in ("eu", "uk")):
        st.warning(
            "Pinnacle is only available in the **Europe** or **UK** regions. "
            "Add one of those regions in the sidebar to enable +EV detection."
        )
        return

    with st.spinner("Scanning for +EV opportunities…"):
        try:
            ev_results = load_ev_bets(s.provider_name, s.sport_key, s.market, s.region, s.bet_from)
        except Exception as e:
            st.error(f"Could not load odds for this sport / market: {e}")
            return

    if not ev_results:
        st.info(
            "No +EV bets found for this sport / market. "
            "Pinnacle may not have lines for this market yet, or the market is very efficient."
        )
        return

    # ── KPIs ─────────────────────────────────────────────────────────────────
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("+EV Bets Found",  len(ev_results))
    k2.metric("Best EV",         f"+{ev_results[0]['ev_pct']:.2f}%")
    k3.metric("Avg EV",          f"+{sum(r['ev_pct'] for r in ev_results) / len(ev_results):.2f}%")
    k4.metric("Books with Edge", len({r["bookmaker"] for r in ev_results}))
    st.markdown("")

    min_ev_filter = st.slider("Show bets with EV ≥ (%)", 0.0, 5.0, 0.5, 0.1)
    filtered_ev   = [r for r in ev_results if r["ev_pct"] >= min_ev_filter]
    st.markdown("")

    if not filtered_ev:
        st.info(f"No bets above {min_ev_filter:.1f}% EV. Lower the filter to see more.")
        return

    # ── Table ────────────────────────────────────────────────────────────────
    ev_df = pd.DataFrame(filtered_ev).rename(columns=EV_COLUMNS)
    columns = ["Game", "Bet On", "Sportsbook", "Decimal Odds", "True Prob (%)", "EV (%)"]
    if s.market != "h2h":
        columns.insert(2, "Line")
    if not s.hide_american_odds:
        columns.insert(columns.index("Decimal Odds"), "American Odds")

    st.subheader(f"+EV Opportunities ({len(filtered_ev)})")
    st.dataframe(ev_df[columns], width="stretch", hide_index=True)

    st.markdown("---")
    st.subheader("Bet Details")
    for bet in filtered_ev[:20]:   # cap at 20 cards to avoid page overload
        _render_bet_card(bet, s)

    st.markdown("---")
    st.download_button(
        "↓ Download +EV Bets (CSV)",
        pd.DataFrame(filtered_ev).to_csv(index=False).encode("utf-8"),
        "ev_bets.csv",
        "text/csv",
        width="stretch",
    )
