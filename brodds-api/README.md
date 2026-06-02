# BrOdds API

Self-hosted odds aggregator for the Brazilian sports betting market.

Scrapes odds from Brazilian sportsbooks (Betano, KTO, Pixbet, Sportingbet, etc.)
and exposes them through a FastAPI service that's wire-compatible with [The
Odds API v4](https://the-odds-api.com/) format. Plug it into BetScan as a
fourth provider and get Brazilian-native books alongside your existing data.

> **Status: Foundation / Path C scaffolding.**
> The architecture, database, scraper framework, FastAPI service, scheduler,
> and one calibration-ready Betano scraper are in place and runnable. Concrete
> Betano parsing logic is template-quality and **must be calibrated against
> live network traffic** before it returns real odds. See
> [Calibrating a scraper](#calibrating-a-scraper) below.

---

## Table of contents

- [Architecture](#architecture)
- [Quick start (local)](#quick-start-local)
- [Project layout](#project-layout)
- [Calibrating a scraper](#calibrating-a-scraper)
- [Adding a new bookmaker](#adding-a-new-bookmaker)
- [Production deployment](#production-deployment)
- [Legal considerations (Brazil)](#legal-considerations-brazil)
- [Roadmap to true production-grade](#roadmap-to-true-production-grade)

---

## Architecture

```
┌─────────────────────────┐
│  Scheduler (APScheduler)│   runs every SCRAPE_INTERVAL_SECONDS
└────────┬────────────────┘
         │ fan-out
         ▼
┌─────────────────────────┐
│  Scrapers (per book)    │   Betano · KTO · Pixbet · Sportingbet · ...
│  - rate-limited          │
│  - proxy-aware           │
│  - retry w/ backoff      │
│  - Playwright fallback   │
└────────┬────────────────┘
         │ ScrapedEvent[]
         ▼
┌─────────────────────────┐
│   Normalizer             │   unify team names across books (Flamengo /
│   - alias table          │   C.R. Flamengo / Flamengo RJ → "flamengo")
│   - rapidfuzz fallback   │
└────────┬────────────────┘
         │ canonical_event_key
         ▼
┌─────────────────────────┐
│   PostgreSQL             │   events · outcomes (current) · odds_snapshots (history)
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│   FastAPI service        │   GET /v4/sports
│   (Odds API v4 format)   │   GET /v4/sports/{sport_key}/odds
└────────┬────────────────┘
         │ HTTP
         ▼
┌─────────────────────────┐
│   BetScan                │   plugs in via providers.py → BroddsLocalProvider
└─────────────────────────┘
```

## Quick start (local)

You need Docker and Docker Compose installed.

```bash
cd brodds-api
cp .env.example .env
# Edit .env — at minimum, set BRODDS_API_KEY to a random string
docker compose up -d
```

That brings up Postgres, Redis, the API, and the scheduler. After the first
scrape cycle (~90s by default) you should see data:

```bash
curl -H "X-API-Key: <BRODDS_API_KEY>" http://localhost:8000/v4/sports
curl -H "X-API-Key: <BRODDS_API_KEY>" http://localhost:8000/v4/sports/soccer_brazil_serie_a/odds
```

Tail the scheduler logs to watch scrapes happen:

```bash
docker compose logs -f scheduler
```

### Wire it into BetScan

Add to your top-level `.env` (the BetScan one, not `brodds-api/.env`):

```
BRODDS_LOCAL_URL=http://localhost:8000
BRODDS_LOCAL_KEY=<the same value you put in BRODDS_API_KEY>
```

Restart Streamlit. The sidebar's "Data provider" dropdown now shows
`BrOdds Local 🇧🇷`. Switch to it and your arbitrage detector runs against
your own scraped data.

## Project layout

```
brodds-api/
├── docker-compose.yml          # Postgres + Redis + API + scheduler
├── Dockerfile                  # Python 3.11 + Playwright Chromium
├── requirements.txt
├── .env.example                # template — copy to .env
└── src/
    ├── config.py               # pydantic-settings (env vars)
    ├── database.py             # async SQLAlchemy engine
    ├── models.py               # ORM (Sport, Bookmaker, Event, Outcome, OddsSnapshot)
    ├── schemas.py              # Pydantic models matching Odds API v4
    ├── normalizer.py           # team-name unification across books
    ├── repository.py           # DB read/write helpers
    ├── scrapers/
    │   ├── base.py             # BaseScraper: rate limit, proxy, retries, browser
    │   ├── betano.py           # concrete Betano scraper (needs calibration)
    │   └── __init__.py         # SCRAPERS registry — add new ones here
    ├── api/
    │   └── main.py             # FastAPI service
    └── scheduler/
        └── jobs.py             # APScheduler runner
```

## Calibrating a scraper

The Betano scraper ships with a **template** — it knows about rate limits,
proxies, browser fallback, and the canonical output shape, but the actual
endpoint paths and JSON parsing are best-effort guesses based on common
patterns. To make it return real odds:

1. **Find the real endpoints.**
   Open <https://www.betano.bet.br> in Chrome with DevTools open. Click on
   "Brasileirão" or any league. Watch the **Network → XHR** tab. Note which
   JSON URLs fire when the odds load.

2. **Update `src/scrapers/betano.py`:**
   - `SPORTS_PATH` and `EVENTS_PATH` — replace with the real paths.
   - `SPORT_ID_TO_KEY` — fill in Betano's actual sport IDs.
   - `_parse_event()` — adjust to match the real JSON keys
     (e.g. `homeTeam` might actually be `home.name`).
   - `_parse_market()` — adjust the `match` arm for whatever Betano's
     market type field actually contains.

3. **Test in isolation:**
   ```bash
   docker compose run --rm scheduler python -c "
   import asyncio
   from src.scrapers.betano import BetanoScraper
   events = asyncio.run(BetanoScraper().scrape())
   print(f'{len(events)} events scraped')
   for e in events[:3]:
       print(f'  {e.home_team} vs {e.away_team} — {len(e.markets)} markets')
   "
   ```

4. **Once it works, the rest is automatic** — the scheduler will pick up the
   new data and the API will start serving it.

## Adding a new bookmaker

1. Create `src/scrapers/<name>.py`:
   ```python
   from .base import BaseScraper, ScrapedEvent

   class KtoScraper(BaseScraper):
       name = "kto"
       title = "KTO"
       base_url = "https://www.kto.com"
       needs_browser = True
       rate_limit_per_minute = 10

       async def scrape(self) -> list[ScrapedEvent]:
           # Your fetch + parse logic here
           ...
   ```
2. Register it in `src/scrapers/__init__.py` by adding it to the `SCRAPERS` list.
3. Restart the scheduler container. Done.

The base class handles everything else — rate limiting, proxy rotation, retries,
user-agent randomization, and (optionally) headless browser rendering.

## Production deployment

What's in the box right now is enough for **single-machine personal use**.
For a real production deployment, you'll want:

| Concern | Local default | Production target |
|---|---|---|
| Postgres | Docker container | Managed (Neon, Supabase, RDS) |
| Redis | Docker container | Managed (Upstash, ElastiCache) |
| Migrations | `Base.metadata.create_all` on boot | Alembic migrations in CI |
| Secrets | `.env` file | Cloud secrets manager (AWS SSM, Doppler) |
| Proxies | Optional | **Required** — rotating residential pool |
| Monitoring | structlog → stdout | Sentry + Datadog/Grafana |
| Anti-bot | Static UA pool | UA rotation + stealth Playwright + CAPTCHA solver |
| API hosting | uvicorn dev server | Fly.io / Railway / ECS / k8s with N replicas |
| Scheduler | One container | One pinned replica with leader election |
| Backups | None | Daily Postgres snapshots |
| Rate limits | None on the API itself | Per-key throttling (e.g. slowapi) |

Each row above is a checkpoint, not a one-line fix. Plan ~2-4 weeks of work
to harden everything for real production traffic.

## Legal considerations (Brazil)

Talk to a Brazilian lawyer before commercializing this. Quick high-level read:

- ✅ **Sports betting is legal in Brazil** since Lei 14.790/2023, regulated
  through Portaria SPA/MF starting 2025.
- ✅ **Aggregating publicly-displayed odds is generally permitted** in most
  jurisdictions — odds are *facts*, not copyrightable content.
- ⚠️ **Sportsbooks' Terms of Service usually forbid scraping.** Civil
  liability is plausible (breach of contract). Criminal exposure is unlikely
  for personal/non-commercial use.
- ⚠️ **Commercial use is materially more risky.** Selling API access raises
  questions around competition law, advertising law, and the licensing
  framework for betting operators. Get proper legal review before charging
  for access.
- ✅ **Personal-use risk profile is low.** If you use scraped odds yourself
  to find arbitrage opportunities, you're broadly in the same territory as
  any odds-comparison enthusiast.

## Roadmap to true production-grade

The below is what would take this from "good foundation" to "production
service you'd put your name on" — roughly the work that's still ahead.

### Phase 1 — Calibrate + expand (2-4 weeks)
- [ ] Calibrate Betano scraper against live traffic (see [Calibrating a scraper](#calibrating-a-scraper))
- [ ] Add KTO, Pixbet, Sportingbet, EstrelaBet scrapers
- [ ] Replace `Base.metadata.create_all` with Alembic migrations
- [ ] Add unit tests for the normalizer and at least one scraper

### Phase 2 — Reliability (2-3 weeks)
- [ ] Sentry / OpenTelemetry integration
- [ ] Per-scraper success/failure metrics + alerts
- [ ] Dead-letter queue for failed scrapes (Redis stream)
- [ ] Stale-data detection: alert when a book hasn't returned data in N minutes
- [ ] Rate-limit middleware on the public API (slowapi, per-X-API-Key)

### Phase 3 — Anti-detection (1-2 weeks)
- [ ] BrightData/Oxylabs residential proxy integration with rotation policy
- [ ] Playwright stealth plugin
- [ ] Captcha solver (2Captcha) integration for sites that gate odds pages
- [ ] Request fingerprint randomization (TLS, header order, viewport)

### Phase 4 — Scale (2-4 weeks)
- [ ] Move to managed Postgres + read replicas
- [ ] Redis cache layer in front of `/v4/sports/{sport}/odds`
- [ ] CDN in front of static responses
- [ ] Multi-region deployment (BR + US for latency)
- [ ] Per-customer API keys + usage tracking + billing hooks

Each phase is independently valuable. Walk it incrementally — most
early-stage odds aggregators get stuck trying to do everything at once.
