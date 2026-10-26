"""Tests for the offline demo provider and its bundled sample data."""

from datetime import datetime, timezone

import pytest

from analyzer.arbitrage import analyze_event
from analyzer.ev import find_ev_bets
from analyzer.providers import get_provider, list_configured_providers

REGIONS = "us,uk,eu"


@pytest.fixture(scope="module")
def demo():
    return get_provider("demo")


def all_events(demo, markets="h2h", regions=REGIONS):
    return [e for s in demo.get_sports() for e in demo.get_odds(s["key"], markets, regions)]


def test_demo_is_always_configured(demo, monkeypatch):
    monkeypatch.delenv("API_KEY", raising=False)
    assert demo in list_configured_providers()


def test_sports_have_canonical_fields(demo):
    sports = demo.get_sports()
    assert len(sports) >= 4
    assert all({"key", "title", "group", "active"} <= set(s) for s in sports)


def test_events_are_canonical(demo):
    for event in all_events(demo, "h2h,spreads,totals"):
        assert {"id", "sport_key", "sport_title", "commence_time",
                "home_team", "away_team", "bookmakers"} <= set(event)
        datetime.fromisoformat(event["commence_time"].replace("Z", "+00:00"))
        for book in event["bookmakers"]:
            assert "region" not in book
            for market in book["markets"]:
                assert all(isinstance(o["price"], int) for o in market["outcomes"])


def test_start_times_are_relative_to_now(demo):
    now = datetime.now(timezone.utc)
    starts = [datetime.fromisoformat(e["commence_time"].replace("Z", "+00:00"))
              for e in all_events(demo)]
    assert sum(s > now for s in starts) >= len(starts) - 1   # at most one live game
    assert any(s <= now for s in starts)                     # ...and one is live


def test_region_filter(demo):
    us_only = demo.get_odds("basketball_nba", "h2h", "us")
    titles = {b["title"] for e in us_only for b in e["bookmakers"]}
    assert titles and titles <= {"DraftKings", "FanDuel", "BetMGM", "Caesars", "BetRivers"}


def test_market_filter(demo):
    events = demo.get_odds("soccer_epl", "totals", REGIONS)
    keys = {m["key"] for e in events for b in e["bookmakers"] for m in b["markets"]}
    assert keys == {"totals"}


def test_unknown_sport_raises(demo):
    with pytest.raises(ValueError):
        demo.get_odds("curling_world_cup")


@pytest.mark.parametrize("market", ["h2h", "spreads", "totals"])
def test_every_event_is_analysable(demo, market):
    events = all_events(demo, market)
    assert all(analyze_event(e, selected_market=market) for e in events)


def test_planted_opportunities_are_detected(demo):
    arbs = {
        (a["event"], market)
        for market in ("h2h", "totals")
        for e in all_events(demo, market)
        if (a := analyze_event(e, selected_market=market)) and a["arbitrage"]
    }
    assert ("Denver Nuggets vs Los Angeles Lakers", "h2h") in arbs
    assert ("Miami Heat vs New York Knicks", "totals") in arbs
    assert ("Chelsea vs Arsenal", "h2h") in arbs
    assert ("Palmeiras vs Flamengo", "h2h") in arbs


def test_demo_contains_ev_bets(demo):
    assert sum(len(find_ev_bets(e)) for e in all_events(demo)) > 0
