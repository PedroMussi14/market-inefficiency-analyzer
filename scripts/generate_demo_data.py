"""Generate the bundled sample odds used by the offline `demo` provider.

Usage (from the repository root):
    python scripts/generate_demo_data.py

How the data is built:
  1. Every event has a "fair" probability for each outcome.
  2. Each bookmaker prices the event from those probabilities plus a small
     random disagreement, then adds its own margin (Pinnacle 2.5%, soft books
     4.5-5.5%). Line markets get slightly different lines per book, as in reality.
  3. A handful of opportunities are planted on purpose (see PLANTS) so the
     demo always has something to show, including one "too good to be true"
     1xBet price that the dashboard's reliability filter is expected to hide.
  4. The script verifies its own output with the real analyzer: every planted
     opportunity must be detected, and no market may contain an accidental one.

Output is deterministic (fixed seed), so regenerating gives identical files.
"""

import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from analyzer.arbitrage import analyze_event  # noqa: E402
from analyzer.odds import decimal_to_american  # noqa: E402
from analyzer.providers.demo import DATA_DIR, build_events  # noqa: E402

SEED = 2026
NOISE_SD = 0.006         # bookmaker disagreement on probabilities
ALL_REGIONS = "us,uk,eu"
ALL_MARKETS = "h2h,spreads,totals"

# =============================================================================
# Bookmakers
# =============================================================================

BOOKS = [
    # key,             title,                region, margin, homepage
    ("draftkings",     "DraftKings",         "us", 0.045, "https://sportsbook.draftkings.com/"),
    ("fanduel",        "FanDuel",            "us", 0.045, "https://sportsbook.fanduel.com/"),
    ("betmgm",         "BetMGM",             "us", 0.050, "https://sports.betmgm.com/"),
    ("williamhill_us", "Caesars",            "us", 0.050, "https://sportsbook.caesars.com/"),
    ("betrivers",      "BetRivers",          "us", 0.055, "https://www.betrivers.com/"),
    ("bet365",         "Bet365",             "uk", 0.050, "https://www.bet365.com/"),
    ("betfair_sb_uk",  "Betfair Sportsbook", "uk", 0.050, "https://www.betfair.com/sport"),
    ("betway",         "Betway",             "uk", 0.050, "https://www.betway.com/"),
    ("sport888",       "888sport",           "uk", 0.055, "https://www.888sport.com/"),
    ("pinnacle",       "Pinnacle",           "eu", 0.025, "https://www.pinnacle.com/"),
    ("betsson",        "Betsson",            "eu", 0.050, "https://www.betsson.com/"),
    ("marathonbet",    "Marathon Bet",       "eu", 0.045, "https://www.marathonbet.com/"),
    ("onexbet",        "1xBet",              "eu", 0.030, "https://1xbet.com/"),
]
US_BOOKS = {key for key, _, region, _, _ in BOOKS if region == "us"}

# =============================================================================
# Sports and events
# =============================================================================

SPORTS = [
    {"key": "basketball_nba", "group": "Basketball", "title": "NBA",
     "description": "US Basketball", "active": True, "has_outrights": False},
    {"key": "soccer_epl", "group": "Soccer", "title": "EPL",
     "description": "English Premier League", "active": True, "has_outrights": False},
    {"key": "soccer_brazil_campeonato", "group": "Soccer", "title": "Brazil Série A",
     "description": "Brasileirão Série A", "active": True, "has_outrights": False},
    {"key": "tennis_atp_paris", "group": "Tennis", "title": "ATP Paris Masters",
     "description": "Men's Singles", "active": True, "has_outrights": False},
]

# Per-sport pricing behaviour:
#   draw         → 3-way moneyline
#   spread_step  → how far a book's line may differ from the fair line
#   spread_k     → probability shift per point of spread
#   total_k      → probability shift per point of total
#   us_books     → whether US books list this sport
SPORT_PROFILE = {
    "basketball_nba":           dict(draw=False, spread_step=0.5,  spread_k=0.030, total_k=0.020, us_books=True),
    "soccer_epl":               dict(draw=True,  spread_step=0.25, spread_k=0.120, total_k=0.110, us_books=True),
    "soccer_brazil_campeonato": dict(draw=True,  spread_step=0.25, spread_k=0.120, total_k=0.110, us_books=False),
    "tennis_atp_paris":         dict(draw=False, spread_step=0.5,  spread_k=0.035, total_k=0.030, us_books=True),
}

