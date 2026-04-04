import requests

API_KEY = "31a6c4c71fa26d1e5c4e373837fc3544"
SPORT = "basketball_nba"   # you can change this later
REGIONS = "us"
MARKETS = "h2h"
ODDS_FORMAT = "american"

def get_odds():
    url = f"https://api.the-odds-api.com/v4/sports/{SPORT}/odds"

    params = {
        "apiKey": API_KEY,
        "regions": REGIONS,
        "markets": MARKETS,
        "oddsFormat": ODDS_FORMAT,
    }

    response = requests.get(url, params=params)

    if response.status_code != 200:
        print("Error:", response.status_code, response.text)
        return []

    return response.json()