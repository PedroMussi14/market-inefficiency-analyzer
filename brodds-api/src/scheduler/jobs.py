"""Periodic scrape runner.

Runs as its own container (`scheduler` in docker-compose.yml). Every
SCRAPE_INTERVAL_SECONDS, it:

  1. Iterates every registered scraper (src/scrapers/__init__.py SCRAPERS list)
  2. Calls scraper.scrape() concurrently (with isolation — one bad scraper
     doesn't break the others)
  3. Persists the results into Postgres
  4. Logs counts + errors

Run locally without Docker:
    DATABASE_URL=... REDIS_URL=... python -m src.scheduler.jobs

In production, run exactly ONE replica of this container — the scrape jobs
are not designed to be horizontally scaled (would just hammer bookmaker sites
and waste proxy bandwidth).
"""

import asyncio
import logging
import signal

import structlog
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from ..config import settings
from ..database import Base, SessionLocal, engine
from ..repository import persist_scraped_events
from ..scrapers import SCRAPERS
from ..scrapers.base import BaseScraper


logging.basicConfig(level=settings.log_level)
structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
)
log = structlog.get_logger("scheduler")


# =============================================================================
# Job
# =============================================================================

async def run_one_scraper(scraper_cls: type[BaseScraper]) -> None:
    """Run one scraper and persist its output. Errors are logged but not raised."""
    scraper = scraper_cls()
    try:
        events = await scraper.scrape()
    except Exception as e:
        log.error("scrape_crashed", scraper=scraper.name, error=str(e))
        return

    try:
        async with SessionLocal() as session:
            count = await persist_scraped_events(session, scraper.title, events)
        log.info("scrape_persisted", scraper=scraper.name, events=count)
    except Exception as e:
        log.error("persist_crashed", scraper=scraper.name, error=str(e))


async def run_all_scrapers() -> None:
    """Fan out to every registered scraper, then collect results."""
    log.info("scrape_cycle_start", scrapers=[c.name for c in SCRAPERS])
    await asyncio.gather(*(run_one_scraper(s) for s in SCRAPERS), return_exceptions=False)
    log.info("scrape_cycle_done")


# =============================================================================
# Main loop
# =============================================================================

async def _ensure_schema() -> None:
    """Create tables on first boot (mirrors what the API does)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def main() -> None:
    await _ensure_schema()

    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        run_all_scrapers,
        trigger="interval",
        seconds=settings.scrape_interval_seconds,
        max_instances=1,                # never overlap cycles
        coalesce=True,                  # drop missed runs instead of stacking them
        next_run_time=None,             # don't fire immediately — wait one interval
    )
    scheduler.start()
    log.info("scheduler_started", interval_seconds=settings.scrape_interval_seconds)

    # Trigger one cycle immediately so we have data on first boot
    await run_all_scrapers()

    # Block forever until SIGTERM/SIGINT
    stop = asyncio.Event()
    for sig in (signal.SIGINT, signal.SIGTERM):
        asyncio.get_event_loop().add_signal_handler(sig, stop.set)
    await stop.wait()
    scheduler.shutdown(wait=True)
    log.info("scheduler_stopped")


if __name__ == "__main__":
    asyncio.run(main())
