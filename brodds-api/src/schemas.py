"""Pydantic schemas — match The Odds API v4 response format exactly.

Keeping our public API shape identical to The Odds API means BetScan (and any
other consumer) can swap providers with zero code changes.
"""

from datetime import datetime
from pydantic import BaseModel, Field


class OutcomeOut(BaseModel):
    name:  str
    price: int               # American odds
    point: float | None = None
    link:  str | None   = None


class MarketOut(BaseModel):
    key:        str          # "h2h" | "spreads" | "totals"
    last_update: datetime
    outcomes:   list[OutcomeOut]


class BookmakerOut(BaseModel):
    key:         str
    title:       str
    last_update: datetime
    markets:     list[MarketOut]


class EventOut(BaseModel):
    id:            str
    sport_key:     str
    sport_title:   str
    commence_time: datetime
    home_team:     str
    away_team:     str
    bookmakers:    list[BookmakerOut]


class SportOut(BaseModel):
    key:           str
    title:         str
    group:         str
    description:   str = ""
    active:        bool = True
    has_outrights: bool = False


class HealthOut(BaseModel):
    status: str       = "ok"
    version: str      = "0.1.0"
    bookmakers_active: int = 0
    events_total: int = 0
