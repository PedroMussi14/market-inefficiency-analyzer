# =============================================================================
# views/ev_bets.py
# Bets priced above Pinnacle's de-vigged fair odds (positive expected value).
# Requires a region that includes Pinnacle (eu or uk).
# =============================================================================

from html import escape

import pandas as pd
import streamlit as st

from ..components import (
    book_tile,
    book_url,
    card_head,
    empty_state,
    facts_html,
    format_market_label,
    format_outcome,
    format_start,
    normalize_book_name,
    percent,
    render_page_header,
    row_html,
)
from ..data import load_ev_bets
from ..sidebar import Settings

MIN_EV_OPTIONS = [0.0, 0.5, 1.0, 2.0]


def _row(b: dict) -> str:
    book = normalize_book_name(b["bookmaker"])
    outcome = format_outcome(b["outcome"], b.get("point"))
    return row_html(
        book_tile(book),
        f'{outcome} at {b["decimal_odds"]:.2f}',
        f'{b["event"]} · {book} · {format_start(b.get("commence_time"))}',
        f'<div class="row-value pos">{percent(b["ev_pct"])}</div>',
        f'fair chance {b["true_prob"]:.1f}%',
        book_url(b["bookmaker"], b.get("link")),
    )


def render(s: Settings) -> None:
    scope = format_market_label(s.market)

    if not any(r in s.region for r in ("eu", "uk")):
        render_page_header("+EV bets", "Prices above Pinnacle's fair odds", s.provider_name)
        empty_state("Pinnacle, the sharp line these bets are measured against, is only listed in the "
                    "<b>Europe</b> and <b>UK</b> regions. Add one of them in the sidebar.")
        return

    with st.spinner("Comparing prices with Pinnacle…"):
        try:
            ev_results = load_ev_bets(s.provider_name, s.sport_key, s.market, s.region, s.bet_from)
        except Exception as e:
            render_page_header("+EV bets", "Prices above Pinnacle's fair odds", s.provider_name)
            st.error(f"Couldn't load odds for this sport and market. {e}")
            return

    if not ev_results:
        render_page_header("+EV bets", f"{scope} · prices above Pinnacle's fair odds", s.provider_name)
        empty_state("No price beats Pinnacle's fair odds here. Pinnacle may not list this market yet, "
                    "or the market is very efficient.")
        return

    sport = ev_results[0].get("sport") or ""
    render_page_header(
        "+EV bets",
        f"{sport} · {scope} · {len(ev_results)} bets beat Pinnacle's fair odds",
        s.provider_name,
    )

    best = ev_results[0]
    with st.container(key="card-best"):
        left, right = st.columns([3, 2], vertical_alignment="center")
        left.markdown(
            '<div><div class="hero-label">Best edge</div>'
            f'<div class="money pos">{percent(best["ev_pct"])}</div>'
            f'<div class="hero-sub"><b>{escape(format_outcome(best["outcome"], best.get("point")))}</b> at '
            f'{escape(normalize_book_name(best["bookmaker"]))}, {best["decimal_odds"]:.2f} against a fair '
            f'{100 / best["true_prob"]:.2f}</div></div>',
            unsafe_allow_html=True,
        )
        right.markdown(facts_html([
            ("Bets found", str(len(ev_results))),
            ("Average edge", percent(sum(r["ev_pct"] for r in ev_results) / len(ev_results))),
            ("Sportsbooks", str(len({r["bookmaker"] for r in ev_results}))),
        ]), unsafe_allow_html=True)

    min_ev = st.segmented_control(
        "Minimum edge", MIN_EV_OPTIONS, default=0.5, key="min_ev",
        format_func=lambda v: "Any" if v == 0 else f"{v:g}% or more",
    )
    filtered = [r for r in ev_results if r["ev_pct"] >= (min_ev or 0)]

    with st.container(key="card-bets"):
        st.markdown(card_head("Bets", f"{len(filtered)} shown · best edge first"), unsafe_allow_html=True)
        if not filtered:
            empty_state("No bets at this edge. Choose a lower minimum to see the rest.")
        else:
            st.markdown('<div class="rows">' + "".join(_row(b) for b in filtered) + "</div>",
                        unsafe_allow_html=True)
        st.caption("Fair chance is Pinnacle's price with its margin removed. The edge is the expected "
                   "return of a $1 bet at the listed price under that chance.")

    col, _ = st.columns([1, 2])
    col.download_button(
        "Download +EV bets (CSV)",
        pd.DataFrame(filtered).to_csv(index=False).encode("utf-8"),
        "ev_bets.csv", "text/csv", width="stretch",
    )
