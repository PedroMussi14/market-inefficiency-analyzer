"""Per-bookmaker scrapers. Each implements `BaseScraper.scrape()` and returns
a list of canonical `ScrapedEvent` objects."""

from .base import BaseScraper, ScrapedEvent, ScrapedMarket, ScrapedOutcome
from .betano import BetanoScraper

# Registry of all available scrapers — the scheduler iterates over this.
SCRAPERS: list[type[BaseScraper]] = [
    BetanoScraper,
    # Add more here as you implement them:
    # KtoScraper, PixbetScraper, SportingbetScraper, EstrelaBetScraper, ...
]

__all__ = ["BaseScraper", "ScrapedEvent", "ScrapedMarket", "ScrapedOutcome", "SCRAPERS"]
