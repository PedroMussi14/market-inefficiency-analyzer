# =============================================================================
# providers/base.py
# The interface every odds data source implements.
#
# Providers return data in The Odds API v4 "canonical" shape, so the analysis
# code and the dashboard never need to know where the data came from:
#
#   {
#     "id": str, "sport_key": str, "sport_title": str,
#     "commence_time": ISO 8601 str,
#     "home_team": str, "away_team": str,
#     "bookmakers": [
#       {
#         "key": str, "title": str, "last_update": str,
#         "markets": [
#           {"key": "h2h" | "spreads" | "totals",
#            "outcomes": [
#              {"name": str, "price": int (American odds), "point": float?,
#               "link": str?, "sid": str?}
#            ]}
#         ]
#       }
#     ]
#   }
# =============================================================================

from abc import ABC, abstractmethod


class Provider(ABC):
    """Common interface every odds data provider must implement."""

    # Subclasses MUST override these
    name: str = ""           # internal identifier (e.g. "odds_api")
    label: str = ""          # display label shown in the dashboard sidebar
    region_hint: str = ""    # short description of geographic coverage

    @abstractmethod
    def get_sports(self) -> list:
        """Return the available sports in canonical form:
        [{"key": str, "title": str, "group": str, "active": bool}, ...]
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
        """Return the upcoming events for `sport` in canonical format."""

    def get_quota_info(self) -> dict:
        """Return {'remaining': int | None, 'used': int | None}.
        Default: the provider does not report a request quota."""
        return {"remaining": None, "used": None}

    def is_configured(self) -> bool:
        """Return True if the provider has everything it needs (e.g. an API key)."""
        return True

    def setup_help(self) -> str:
        """Short instructions shown when the provider is not configured yet."""
        return ""
