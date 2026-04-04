import pandas as pd
import streamlit as st

from api_client import get_odds, get_sports
from arbitrage import analyze_event
from exporter import analyses_to_dataframe

st.set_page_config(page_title="Best Betting Opportunities", layout="wide")


BOOK_LINKS = {
    "DraftKings": "https://sportsbook.draftkings.com/",
    "FanDuel": "https://www.fanduel.com/",
    "BetMGM": "https://sports.betmgm.com/",
    "BetRivers": "https://betrivers.com/",
    "Bovada": "https://www.bovada.lv/",
    "MyBookie.ag": "https://www.mybookie.ag/",
    "LowVig.ag": "https://www.lowvig.ag/",
    "BetOnline.ag": "https://www.betonline.ag/",
    "BetUS": "https://www.betus.com.pa/",
}


@st.cache_data(ttl=300)
def load_sports():
    sports = get_sports()

    excluded_keywords = [
        "winner",
        "outrights",
        "championship",
    ]

    filtered_sports = {}
    for sport in sports:
        key = sport["key"]
        title = sport["title"]

        if any(word in key.lower() for word in excluded_keywords):
            continue

        filtered_sports[title] = key

    return filtered_sports


@st.cache_data(ttl=60)
def load_data(sport_key: str, market: str, region: str, bankroll: float):
    try:
        events = get_odds(
            sport=sport_key,
            markets=market,
            regions=region,
            odds_format="american",
        )
    except Exception as e:
        raise Exception(
            "This sport or market is not supported. Try another option."
        )

    all_analyses = []
    for event in events:
        analysis = analyze_event(event, bankroll)
        if analysis is not None:
            all_analyses.append(analysis)

    detail_df = analyses_to_dataframe(all_analyses)
    event_df = summarize_by_event(all_analyses)

    return all_analyses, detail_df, event_df


def summarize_by_event(all_analyses):
    rows = []

    for analysis in all_analyses:
        rows.append({
            "Game": analysis["event"],
            "Sport": analysis["sport"],
            "Start Time": analysis["commence_time"],
            "Market Efficiency": round(analysis["implied_prob_sum"], 4),
            "Guaranteed Profit": "Yes" if analysis["arbitrage"] else "No",
            "Profit ($)": round(analysis["profit"], 2) if analysis["profit"] is not None else None,
            "Return (%)": round(analysis["roi"], 2) if analysis["roi"] is not None else None,
        })

    return pd.DataFrame(rows)


def format_market_label(market_key: str) -> str:
    labels = {
        "h2h": "Moneyline / Match Winner",
        "spreads": "Point Spread",
        "totals": "Game Total",
    }
    return labels.get(market_key, market_key)


def format_event_detail(df: pd.DataFrame) -> pd.DataFrame:
    display_df = df.copy()

    rename_map = {
        "event": "Game",
        "sport": "Sport",
        "commence_time": "Start Time",
        "implied_prob_sum": "Market Efficiency",
        "arbitrage": "Guaranteed Profit",
        "profit": "Profit ($)",
        "roi": "Return (%)",
        "outcome": "Bet On",
        "bookmaker": "Sportsbook",
        "american_odds": "American Odds",
        "decimal_odds": "Decimal Odds",
        "stake": "Suggested Bet ($)",
    }

    display_df = display_df.rename(columns=rename_map)

    if "Guaranteed Profit" in display_df.columns:
        display_df["Guaranteed Profit"] = display_df["Guaranteed Profit"].map({
            True: "Yes",
            False: "No"
        })

    for col in ["Market Efficiency", "Profit ($)", "Return (%)", "Decimal Odds", "Suggested Bet ($)"]:
        if col in display_df.columns:
            if col in ["Market Efficiency", "Decimal Odds"]:
                display_df[col] = pd.to_numeric(display_df[col], errors="coerce").round(4).fillna("")
            else:
                display_df[col] = pd.to_numeric(display_df[col], errors="coerce").round(2).fillna("")

    return display_df


st.title("Best Betting Opportunities")
st.caption(
    "We scan sportsbook odds and show the games with the best potential return. "
    "Focus on the game, the sportsbook, and the expected return."
)

available_sports = load_sports()

common_sports = [
    "NBA",
    "NFL",
    "MLB",
    "NHL",
    "English Premier League",
    "NCAAB",
    "NCAAF",
]

sport_options = [sport for sport in common_sports if sport in available_sports]
remaining_sports = [sport for sport in available_sports if sport not in sport_options]
sport_options.extend(remaining_sports)

with st.sidebar:
    st.header("Choose what to analyze")

    sport_title = st.selectbox("Sport", sport_options)
    sport_key = available_sports[sport_title]

    market_display = st.selectbox(
        "Market type",
        ["Moneyline / Match Winner", "Point Spread", "Game Total"],
    )
    market_map = {
        "Moneyline / Match Winner": "h2h",
        "Point Spread": "spreads",
        "Game Total": "totals",
    }
    market = market_map[market_display]

    region_display = st.selectbox(
        "Sportsbook region",
        ["United States", "United Kingdom", "Europe", "Australia"],
        index=0,
    )
    region_map = {
        "United States": "us",
        "United Kingdom": "uk",
        "Europe": "eu",
        "Australia": "au",
    }
    region = region_map[region_display]

    bankroll = st.number_input(
        "Budget per game ($)",
        min_value=1.0,
        value=100.0,
        step=10.0,
    )

    view_mode = st.radio("View", ["Simple", "Advanced"], horizontal=True)

    show_only_arbitrage = st.checkbox("Show only arbitrage opportunities", value=False)

    if view_mode == "Advanced":
        max_efficiency = st.slider(
            "Maximum market efficiency",
            min_value=1.00,
            max_value=1.10,
            value=1.03,
            step=0.001,
            help="Closer to 1.00 means better pricing."
        )
        top_n = st.slider(
            "How many games to show",
            min_value=5,
            max_value=100,
            value=15,
            step=5,
        )
    else:
        max_efficiency = 1.03
        top_n = 10

    refresh = st.button("Refresh data", use_container_width=True)

