import pandas as pd
import streamlit as st

from urllib.parse import quote_plus


from api_client import get_odds, get_sports
from arbitrage import analyze_event
from exporter import (
    analyses_to_dataframe,
    export_detailed_csv,
    export_summary_csv,
)

st.set_page_config(page_title="Best Betting Opportunities", layout="wide")


BOOK_LINKS = {
    "DraftKings": "https://sportsbook.draftkings.com/",
    "FanDuel": "https://sportsbook.fanduel.com/",
    "BetMGM": "https://sports.betmgm.com/",
    "Caesars": "https://sportsbook.caesars.com/",
    "BetRivers": "https://www.betrivers.com/",
    "PointsBet": "https://pointsbet.com/",
    "Barstool": "https://barstoolsportsbook.com/",
    "Hard Rock Bet": "https://www.hardrock.bet/",
    "ESPN BET": "https://espnbet.com/",
    "Fanatics": "https://sportsbook.fanatics.com/",
    "Bet365": "https://www.bet365.com/",
    "William Hill": "https://www.williamhill.com/",
    "888sport": "https://www.888sport.com/",
    "Unibet": "https://www.unibet.com/",
    "Pinnacle": "https://www.pinnacle.com/",
    "Betway": "https://www.betway.com/",
    "LeoVegas": "https://www.leovegas.com/",
    "Coral": "https://sports.coral.co.uk/",
    "Ladbrokes": "https://sports.ladbrokes.com/",
    "Bovada": "https://www.bovada.lv/",
    "MyBookie.ag": "https://www.mybookie.ag/",
    "LowVig.ag": "https://www.lowvig.ag/",
}


@st.cache_data(ttl=300)
def load_sports():
    sports = get_sports()

    excluded_keywords = ["winner", "outrights", "championship"]

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
        ) from e

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

    for col in ["Market Efficiency", "Profit ($)", "Return (%)", "Decimal Odds", "Suggested Bet ($)"]:
        if col in display_df.columns:
            if col in ["Market Efficiency", "Decimal Odds"]:
                display_df[col] = pd.to_numeric(display_df[col], errors="coerce").round(4)
            else:
                display_df[col] = pd.to_numeric(display_df[col], errors="coerce").round(2)

    return display_df


def build_game_info_link(game_name: str) -> str:
    query = quote_plus(game_name + " ESPN")
    return f"https://www.google.com/search?q={query}"


def build_general_odds_info_link(game_name: str) -> str:
    query = quote_plus(game_name + " odds")
    return f"https://www.google.com/search?q={query}"


def normalize_book_name(name: str) -> str:
    name = name.lower()

    mapping = {
        "draftkings": "DraftKings",
        "fanduel": "FanDuel",
        "betmgm": "BetMGM",
        "caesars": "Caesars",
        "betrivers": "BetRivers",
        "pointsbet": "PointsBet",
        "barstool": "Barstool",
        "hard rock": "Hard Rock Bet",
        "espn": "ESPN BET",
        "fanatics": "Fanatics",
        "bet365": "Bet365",
        "william hill": "William Hill",
        "888": "888sport",
        "unibet": "Unibet",
        "pinnacle": "Pinnacle",
        "betway": "Betway",
        "leovegas": "LeoVegas",
        "coral": "Coral",
        "ladbrokes": "Ladbrokes",
        "bovada": "Bovada",
        "mybookie": "MyBookie.ag",
        "lowvig": "LowVig.ag",
    }

    for key in mapping:
        if key in name:
            return mapping[key]

    return name.title()

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
            help="Closer to 1.00 means better pricing.",
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

filtered_analyses = [a for a in all_analyses if a["event"] in matching_games]
summary_export_df = export_summary_csv("betting_opportunities_summary.csv", filtered_analyses)
detailed_export_df = export_detailed_csv("betting_opportunities_detailed.csv", filtered_analyses)

best_efficiency = float(filtered_event_df["Market Efficiency"].min()) if not filtered_event_df.empty else None
arb_count = int((filtered_event_df["Guaranteed Profit"] == "Yes").sum())

st.subheader("Quick summary")
c1, c2, c3 = st.columns(3)
c1.metric("Games analyzed", len(event_df))
c2.metric("Guaranteed profit games", arb_count)
c3.metric(
    "Best market efficiency",
    f"{best_efficiency:.4f}" if best_efficiency is not None else "No data"
)

