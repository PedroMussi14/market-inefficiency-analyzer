# =============================================================================
# views/scanner.py
# Market Scanner: one sport in depth. The screen answers "is there a
# guaranteed profit in this market right now, and how do I stake it?":
# the focus card shows the selected game's legs, stakes and booking links,
# beside every game's distance from break-even; the full table and CSV
# exports follow.
# =============================================================================

from html import escape

import pandas as pd
import streamlit as st

from analyzer.export import analyses_to_dataframe, analyses_to_summary_dataframe

from ..charts import chart_break_even, locked_in_return
from ..components import (
    build_game_info_link,
    build_general_odds_info_link,
    card_title,
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
    status_pill,
)
from ..data import format_event_detail, load_data
from ..sidebar import Settings

CHART_CONFIG = {"displayModeBar": False}


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


def _finding(event_df: pd.DataFrame, arb_df: pd.DataFrame, bankroll: float) -> str:
    """The one line under the title: what in this scan most needs attention."""
    total = len(event_df)
    if not arb_df.empty:
        best = arb_df.iloc[0]
        count = len(arb_df)
        return (
            f"<b>{count} of {total}</b> games guarantee a profit. Best: <b>{escape(best['Game'])}</b>, "
            f"{money(best['Profit ($)'], signed=True)} on {money(bankroll)} "
            f"({percent(best['Return (%)'])})."
        )
    closest = event_df.sort_values("Market Efficiency").iloc[0]
    return (
        f"No guaranteed profit in <b>{total}</b> games. Closest: <b>{escape(closest['Game'])}</b>, "
        f"{percent(locked_in_return(closest['Market Efficiency']))} backing every outcome."
    )


def _render_kpis(event_df: pd.DataFrame, filtered: pd.DataFrame) -> None:
    arb_count  = int((filtered["Guaranteed Profit"] == "Yes").sum())
    roi_values = filtered["Return (%)"].dropna()
    best_eff   = float(filtered["Market Efficiency"].min()) if not filtered.empty else None

    with st.container(key="kpis"):
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Games scanned", len(event_df))
        c2.metric("Guaranteed profits", arb_count)
        c3.metric("Best return", percent(float(roi_values.max())) if not roi_values.empty else "—")
        c4.metric("Lowest implied sum", f"{best_eff:.4f}" if best_eff is not None else "—")


def _render_focus(game: str, analysis: dict, s: Settings) -> None:
    """The selected game: its figures, the legs table and the stake split."""
    efficiency = analysis["implied_prob_sum"]
    meta = " · ".join(filter(None, [
        analysis.get("sport"), format_market_label(s.market), format_start(analysis.get("commence_time")),
    ]))
    # The game's name is already in the selector above, so the head carries only its context
    st.markdown(
        game_head_html("", meta, live_badge(analysis.get("commence_time")) + status_pill(efficiency)),
        unsafe_allow_html=True,
    )

    if analysis["arbitrage"]:
        figures = [
            (f"Guaranteed profit on {money(s.bankroll)}", money(analysis["profit"], signed=True), "pos", True),
            ("Return", percent(analysis["roi"]), "", False),
            ("Implied sum", f"{efficiency:.4f}", "", False),
        ]
    else:
        figures = [
            ("Return backing every outcome", percent(locked_in_return(efficiency)), "", True),
            ("Implied sum", f"{efficiency:.4f}", "", False),
        ]
    st.markdown(figures_html(figures), unsafe_allow_html=True)

    st.markdown(legs_table_html(analysis["results"], hide_american=s.hide_american_odds),
                unsafe_allow_html=True)
    if analysis["arbitrage"]:
        st.markdown(stake_split_html(analysis["results"]), unsafe_allow_html=True)
    else:
        empty_state("These best prices still leave the bookmakers a margin, so no stake split guarantees "
                    "a profit. Prices move: refresh to re-check.")

    st.markdown(
        '<div class="links">'
        f'{link_html("Matchup news", build_game_info_link(game))}'
        f'{link_html("Compare odds elsewhere", build_general_odds_info_link(game))}'
        '</div>',
        unsafe_allow_html=True,
    )


def _render_games_table(filtered: pd.DataFrame, s: Settings) -> None:
    df = filtered.sort_values("Market Efficiency").copy()
    df["Start"] = df["Start Time"].map(format_start)
    df["Locked-in return"] = locked_in_return(df["Market Efficiency"]).round(2)
    # Profit only exists for arbitrage games: a dash, not "None", elsewhere
    df["Profit"] = df["Profit ($)"].map(lambda v: money(v, signed=True))
    columns = ["Game", "Start"]
    if "Line" in df.columns and s.market != "h2h":
        columns.append("Line")
    columns += ["Market Efficiency", "Locked-in return", "Profit"]

    st.dataframe(
        df[columns],
        width="stretch",
        hide_index=True,
        column_config={
            "Game": st.column_config.TextColumn("Game", width="large"),
            "Market Efficiency": st.column_config.NumberColumn("Implied sum", format="%.4f"),
            "Locked-in return": st.column_config.NumberColumn(
                "Return backing every outcome", format="%+.2f%%",
                help="Positive: a guaranteed profit. Negative: the margin the bookmakers keep.",
            ),
            "Profit": st.column_config.TextColumn(f"Profit on ${s.bankroll:,.0f}", alignment="right"),
        },
    )


