# =============================================================================
# providers.py
# Multi-provider odds API abstraction.
#
# Each provider implements the same interface (get_sports / get_odds /
# get_quota_info / is_configured) and returns data in The Odds API canonical
# format so arbitrage.py and the dashboard don't need to care which API the
# data came from.
#
# To add a NEW provider:
#   1. Subclass Provider below
#   2. Implement get_sports() and get_odds() (return canonical format)
#   3. Add the class instance to the PROVIDERS list at the bottom
#
# Canonical event format (matches The Odds API v4 /odds response):
#   {
#     "id": str, "sport_key": str, "sport_title": str,
#     "commence_time": ISO8601 str,
#     "home_team": str, "away_team": str,
#     "bookmakers": [
#       {
#         "key": str, "title": str, "last_update": str,
#         "markets": [
#           {"key": "h2h"|"spreads"|"totals",
#            "outcomes": [
#              {"name": str, "price": int (american odds), "point": float?}
#            ]}
#         ]
#       }
#     ]
#   }
# =============================================================================

import os
from abc import ABC, abstractmethod

# Load .env so is_configured() checks see API keys from the file, not just
# OS-level env vars. Idempotent — safe even if other modules call it too.
from dotenv import load_dotenv
load_dotenv()


class Provider(ABC):
    """Common interface every odds API provider must implement."""

    # Subclasses MUST override these
    name: str = ""           # internal identifier (e.g. "odds_api")
    label: str = ""          # display label shown in the sidebar selectbox
    region_hint: str = ""    # short description of geographic coverage

    @abstractmethod
    def get_sports(self) -> list:
        """Return a list of sport dicts in canonical form:
        [{"key": "...", "title": "...", "group": "...", "active": bool, "has_outrights": bool}, ...]
        """

    @abstractmethod
    def get_odds(
        self,
        sport: str,
        markets: str = "h2h",
        regions: str = "us",
        odds_format: str = "american",
        include_links: bool = True,
        include_sids: bool = True,
    ) -> list:
        """Return a list of events in canonical format (see module docstring)."""

    def get_quota_info(self) -> dict:
        """Optional. Return {'remaining': int|None, 'used': int|None}.
        Default: provider doesn't report quota."""
        return {"remaining": None, "used": None}

    def is_configured(self) -> bool:
        """Return True if the provider's API key is present in env. Default True."""
        return True

    def setup_help(self) -> str:
        """Short instructions shown when the provider isn't configured yet."""
        return ""


# =============================================================================
# Provider 1 — The Odds API  (current default, fully working)
# =============================================================================

class OddsApiProvider(Provider):
    """Wraps the existing api_client.py functions.

    Coverage in Brazil: select EU+UK regions to get Bet365, Betfair, Pinnacle,
    1xBet, Betsson — all of which accept Brazilian users.
    """

    name        = "odds_api"
    label       = "The Odds API 🌍"
    region_hint = "Global. Use EU+UK for BR-friendly books."

    def get_sports(self):
        from api_client import get_sports
        return get_sports()

    def get_odds(self, sport, markets="h2h", regions="us", odds_format="american",
                 include_links=True, include_sids=True):
        from api_client import get_odds
        return get_odds(
            sport=sport, markets=markets, regions=regions,
            odds_format=odds_format,
            include_links=include_links, include_sids=include_sids,
        )

    def get_quota_info(self):
        from api_client import get_quota_info
        return get_quota_info()

    def is_configured(self):
        return bool(os.getenv("API_KEY"))

    def setup_help(self):
        return ("Sign up at https://the-odds-api.com → copy your key → "
                "add `API_KEY=...` to your .env file.")


