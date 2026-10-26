# =============================================================================
# views/all_arbitrage.py
# Scans every sport at once and lists only guaranteed-profit opportunities,
# each with its legs, stakes and booking links.
# =============================================================================

from html import escape

import pandas as pd
import streamlit as st

from analyzer.export import analyses_to_summary_dataframe

from ..components import (
    build_general_odds_info_link,
    empty_state,
    figures_html,
    format_market_label,
    format_start,
    game_head_html,
    legs_table_html,
    link_html,
    live_badge,
    money,
    percent,
    render_page_header,
    section,
    source_stamp,
    stake_split_html,
)
from ..data import load_all_arbitrage
from ..sidebar import Settings


def _summary_table(analyses: list) -> pd.DataFrame:
    rows = []
    for a in analyses:
        books = " · ".join(sorted({r["bookmaker"] for r in a.get("results", [])}))
        rows.append({
            "Game":        a["event"],
            "Sport":       a["sport"],
            "Start":       format_start(a["commence_time"]),
            "Return (%)":  round(a["roi"], 2) if a.get("roi") is not None else None,
            "Profit ($)":  round(a["profit"], 2) if a.get("profit") is not None else None,
            "Implied sum": round(a["implied_prob_sum"], 4),
            "Sportsbooks": books,
        })
    return pd.DataFrame(rows).sort_values("Return (%)", ascending=False)


def _render_game(i: int, analysis: dict, s: Settings) -> None:
    results = analysis.get("results", [])
    meta = " · ".join(filter(None, [
        analysis.get("sport"), format_market_label(s.market), format_start(analysis.get("commence_time")),
    ]))
    with st.container(key=f"card-arb-{i}"):
        left, right = st.columns([3, 1], gap="medium")
        with left:
            st.markdown(game_head_html(analysis["event"], meta, live_badge(analysis.get("commence_time"))),
                        unsafe_allow_html=True)
            st.markdown(legs_table_html(results, hide_american=s.hide_american_odds), unsafe_allow_html=True)
            st.markdown(stake_split_html(results), unsafe_allow_html=True)
        with right:
            st.markdown(figures_html([
                (f"Profit on {money(s.bankroll)}", money(analysis["profit"], signed=True), "pos", True),
            ]), unsafe_allow_html=True)
            st.markdown(figures_html([
                ("Return", percent(analysis["roi"]), "", False),
                ("Implied sum", f'{analysis["implied_prob_sum"]:.4f}', "", False),
            ]), unsafe_allow_html=True)
            odds_link = link_html("Compare odds elsewhere", build_general_odds_info_link(analysis["event"]))
            st.markdown(f'<div class="links">{odds_link}</div>', unsafe_allow_html=True)


def render(s: Settings) -> None:
    with st.spinner("Scanning every sport for arbitrage…"):
        arb_all, failed_sports = load_all_arbitrage(
            s.provider_name, s.market, s.region, s.bankroll, s.bet_from,
        )

    stamp = source_stamp(s.provider_name, 120)
    if not arb_all:
        render_page_header(
            "All arbitrage",
            "No guaranteed profit in any sport right now. Try another market type or region.",
            stamp,
        )
        if failed_sports:
            st.caption(f"{len(failed_sports)} sport(s) could not be loaded: {', '.join(failed_sports)}")
        return

    sports_with_arb = sorted({a["sport"] for a in arb_all if a.get("sport")})
    best = arb_all[0]
    render_page_header(
        "All arbitrage",
        f"<b>{len(arb_all)}</b> guaranteed profits across {len(sports_with_arb)} sports. "
        f"Best: <b>{escape(best['event'])}</b>, {money(best['profit'], signed=True)} on {money(s.bankroll)} "
        f"({percent(best['roi'])}).",
        stamp,
    )

    with st.container(key="kpis"):
        ka, kb, kc, kd = st.columns(4)
        ka.metric("Opportunities", len(arb_all))
        kb.metric("Sports", len(sports_with_arb))
        kc.metric("Best return", percent(max(a["roi"] for a in arb_all)))
        kd.metric("Best profit", money(max(a["profit"] for a in arb_all), signed=True))

    if failed_sports:
        st.caption(f"{len(failed_sports)} sport(s) could not be loaded: {', '.join(failed_sports)}")

    filter_col, _ = st.columns([2, 3])
    sport_filter = filter_col.multiselect(
        "Sports", options=sports_with_arb, default=sports_with_arb, key="arb_sport_filter",
    )
    filtered_arb = [a for a in arb_all if a.get("sport") in sport_filter]
    if not filtered_arb:
        empty_state("No opportunities in the selected sports.")
        return

    section(f"Opportunities ({len(filtered_arb)})")
    st.dataframe(
        _summary_table(filtered_arb),
        width="stretch",
        hide_index=True,
        column_config={
            "Game": st.column_config.TextColumn(width="large"),
            "Return (%)": st.column_config.NumberColumn("Return", format="%.2f%%"),
            "Profit ($)": st.column_config.NumberColumn(
                "Profit", format="$%.2f", help=f"Guaranteed profit on a ${s.bankroll:,.0f} budget.",
            ),
            "Implied sum": st.column_config.NumberColumn(format="%.4f"),
        },
    )

    section("Stakes and where to place them")
    for i, analysis in enumerate(filtered_arb):
        _render_game(i, analysis, s)

    col, _ = st.columns([1, 2])
    col.download_button(
        "Download opportunities (CSV)",
        analyses_to_summary_dataframe(filtered_arb).to_csv(index=False).encode("utf-8"),
        "all_arbitrage_opportunities.csv",
        "text/csv",
        width="stretch",
    )