def _render_all_prices(display_detail_df: pd.DataFrame, s: Settings) -> None:
    with st.expander("Every best price for the filtered games"):
        if display_detail_df.empty:
            empty_state("No prices to show for these filters.")
            return
        columns = [
            "Game", "Bet On", "Line", "Sportsbook", "American Odds", "Decimal Odds",
            "Suggested Bet ($)", "Profit ($)", "Return (%)",
        ]
        if s.hide_american_odds:
            columns.remove("American Odds")
        if s.market == "h2h":
            columns.remove("Line")
        existing = [c for c in columns if c in display_detail_df.columns]
        df = display_detail_df[existing].sort_values(["Game", "Decimal Odds"], ascending=[True, False])
        for col in ("Suggested Bet ($)", "Profit ($)"):
            if col in df.columns:
                df[col] = df[col].map(money)
        if "Return (%)" in df.columns:
            df["Return (%)"] = df["Return (%)"].map(percent)
        right = dict(alignment="right")
        st.dataframe(
            df,
            width="stretch",
            hide_index=True,
            column_config={
                "Decimal Odds": st.column_config.NumberColumn(format="%.3f"),
                "Suggested Bet ($)": st.column_config.TextColumn("Stake", **right),
                "Profit ($)": st.column_config.TextColumn("Profit", **right),
                "Return (%)": st.column_config.TextColumn("Return", **right),
            },
        )


def _render_downloads(summary_df: pd.DataFrame, detailed_df: pd.DataFrame) -> None:
    col1, col2, _ = st.columns([1, 1, 1])
    with col1:
        st.download_button(
            "Download summary (CSV)",
            summary_df.to_csv(index=False).encode("utf-8"),
            "betting_opportunities_summary.csv",
            "text/csv",
            width="stretch",
        )
    with col2:
        st.download_button(
            "Download every price (CSV)",
            detailed_df.to_csv(index=False).encode("utf-8"),
            "betting_opportunities_detailed.csv",
            "text/csv",
            width="stretch",
        )


def render(s: Settings) -> None:
    # ── Data pipeline ────────────────────────────────────────────────────────
    with st.spinner("Scanning sportsbooks…"):
        try:
            all_analyses, detail_df, event_df = load_data(
                s.provider_name, s.sport_key, s.market, s.region, s.bankroll,
                s.bet_from, s.excluded_books,
            )
        except Exception as e:
            render_page_header("Market scanner")
            st.error(f"Couldn't load odds for this sport and market. {e}")
            return

    if event_df.empty:
        render_page_header("Market scanner", "No games were returned for these settings.",
                           source_stamp(s.provider_name, 60))
        return

    filtered          = _apply_filters(event_df, s)
    matching_games    = filtered["Game"].tolist()
    display_detail_df = format_event_detail(detail_df[detail_df["event"].isin(matching_games)])
    filtered_analyses = [a for a in all_analyses if a["event"] in matching_games]
    arb_df = filtered[filtered["Guaranteed Profit"] == "Yes"].sort_values("Return (%)", ascending=False)

    # ── Title row + KPIs ─────────────────────────────────────────────────────
    render_page_header("Market scanner", _finding(event_df, arb_df, s.bankroll),
                       source_stamp(s.provider_name, 60))
    _render_kpis(event_df, filtered)

    if not matching_games:
        empty_state("No games match the current filters. Loosen <b>Max market efficiency</b> or "
                    "turn off <b>Show only arbitrage</b> in the sidebar.")
        return

    # ── Focus card (the answer) beside every game's distance to break-even ──
    # Arbitrage games first, by return; then the closest markets
    ordered = arb_df["Game"].tolist() + [
        g for g in filtered.sort_values("Market Efficiency")["Game"] if g not in set(arb_df["Game"])
    ]
    left, right = st.columns([7, 5], gap="medium")
    with left, st.container(key="card-focus"):
        selected = st.selectbox("Game", ordered, help="Arbitrage games are listed first, best return on top.")
        analysis = next(a for a in filtered_analyses if a["event"] == selected)
        _render_focus(selected, analysis, s)
    with right, st.container(key="card-chart"):
        st.markdown(card_title(
            "Return backing every outcome",
            "At the best prices, staked to pay the same whatever happens. "
            "Right of the line is a guaranteed profit.",
        ), unsafe_allow_html=True)
        st.plotly_chart(chart_break_even(filtered, top_n=s.top_n, selected=selected),
                        width="stretch", config=CHART_CONFIG)

    # ── Every game, then every price ─────────────────────────────────────────
    section(f"All games ({len(filtered)})")
    _render_games_table(filtered, s)
    _render_all_prices(display_detail_df, s)

    summary_df = analyses_to_summary_dataframe(filtered_analyses)
    _render_downloads(summary_df, analyses_to_dataframe(filtered_analyses))