# =============================================================================
# Provider 2 — OddsPapi  (skeleton — requires key + transformer verification)
# =============================================================================
# OddsPapi specifically covers Brazilian books that The Odds API doesn't:
#   Betano, KTO, Pixbet, Sportingbet, EstrelaBet, Galera Bet, Esportes da Sorte
#
# Caveats discovered from their docs:
#   - Per-fixture model: scanning a sport requires (1) /fixtures call,
#     then (2) one /odds call per fixture, with 500ms cooldown between requests.
#     A 30-game NBA scan = ~31 requests + ~15s wall time.
#   - Numeric market/outcome IDs whose meanings depend on fixture type;
#     a real response is needed to build the ID → canonical-name mapping.
#   - Free tier = 250 req/month (very limiting for arbitrage scanning).
#
# To finish this adapter:
#   1. Sign up at https://oddspapi.io, get a key, set ODDSPAPI_KEY in .env
#   2. Capture one /v4/odds response and one /v4/fixtures response
#   3. Fill in the TODO markers below
# =============================================================================

class OddsPapiProvider(Provider):

    name        = "oddspapi"
    label       = "OddsPapi 🇧🇷 (Betano · KTO · Pixbet)"
    region_hint = "Brazilian-native books. Per-fixture model — slower scans."

    BASE_URL = "https://api.oddspapi.io/v4"

    def is_configured(self):
        return bool(os.getenv("ODDSPAPI_KEY"))

    def setup_help(self):
        return ("Sign up at https://oddspapi.io → copy your key → "
                "add `ODDSPAPI_KEY=...` to your .env file. "
                "Note: free tier = 250 req/month; per-fixture model is slow.")

    def get_sports(self):
        # TODO Verify endpoint name and response shape.
        # Likely: GET https://api.oddspapi.io/v4/sports?apiKey=KEY
        # Expected canonical return: [{"key", "title", "group", "active", "has_outrights"}, ...]
        raise NotImplementedError(
            "OddsPapi /sports adapter pending. Capture a real response and "
            "implement the transformer in providers.py → OddsPapiProvider.get_sports."
        )

    def get_odds(self, sport, markets="h2h", regions="us", odds_format="american",
                 include_links=True, include_sids=True):
        # Implementation outline (pseudo-code):
        #
        #   import requests, time
        #   key = os.getenv("ODDSPAPI_KEY")
        #
        #   # 1. Fetch fixtures for this sport
        #   fixtures_url = f"{self.BASE_URL}/fixtures"
        #   fixtures = requests.get(fixtures_url, params={"sport": sport, "apiKey": key}).json()
        #
        #   events = []
        #   for fx in fixtures:
        #       # 2. Fetch odds for each fixture (respecting 500ms rate limit)
        #       odds_resp = requests.get(
        #           f"{self.BASE_URL}/odds",
        #           params={"fixtureId": fx["id"], "apiKey": key, "oddsFormat": "american"},
        #       ).json()
        #
        #       # 3. Transform numeric market/outcome IDs → canonical h2h/spreads/totals
        #       events.append(self._transform_fixture(fx, odds_resp, markets))
        #
        #       time.sleep(0.5)
        #
        #   return events
        raise NotImplementedError(
            "OddsPapi /odds adapter pending. The transformer needs a real "
            "response to verify market/outcome ID mapping."
        )

    def _transform_fixture(self, fixture: dict, odds_response: dict, market_filter: str) -> dict:
        """Translate one OddsPapi fixture+odds pair into canonical event format.

        TODO Mapping table needed (verify with real responses):
            market_id 101 → "h2h"      (Match Result / 1X2)
            market_id ??? → "spreads"  (Asian Handicap)
            market_id ??? → "totals"   (Over/Under)
            outcome_id 101 → "Home"
            outcome_id 102 → "Draw"
            outcome_id 103 → "Away"
        """
        raise NotImplementedError("Transformer pending real-response verification.")


# =============================================================================
# Provider 3 — OpticOdds  (skeleton — requires key + transformer verification)
# =============================================================================
# OpticOdds claims 350+ bookmakers including Betano. They have a sport-level
# odds endpoint (similar to The Odds API's model) which would be far more
# practical for BetScan than OddsPapi's per-fixture approach.
#
# To finish this adapter:
#   1. Sign up at https://opticodds.com, get a key, set OPTICODDS_KEY in .env
#   2. Capture one sport-level odds response
#   3. Fill in the get_odds transformer below
# =============================================================================