# (away, home, probabilities [home, (draw,) away], hours until start,
#  fair home spread, fair total). Negative hours = already live.
EVENTS = {
    "basketball_nba": [
        ("Golden State Warriors", "Boston Celtics",        [0.64, 0.36],  3,   -5.5, 226.5),
        ("Denver Nuggets",        "Los Angeles Lakers",    [0.45, 0.55],  6,    1.5, 231.5),
        ("Miami Heat",            "New York Knicks",       [0.58, 0.42], 26,   -3.5, 214.5),
        ("Phoenix Suns",          "Dallas Mavericks",      [0.55, 0.45], 28,   -2.5, 229.5),
        ("Milwaukee Bucks",       "Philadelphia 76ers",    [0.47, 0.53], 50,    1.0, 221.5),
        ("Oklahoma City Thunder", "Minnesota Timberwolves", [0.42, 0.58], 52,   2.5, 218.5),
        ("Sacramento Kings",      "Chicago Bulls",         [0.52, 0.48], -0.6, -1.5, 232.5),
        ("Cleveland Cavaliers",   "Orlando Magic",         [0.40, 0.60], 74,    3.5, 210.5),
    ],
    "soccer_epl": [
        ("Chelsea",           "Arsenal",          [0.48, 0.27, 0.25], 20, -0.5, 2.5),
        ("Manchester United", "Liverpool",        [0.62, 0.21, 0.17], 22, -1.0, 3.0),
        ("Tottenham Hotspur", "Manchester City",  [0.66, 0.19, 0.15], 45, -1.5, 3.5),
        ("Aston Villa",       "Newcastle United", [0.44, 0.27, 0.29], 46, -0.5, 2.5),
        ("Brighton",          "West Ham",         [0.38, 0.27, 0.35], 68,  0.0, 2.5),
        ("Everton",           "Brentford",        [0.42, 0.28, 0.30], 70, -0.5, 2.5),
    ],
    "soccer_brazil_campeonato": [
        ("Palmeiras",     "Flamengo",         [0.47, 0.28, 0.25], 30, -0.5, 2.5),
        ("Corinthians",   "São Paulo",        [0.43, 0.30, 0.27], 31, -0.5, 2.5),
        ("Grêmio",        "Internacional",    [0.45, 0.29, 0.26], 54, -0.5, 2.5),
        ("Botafogo",      "Fluminense",       [0.36, 0.29, 0.35], 55,  0.0, 2.5),
        ("Vasco da Gama", "Atlético Mineiro", [0.50, 0.27, 0.23], 78, -0.5, 2.5),
        ("Santos",        "Cruzeiro",         [0.46, 0.29, 0.25], 79, -0.5, 2.0),
    ],
    "tennis_atp_paris": [
        ("Carlos Alcaraz",    "Jannik Sinner",  [0.52, 0.48], 4,  -1.5, 22.5),
        ("Alexander Zverev",  "Novak Djokovic", [0.60, 0.40], 8,  -2.5, 23.5),
        ("Daniil Medvedev",   "Taylor Fritz",   [0.47, 0.53], 27,  0.5, 22.5),
        ("Holger Rune",       "Casper Ruud",    [0.50, 0.50], 31, -0.5, 23.5),
    ],
}

# =============================================================================
# Planted opportunities
# =============================================================================
# kind="arb": the listed books get prices whose implied probabilities sum to
#             `target` (below 1.0 = guaranteed profit) on the fair line.
# kind="ev":  one soft-book price beats Pinnacle's fair price without creating
#             an arbitrage. `edge` is the target expected value.
# `expect_books` is what the analyzer must report when ALL books are included.

PLANTS = [
    dict(sport="basketball_nba", home="Los Angeles Lakers", market="h2h", kind="arb",
         target=0.985, books={"home": "betsson", "away": "bet365"},
         note="Moneyline arb between two Brazil-accessible books"),
    dict(sport="basketball_nba", home="New York Knicks", market="totals", kind="arb",
         target=0.980, books={"over": "betfair_sb_uk", "under": "sport888"},
         note="Totals arb on one line while other books post different lines"),
    dict(sport="basketball_nba", home="Dallas Mavericks", market="h2h", kind="arb",
         target=0.988, books={"home": "draftkings", "away": "fanduel"},
         note="US-only arb, visible with the USA / Anywhere filters"),
    dict(sport="basketball_nba", home="Philadelphia 76ers", market="h2h", kind="arb",
         target=0.890, books={"away": "onexbet"}, phantom=True,
         note="'Too good to be true' 1xBet price, hidden by the reliability filter"),
    dict(sport="soccer_epl", home="Arsenal", market="h2h", kind="arb",
         target=0.982, books={"home": "betway", "draw": "marathonbet", "away": "pinnacle"},
         note="3-way soccer arb across three books"),
    dict(sport="soccer_brazil_campeonato", home="Flamengo", market="h2h", kind="arb",
         target=0.992, books={"home": "betsson", "draw": "bet365", "away": "betway"},
         note="Brasileirão 3-way arb"),
    dict(sport="soccer_brazil_campeonato", home="São Paulo", market="h2h", kind="ev",
         edge=0.035, books={"home": "betway"},
         note="+EV price vs Pinnacle that is not an arbitrage"),
]

