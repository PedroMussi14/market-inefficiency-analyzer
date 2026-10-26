# =============================================================================
# config.py
# Static dashboard configuration: selector options, thresholds and the
# bookmaker homepage registry.
# =============================================================================

APP_NAME = "Market Inefficiency Analyzer"

# Fallback URLs used when a provider does not return a deep link for a bookmaker.
BOOK_LINKS = {
    "DraftKings":    "https://sportsbook.draftkings.com/",
    "FanDuel":       "https://sportsbook.fanduel.com/",
    "BetMGM":        "https://sports.betmgm.com/",
    "Caesars":       "https://sportsbook.caesars.com/",
    "BetRivers":     "https://www.betrivers.com/",
    "PointsBet":     "https://pointsbet.com/",
    "Barstool":      "https://barstoolsportsbook.com/",
    "Hard Rock Bet": "https://www.hardrock.bet/",
    "ESPN BET":      "https://espnbet.com/",
    "Fanatics":      "https://sportsbook.fanatics.com/",
    "Bet365":        "https://www.bet365.com/",
    "William Hill":  "https://www.williamhill.com/",
    "888sport":      "https://www.888sport.com/",
    "Unibet":        "https://www.unibet.com/",
    "Pinnacle":      "https://www.pinnacle.com/",
    "Betway":        "https://www.betway.com/",
    "LeoVegas":      "https://www.leovegas.com/",
    "Coral":         "https://sports.coral.co.uk/",
    "Ladbrokes":     "https://sports.ladbrokes.com/",
    "Bovada":        "https://www.bovada.lv/",
    "MyBookie.ag":   "https://www.mybookie.ag/",
    "LowVig.ag":     "https://www.lowvig.ag/",
    "BetUS":         "https://www.betus.com.pa/",
    "BetUS.ag":      "https://www.betus.com.pa/",
    "BetOnline":     "https://www.betonline.ag/",
    "BetOnline.ag":  "https://www.betonline.ag/",
}

# Season-long markets (futures) can't be arbitraged per game; hide them.
EXCLUDED_SPORT_KEYWORDS = ["winner", "outrights", "championship"]

# Sports shown at the top of the selector for quick access
PRIORITY_SPORTS = ["NBA", "NFL", "MLB", "NHL", "EPL", "Brazil Série A", "NCAAB", "NCAAF"]

# Market display name → API key
MARKET_OPTIONS = {
    "Moneyline / Match Winner": "h2h",
    "Point Spread":             "spreads",
    "Game Total":               "totals",
}

# Sportsbook region display name → API region key(s).
# "Brasil" is a convenience preset for eu+uk: the regions covering the major
# books that accept Brazilian users (Bet365, Betfair, Pinnacle, Betsson, ...).
REGION_OPTIONS = {
    "Brasil 🇧🇷":      "eu,uk",
    "United States":  "us",
    "United Kingdom": "uk",
    "Europe":         "eu",
    "Australia":      "au",
}

# "I bet from…" display label → analyzer.filters.ACCESSIBILITY_PRESETS key
BET_FROM_OPTIONS = {
    "Anywhere 🌍":        "anywhere",
    "Brasil 🇧🇷":          "brazil",
    "USA 🇺🇸":             "usa",
    "United Kingdom 🇬🇧":  "uk",
    "Europe 🇪🇺":          "europe",
}

# Market efficiency (implied probability sum) below which a market is "near arbitrage"
NEAR_ARB_THRESHOLD = 1.015

# Default sidebar values
DEFAULT_MAX_EFFICIENCY = 1.03
DEFAULT_TOP_N          = 10
