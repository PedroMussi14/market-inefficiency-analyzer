# =============================================================================
# views/scanner.py
# Market Scanner: one sport in depth (efficiency ranking, top games,
# per-game breakdown with charts, stakes and sportsbook links, CSV export).
# =============================================================================

import pandas as pd
import streamlit as st

from analyzer.export import analyses_to_dataframe, analyses_to_summary_dataframe

from ..charts import (
    chart_efficiency_gauge,
    chart_efficiency_ranking,
    chart_odds_comparison,
    chart_roi_scatter,
    chart_stake_pie,
)
from ..components import (
    build_game_info_link,
    build_general_odds_info_link,
    build_prices_table,
    efficiency_badge,
    format_market_label,
    game_card_html,
    live_badge,
    render_bookmaker_links,
    render_page_header,
)
from ..config import APP_NAME
from ..data import format_event_detail, load_data
from ..sidebar import Settings

CHART_CONFIG = {"displayModeBar": False}

SUMMARY_COLUMNS = {
    "event":              "Game",
    "sport":              "Sport",
    "commence_time":      "Start Time",
    "line":               "Line",
    "implied_prob_sum":   "Market Efficiency",
    "arbitrage":          "Guaranteed Profit",
    "profit":             "Profit ($)",
    "roi":                "Return (%)",
    "best_outcome":       "Best Team / Side",
    "best_bookmaker":     "Best Sportsbook",
    "best_american_odds": "Best American Odds",
    "best_decimal_odds":  "Best Decimal Odds",
}


def _apply_filters(event_df: pd.DataFrame, s: Settings) -> pd.DataFrame:
    """Apply the sidebar's efficiency / arbitrage / ROI filters to the event table."""
    df = event_df[event_df["Market Efficiency"] <= s.max_efficiency].copy()
    if s.show_only_arbitrage:
        df = df[df["Guaranteed Profit"] == "Yes"]
    if s.min_roi > 0:
        arb_mask = df["Guaranteed Profit"] == "Yes"
        roi_mask = df["Return (%)"].fillna(0) >= s.min_roi
        df = df[~arb_mask | (arb_mask & roi_mask)]
    return df


def _render_kpis(event_df: pd.DataFrame, filtered: pd.DataFrame) -> int:
    """Render the KPI row and return the number of arbitrage games."""
    best_efficiency = float(filtered["Market Efficiency"].min()) if not filtered.empty else None
    arb_count       = int((filtered["Guaranteed Profit"] == "Yes").sum())
    roi_values      = filtered["Return (%)"].dropna()
    best_roi        = float(roi_values.max()) if not roi_values.empty else None

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Games Scanned",   len(event_df))
    c2.metric("Arbitrage Found", arb_count, delta="guaranteed" if arb_count > 0 else None)
    c3.metric("Best Efficiency", f"{best_efficiency:.4f}" if best_efficiency else "—")
    c4.metric("Best ROI",        f"{best_roi:.2f}%" if best_roi else "—")
    st.markdown("")
    return arb_count


def _render_top_games(filtered: pd.DataFrame, arb_df: pd.DataFrame, top_n: int) -> None:
    st.subheader("Top Games Right Now")

    if arb_df.empty:
        closest_df = filtered.sort_values("Market Efficiency").head(top_n)
        if closest_df.empty:
            st.info("No games match your current filters.")
        else:
            st.info("No guaranteed-profit games found. Showing closest opportunities.")
            st.dataframe(closest_df, width="stretch", hide_index=True)
    else:
        top_display_df = arb_df.head(top_n)
        st.dataframe(top_display_df, width="stretch", hide_index=True)

        best = top_display_df.iloc[0]
        if pd.notna(best["Return (%)"]) and pd.notna(best["Profit ($)"]):
            st.success(
                f"⚡ Best right now: **{best['Game']}** · "
                f"Return: **{best['Return (%)']:.2f}%** · "
                f"Profit: **${best['Profit ($)']:.2f}**"
            )
    st.markdown("---")


def _render_breakdown(selected_game: str, summary: pd.Series, event_rows: pd.DataFrame,
                      analyses: list, s: Settings) -> None:
    """Per-game charts, best-prices table and sportsbook links."""
    efficiency = float(summary["Market Efficiency"])
    profit_val = summary["Profit ($)"]
    roi_val    = summary["Return (%)"]

    st.markdown(
        game_card_html(
            label="Selected Game",
            title=selected_game,
            subtitle=f'{summary["Sport"]} · {format_market_label(s.market)}',
            badges_html=live_badge(summary.get("Start Time")) + efficiency_badge(efficiency),
        ),
        unsafe_allow_html=True,
    )

    # ── Charts: odds comparison | stake split | efficiency gauge ─────────────
    ch1, ch2, ch3 = st.columns([2.2, 2.2, 1.6])
    with ch1:
        st.plotly_chart(chart_odds_comparison(event_rows, selected_game),
                        width="stretch", config=CHART_CONFIG)
    with ch2:
        pie_fig = chart_stake_pie(event_rows, s.bankroll)
        if pie_fig:
            st.plotly_chart(pie_fig, width="stretch", config=CHART_CONFIG)
        else:
            st.info("Stake split only shown for arbitrage games.")
    with ch3:
        st.plotly_chart(chart_efficiency_gauge(efficiency), width="stretch", config=CHART_CONFIG)

    # ── Best prices (left) | links & metrics (right) ─────────────────────────
    left, right = st.columns([1.5, 1])
    with left:
        st.markdown("##### Best Prices")
        st.markdown(build_prices_table(event_rows, s.bankroll, hide_american=s.hide_american_odds),
                    unsafe_allow_html=True)
        st.markdown("")
        if pd.notna(roi_val):
            st.success(f"Expected return: **{roi_val:.2f}%** · Estimated profit: **${profit_val:.2f}**")
        else:
            st.info("No guaranteed arbitrage opportunity for this game.")

    with right:
        st.markdown("##### Links & Info")
        m1, m2 = st.columns(2)
        m1.metric(f"Profit (${s.bankroll:.0f})", f"${profit_val:.2f}" if pd.notna(profit_val) else "N/A")
        m2.metric("Return", f"{roi_val:.2f}%" if pd.notna(roi_val) else "N/A")

        st.markdown("")
        st.link_button("Open matchup news", build_game_info_link(selected_game), width="stretch")
        st.link_button("Search odds info", build_general_odds_info_link(selected_game), width="stretch")

        st.markdown("")
        st.markdown('<span class="section-label">Sportsbooks</span>', unsafe_allow_html=True)
        analysis = next(a for a in analyses if a["event"] == selected_game)
        render_bookmaker_links({r["bookmaker"]: r.get("link") for r in analysis["results"]})

    st.caption("Direct links are provided by the bookmaker when available.")