# =============================================================================
# Pricing helpers
# =============================================================================


def to_american(decimal_odds: float) -> int:
    """Round to a realistic 2-decimal price, then express it in American odds."""
    return decimal_to_american(round(decimal_odds, 2))


def price_outcomes(probs: list[float], margin: float, rng: random.Random) -> list[int]:
    """Price a market from fair probabilities plus noise plus the book's margin."""
    noisy = [max(0.02, p + rng.gauss(0, NOISE_SD)) for p in probs]
    total = sum(noisy)
    return [to_american(1 / ((x / total) * (1 + margin))) for x in noisy]


def clamp(p: float) -> float:
    return min(max(p, 0.05), 0.95)


def build_market(market: str, event: dict, book: tuple, rng: random.Random,
                 pinned: bool) -> dict:
    """Price one market for one bookmaker. `pinned` forces the fair line."""
    key, _, _, margin, _ = book
    profile = SPORT_PROFILE[event["sport_key"]]
    home, away = event["home_team"], event["away_team"]

    if market == "h2h":
        names = [home, "Draw", away] if profile["draw"] else [home, away]
        prices = price_outcomes(event["_probs"], margin, rng)
        return {"key": "h2h", "outcomes": [{"name": n, "price": p} for n, p in zip(names, prices)]}

    step = profile["spread_step"]
    shift = 0.0 if pinned else rng.choice([0, 0, 0, -step, step])

    if market == "spreads":
        line = event["_spread"] + shift
        p_home = clamp(0.5 + shift * profile["spread_k"])
        prices = price_outcomes([p_home, 1 - p_home], margin, rng)
        return {"key": "spreads", "outcomes": [
            {"name": home, "price": prices[0], "point": line},
            {"name": away, "price": prices[1], "point": -line if line else 0.0},
        ]}

    line = event["_total"] + shift
    p_over = clamp(0.5 - shift * profile["total_k"])
    prices = price_outcomes([p_over, 1 - p_over], margin, rng)
    return {"key": "totals", "outcomes": [
        {"name": "Over", "price": prices[0], "point": line},
        {"name": "Under", "price": prices[1], "point": line},
    ]}


def books_for(sport_key: str) -> list[tuple]:
    if SPORT_PROFILE[sport_key]["us_books"]:
        return BOOKS
    return [b for b in BOOKS if b[0] not in US_BOOKS]


def find_market(event: dict, book_key: str, market: str) -> dict:
    book = next(b for b in event["bookmakers"] if b["key"] == book_key)
    return next(m for m in book["markets"] if m["key"] == market)


def outcome_role(event: dict, outcome: dict) -> str:
    """Map an outcome name to the role used in PLANTS (home/draw/away/over/under)."""
    name = outcome["name"]
    if name == event["home_team"]:
        return "home"
    if name == event["away_team"]:
        return "away"
    return name.lower()


def fair_role_probs(event: dict, market: str) -> dict:
    if market != "h2h":
        return {"home": 0.5, "away": 0.5, "over": 0.5, "under": 0.5}
    probs = event["_probs"]
    if len(probs) == 3:
        return {"home": probs[0], "draw": probs[1], "away": probs[2]}
    return {"home": probs[0], "away": probs[1]}


# =============================================================================
# Generation
# =============================================================================


def make_event(sport: dict, index: int, spec: tuple, rng: random.Random,
               pinned_books: set) -> dict:
    away, home, probs, hours, spread, total = spec
    event = {
        "id": f"demo_{sport['key']}_{index:02d}",
        "sport_key": sport["key"],
        "sport_title": sport["title"],
        "commence_in_hours": hours,
        "home_team": home,
        "away_team": away,
        "_probs": probs,
        "_spread": spread,
        "_total": total,
        "bookmakers": [],
    }
    for book in books_for(sport["key"]):
        key, title, region, _, link = book
        event["bookmakers"].append({
            "key": key, "title": title, "region": region, "link": link,
            "markets": [build_market(m, event, book, rng, key in pinned_books)
                        for m in ("h2h", "spreads", "totals")],
        })
    return event


def reprice(event: dict, market: str, rng: random.Random, pinned_books: set) -> None:
    for book_tuple in books_for(event["sport_key"]):
        book = next(b for b in event["bookmakers"] if b["key"] == book_tuple[0])
        idx = next(i for i, m in enumerate(book["markets"]) if m["key"] == market)
        book["markets"][idx] = build_market(market, event, book_tuple, rng,
                                            book_tuple[0] in pinned_books)


