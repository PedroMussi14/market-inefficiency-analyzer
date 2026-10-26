"""Bug 2 (scraper side): Betano soccer events need all three 1X2 prices."""

from src.scrapers.betano import BetanoScraper

KICKOFF_MS = 1_900_000_000_000


def make_event(selections: list[dict]) -> dict:
    return {
        "participants": [{"name": "Flamengo"}, {"name": "Palmeiras"}],
        "markets": [{
            "type": "MRES",
            "marketCloseTimeMillis": KICKOFF_MS,
            "selections": selections,
        }],
    }


def test_full_1x2_market_is_parsed():
    event = BetanoScraper()._parse_event(
        make_event([
            {"name": "1", "price": 2.10},
            {"name": "X", "price": 3.30},
            {"name": "2", "price": 3.60},
        ]),
        "soccer_brazil_serie_a",
    )

    assert event is not None
    (market,) = event.markets
    assert [o.name for o in market.outcomes] == ["Flamengo", "Draw", "Palmeiras"]


def test_soccer_market_missing_the_draw_is_rejected():
    event = BetanoScraper()._parse_event(
        make_event([{"name": "1", "price": 2.10}, {"name": "2", "price": 3.60}]),
        "soccer_brazil_serie_a",
    )
    assert event is None
