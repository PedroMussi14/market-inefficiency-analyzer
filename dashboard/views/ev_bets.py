# =============================================================================
# views/ev_bets.py
# Bets priced above Pinnacle's de-vigged fair odds (positive expected value).
# Requires a region that includes Pinnacle (eu or uk).
# =============================================================================

from html import escape

import pandas as pd
import streamlit as st

from ..components import (
    book_url,
    empty_state,
    format_outcome,
    format_start,
    normalize_book_name,
    percent,
    render_page_header,
    section,
    source_stamp,
)
from ..data import load_ev_bets
from ..sidebar import Settings


def _table(bets: list, s: Settings) -> pd.DataFrame:
    rows = []
    for b in bets:
        book = normalize_book_name(b["bookmaker"])
        row = {
            "Game":       b["event"],
            "Start":      format_start(b.get("commence_time")),
            "Bet on":     format_outcome(b["outcome"], b.get("point")),
            "Sportsbook": book,
        }
        if not s.hide_american_odds:
            row["American"] = f'{"+" if b["american_odds"] > 0 else ""}{b["american_odds"]}'
        row.update({
            "Decimal":    b["decimal_odds"],
            "Fair prob.": b["true_prob"],
            "EV":         b["ev_pct"],
            "Place bet":  book_url(b["bookmaker"], b.get("link")),
        })
        rows.append(row)
    return pd.DataFrame(rows)


def render(s: Settings) -> None:
    stamp = source_stamp(s.provider_name, 60)

    if not any(r in s.region for r in ("eu", "uk")):
        render_page_header(
            "+EV bets",
            "Pinnacle, the sharp line these bets are measured against, is only listed in the "
            "<b>Europe</b> and <b>UK</b> regions. Add one of them in the sidebar.",
            stamp,
        )
        return

    with st.spinner("Comparing prices with Pinnacle…"):
        try:
            ev_results = load_ev_bets(s.provider_name, s.sport_key, s.market, s.region, s.bet_from)
        except Exception as e:
            render_page_header("+EV bets", "", stamp)
            st.error(f"Couldn't load odds for this sport and market. {e}")
            return

    if not ev_results:
        render_page_header(
            "+EV bets",
            "No price beats Pinnacle's fair odds in this sport and market. Pinnacle may not list "
            "it yet, or the market is very efficient.",
            stamp,
        )
        return

    best = ev_results[0]
    render_page_header(
        "+EV bets",
        f"<b>{len(ev_results)}</b> prices beat Pinnacle's de-vigged fair odds. Best: "
        f"<b>{escape(format_outcome(best['outcome'], best.get('point')))}</b> at "
        f"{escape(normalize_book_name(best['bookmaker']))}, {percent(best['ev_pct'])} expected value.",
        stamp,
    )

    with st.container(key="kpis"):
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("+EV bets found", len(ev_results))
        k2.metric("Best EV", percent(best["ev_pct"]))
        k3.metric("Average EV", percent(sum(r["ev_pct"] for r in ev_results) / len(ev_results)))
        k4.metric("Sportsbooks with an edge", len({r["bookmaker"] for r in ev_results}))

    slider_col, _ = st.columns([2, 3])
    min_ev = slider_col.slider("Minimum EV (%)", 0.0, 5.0, 0.5, 0.1)
    filtered = [r for r in ev_results if r["ev_pct"] >= min_ev]

    section(f"Bets ({len(filtered)})")
    if not filtered:
        empty_state(f"No bets at {min_ev:.1f}% EV or more. Lower the minimum to see the rest.")
        return

    st.dataframe(
        _table(filtered, s),
        width="stretch",
        hide_index=True,
        column_config={
            "Game": st.column_config.TextColumn(width="large"),
            "Decimal": st.column_config.NumberColumn(format="%.3f"),
            "Fair prob.": st.column_config.NumberColumn(format="%.1f%%"),
            "EV": st.column_config.NumberColumn(format="+%.2f%%"),
            "Place bet": st.column_config.LinkColumn(display_text="Open ↗"),
        },
    )
    st.caption("Fair probability is Pinnacle's price with its margin removed. EV is the expected "
               "return of a $1 bet at the listed price under that probability.")

    col, _ = st.columns([1, 2])
    col.download_button(
        "Download +EV bets (CSV)",
        pd.DataFrame(filtered).to_csv(index=False).encode("utf-8"),
        "ev_bets.csv",
        "text/csv",
        width="stretch",
    )
