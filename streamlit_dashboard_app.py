import pandas as pd
import streamlit as st

from api_client import get_odds
from arbitrage import analyze_event
from exporter import analyses_to_dataframe

st.set_page_config(page_title="Market Inefficiency Analyzer", layout="wide")


@st.cache_data(ttl=60)
def load_data(bankroll: float) -> tuple[list[dict], pd.DataFrame]:
    events = get_odds()
    all_analyses = []

    for event in events:
        analysis = analyze_event(event, bankroll)
        if analysis is not None:
            all_analyses.append(analysis)

    df = analyses_to_dataframe(all_analyses)
    return all_analyses, df


def summarize_by_event(all_analyses: list[dict]) -> pd.DataFrame:
    rows = []
    for analysis in all_analyses:
        rows.append({
            "event": analysis["event"],
            "sport": analysis["sport"],
            "commence_time": analysis["commence_time"],
            "implied_prob_sum": round(analysis["implied_prob_sum"], 4),
            "arbitrage": analysis["arbitrage"],
            "profit": round(analysis["profit"], 2) if analysis["profit"] is not None else None,
            "roi": round(analysis["roi"], 2) if analysis["roi"] is not None else None,
        })
    return pd.DataFrame(rows)


st.title("Market Inefficiency Analyzer")
st.caption("Live odds dashboard with arbitrage detection and near-arbitrage ranking")

with st.sidebar:
    st.header("Filters")
    bankroll = st.number_input("Bankroll per event", min_value=1.0, value=100.0, step=10.0)
    show_only_arbitrage = st.checkbox("Show only arbitrage opportunities", value=False)
    max_implied_prob = st.slider("Maximum implied probability sum", min_value=1.00, max_value=1.10, value=1.03, step=0.001)
    top_n = st.slider("Number of closest markets", min_value=5, max_value=50, value=10, step=5)
    refresh = st.button("Refresh data")

if refresh:
    st.cache_data.clear()

try:
    all_analyses, detail_df = load_data(bankroll)
except Exception as e:
    st.error(f"Error loading API data: {e}")
    st.stop()

if detail_df.empty:
    st.warning("No complete events were returned by the API.")
    st.stop()

event_df = summarize_by_event(all_analyses)

sports = sorted(event_df["sport"].dropna().unique().tolist())
selected_sports = st.multiselect("Sport", sports, default=sports)

filtered_event_df = event_df[event_df["sport"].isin(selected_sports)].copy()
filtered_event_df = filtered_event_df[filtered_event_df["implied_prob_sum"] <= max_implied_prob]

if show_only_arbitrage:
    filtered_event_df = filtered_event_df[filtered_event_df["arbitrage"] == True]

matching_events = filtered_event_df["event"].tolist()
filtered_detail_df = detail_df[detail_df["event"].isin(matching_events)].copy()

col1, col2, col3, col4 = st.columns(4)
col1.metric("Events analyzed", len(event_df))
col2.metric("Arbitrage opportunities", int(event_df["arbitrage"].sum()))
col3.metric("Best implied prob.", f"{event_df['implied_prob_sum'].min():.4f}")
col4.metric("Closest edge", f"{((1 - event_df['implied_prob_sum'].min()) * 100):.2f}%")

st.subheader("Top markets closest to arbitrage")
closest_df = filtered_event_df.sort_values("implied_prob_sum").head(top_n)
st.dataframe(closest_df, use_container_width=True)

arb_df = filtered_event_df[filtered_event_df["arbitrage"] == True].sort_values("roi", ascending=False)
st.subheader("Profitable arbitrage opportunities")
if arb_df.empty:
    st.info("No profitable arbitrage opportunities found in the current API response.")
else:
    st.dataframe(arb_df, use_container_width=True)

st.subheader("Outcome-level detail")
st.dataframe(filtered_detail_df.sort_values(["event", "decimal_odds"], ascending=[True, False]), use_container_width=True)

csv_bytes = filtered_detail_df.to_csv(index=False).encode("utf-8")
st.download_button(
    label="Download filtered results as CSV",
    data=csv_bytes,
    file_name="market_analysis_results_filtered.csv",
    mime="text/csv",
)

st.subheader("Event explorer")
if matching_events:
    selected_event = st.selectbox("Select an event", matching_events)
    event_rows = filtered_detail_df[filtered_detail_df["event"] == selected_event]
    event_summary = filtered_event_df[filtered_event_df["event"] == selected_event].iloc[0]

    left, right = st.columns([2, 1])
    with left:
        st.dataframe(event_rows, use_container_width=True)
    with right:
        st.markdown("### Summary")
        st.write(f"**Sport:** {event_summary['sport']}")
        st.write(f"**Start Time:** {event_summary['commence_time']}")
        st.write(f"**Implied Probability Sum:** {event_summary['implied_prob_sum']:.4f}")
        st.write(f"**Arbitrage:** {'Yes' if event_summary['arbitrage'] else 'No'}")
        if pd.notna(event_summary['profit']):
            st.write(f"**Profit:** ${event_summary['profit']:.2f}")
        if pd.notna(event_summary['roi']):
            st.write(f"**ROI:** {event_summary['roi']:.2f}%")
else:
    st.info("No events match the selected filters.")
