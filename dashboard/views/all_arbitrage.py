# =============================================================================
# views/all_arbitrage.py
# Scans every sport at once and lists only guaranteed-profit opportunities,
# each as an order ticket: the stake per sportsbook and where to place it.
# =============================================================================

import streamlit as st

from analyzer.export import analyses_to_summary_dataframe

from ..components import (
    card_head,
    empty_state,
    facts_html,
    format_market_label,
    format_start,
    live_badge,
    matchup_html,
    money,
    money_html,
    percent,
    pill,
    render_page_header,
    stake_split_html,
    ticket_html,
)
from ..data import load_all_arbitrage
from ..sidebar import Settings


def _render_ticket(i: int, analysis: dict, s: Settings) -> None:
    meta = " · ".join(filter(None, [
        analysis.get("sport"), format_market_label(s.market), format_start(analysis.get("commence_time")),
    ]))
    with st.container(key=f"card-arb-{i}"):
        st.markdown(
            matchup_html(analysis["event"], meta,
                         live_badge(analysis.get("commence_time"))
                         + pill(f'{money(analysis["profit"], signed=True)} · {percent(analysis["roi"])}',
                                "positive")),
            unsafe_allow_html=True,
        )
        st.markdown(ticket_html(analysis.get("results", []), hide_american=s.hide_american_odds),
                    unsafe_allow_html=True)
        st.markdown(stake_split_html(analysis.get("results", [])), unsafe_allow_html=True)


def render(s: Settings) -> None:
    with st.spinner("Scanning every sport for arbitrage…"):
        arb_all, failed_sports = load_all_arbitrage(
            s.provider_name, s.market, s.region, s.bankroll, s.bet_from,
        )

    if not arb_all:
        render_page_header("All arbitrage", "Every sport, scanned at once", s.provider_name)
        empty_state("No guaranteed profit in any sport right now. Try another market type or region.")
        if failed_sports:
            st.caption(f"{len(failed_sports)} sport(s) could not be loaded: {', '.join(failed_sports)}")
        return

    sports_with_arb = sorted({a["sport"] for a in arb_all if a.get("sport")})
    render_page_header(
        "All arbitrage",
        f"Every sport, scanned at once · {len(arb_all)} guaranteed-profit opportunities",
        s.provider_name,
    )
    if failed_sports:
        st.caption(f"{len(failed_sports)} sport(s) could not be loaded: {', '.join(failed_sports)}")

    sport_filter = st.pills(
        "Sports", sports_with_arb, selection_mode="multi", default=sports_with_arb, key="arb_sport_filter",
    )
    filtered = [a for a in arb_all if a.get("sport") in (sport_filter or [])]
    if not filtered:
        empty_state("No opportunities in the selected sports.")
        return

    # The headline sum: what taking every opportunity shown would lock in
    total_profit = sum(a["profit"] for a in filtered)
    with st.container(key="card-total"):
        left, right = st.columns([3, 2], vertical_alignment="center")
        left.markdown(
            f'<div><div class="hero-label">Guaranteed profit across {len(filtered)} games, '
            f'{money(s.bankroll)} each</div>{money_html(total_profit, positive=True)}'
            f'<div class="hero-sub">on <b>{money(s.bankroll * len(filtered))}</b> staked in total</div></div>',
            unsafe_allow_html=True,
        )
        right.markdown(facts_html([
            ("Best return", percent(max(a["roi"] for a in filtered))),
            ("Sports", str(len({a["sport"] for a in filtered}))),
            ("Sportsbooks", str(len({r["bookmaker"] for a in filtered for r in a["results"]}))),
        ]), unsafe_allow_html=True)

    st.markdown(card_head("Opportunities", "best return first"), unsafe_allow_html=True)
    for i, analysis in enumerate(filtered):
        _render_ticket(i, analysis, s)

    col, _ = st.columns([1, 2])
    col.download_button(
        "Download opportunities (CSV)",
        analyses_to_summary_dataframe(filtered).to_csv(index=False).encode("utf-8"),
        "all_arbitrage_opportunities.csv", "text/csv", width="stretch",
    )
