# =============================================================================
# providers/brodds.py
# Client for the self-hosted BrOdds service (see ../../brodds-api/).
#
# BrOdds scrapes Brazilian sportsbooks (Betano today) and serves them through
# an API that mirrors The Odds API v4, so this client is a thin HTTP wrapper.
# =============================================================================

import os

import requests

from .base import Provider

DEFAULT_URL = "http://localhost:8000"


class BroddsLocalProvider(Provider):
    """Native Brazilian books (Betano, ...) via your own scraper service.

    Setup:
        cd brodds-api && cp .env.example .env && docker compose up -d
        then set in the root .env:
            BRODDS_LOCAL_URL=http://localhost:8000
            BRODDS_LOCAL_KEY=<BRODDS_API_KEY from brodds-api/.env>
    """

    name        = "brodds_local"
    label       = "BrOdds Local (self-hosted scrapers)"
    region_hint = "Your own scrapers. Native BR books. No quota limits."

    @staticmethod
    def _base_url() -> str:
        return os.getenv("BRODDS_LOCAL_URL", DEFAULT_URL).rstrip("/")

    @staticmethod
    def _headers() -> dict:
        return {"X-API-Key": os.getenv("BRODDS_LOCAL_KEY", "")}

    def is_configured(self) -> bool:
        return bool(os.getenv("BRODDS_LOCAL_URL") and os.getenv("BRODDS_LOCAL_KEY"))

    def setup_help(self) -> str:
        return ("Start the scraper service: cd brodds-api && cp .env.example .env && "
                "docker compose up -d. Then add BRODDS_LOCAL_URL and BRODDS_LOCAL_KEY to .env.")

    def get_sports(self) -> list:
        response = requests.get(f"{self._base_url()}/v4/sports", headers=self._headers(), timeout=10)
        response.raise_for_status()
        return response.json()

    def get_odds(self, sport, markets="h2h", regions="us", odds_format="american",
                 include_links=True, include_sids=True) -> list:
        response = requests.get(
            f"{self._base_url()}/v4/sports/{sport}/odds",
            headers=self._headers(),
            params={"markets": markets, "regions": regions, "oddsFormat": odds_format},
            timeout=20,
        )
        response.raise_for_status()
        return response.json()