if refresh:
    st.cache_data.clear()

with st.spinner("Loading odds and finding the best opportunities..."):
    try:
        all_analyses, detail_df, event_df = load_data(sport_key, market, region, bankroll)
    except Exception as e:
        st.error(f"Error loading API data: {e}")
        st.stop()

if event_df.empty:
    st.warning("No complete games were returned for these settings.")
    st.stop()

filtered_event_df = event_df.copy()
filtered_event_df = filtered_event_df[filtered_event_df["Market Efficiency"] <= max_efficiency]

if show_only_arbitrage:
    filtered_event_df = filtered_event_df[filtered_event_df["Guaranteed Profit"] == "Yes"]

matching_games = filtered_event_df["Game"].tolist()
filtered_detail_df = detail_df[detail_df["event"].isin(matching_games)].copy()
display_detail_df = format_event_detail(filtered_detail_df)

best_efficiency = float(event_df["Market Efficiency"].min())
arb_count = int((event_df["Guaranteed Profit"] == "Yes").sum())

st.subheader("Quick summary")
c1, c2, c3 = st.columns(3)
c1.metric("Games analyzed", len(event_df))
c2.metric("Guaranteed profit games", arb_count)
c3.metric("Best market efficiency", f"{best_efficiency:.4f}")

with st.expander("How to read this page"):
    st.write(
        "If a game shows guaranteed profit, the app found prices across sportsbooks "
        "that may allow a profit no matter the outcome."
    )
    st.write(
        "The most important numbers are the game, the return percentage, the profit, "
        "and the sportsbook to use."
    )

arb_df = filtered_event_df[filtered_event_df["Guaranteed Profit"] == "Yes"].sort_values(
    "Return (%)", ascending=False
)

st.subheader("Top Games to Bet Right Now")

if arb_df.empty:
    closest_df = filtered_event_df.sort_values("Market Efficiency").head(top_n)
    if closest_df.empty:
        st.info("No games match your filters.")
    else:
        st.info("No guaranteed-profit games were found right now. Here are the closest opportunities.")
        st.dataframe(closest_df, use_container_width=True, hide_index=True)
else:
    top_display_df = arb_df.head(top_n)
    st.dataframe(top_display_df, use_container_width=True, hide_index=True)

    best = top_display_df.iloc[0]
    if pd.notna(best["Return (%)"]) and pd.notna(best["Profit ($)"]):
        st.success(
            f"Best opportunity right now: **{best['Game']}** | "
            f"Expected return: **{best['Return (%)']:.2f}%** | "
            f"Estimated profit: **${best['Profit ($)']:.2f}**"
        )

st.subheader("How to Bet This Game")

if matching_games:
    preferred_games = arb_df["Game"].tolist() if not arb_df.empty else filtered_event_df.sort_values("Market Efficiency")["Game"].tolist()
    selected_game = st.selectbox("Select a game", preferred_games)

    event_rows = display_detail_df[display_detail_df["Game"] == selected_game].copy()
    event_summary = filtered_event_df[filtered_event_df["Game"] == selected_game].iloc[0]

    left, right = st.columns([2, 1])

    with left:
        simple_cols = ["Bet On", "Sportsbook", "American Odds", "Decimal Odds"]
        if "Suggested Bet ($)" in event_rows.columns and event_rows["Suggested Bet ($)"].notna().any():
            simple_cols.append("Suggested Bet ($)")

        st.write("Place these bets:")
        st.dataframe(event_rows[simple_cols], use_container_width=True, hide_index=True)

    with right:
        st.markdown("### Summary")
        st.write(f"**Game:** {event_summary['Game']}")
        st.write(f"**Sport:** {event_summary['Sport']}")
        st.write(f"**Market:** {format_market_label(market)}")
        st.write(f"**Guaranteed Profit:** {event_summary['Guaranteed Profit']}")

        if pd.notna(event_summary["Profit ($)"]):
            st.write(f"**Estimated Profit:** ${event_summary['Profit ($)']:.2f}")

        if pd.notna(event_summary["Return (%)"]):
            st.write(f"**Expected Return:** {event_summary['Return (%)']:.2f}%")

        sportsbooks_used = event_rows["Sportsbook"].dropna().unique().tolist()
        if sportsbooks_used:
            st.markdown("### Sportsbook links")
            for book in sportsbooks_used:
                if book in BOOK_LINKS:
                    st.markdown(f"[Open {book}]({BOOK_LINKS[book]})")
                else:
                    st.write(book)
else:
    st.info("No games match the current filters.")

with st.expander("Show all filtered results"):
    if display_detail_df.empty:
        st.info("No results to show.")
    else:
        useful_cols = [
            "Game",
            "Sport",
            "Bet On",
            "Sportsbook",
            "American Odds",
            "Decimal Odds",
            "Suggested Bet ($)",
            "Profit ($)",
            "Return (%)",
            "Guaranteed Profit",
        ]
        existing_cols = [col for col in useful_cols if col in display_detail_df.columns]
        st.dataframe(
            display_detail_df[existing_cols].sort_values(["Game", "Decimal Odds"], ascending=[True, False]),
            use_container_width=True,
            hide_index=True,
        )

csv_bytes = display_detail_df.to_csv(index=False).encode("utf-8")
st.download_button(
    label="Download results as CSV",
    data=csv_bytes,
    file_name="betting_opportunities.csv",
    mime="text/csv",
    use_container_width=True,
)