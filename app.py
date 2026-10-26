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
    page_title=f"{APP_NAME} · Arbitrage Finder",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

from dashboard.sidebar import render_sidebar  # noqa: E402
from dashboard.theme import inject_css  # noqa: E402
from dashboard.views import all_arbitrage, ev_bets, scanner  # noqa: E402

VIEWS = {
    "📊 Market Scanner": scanner.render,
    "⚡ All Arbitrage":  all_arbitrage.render,
    "📈 +EV Bets":       ev_bets.render,
}

inject_css()
settings = render_sidebar()
VIEWS[settings.page](settings)