with st.expander("How to read this page"):
    st.write(
        "If a game shows guaranteed profit, the app found prices across sportsbooks "
        "that may allow a profit no matter the outcome."
    )
    st.write(
        "The most important numbers are the game, the return percentage, the profit, "
        "and the sportsbook with the best price."
    )

arb_df = filtered_event_df[filtered_event_df["Guaranteed Profit"] == "Yes"].sort_values(
    "Return (%)", ascending=False
)

st.subheader("Top Games Right Now")

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

st.subheader("Summary View")

summary_display_df = summary_export_df.copy()

summary_display_df = summary_display_df.rename(columns={
    "event": "Game",
    "sport": "Sport",
    "commence_time": "Start Time",
    "implied_prob_sum": "Market Efficiency",
    "arbitrage": "Guaranteed Profit",
    "profit": "Profit ($)",
    "roi": "Return (%)",
    "best_outcome": "Best Team / Side",
    "best_bookmaker": "Best Sportsbook",
    "best_american_odds": "Best American Odds",
    "best_decimal_odds": "Best Decimal Odds",
})

st.dataframe(summary_display_df, use_container_width=True, hide_index=True)

st.subheader("Game Breakdown")

if matching_games:
    preferred_games = (
        arb_df["Game"].tolist()
        if not arb_df.empty
        else filtered_event_df.sort_values("Market Efficiency")["Game"].tolist()
    )

    selected_game = st.selectbox("Select a game", preferred_games)

    event_rows = display_detail_df[display_detail_df["Game"] == selected_game].copy()
    event_summary = filtered_event_df[filtered_event_df["Game"] == selected_game].iloc[0]

    left, right = st.columns([2, 1])

    with left:
        simple_cols = ["Bet On", "Sportsbook", "American Odds", "Decimal Odds"]
        if "Suggested Bet ($)" in event_rows.columns and event_rows["Suggested Bet ($)"].notna().any():
            simple_cols.append("Suggested Bet ($)")

        st.write("Best available prices for this game:")
        st.dataframe(event_rows[simple_cols], use_container_width=True, hide_index=True)

    with right:
        st.markdown("### Summary")

        st.write(f"**Game:** {event_summary['Game']}")
        st.write(f"**Sport:** {event_summary['Sport']}")
        st.write(f"**Market:** {format_market_label(market)}")
        st.write(f"**Guaranteed Profit:** {event_summary['Guaranteed Profit']}")

        profit = event_summary["Profit ($)"]
        roi = event_summary["Return (%)"]

        col_a, col_b = st.columns(2)

        with col_a:
            st.metric(
                label=f"Profit (on ${bankroll:.0f})",
                value=f"${profit:.2f}" if pd.notna(profit) else "N/A"
            )

        with col_b:
            st.metric(
                label="Return",
                value=f"{roi:.2f}%" if pd.notna(roi) else "N/A"
            )

        st.markdown("### Learn more")
        game_info_link = build_game_info_link(selected_game)
        general_odds_link = build_general_odds_info_link(selected_game)

        st.link_button(
            label="Open matchup info and news",
            url=game_info_link,
            use_container_width=True,
        )
        st.link_button(
            label="Search general odds info",
            url=general_odds_link,
            use_container_width=True,
        )

        sportsbooks_used = event_rows["Sportsbook"].dropna().unique().tolist()

        if sportsbooks_used:
            st.markdown("### Best prices found at")

            for book in sportsbooks_used:
                normalized = normalize_book_name(book)

                url = BOOK_LINKS.get(normalized)

                if url:
                    st.link_button(
                        label=normalized,
                        url=url,
                        use_container_width=True,
                    )
                else:
                    st.write(normalized)

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

summary_csv_bytes = summary_export_df.to_csv(index=False).encode("utf-8")
detailed_csv_bytes = detailed_export_df.to_csv(index=False).encode("utf-8")

st.subheader("Download Data")

col1, col2 = st.columns(2)

with col1:
    st.download_button(
        label="Download summary CSV",
        data=summary_csv_bytes,
        file_name="betting_opportunities_summary.csv",
        mime="text/csv",
        use_container_width=True,
    )

with col2:
    st.download_button(
        label="Download detailed CSV",
        data=detailed_csv_bytes,
        file_name="betting_opportunities_detailed.csv",
        mime="text/csv",
        use_container_width=True,
    )   