def _render_all_results(display_detail_df: pd.DataFrame, s: Settings) -> None:
    with st.expander("🗂 Show all filtered results"):
        if display_detail_df.empty:
            st.info("No results to show.")
            return
        columns = [
            "Game", "Sport", "Bet On", "Line", "Sportsbook", "American Odds", "Decimal Odds",
            "Suggested Bet ($)", "Profit ($)", "Return (%)", "Guaranteed Profit",
        ]
        if s.hide_american_odds:
            columns.remove("American Odds")
        if s.market == "h2h":
            columns.remove("Line")
        existing = [c for c in columns if c in display_detail_df.columns]
        st.dataframe(
            display_detail_df[existing].sort_values(["Game", "Decimal Odds"], ascending=[True, False]),
            width="stretch",
            hide_index=True,
        )


def _render_downloads(summary_df: pd.DataFrame, detailed_df: pd.DataFrame) -> None:
    st.subheader("Download Data")
    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            "↓ Summary CSV",
            summary_df.to_csv(index=False).encode("utf-8"),
            "betting_opportunities_summary.csv",
            "text/csv",
            width="stretch",
        )
    with col2:
        st.download_button(
            "↓ Detailed CSV",
            detailed_df.to_csv(index=False).encode("utf-8"),
            "betting_opportunities_detailed.csv",
            "text/csv",
            width="stretch",
        )


def render(s: Settings) -> None:
    # ── Data pipeline ────────────────────────────────────────────────────────
    with st.spinner("Scanning sportsbooks for value…"):
        try:
            all_analyses, detail_df, event_df = load_data(
                s.provider_name, s.sport_key, s.market, s.region, s.bankroll,
                s.bet_from, s.excluded_books,
            )
        except Exception as e:
            st.error(f"Error loading odds data: {e}")
            return

    if event_df.empty:
        st.warning("No games were returned for these settings.")
        return

    filtered          = _apply_filters(event_df, s)
    matching_games    = filtered["Game"].tolist()
    display_detail_df = format_event_detail(detail_df[detail_df["event"].isin(matching_games)])
    filtered_analyses = [a for a in all_analyses if a["event"] in matching_games]
    arb_df = filtered[filtered["Guaranteed Profit"] == "Yes"].sort_values("Return (%)", ascending=False)

    # ── Header + KPIs ────────────────────────────────────────────────────────
    render_page_header(
        APP_NAME, "Live Odds",
        "Arbitrage detection across sportsbooks: the best price for every outcome, "
        "and whether together they guarantee a profit. Data is cached for 60 seconds.",
    )
    arb_count = _render_kpis(event_df, filtered)

    # ── Market efficiency charts ─────────────────────────────────────────────
    with st.expander("📊 Market Efficiency Ranking — all games", expanded=True):
        st.plotly_chart(chart_efficiency_ranking(event_df, top_n=min(s.top_n, len(event_df))),
                        width="stretch", config=CHART_CONFIG)
        if arb_count > 0 and (scatter_fig := chart_roi_scatter(event_df)):
            st.plotly_chart(scatter_fig, width="stretch", config=CHART_CONFIG)

    _render_top_games(filtered, arb_df, s.top_n)

    summary_df = analyses_to_summary_dataframe(filtered_analyses)
    with st.expander("📋 Summary View — all filtered games"):
        st.dataframe(summary_df.rename(columns=SUMMARY_COLUMNS), width="stretch", hide_index=True)

    # ── Game breakdown ───────────────────────────────────────────────────────
    st.subheader("Game Breakdown")
    if matching_games:
        # Arbitrage games first in the selector, otherwise closest markets first
        preferred_games = (
            arb_df["Game"].tolist() if not arb_df.empty
            else filtered.sort_values("Market Efficiency")["Game"].tolist()
        )
        selected_game = st.selectbox("Select a game", preferred_games)
        _render_breakdown(
            selected_game,
            filtered[filtered["Game"] == selected_game].iloc[0],
            display_detail_df[display_detail_df["Game"] == selected_game],
            filtered_analyses,
            s,
        )
    else:
        st.info("No games match the current filters.")
    st.markdown("---")

    _render_all_results(display_detail_df, s)
    _render_downloads(summary_df, analyses_to_dataframe(filtered_analyses))
