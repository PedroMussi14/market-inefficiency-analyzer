import pandas as pd
import streamlit as st

from api_client import get_odds, get_sports
from arbitrage import analyze_event
from exporter import analyses_to_dataframe

st.set_page_config(page_title="Market Inefficiency Analyzer", layout="wide")


@st.cache_data(ttl=300)
def load_sports():
    sports = get_sports()
    return {sport["title"]: sport["key"] for sport in sports}


@st.cache_data(ttl=60)
def load_data(sport_key: str, market: str, region: str, bankroll: float):
    events = get_odds(
        sport=sport_key,
        markets=market,
        regions=region,
        odds_format="american",
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
            "Event": analysis["event"],
            "Sport": analysis["sport"],
            "Start Time": analysis["commence_time"],
            "Implied Probability": round(analysis["implied_prob_sum"], 4),
            "Arbitrage Found": "Yes" if analysis["arbitrage"] else "No",
            "Profit ($)": round(analysis["profit"], 2) if analysis["profit"] is not None else None,
            "ROI (%)": round(analysis["roi"], 2) if analysis["roi"] is not None else None,
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
        "event": "Event",
        "sport": "Sport",
        "commence_time": "Start Time",
        "implied_prob_sum": "Implied Probability",
        "arbitrage": "Arbitrage Found",
        "profit": "Profit ($)",
        "roi": "ROI (%)",
        "outcome": "Outcome",
        "bookmaker": "Sportsbook",
        "american_odds": "American Odds",
        "decimal_odds": "Decimal Odds",
        "stake": "Suggested Stake ($)",
    }
    display_df = display_df.rename(columns=rename_map)

    if "Arbitrage Found" in display_df.columns:
        display_df["Arbitrage Found"] = display_df["Arbitrage Found"].map({True: "Yes", False: "No"})

    for col in ["Implied Probability", "Profit ($)", "ROI (%)", "Decimal Odds", "Suggested Stake ($)"]:
        if col in display_df.columns:
            display_df[col] = display_df[col].round(4 if col in ["Implied Probability", "Decimal Odds"] else 2)

    return display_df


st.title("Market Inefficiency Analyzer")
st.caption("Finds the best sportsbook price for each side of a game and checks whether a low-risk arbitrage setup exists.")

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

    sport_title = st.selectbox(
        "Sport",
        sport_options,
        help="Pick the league you want to scan.",
    )
    sport_key = available_sports[sport_title]

    market_display = st.selectbox(
        "Market type",
        ["Moneyline / Match Winner", "Point Spread", "Game Total"],
        help="Moneyline is the easiest place to start.",
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
        help="Used only to estimate stake sizing and profit.",
    )

    mode = st.radio(
        "View",
        ["Simple", "Advanced"],
        horizontal=True,
        help="Simple keeps only the most useful filters visible.",
    )

    show_only_arbitrage = st.checkbox(
        "Show only arbitrage opportunities",
        value=False,
    )

    if mode == "Advanced":
        max_implied_prob = st.slider(
            "Maximum implied probability",
            min_value=1.00,
            max_value=1.10,
            value=1.03,
            step=0.001,
            help="Lower values are closer to arbitrage.",
        )
        top_n = st.slider(
            "How many closest games to show",
            min_value=5,
            max_value=100,
            value=25,
            step=5,
        )
    else:
        max_implied_prob = 1.03
        top_n = 10

    refresh = st.button("Refresh data", use_container_width=True)

if refresh:
    st.cache_data.clear()

with st.spinner("Loading live odds and analyzing markets..."):
    try:
        all_analyses, detail_df, event_df = load_data(sport_key, market, region, bankroll)
    except Exception as e:
        st.error(f"Error loading API data: {e}")
        st.stop()

if event_df.empty:
    st.warning("No complete events were returned by the API for these settings.")
    st.stop()

filtered_event_df = event_df.copy()
filtered_event_df = filtered_event_df[filtered_event_df["Implied Probability"] <= max_implied_prob]

if show_only_arbitrage:
    filtered_event_df = filtered_event_df[filtered_event_df["Arbitrage Found"] == "Yes"]

matching_events = filtered_event_df["Event"].tolist()
filtered_detail_df = detail_df[detail_df["event"].isin(matching_events)].copy()
display_detail_df = format_event_detail(filtered_detail_df)

best_implied_prob = float(event_df["Implied Probability"].min())
arb_count = int((event_df["Arbitrage Found"] == "Yes").sum())
closest_edge = (1 - best_implied_prob) * 100

st.subheader("Quick summary")
metric_1, metric_2, metric_3, metric_4 = st.columns(4)
metric_1.metric("Games analyzed", len(event_df))
metric_2.metric("Arbitrage found", arb_count)
metric_3.metric("Closest game", f"{best_implied_prob:.4f}")
metric_4.metric("Best edge", f"{closest_edge:.2f}%")

with st.expander("What do these numbers mean?"):
    st.write(
        "A value below 1.00 means a true arbitrage opportunity exists. "
        "The closer a game is to 1.00, the closer it is to becoming profitable."
    )
    st.write(
        "Suggested stake sizes only appear when an arbitrage opportunity is found."
    )

st.subheader("Best opportunities right now")
closest_df = filtered_event_df.sort_values("Implied Probability").head(top_n)

if closest_df.empty:
    st.info("No games match the current filters.")
else:
    st.dataframe(closest_df, use_container_width=True, hide_index=True)

arb_df = filtered_event_df[filtered_event_df["Arbitrage Found"] == "Yes"].sort_values("ROI (%)", ascending=False)
st.subheader("Profitable arbitrage opportunities")
if arb_df.empty:
    st.info("No profitable arbitrage opportunities were found in this batch.")
else:
    st.dataframe(arb_df, use_container_width=True, hide_index=True)

st.subheader("Explore one game")
if matching_events:
    selected_event = st.selectbox("Select a game", matching_events)
    event_rows = display_detail_df[display_detail_df["Event"] == selected_event].copy()
    event_summary = filtered_event_df[filtered_event_df["Event"] == selected_event].iloc[0]

    left, right = st.columns([2, 1])

    with left:
        st.dataframe(event_rows, use_container_width=True, hide_index=True)

    with right:
        st.markdown("### Summary")
        st.write(f"**Sport:** {event_summary['Sport']}")
        st.write(f"**Market:** {format_market_label(market)}")
        st.write(f"**Start Time:** {event_summary['Start Time']}")
        st.write(f"**Implied Probability:** {event_summary['Implied Probability']:.4f}")
        st.write(f"**Arbitrage Found:** {event_summary['Arbitrage Found']}")

        if pd.notna(event_summary["Profit ($)"]):
            st.write(f"**Estimated Profit:** ${event_summary['Profit ($)']:.2f}")
        if pd.notna(event_summary["ROI (%)"]):
            st.write(f"**Estimated ROI:** {event_summary['ROI (%)']:.2f}%")
else:
    st.info("No events match the current filters.")

with st.expander("Show all filtered outcome details"):
    if display_detail_df.empty:
        st.info("No detailed rows to show.")
    else:
        st.dataframe(
            display_detail_df.sort_values(["Event", "Decimal Odds"], ascending=[True, False]),
            use_container_width=True,
            hide_index=True,
        )

csv_bytes = display_detail_df.to_csv(index=False).encode("utf-8")
st.download_button(
    label="Download filtered results as CSV",
    data=csv_bytes,
    file_name="market_analysis_results_filtered.csv",
    mime="text/csv",
    use_container_width=True,
)
