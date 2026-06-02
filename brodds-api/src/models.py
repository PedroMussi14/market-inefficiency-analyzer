"""ORM models for the BrOdds aggregator.

Schema design notes:
  - `Sport` and `Bookmaker` are static reference tables.
  - `Event` represents one match — we store one row per match across all books.
  - `Outcome` is the latest known price for one (event, bookmaker, market, outcome_name).
  - `OddsSnapshot` is a write-once history table — every scrape inserts new rows
    so we can analyse line movement and detect when books update prices.

Design tradeoff: we deliberately do NOT update Outcome rows in-place — instead,
we upsert them and write the previous value to OddsSnapshot. This makes the API
fast (read-current-only) while keeping a full audit trail for backtesting.
"""

from datetime import datetime

from sqlalchemy import (
    Boolean, DateTime, Float, ForeignKey, Index, Integer, String, UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class Sport(Base):
    __tablename__ = "sports"

    id:          Mapped[int] = mapped_column(Integer, primary_key=True)
    key:         Mapped[str] = mapped_column(String(64), unique=True, index=True)
    title:       Mapped[str] = mapped_column(String(128))
    group:       Mapped[str] = mapped_column(String(64))   # e.g. "Soccer", "Basketball"
    active:      Mapped[bool] = mapped_column(Boolean, default=True)

    events: Mapped[list["Event"]] = relationship(back_populates="sport")


class Bookmaker(Base):
    __tablename__ = "bookmakers"

    id:        Mapped[int]  = mapped_column(Integer, primary_key=True)
    key:       Mapped[str]  = mapped_column(String(64), unique=True, index=True)
    title:     Mapped[str]  = mapped_column(String(128))
    homepage:  Mapped[str | None] = mapped_column(String(255))
    active:    Mapped[bool] = mapped_column(Boolean, default=True)


class Event(Base):
    """One sporting match. Stable across bookmaker variations of team names."""
    __tablename__ = "events"

    id:             Mapped[int]      = mapped_column(Integer, primary_key=True)
    sport_id:       Mapped[int]      = mapped_column(ForeignKey("sports.id"))
    home_team:      Mapped[str]      = mapped_column(String(128))
    away_team:      Mapped[str]      = mapped_column(String(128))
    commence_time:  Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    canonical_key:  Mapped[str]      = mapped_column(String(255), unique=True, index=True)

    sport:    Mapped[Sport]            = relationship(back_populates="events")
    outcomes: Mapped[list["Outcome"]]  = relationship(back_populates="event", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_events_sport_commence", "sport_id", "commence_time"),
    )


class Outcome(Base):
    """The current price for one (event, bookmaker, market, outcome) combination."""
    __tablename__ = "outcomes"

    id:           Mapped[int]      = mapped_column(Integer, primary_key=True)
    event_id:     Mapped[int]      = mapped_column(ForeignKey("events.id", ondelete="CASCADE"), index=True)
    bookmaker_id: Mapped[int]      = mapped_column(ForeignKey("bookmakers.id"), index=True)
    market:       Mapped[str]      = mapped_column(String(32))      # h2h | spreads | totals
    outcome_name: Mapped[str]      = mapped_column(String(128))     # e.g. "Flamengo", "Over"
    point:        Mapped[float | None] = mapped_column(Float)        # for spreads/totals
    price_decimal:  Mapped[float]      = mapped_column(Float)
    price_american: Mapped[int]        = mapped_column(Integer)
    deep_link:    Mapped[str | None] = mapped_column(String(500))
    last_update:  Mapped[datetime] = mapped_column(DateTime(timezone=True))

    event:     Mapped[Event]     = relationship(back_populates="outcomes")
    bookmaker: Mapped[Bookmaker] = relationship()

    __table_args__ = (
        UniqueConstraint("event_id", "bookmaker_id", "market", "outcome_name", "point",
                         name="uq_outcome_unique"),
    )


class OddsSnapshot(Base):
    """Append-only history of every odds value seen by every scraper.

    Used for line-movement analysis and proving when prices were quoted.
    Partition by month in production for cheap retention.
    """
    __tablename__ = "odds_snapshots"

    id:             Mapped[int]      = mapped_column(Integer, primary_key=True)
    event_id:       Mapped[int]      = mapped_column(ForeignKey("events.id", ondelete="CASCADE"))
    bookmaker_id:   Mapped[int]      = mapped_column(ForeignKey("bookmakers.id"))
    market:         Mapped[str]      = mapped_column(String(32))
    outcome_name:   Mapped[str]      = mapped_column(String(128))
    point:          Mapped[float | None] = mapped_column(Float)
    price_decimal:  Mapped[float]    = mapped_column(Float)
    captured_at:    Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)

    __table_args__ = (
        Index("ix_snap_event_book_time", "event_id", "bookmaker_id", "captured_at"),
    )
