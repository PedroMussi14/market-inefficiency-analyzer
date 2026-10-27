# =============================================================================
# views/scanner.py
# Market Scanner: one sport in depth. The screen answers "is there a
# guaranteed profit in this market right now, and how do I stake it?":
# the selected game's profit and order ticket lead, the list of games beside
# it picks the game, and the market strip shows where every game sits.
# =============================================================================

from html import escape

import pandas as pd
import streamlit as st

from analyzer.export import analyses_to_dataframe, analyses_to_summary_dataframe

from ..charts import market_strip_svg
from ..components import (
    build_game_info_link,
    build_general_odds_info_link,
    card_head,
    empty_state,
    facts_html,
    format_market_label,
    format_start,
    hero_panel_html,
    live_badge,
    locked_in_return,
    matchup_html,
    money,
    money_html,
    open_link,
    percent,
    render_page_header,
    short_game,
    stake_split_html,
    status_pill,
    ticket_html,
)
from ..data import load_data
from ..sidebar import Settings


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


def _render_hero(game: str, analysis: dict, s: Settings) -> None:
    """The selected game: its headline figure, then the order ticket."""
    efficiency = analysis["implied_prob_sum"]
    meta = " · ".join(filter(None, [
        analysis.get("sport"), format_market_label(s.market), format_start(analysis.get("commence_time")),
    ]))

    st.markdown(
        matchup_html(game, meta, live_badge(analysis.get("commence_time")) + status_pill(efficiency)),
        unsafe_allow_html=True,
    )

    if analysis["arbitrage"]:
        figure = (f'<div class="hero-label">Guaranteed profit on {money(s.bankroll)}</div>'
                  f'{money_html(analysis["profit"], positive=True)}'
                  '<div class="hero-sub">whatever the result</div>')
        facts = [("Return", percent(analysis["roi"])), ("Implied sum", f"{efficiency:.4f}"),
                 ("Legs", str(len(analysis["results"])))]
    else:
        figure = ('<div class="hero-label">Return backing every outcome</div>'
                  f'<div class="money">{percent(locked_in_return(efficiency))}</div>'
                  '<div class="hero-sub">the bookmakers still keep a margin</div>')
        facts = [("Implied sum", f"{efficiency:.4f}"), ("Budget", money(s.bankroll)),
                 ("Legs", str(len(analysis["results"])))]
    st.markdown(hero_panel_html(figure, facts), unsafe_allow_html=True)
    st.markdown(ticket_html(analysis["results"], hide_american=s.hide_american_odds), unsafe_allow_html=True)
    if analysis["arbitrage"]:
        st.markdown(stake_split_html(analysis["results"]), unsafe_allow_html=True)
    st.markdown(
        '<div class="links">'
        f'{open_link(build_game_info_link(game), "Matchup news")}'
        f'{open_link(build_general_odds_info_link(game), "Compare odds elsewhere")}</div>',
        unsafe_allow_html=True,
    )


def _watch_label(row: pd.Series) -> str:
    """A watchlist row: the game, and its return as a badge on the right."""
    ret = locked_in_return(row["Market Efficiency"])
    colour = "green" if ret > 0 else "gray"
    name = short_game(str(row["Game"]), limit=32).replace("[", "(").replace("]", ")")
    return f"{name} :{colour}-badge[{percent(ret)}]"


def _render_downloads(filtered_analyses: list) -> None:
    col1, col2, _ = st.columns([1, 1, 1])
    col1.download_button(
        "Download summary (CSV)",
        analyses_to_summary_dataframe(filtered_analyses).to_csv(index=False).encode("utf-8"),
        "betting_opportunities_summary.csv", "text/csv", width="stretch",
    )
    col2.download_button(
        "Download every price (CSV)",
        analyses_to_dataframe(filtered_analyses).to_csv(index=False).encode("utf-8"),
        "betting_opportunities_detailed.csv", "text/csv", width="stretch",
    )


def render(s: Settings) -> None:
    with st.spinner("Scanning sportsbooks…"):
        try:
            all_analyses, _, event_df = load_data(
                s.provider_name, s.sport_key, s.market, s.region, s.bankroll,
                s.bet_from, s.excluded_books,
            )
        except Exception as e:
            render_page_header("Market scanner", provider_name=s.provider_name)
            st.error(f"Couldn't load odds for this sport and market. {e}")
            return

    sport = event_df["Sport"].iloc[0] if not event_df.empty else ""
    scope = " · ".join(filter(None, [sport, format_market_label(s.market)]))

    if event_df.empty:
        render_page_header("Market scanner", f"{escape(scope)} · no games right now", s.provider_name)
        empty_state("No games were returned for these settings. Try another sport or region.")
        return

    filtered = _apply_filters(event_df, s)
    filtered_analyses = [a for a in all_analyses if a["event"] in set(filtered["Game"])]
    arb_df = filtered[filtered["Guaranteed Profit"] == "Yes"].sort_values("Return (%)", ascending=False)

    render_page_header(
        "Market scanner",
        f"{escape(scope)} · {len(event_df)} games scanned · {len(arb_df)} with a guaranteed profit",
        s.provider_name,
    )

    if filtered.empty:
        empty_state("No games match the current filters. Loosen <b>Max market efficiency</b> or "
                    "turn off <b>Show only arbitrage</b> in the sidebar.")
        return

    # Arbitrage games first by return, then the closest markets
    ordered = pd.concat([arb_df, filtered[filtered["Guaranteed Profit"] != "Yes"]
                         .sort_values("Market Efficiency")])
    labels = {row["Game"]: _watch_label(row) for _, row in ordered.iterrows()}
    captions = [format_start(t) for t in ordered["Start Time"]]

    left, right = st.columns([7, 5], gap="medium")
    with right, st.container(key="card-watch"):
        st.markdown(card_head("Games", f"{len(ordered)} · best first", "list", ruled=True),
                    unsafe_allow_html=True)
        selected = st.radio(
            "Game", list(labels), format_func=labels.get, captions=captions,
            label_visibility="collapsed", key="watch",
        )
    with left, st.container(key="card-hero"):
        st.markdown(card_head("Selected game", "stakes sized to pay the same on every outcome", "ticket",
                              ruled=True), unsafe_allow_html=True)
        analysis = next(a for a in filtered_analyses if a["event"] == selected)
        _render_hero(selected, analysis, s)

    with st.container(key="card-market"):
        st.markdown(card_head("Where every game sits",
                              "return from backing every outcome at the best prices", "strip", ruled=True),
                    unsafe_allow_html=True)
        st.markdown(market_strip_svg(filtered, selected), unsafe_allow_html=True)
        st.markdown(
            '<div class="key"><span><i style="background:#1d5fd6"></i>Guaranteed profit</span>'
            '<span><i style="background:#c4c8cd"></i>Bookmakers keep a margin</span>'
            '<span><i class="ring"></i>Selected game</span>'
            '<span>Dots stacked vertically share the same return</span></div>',
            unsafe_allow_html=True,
        )
        roi = arb_df["Return (%)"].dropna()
        st.markdown(facts_html([
            ("Games scanned", str(len(event_df))),
            ("Guaranteed profits", str(len(arb_df))),
            ("Best return", percent(float(roi.max())) if not roi.empty else "—"),
            ("Lowest implied sum", f'{filtered["Market Efficiency"].min():.4f}'),
        ], boxed=True), unsafe_allow_html=True)

    _render_downloads(filtered_analyses)
