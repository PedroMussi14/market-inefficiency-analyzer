import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_KEY")

_quota = {"remaining": None, "used": None}


def get_quota_info() -> dict:
    """Return the last known API quota from The Odds API response headers."""
    return dict(_quota)


def get_sports():
    url = "https://api.the-odds-api.com/v4/sports"
    params = {"apiKey": API_KEY}
    response = requests.get(url, params=params, timeout=20)
    response.raise_for_status()
    return response.json()


def get_odds(
    sport="basketball_nba",
    markets="h2h",
    regions="us",
    odds_format="american",
    include_links=True,      # New parameter (default True)
    include_sids=True        # New parameter (default True)
):
    """
    Fetch odds with optional deep links to bookmaker event pages and betslips.
    """
    url = f"https://api.the-odds-api.com/v4/sports/{sport}/odds"
    
    params = {
        "apiKey": API_KEY,
        "regions": regions,
        "markets": markets,
        "oddsFormat": odds_format,
        "includeLinks": str(include_links).lower(),   # "true" or "false"
        "includeSids": str(include_sids).lower(),
    }

    response = requests.get(url, params=params, timeout=20)
    response.raise_for_status()
    _quota["remaining"] = response.headers.get("x-requests-remaining")
    _quota["used"] = response.headers.get("x-requests-used")
    return response.json()