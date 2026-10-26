# =============================================================================
# views/all_arbitrage.py
# Scans every sport at once and lists only guaranteed-profit opportunities.
# =============================================================================

import pandas as pd
import streamlit as st

from analyzer.export import analyses_to_summary_dataframe

from ..components import (
    build_general_odds_info_link,
    build_prices_table,
    efficiency_badge,
    format_market_label,
    game_card_html,
    live_badge,
    render_bookmaker_links,
    render_page_header,
)
from ..data import load_all_arbitrage
from ..sidebar import Settings
from ..theme import COLORS


def _summary_table(analyses: list) -> pd.DataFrame:
    rows = []
    for a in analyses:
        books = " · ".join(sorted({r["bookmaker"] for r in a.get("results", [])}))
        rows.append({
            "Game":        a["event"],
            "Sport":       a["sport"],
            "Start Time":  a["commence_time"],
            "ROI (%)":     round(a["roi"], 2) if a.get("roi") else None,
            "Profit ($)":  round(a["profit"], 2) if a.get("profit") else None,
            "Efficiency":  round(a["implied_prob_sum"], 4),
            "Sportsbooks": books,
        })
    return pd.DataFrame(rows).sort_values("ROI (%)", ascending=False)


def _render_game(analysis: dict, s: Settings) -> None:
    results = analysis.get("results", [])
    right = (
        f'<span style="font-size:0.9rem;font-weight:700;color:{COLORS["arb_green"]};">'
        f'+{analysis["roi"]:.2f}% ROI</span>'
        f'<span style="font-size:0.78rem;color:{COLORS["text_muted"]};">'
        f'Profit: ${analysis["profit"]:.2f}</span>'
    )
    st.markdown(
        game_card_html(
            label=f'{analysis["sport"]} · {format_market_label(s.market)}',
            title=analysis["event"],
            subtitle=str(analysis.get("commence_time", "")),
            badges_html=live_badge(analysis.get("commence_time")) + efficiency_badge(analysis["implied_prob_sum"]),
            accent=COLORS["arb_green"],
            right_html=right,
        ),
        unsafe_allow_html=True,
    )

    col_left, col_right = st.columns([2, 1])
    with col_left:
        prices = pd.DataFrame([
            {
                "Bet On":            r["outcome"],
                "Line":              r.get("point"),
                "Sportsbook":        r["bookmaker"],
                "American Odds":     r["american_odds"],
                "Decimal Odds":      r["decimal_odds"],
                "Suggested Bet ($)": round(r["stake"], 2) if "stake" in r else None,
                "Direct Link":       r.get("link"),
            }
            for r in results
        ])
        st.markdown(build_prices_table(prices, s.bankroll, hide_american=s.hide_american_odds),
                    unsafe_allow_html=True)

    with col_right:
        st.markdown(
            '<span class="section-label" style="margin-top:4px;display:block;">Sportsbooks</span>',
            unsafe_allow_html=True,
        )
        render_bookmaker_links({r["bookmaker"]: r.get("link") for r in results})
        st.markdown("")
        st.link_button("🔍 Search odds", build_general_odds_info_link(analysis["event"]), width="stretch")

    st.markdown("")


def render(s: Settings) -> None:
    render_page_header(
        "All Arbitrage", "Cross-Sport",
        "Every sport scanned simultaneously. Only guaranteed-profit opportunities are shown. "
        "Cached for 2 minutes — hit Refresh to force a new scan.",
    )

    with st.spinner("Scanning all sports for arbitrage…"):
        arb_all, failed_sports = load_all_arbitrage(
            s.provider_name, s.market, s.region, s.bankroll, s.bet_from,
        )

    if failed_sports:
        st.caption(f"⚠️ {len(failed_sports)} sport(s) could not be loaded: {', '.join(failed_sports)}")

    if not arb_all:
        st.info(
            "No arbitrage opportunities found across any sport right now. "
            "Markets are efficient — try a different market type or region."
        )
        return

    # ── KPI strip ────────────────────────────────────────────────────────────
    sports_with_arb = sorted({a["sport"] for a in arb_all if a.get("sport")})
    ka, kb, kc, kd = st.columns(4)
    ka.metric("Opportunities",   len(arb_all))
    kb.metric("Sports Affected", len(sports_with_arb))
    kc.metric("Best ROI",        f"{max(a['roi'] for a in arb_all):.2f}%")
    kd.metric("Best Profit",     f"${max(a['profit'] for a in arb_all):.2f}")
    st.markdown("")

    sport_filter = st.multiselect(
        "Filter by sport", options=sports_with_arb, default=sports_with_arb, key="arb_sport_filter",
    )
    filtered_arb = [a for a in arb_all if a.get("sport") in sport_filter]
    st.markdown("")

    if not filtered_arb:
        st.info("No opportunities match the selected sports.")
        return

    # ── Summary table + top pick ─────────────────────────────────────────────
    st.subheader(f"Guaranteed-Profit Games ({len(filtered_arb)})")
    st.dataframe(_summary_table(filtered_arb), width="stretch", hide_index=True)

    best = filtered_arb[0]
    st.success(
        f"⚡ Top pick: **{best['event']}** ({best['sport']}) · "
        f"ROI **{best['roi']:.2f}%** · Profit **${best['profit']:.2f}**"
    )
    st.markdown("---")

    # ── Per-game cards ───────────────────────────────────────────────────────
    st.subheader("Game Breakdown")
    for analysis in filtered_arb:
        _render_game(analysis, s)

    # ── CSV download ─────────────────────────────────────────────────────────
    st.markdown("---")
    st.subheader("Download")
    st.download_button(
        "↓ Download All Arbitrage (CSV)",
        analyses_to_summary_dataframe(filtered_arb).to_csv(index=False).encode("utf-8"),
        "all_arbitrage_opportunities.csv",
        "text/csv",
        width="stretch",
    )
