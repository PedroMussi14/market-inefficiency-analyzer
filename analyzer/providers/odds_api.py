# =============================================================================
# providers/odds_api.py
# The Odds API v4 (https://the-odds-api.com): the default live data source.
#
# Its response format is the canonical format used across the project, so no
# transformation is needed. Each /odds request costs quota credits equal to
# (number of markets) x (number of regions); the remaining quota is read from
# the response headers and surfaced in the dashboard.
# =============================================================================

import os

import requests

from .base import Provider

BASE_URL = "https://api.the-odds-api.com/v4"
REQUEST_TIMEOUT_SECONDS = 20


class OddsApiProvider(Provider):
    """Global coverage. For books that accept Brazilian users, use EU + UK regions
    (Bet365, Betfair, Pinnacle, Betsson, ...)."""

    name        = "odds_api"
    label       = "The Odds API"
    region_hint = "Global. Use EU+UK for BR-friendly books."

    def __init__(self) -> None:
        self._quota = {"remaining": None, "used": None}

    @staticmethod
    def _api_key() -> str | None:
        return os.getenv("API_KEY")

    def is_configured(self) -> bool:
        return bool(self._api_key())

    def setup_help(self) -> str:
        return ("Sign up at https://the-odds-api.com → copy your key → "
                "add `API_KEY=...` to your .env file.")

    def get_quota_info(self) -> dict:
        return dict(self._quota)

    def get_sports(self) -> list:
        response = requests.get(
            f"{BASE_URL}/sports",
            params={"apiKey": self._api_key()},
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        return response.json()

    def get_odds(self, sport, markets="h2h", regions="us", odds_format="american",
                 include_links=True, include_sids=True) -> list:
        """Fetch odds, optionally with deep links to bookmaker event pages/betslips."""
        response = requests.get(
            f"{BASE_URL}/sports/{sport}/odds",
            params={
                "apiKey":       self._api_key(),
                "regions":      regions,
                "markets":      markets,
                "oddsFormat":   odds_format,
                "includeLinks": str(include_links).lower(),
                "includeSids":  str(include_sids).lower(),
            },
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        self._quota = {
            "remaining": response.headers.get("x-requests-remaining"),
            "used":      response.headers.get("x-requests-used"),
        }
        return response.json()
