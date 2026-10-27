"""End-to-end smoke tests: run the real Streamlit app on the offline demo data."""

import pytest
from streamlit.testing.v1 import AppTest

APP = "../app.py"   # relative to this test file


@pytest.fixture
def app(monkeypatch):
    """The dashboard with no API key configured, so the demo provider is the default."""
    monkeypatch.setenv("API_KEY", "")
    return AppTest.from_file(APP, default_timeout=60)


def widget(collection, label):
    return next(w for w in collection if w.label == label)


def page_text(at) -> str:
    return " ".join(str(m.value) for m in at.markdown)


def go_to(at, page: str):
    widget(at.sidebar.radio, "Page").set_value(page).run()
    return at


def test_market_scanner_renders_demo_data(app):
    at = app.run()

    assert not at.exception
    assert widget(at.sidebar.selectbox, "Data provider").value.startswith("Demo data")
    games = at.radio(key="watch")
    assert len(games.options) == 7   # 8 demo NBA games, one already in progress
    assert "Guaranteed profit on" in page_text(at)   # the demo NBA slate has an arbitrage


@pytest.mark.parametrize("market", ["Point Spread", "Game Total"])
def test_line_markets_render(app, market):
    at = app.run()
    widget(at.sidebar.selectbox, "Market type").set_value(market).run()

    assert not at.exception
    assert len(at.radio(key="watch").options) == 7


def test_all_arbitrage_hides_unreliable_books(app):
    at = go_to(app.run(), "All arbitrage")

    assert not at.exception
    # Default filter (I bet from: Brasil) → the three Brazil-accessible planted arbs
    assert "3 guaranteed-profit opportunities" in page_text(at)
    assert "1xBet" not in page_text(at)


def test_all_arbitrage_anywhere_includes_us_books(app):
    at = go_to(app.run(), "All arbitrage")
    widget(at.sidebar.multiselect, "Sportsbook region").set_value(["Brasil", "United States"]).run()
    widget(at.sidebar.selectbox, "I bet from").set_value("Anywhere").run()

    assert not at.exception
    # + the US-only DraftKings/FanDuel arb
    assert "4 guaranteed-profit opportunities" in page_text(at)


def test_ev_bets_page_renders(app):
    at = go_to(app.run(), "+EV bets")

    assert not at.exception
    assert "bets beat Pinnacle" in page_text(at)
    assert "1xBet" not in page_text(at)
