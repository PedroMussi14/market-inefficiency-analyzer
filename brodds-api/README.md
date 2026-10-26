# BrOdds API

A self-hosted odds service for **Brazilian sportsbooks**, built as a companion
to the [Market Inefficiency Analyzer](../README.md).

Commercial odds APIs cover international bookmakers but not Brazilian-native
ones such as Betano. BrOdds collects their published odds on a schedule, unifies
team names across books, stores current prices plus a full price history in
PostgreSQL, and serves everything through a FastAPI service that speaks the
**[The Odds API v4](https://the-odds-api.com/) format**. To the analyzer it is
just another provider.

> **Status:** working end-to-end foundation with one bookmaker (Betano,
> Brasileirão Série A moneyline). More books and markets are on the roadmap.

---

## Architecture

```
┌──────────────────────────┐
│  Scheduler (APScheduler) │  one cycle on boot, then every SCRAPE_INTERVAL_SECONDS
└────────────┬─────────────┘
             │ runs every registered scraper concurrently, isolated from each other
             ▼
┌──────────────────────────┐
│  Scrapers                │  BaseScraper: rate limiting, retries with backoff,
│  (one class per book)    │  optional proxy, headless Chromium (Playwright)
└────────────┬─────────────┘
             │ ScrapedEvent[]  (canonical, decimal odds)
             ▼
┌──────────────────────────┐
│  Normaliser              │  "C.R. Flamengo" / "Flamengo RJ" → "flamengo"
│                          │  alias table + rapidfuzz fallback → canonical_event_key
└────────────┬─────────────┘
             ▼
┌──────────────────────────┐
│  PostgreSQL              │  events · outcomes (latest price) · odds_snapshots (history)
└────────────┬─────────────┘
             ▼
┌──────────────────────────┐
│  FastAPI                 │  GET /                              health (no auth)
│  (Odds API v4 format)    │  GET /v4/sports                     X-API-Key required
│                          │  GET /v4/sports/{sport_key}/odds    X-API-Key required
└────────────┬─────────────┘
             ▼
     Market Inefficiency Analyzer  (BroddsLocalProvider)
```

Design notes:

- **Same wire format as The Odds API:** clients built for it work unchanged.
- **Cross-book identity:** the same match listed as "Flamengo" and "C.R. Flamengo"
  must become one event, or prices from different books can never be compared.
  The normaliser builds a `canonical_event_key` from normalised team names and the
  match date.
- **Latest price + history:** `outcomes` holds the current price for fast reads;
  every scrape also appends to `odds_snapshots` for line-movement analysis.
- **Failure isolation:** one failing scraper does not stop the others, and one bad
  event is rolled back on its own (a database SAVEPOINT) without losing the batch.

## Quick start

Requires Docker and Docker Compose.

```bash
cd brodds-api
cp .env.example .env
# Set BRODDS_API_KEY to a random value:
#   python -c "import secrets; print(secrets.token_urlsafe(32))"
docker compose up -d
```

This starts PostgreSQL, Redis, the API (port 8000) and the scheduler. After the
first scrape cycle:

```bash
curl http://localhost:8000/
curl -H "X-API-Key: <BRODDS_API_KEY>" http://localhost:8000/v4/sports
curl -H "X-API-Key: <BRODDS_API_KEY>" http://localhost:8000/v4/sports/soccer_brazil_serie_a/odds
docker compose logs -f scheduler      # watch scrape cycles
```

### Connect it to the analyzer

In the **root** `.env` of the repository (not `brodds-api/.env`):

```
BRODDS_LOCAL_URL=http://localhost:8000
BRODDS_LOCAL_KEY=<same value as BRODDS_API_KEY>
```

Restart the dashboard and choose **BrOdds Local** as the data provider.

## Configuration

`brodds-api/.env` (see `.env.example`):

| Variable | Default | Purpose |
|---|---|---|
| `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` | `brodds` / placeholder / `brodds` | Database credentials used by Docker Compose |
| `BRODDS_API_KEY` | none | Key clients must send in the `X-API-Key` header |
| `SCRAPE_INTERVAL_SECONDS` | `90` | Time between scrape cycles |
| `PROXY_URL` | empty | Optional outbound HTTP/SOCKS proxy |
| `LOG_LEVEL` | `INFO` | Structured JSON logging level |

## Project layout

```
brodds-api/
├── docker-compose.yml      PostgreSQL + Redis + API + scheduler
├── Dockerfile              Python 3.11 + Playwright Chromium
├── requirements.txt        pinned dependencies (incl. test tools)
├── src/
│   ├── config.py           settings from environment (pydantic-settings)
│   ├── database.py         async SQLAlchemy engine + session
│   ├── models.py           Sport, Bookmaker, Event, Outcome, OddsSnapshot
│   ├── schemas.py          response models matching The Odds API v4
│   ├── normalizer.py       team-name unification across books
│   ├── repository.py       database reads and writes
│   ├── scrapers/
│   │   ├── base.py         BaseScraper and the canonical ScrapedEvent types
│   │   ├── betano.py       Betano scraper
│   │   └── __init__.py     SCRAPERS registry
│   ├── api/main.py         FastAPI application
│   └── scheduler/jobs.py   periodic scrape runner
└── tests/                  pytest suite
```

## How the Betano scraper works

`src/scrapers/betano.py`:

1. **Leagues** are listed in `LEAGUE_URLS`, which maps a sport key to the JSON
   endpoint Betano's own website uses for that league.
2. The page is loaded in headless Chromium (`needs_browser = True`), because the
   endpoint is not reachable with a plain HTTP client.
3. The JSON is walked recursively. Any object with `participants` and `markets`
   is treated as an event (`_looks_like_event`), which keeps the parser robust to
   layout changes.
4. `_parse_event` reads the match-result market (`type == "MRES"`) and maps
   `1 / X / 2` to home / Draw / away (`_map_outcome`). Soccer markets missing any
   of the three prices are rejected, because an incomplete market would show up
   downstream as a false arbitrage.
5. If nothing is extracted, a diagnostic log lists the JSON paths that look like
   events, to speed up re-calibration when the site changes.

To add a league, open the league page on betano.bet.br with the browser's
DevTools **Network** tab open. Find the JSON request matching the pattern in the
module docstring and add its path to `LEAGUE_URLS`.

## Adding a bookmaker

```python
# src/scrapers/kto.py
from .base import BaseScraper, ScrapedEvent

class KtoScraper(BaseScraper):
    name = "kto"
    title = "KTO"
    base_url = "https://www.kto.bet.br"
    rate_limit_per_minute = 10

    async def scrape(self) -> list[ScrapedEvent]:
        response = await self.fetch(f"{self.base_url}/…")   # retries + rate limit built in
        return [...]                                          # canonical ScrapedEvent objects
```

Register the class in `SCRAPERS` (`src/scrapers/__init__.py`). The scheduler,
database and API need no changes.

## Tests

```bash
cd brodds-api
pip install -r requirements.txt
pytest
```

The suite runs without PostgreSQL (an in-memory SQLite URL is used for imports)
and covers the scheduler configuration and the Betano parser. CI runs it on every
push against the pinned versions in `requirements.txt`.

## Responsible use

- Collect only publicly displayed odds, at a low request rate. The defaults are
  one request per league per cycle, with a 10 requests/minute cap per scraper.
- Bookmakers' terms of service often restrict automated access. Review them, and
  local law, before running this anywhere beyond personal research.
- Sports betting in Brazil is regulated under Lei 14.790/2023. This project does
  not place bets.

## Roadmap

- [ ] More bookmakers (KTO, Sportingbet, EstrelaBet) and markets (totals, handicaps)
- [ ] Alembic migrations instead of `create_all` on startup
- [ ] Use Redis (already provisioned) as a response cache for `/v4/sports/{sport}/odds`
- [ ] Stale-data alerts when a bookmaker stops returning prices
- [ ] Per-key rate limiting on the public API
- [ ] Metrics per scraper (success rate, latency, events per cycle)
