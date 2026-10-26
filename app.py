"""Market Inefficiency Analyzer: Streamlit dashboard entry point.

Run with:
    streamlit run app.py

The page layout lives in dashboard/views/; this file only configures the page,
draws the sidebar and routes to the selected view.
"""

import streamlit as st

from dashboard.config import APP_NAME

# Page config must be the first Streamlit call of the run
st.set_page_config(
    page_title=APP_NAME,
    page_icon=":material/query_stats:",
    layout="wide",
    initial_sidebar_state="auto",   # open on desktop, folded away on a phone
)

from dashboard.sidebar import render_sidebar  # noqa: E402
from dashboard.theme import inject_css  # noqa: E402
from dashboard.views import all_arbitrage, ev_bets, scanner  # noqa: E402

VIEWS = {
    "Market scanner": scanner.render,
    "All arbitrage":  all_arbitrage.render,
    "+EV bets":       ev_bets.render,
}

inject_css()
settings = render_sidebar()
VIEWS[settings.page](settings)