def analyse(event: dict, market: str, exclude: set = frozenset()) -> dict | None:
    stored = dict(event, bookmakers=[b for b in event["bookmakers"] if b["key"] not in exclude])
    (canonical,) = build_events([stored], ALL_MARKETS, ALL_REGIONS)
    return analyze_event(canonical, selected_market=market)


def apply_arb(event: dict, plant: dict) -> None:
    probs = fair_role_probs(event, plant["market"])
    for role, book_key in plant["books"].items():
        market = find_market(event, book_key, plant["market"])
        for outcome in market["outcomes"]:
            if outcome_role(event, outcome) == role:
                outcome["price"] = to_american(1 / (probs[role] * plant["target"]))


def apply_ev(event: dict, plant: dict) -> None:
    """Raise one price to the target edge, capped so no arbitrage appears."""
    (role, book_key), = plant["books"].items()
    probs = fair_role_probs(event, plant["market"])
    best = analyse(event, plant["market"])
    others = sum(1 / r["decimal_odds"] for r in best["results"]
                 if outcome_role(event, {"name": r["outcome"]}) != role)
    implied = max(probs[role] / (1 + plant["edge"]), 1.006 - others)

    market = find_market(event, book_key, plant["market"])
    for outcome in market["outcomes"]:
        if outcome_role(event, outcome) == role:
            outcome["price"] = to_american(1 / implied)


def generate() -> dict:
    rng = random.Random(SEED)
    plants_by_event = {}
    for plant in PLANTS:
        plants_by_event.setdefault((plant["sport"], plant["home"]), []).append(plant)

    output = {}
    for sport in SPORTS:
        events = []
        for index, spec in enumerate(EVENTS[sport["key"]], start=1):
            plants = plants_by_event.get((sport["key"], spec[1]), [])
            pinned = {bk for p in plants for bk in p["books"].values()}
            event = make_event(sport, index, spec, rng, pinned)

            planted_markets = {p["market"] for p in plants if p["kind"] == "arb"}
            for market in ("h2h", "spreads", "totals"):
                if market in planted_markets:
                    continue
                for _ in range(200):          # reprice until no accidental arb
                    result = analyse(event, market)
                    if result is None or not result["arbitrage"]:
                        break
                    reprice(event, market, rng, pinned)
                else:
                    raise RuntimeError(f"Could not remove accidental arb: {event['id']} {market}")

            for plant in plants:
                (apply_arb if plant["kind"] == "arb" else apply_ev)(event, plant)
            verify(event, plants)
            events.append(event)
        output[sport["key"]] = events
    return output


def verify(event: dict, plants: list) -> None:
    """Fail loudly if the analyzer does not see exactly what was planted."""
    planted_arbs = {p["market"]: p for p in plants if p["kind"] == "arb"}

    for market in ("h2h", "spreads", "totals"):
        result = analyse(event, market)
        plant = planted_arbs.get(market)
        if plant is None:
            assert result is None or not result["arbitrage"], f"Unplanned arb: {event['id']} {market}"
            continue

        assert result and result["arbitrage"], f"Planted arb not detected: {event['id']} {market}"
        titles = {b[0]: b[1] for b in BOOKS}
        found = {r["bookmaker"] for r in result["results"]}
        assert {titles[k] for k in plant["books"].values()} <= found, (event["id"], found)

        if plant.get("phantom"):
            without = analyse(event, market, exclude={"onexbet"})
            assert not without["arbitrage"], "Phantom arb must disappear without 1xBet"

    for plant in plants:
        if plant["kind"] == "ev":
            assert not analyse(event, plant["market"])["arbitrage"], "EV plant created an arb"


def write(output: dict) -> None:
    (DATA_DIR / "odds").mkdir(parents=True, exist_ok=True)
    with (DATA_DIR / "sports.json").open("w", encoding="utf-8") as fh:
        json.dump(SPORTS, fh, ensure_ascii=False, indent=2)
        fh.write("\n")

    for sport_key, events in output.items():
        public = [{k: v for k, v in e.items() if not k.startswith("_")} for e in events]
        with (DATA_DIR / "odds" / f"{sport_key}.json").open("w", encoding="utf-8") as fh:
            json.dump(public, fh, ensure_ascii=False, indent=1)
            fh.write("\n")


def main() -> None:
    output = generate()
    write(output)
    total = sum(len(v) for v in output.values())
    print(f"Wrote {total} events across {len(output)} sports to {DATA_DIR}")
    for plant in PLANTS:
        print(f"  planted {plant['kind']:<3} {plant['sport']:<26} {plant['home']:<20} "
              f"{plant['market']:<7} {plant['note']}")


if __name__ == "__main__":
    main()
