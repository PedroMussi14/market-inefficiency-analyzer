"""Database read/write helpers.

Keeps SQL out of the scraper, scheduler, and API layers.
"""

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from . import models, normalizer
from .scrapers.base import ScrapedEvent


# =============================================================================
# Reference data (sports, bookmakers)
# =============================================================================

async def upsert_sport(session: AsyncSession, key: str, title: str, group: str) -> models.Sport:
    """Get-or-create a Sport row."""
    res = await session.execute(select(models.Sport).where(models.Sport.key == key))
    sport = res.scalar_one_or_none()
    if sport is None:
        sport = models.Sport(key=key, title=title, group=group, active=True)
        session.add(sport)
        await session.flush()
    return sport


async def upsert_bookmaker(session: AsyncSession, key: str, title: str,
                           homepage: str | None = None) -> models.Bookmaker:
    """Get-or-create a Bookmaker row."""
    res = await session.execute(select(models.Bookmaker).where(models.Bookmaker.key == key))
    book = res.scalar_one_or_none()
    if book is None:
        book = models.Bookmaker(key=key, title=title, homepage=homepage, active=True)
        session.add(book)
        await session.flush()
    return book


# =============================================================================
# Persistence — called by the scheduler after each scrape pass
# =============================================================================

async def persist_scraped_events(session: AsyncSession, scraper_title: str,
                                 events: list[ScrapedEvent]) -> int:
    """Write a batch of scraped events (and their odds) into the DB.

    Returns the number of events successfully persisted.
    """
    if not events:
        return 0

    # Resolve the bookmaker once
    book = await upsert_bookmaker(session,
                                  key=events[0].bookmaker_key,
                                  title=scraper_title)

    persisted = 0
    for ev in events:
        try:
            await _persist_one_event(session, book, ev)
            persisted += 1
        except Exception:
            # Swallow per-event errors so one bad row doesn't kill the batch
            await session.rollback()
            continue

    await session.commit()
    return persisted


async def _persist_one_event(session: AsyncSession, book: models.Bookmaker,
                             scraped: ScrapedEvent) -> None:
    sport = await upsert_sport(session, scraped.sport_key,
                               title=scraped.sport_key.replace("_", " ").title(),
                               group=_sport_group(scraped.sport_key))

    canonical_key = normalizer.canonical_event_key(
        scraped.home_team, scraped.away_team, scraped.commence_time,
    )

    # Get-or-create the event row
    res = await session.execute(select(models.Event).where(models.Event.canonical_key == canonical_key))
    event = res.scalar_one_or_none()
    if event is None:
        event = models.Event(
            sport_id      = sport.id,
            home_team     = scraped.home_team,
            away_team     = scraped.away_team,
            commence_time = scraped.commence_time,
            canonical_key = canonical_key,
        )
        session.add(event)
        await session.flush()

    now = datetime.now(timezone.utc)

    # Upsert outcomes + write history snapshot
    for market in scraped.markets:
        for outcome in market.outcomes:
            price_american = decimal_to_american(outcome.price_decimal)

            # Upsert outcome
            stmt = (
                pg_insert(models.Outcome.__table__)
                .values(
                    event_id      = event.id,
                    bookmaker_id  = book.id,
                    market        = market.key,
                    outcome_name  = outcome.name,
                    point         = outcome.point,
                    price_decimal = outcome.price_decimal,
                    price_american= price_american,
                    deep_link     = outcome.deep_link,
                    last_update   = now,
                )
                .on_conflict_do_update(
                    constraint="uq_outcome_unique",
                    set_={
                        "price_decimal":  outcome.price_decimal,
                        "price_american": price_american,
                        "deep_link":      outcome.deep_link,
                        "last_update":    now,
                    },
                )
            )
            await session.execute(stmt)

            # Append history
            session.add(models.OddsSnapshot(
                event_id      = event.id,
                bookmaker_id  = book.id,
                market        = market.key,
                outcome_name  = outcome.name,
                point         = outcome.point,
                price_decimal = outcome.price_decimal,
                captured_at   = now,
            ))


# =============================================================================
# Read helpers — used by the API layer
# =============================================================================

async def list_sports(session: AsyncSession) -> list[models.Sport]:
    res = await session.execute(select(models.Sport).where(models.Sport.active.is_(True)))
    return list(res.scalars())


async def list_events_with_odds(session: AsyncSession, sport_key: str) -> list[models.Event]:
    """Return events for one sport with eager-loaded outcomes + bookmakers + sport.

    Without `selectinload(Event.sport)`, the API layer's `ev.sport.title`
    triggers a lazy load outside an active session, which raises
    `sqlalchemy.exc.MissingGreenlet` and turns the response into a 500.
    """
    from sqlalchemy.orm import selectinload

    stmt = (
        select(models.Event)
        .join(models.Sport)
        .where(models.Sport.key == sport_key)
        .where(models.Event.commence_time >= datetime.now(timezone.utc))
        .options(
            selectinload(models.Event.sport),
            selectinload(models.Event.outcomes).selectinload(models.Outcome.bookmaker),
        )
        .order_by(models.Event.commence_time)
    )
    res = await session.execute(stmt)
    return list(res.scalars())


# =============================================================================
# Helpers
# =============================================================================

def decimal_to_american(decimal_odds: float) -> int:
    """Inverse of arbitrage.american_to_decimal — round to nearest integer."""
    if decimal_odds >= 2.0:
        return round((decimal_odds - 1) * 100)
    return round(-100 / (decimal_odds - 1))


def _sport_group(sport_key: str) -> str:
    if "soccer" in sport_key or "football" in sport_key:
        return "Soccer"
    if "basketball" in sport_key:
        return "Basketball"
    if "tennis" in sport_key:
        return "Tennis"
    return "Other"
