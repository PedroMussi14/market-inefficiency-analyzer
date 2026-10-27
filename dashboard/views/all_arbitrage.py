# =============================================================================
# views/all_arbitrage.py
# Scans every sport at once and lists only guaranteed-profit opportunities,
# each as an order ticket: the stake per sportsbook and where to place it.
# =============================================================================

from html import escape

import streamlit as st

from analyzer.export import analyses_to_summary_dataframe

from ..components import (
    card_head,
    empty_state,
    format_market_label,
    format_start,
    hero_panel_html,
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
from ..data import load_all_arbitrage, load_sports
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


def _confirm_live_scan(s: Settings) -> bool:
    """On a paid provider, scan every sport only after the user accepts the credit cost."""
    if s.provider_name == "demo":
        return True
    scan_id = (s.provider_name, s.market, s.region, s.bet_from, s.bankroll)
    if st.session_state.get("arb_scan_confirmed") == scan_id:
        return True

    n_sports = len(load_sports(s.provider_name))
    cost = n_sports * len(s.region.split(","))
    render_page_header("All arbitrage", "Every sport, scanned at once", s.provider_name)
    with st.container(key="card-confirm"):
        st.markdown(card_head("Scan every sport?", "", "spark", ruled=True), unsafe_allow_html=True)
        st.markdown(
            f'<div class="hero-sub">This sends one request per sport and region: <b>{n_sports} sports × '
            f'{len(s.region.split(","))} region(s) ≈ {cost} API credits</b>. The free plan has 500 a month. '
            'Results are cached for 2 minutes.</div>',
            unsafe_allow_html=True,
        )
        if st.button(f"Scan all sports (≈{cost} credits)", key="arb_scan_go"):
            st.session_state["arb_scan_confirmed"] = scan_id
            st.rerun()
    return False


def _report_failures(failed_sports: list, reason: str) -> None:
    """One sentence about sports that failed, with the full list folded away."""
    if not failed_sports:
        return
    empty_state(f"<b>{len(failed_sports)} sports couldn't be loaded.</b> {escape(reason)}")
    with st.expander("Show which sports"):
        st.caption(", ".join(failed_sports))


def render(s: Settings) -> None:
    if not _confirm_live_scan(s):
        return

    with st.spinner("Scanning every sport for arbitrage…"):
        arb_all, failed_sports, reason = load_all_arbitrage(
            s.provider_name, s.market, s.region, s.bankroll, s.bet_from,
        )

    if not arb_all:
        render_page_header("All arbitrage", "Every sport, scanned at once", s.provider_name)
        _report_failures(failed_sports, reason)
        empty_state("No guaranteed profit in any sport right now. Try another market type or region.")
        return

    sports_with_arb = sorted({a["sport"] for a in arb_all if a.get("sport")})
    render_page_header(
        "All arbitrage",
        f"Every sport, scanned at once · {len(arb_all)} guaranteed-profit opportunities",
        s.provider_name,
    )
    _report_failures(failed_sports, reason)

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
        st.markdown(card_head("If you take every opportunity", f"{money(s.bankroll)} budget per game",
                              "spark", ruled=True), unsafe_allow_html=True)
        st.markdown(hero_panel_html(
            f'<div class="hero-label">Guaranteed profit across {len(filtered)} games</div>'
            f'{money_html(total_profit, positive=True)}'
            f'<div class="hero-sub">on <b>{money(s.bankroll * len(filtered))}</b> staked in total</div>',
            [
                ("Best return", percent(max(a["roi"] for a in filtered))),
                ("Sports", str(len({a["sport"] for a in filtered}))),
                ("Sportsbooks", str(len({r["bookmaker"] for a in filtered for r in a["results"]}))),
            ],
        ), unsafe_allow_html=True)

    st.markdown(card_head("Opportunities", "best return first", "ticket"), unsafe_allow_html=True)
    for i, analysis in enumerate(filtered):
        _render_ticket(i, analysis, s)

    col, _ = st.columns([1, 2])
    col.download_button(
        "Download opportunities (CSV)",
        analyses_to_summary_dataframe(filtered).to_csv(index=False).encode("utf-8"),
        "all_arbitrage_opportunities.csv", "text/csv", width="stretch",
    )
