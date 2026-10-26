# =============================================================================
# providers/demo.py
# Offline demo provider backed by bundled sample odds.
#
# Needs no API key and no internet connection, so the dashboard and CLI can be
# demonstrated anywhere. The sample data is produced by
# scripts/generate_demo_data.py and lives in analyzer/data/demo/:
#
#   sports.json          list of sports (canonical /sports format)
#   odds/<sport>.json    events for one sport, in canonical format plus two
#                        demo-only fields that this module resolves:
#                          event.commence_in_hours → commence_time (relative to now)
#                          bookmaker.region        → filtered by `regions`
#
# Start times are relative to the moment of the request, so the games always
# look upcoming (or, for negative offsets, live) whenever the demo is run.
# =============================================================================

import json
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from pathlib import Path

from .base import Provider

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "demo"


def _iso(moment: datetime) -> str:
    return moment.strftime("%Y-%m-%dT%H:%M:%SZ")


@lru_cache(maxsize=None)
def _load_json(path: Path):
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def build_events(raw_events: list, markets: str, regions: str,
                 now: datetime | None = None) -> list:
    """Turn stored demo events into canonical events for the given filters.

    Bookmakers outside `regions` and markets outside `markets` (both
    comma-separated) are dropped, mirroring how The Odds API behaves.
    """
    now = now or datetime.now(timezone.utc)
    wanted_markets = {m.strip() for m in markets.split(",") if m.strip()}
    wanted_regions = {r.strip() for r in regions.split(",") if r.strip()}

    events = []
    for raw in raw_events:
        bookmakers = []
        for book in raw["bookmakers"]:
            if book["region"] not in wanted_regions:
                continue
            book_markets = [m for m in book["markets"] if m["key"] in wanted_markets]
            if not book_markets:
                continue
            bookmakers.append({
                "key":         book["key"],
                "title":       book["title"],
                "link":        book.get("link"),
                "last_update": _iso(now - timedelta(minutes=2)),
                "markets":     book_markets,
            })

        events.append({
            "id":            raw["id"],
            "sport_key":     raw["sport_key"],
            "sport_title":   raw["sport_title"],
            "commence_time": _iso(now + timedelta(hours=raw["commence_in_hours"])),
            "home_team":     raw["home_team"],
            "away_team":     raw["away_team"],
            "bookmakers":    bookmakers,
        })
    return events


class DemoProvider(Provider):
    """Bundled, reproducible sample odds for offline demonstrations."""

    name        = "demo"
    label       = "Demo data 🎓 (offline sample)"
    region_hint = "Bundled sample odds. No API key or internet needed."

    def setup_help(self) -> str:
        return "Always available. Regenerate the data with scripts/generate_demo_data.py."

    def get_sports(self) -> list:
        return _load_json(DATA_DIR / "sports.json")

    def get_odds(self, sport, markets="h2h", regions="us", odds_format="american",
                 include_links=True, include_sids=True) -> list:
        path = DATA_DIR / "odds" / f"{sport}.json"
        if not path.exists():
            raise ValueError(f"No demo data for sport '{sport}'.")
        return build_events(_load_json(path), markets, regions)
