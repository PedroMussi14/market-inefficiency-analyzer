"""FastAPI service exposing scraped odds in The Odds API v4 format.

Endpoints:
    GET /                                    health check
    GET /v4/sports                           list of available sports
    GET /v4/sports/{sport_key}/odds          events + bookmakers + odds for a sport

Auth: every request must include `X-API-Key: <BRODDS_API_KEY>` header.
"""

import logging
from collections import defaultdict
from datetime import datetime, timezone

import structlog
from fastapi import Depends, FastAPI, Header, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from .. import models, repository, schemas
from ..config import settings
from ..database import get_session


# =============================================================================
# Logging setup — structured JSON logs in production, plain in dev
# =============================================================================

logging.basicConfig(level=settings.log_level)
structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
)
log = structlog.get_logger("api")


# =============================================================================
# App
# =============================================================================

app = FastAPI(
    title="BrOdds API",
    description="Brazilian sportsbook odds aggregator. Compatible with The Odds API v4 format.",
    version="0.1.0",
)


# =============================================================================
# Auth dependency
# =============================================================================

async def require_api_key(x_api_key: str | None = Header(None, alias="X-API-Key")):
    """Reject requests without a valid API key."""
    if x_api_key != settings.api_key:
        raise HTTPException(status_code=401, detail="Invalid or missing X-API-Key header")


# =============================================================================
# Routes
# =============================================================================

@app.get("/", response_model=schemas.HealthOut)
async def health(session: AsyncSession = Depends(get_session)) -> schemas.HealthOut:
    """Public health check — no auth required so external monitors can hit it."""
    book_count = (await session.execute(
        select(func.count()).select_from(models.Bookmaker).where(models.Bookmaker.active.is_(True))
    )).scalar() or 0

    event_count = (await session.execute(
        select(func.count()).select_from(models.Event)
    )).scalar() or 0

    return schemas.HealthOut(
        bookmakers_active=int(book_count),
        events_total=int(event_count),
    )


@app.get("/v4/sports", response_model=list[schemas.SportOut],
         dependencies=[Depends(require_api_key)])
async def list_sports(session: AsyncSession = Depends(get_session)) -> list[schemas.SportOut]:
    """Return all sports we currently have odds for."""
    rows = await repository.list_sports(session)
    return [
        schemas.SportOut(key=s.key, title=s.title, group=s.group, active=s.active)
        for s in rows
    ]


@app.get("/v4/sports/{sport_key}/odds", response_model=list[schemas.EventOut],
         dependencies=[Depends(require_api_key)])
async def get_odds(
    sport_key: str,
    regions: str = Query("br", description="Ignored — kept for Odds API compatibility."),
    markets: str = Query("h2h", description="Comma-separated markets to include."),
    odds_format: str = Query("american", alias="oddsFormat"),
    session: AsyncSession = Depends(get_session),
) -> list[schemas.EventOut]:
    """Return all upcoming events for a sport, with all bookmakers and markets.

    Response shape matches The Odds API v4 exactly so any client built for that
    API works against this one without code changes.
    """
    requested_markets = {m.strip() for m in markets.split(",") if m.strip()}

    events = await repository.list_events_with_odds(session, sport_key)
    if not events:
        return []

    out: list[schemas.EventOut] = []
    for ev in events:
        # Group outcomes by (bookmaker, market)
        grouped: dict[tuple[int, str], list[models.Outcome]] = defaultdict(list)
        for o in ev.outcomes:
            if o.market not in requested_markets:
                continue
            grouped[(o.bookmaker_id, o.market)].append(o)

        # Build bookmaker → markets nested structure
        by_book: dict[int, list[schemas.MarketOut]] = defaultdict(list)
        book_titles: dict[int, str] = {}
        book_keys:   dict[int, str] = {}
        book_updates: dict[int, datetime] = {}

        for (bid, market_key), outcomes in grouped.items():
            book_titles[bid] = outcomes[0].bookmaker.title
            book_keys[bid]   = outcomes[0].bookmaker.key
            most_recent      = max(o.last_update for o in outcomes)
            book_updates[bid] = max(book_updates.get(bid, most_recent), most_recent)

            by_book[bid].append(schemas.MarketOut(
                key         = market_key,
                last_update = most_recent,
                outcomes    = [
                    schemas.OutcomeOut(
                        name  = o.outcome_name,
                        price = o.price_american,
                        point = o.point,
                        link  = o.deep_link,
                    )
                    for o in outcomes
                ],
            ))

        bookmakers = [
            schemas.BookmakerOut(
                key         = book_keys[bid],
                title       = book_titles[bid],
                last_update = book_updates[bid],
                markets     = book_markets,
            )
            for bid, book_markets in by_book.items()
        ]

        # Defensive: if the sport relationship somehow wasn't eagerly loaded,
        # derive a title from sport_key rather than triggering a lazy-load
        # crash (which would 500 the whole request).
        sport_title = ev.sport.title if ev.sport else sport_key.replace("_", " ").title()

        out.append(schemas.EventOut(
            id            = f"brodds_{ev.id}",
            sport_key     = sport_key,
            sport_title   = sport_title,
            commence_time = ev.commence_time,
            home_team     = ev.home_team,
            away_team     = ev.away_team,
            bookmakers    = bookmakers,
        ))

    return out


# =============================================================================
# Startup — create tables on first run (production should use alembic instead)
# =============================================================================

@app.on_event("startup")
async def on_startup() -> None:
    # NOTE: there is NO src/api/database.py — the engine lives at src/database.py.
    # The previous `from .database import engine` line was a typo that crashed
    # the API on startup with ModuleNotFoundError. Fixed: use the parent package.
    from ..database import Base, engine as db_engine
    async with db_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    log.info("api_started", db=settings.database_url.split("@")[-1])