class OpticOddsProvider(Provider):

    name        = "opticodds"
    label       = "OpticOdds 🌎 (Betano + 350 books)"
    region_hint = "Sport-level endpoint, faster than OddsPapi."

    BASE_URL = "https://api.opticodds.com/api/v3"

    def is_configured(self):
        return bool(os.getenv("OPTICODDS_KEY"))

    def setup_help(self):
        return ("Sign up at https://opticodds.com → copy your key → "
                "add `OPTICODDS_KEY=...` to your .env file.")

    def get_sports(self):
        # TODO Likely: GET {BASE_URL}/sports with header X-Api-Key: KEY
        raise NotImplementedError(
            "OpticOdds /sports adapter pending. See https://opticodds.com for docs."
        )

    def get_odds(self, sport, markets="h2h", regions="us", odds_format="american",
                 include_links=True, include_sids=True):
        # TODO Likely: GET {BASE_URL}/fixtures/active?sport={sport}&league=...
        #              GET {BASE_URL}/odds?fixture_id=... or sport-level equivalent
        raise NotImplementedError(
            "OpticOdds /odds adapter pending. Capture a real response to verify shape."
        )


# =============================================================================
# Registry
# =============================================================================
# Order matters — first item is the default provider in the sidebar.

class BroddsLocalProvider(Provider):
    """Talks to your self-hosted brodds-api service (see ./brodds-api/).

    This is the only provider that can give you native Brazilian books like
    Betano, KTO, and Pixbet — because you run the scrapers yourself.

    Setup:
        cd brodds-api && cp .env.example .env && docker compose up -d
        then add to your main .env:
            BRODDS_LOCAL_URL=http://localhost:8000
            BRODDS_LOCAL_KEY=<the BRODDS_API_KEY value from brodds-api/.env>
    """

    name        = "brodds_local"
    label       = "BrOdds Local 🇧🇷 (self-hosted: Betano, KTO, Pixbet)"
    region_hint = "Your own scrapers. Native BR books. No quota limits."

    def _base_url(self) -> str:
        return os.getenv("BRODDS_LOCAL_URL", "http://localhost:8000").rstrip("/")

    def _headers(self) -> dict:
        return {"X-API-Key": os.getenv("BRODDS_LOCAL_KEY", "")}

    def is_configured(self):
        return bool(os.getenv("BRODDS_LOCAL_URL") and os.getenv("BRODDS_LOCAL_KEY"))

    def setup_help(self):
        return ("Stand up your own scraper service: cd brodds-api && "
                "cp .env.example .env && docker compose up -d. "
                "Then add BRODDS_LOCAL_URL and BRODDS_LOCAL_KEY to .env.")

    def get_sports(self):
        import requests
        r = requests.get(f"{self._base_url()}/v4/sports", headers=self._headers(), timeout=10)
        r.raise_for_status()
        return r.json()

    def get_odds(self, sport, markets="h2h", regions="us", odds_format="american",
                 include_links=True, include_sids=True):
        import requests
        r = requests.get(
            f"{self._base_url()}/v4/sports/{sport}/odds",
            headers=self._headers(),
            params={"markets": markets, "regions": regions, "oddsFormat": odds_format},
            timeout=20,
        )
        r.raise_for_status()
        return r.json()


_PROVIDER_INSTANCES = [
    OddsApiProvider(),
    BroddsLocalProvider(),
    OddsPapiProvider(),
    OpticOddsProvider(),
]

PROVIDERS = {p.name: p for p in _PROVIDER_INSTANCES}


def get_provider(name: str) -> Provider:
    """Resolve a provider by its `name` attribute. Raises KeyError if unknown."""
    return PROVIDERS[name]


def list_providers() -> list:
    """Return all registered providers (configured or not)."""
    return list(PROVIDERS.values())


def list_configured_providers() -> list:
    """Return only providers whose API key is present in env."""
    return [p for p in PROVIDERS.values() if p.is_configured()]
