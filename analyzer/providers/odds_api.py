# =============================================================================
# providers/odds_api.py
# The Odds API v4 (https://the-odds-api.com): the default live data source.
#
# Its response format is the canonical format used across the project, so no
# transformation is needed. Each /odds request costs quota credits equal to
# (number of markets) x (number of regions); the remaining quota is read from
# the response headers and surfaced in the dashboard.
#
# The API key travels as a query parameter, so request errors are re-raised
# as OddsApiError with a message that never contains the request URL.
# =============================================================================

import os

import requests

from .base import Provider

BASE_URL = "https://api.the-odds-api.com/v4"
REQUEST_TIMEOUT_SECONDS = 20


class OddsApiError(RuntimeError):
    """A failed Odds API request, described without the URL (which holds the key)."""

    def __init__(self, message: str, quota_exhausted: bool = False) -> None:
        super().__init__(message)
        self.quota_exhausted = quota_exhausted


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

    def _get(self, path: str, params: dict) -> list:
        """GET an endpoint; record the quota headers; raise OddsApiError on failure."""
        try:
            response = requests.get(
                f"{BASE_URL}{path}",
                params={"apiKey": self._api_key(), **params},
                timeout=REQUEST_TIMEOUT_SECONDS,
            )
        except requests.RequestException as e:
            # Connection errors can echo the URL too: report only the error type
            raise OddsApiError(f"Couldn't reach The Odds API ({type(e).__name__}).") from None

        if "x-requests-remaining" in response.headers:
            self._quota = {
                "remaining": response.headers.get("x-requests-remaining"),
                "used":      response.headers.get("x-requests-used"),
            }
        if response.ok:
            return response.json()

        try:
            detail = response.json().get("message", "")
        except ValueError:
            detail = ""
        remaining = self._quota["remaining"]
        out_of_quota = response.status_code == 429 or (
            response.status_code == 401 and (remaining == "0" or "quota" in detail.lower())
        )
        if out_of_quota:
            raise OddsApiError(
                "The Odds API usage quota is used up for this month. "
                "Switch the data provider to Demo data, or wait for the quota to reset.",
                quota_exhausted=True,
            )
        if response.status_code == 401:
            raise OddsApiError("The Odds API rejected the API key (401). Check API_KEY in .env.")
        raise OddsApiError(f"The Odds API returned {response.status_code}. {detail}".strip())

    def get_sports(self) -> list:
        return self._get("/sports", {})

    def get_odds(self, sport, markets="h2h", regions="us", odds_format="american",
                 include_links=True, include_sids=True) -> list:
        """Fetch odds, optionally with deep links to bookmaker event pages/betslips."""
        return self._get(f"/sports/{sport}/odds", {
            "regions":      regions,
            "markets":      markets,
            "oddsFormat":   odds_format,
            "includeLinks": str(include_links).lower(),
            "includeSids":  str(include_sids).lower(),
        })
