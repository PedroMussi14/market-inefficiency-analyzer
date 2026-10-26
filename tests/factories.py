"""Builders for synthetic odds events in The Odds API v4 format."""


def make_outcome(name: str, price: int, point: float | None = None) -> dict:
    outcome = {"name": name, "price": price}
    if point is not None:
        outcome["point"] = point
    return outcome


def make_book(title: str, market: str, outcomes: list[dict]) -> dict:
    return {
        "key": title.lower().replace(" ", "_"),
        "title": title,
        "markets": [{"key": market, "outcomes": outcomes}],
    }


def make_event(
    bookmakers: list[dict],
    home: str = "Home",
    away: str = "Away",
    sport_key: str = "basketball_nba",
) -> dict:
    return {
        "id": "evt_1",
        "sport_key": sport_key,
        "sport_title": "Test League",
        "commence_time": "2030-01-01T00:00:00Z",
        "home_team": home,
        "away_team": away,
        "bookmakers": bookmakers,
    }
