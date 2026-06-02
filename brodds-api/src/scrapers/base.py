"""Base scraper framework.

Every concrete scraper subclasses `BaseScraper` and implements `scrape()`.
The base class handles cross-cutting concerns:

  - Async HTTP via httpx (with optional proxy)
  - Headless browser fallback via Playwright (for Cloudflare-protected sites)
  - User-agent rotation
  - Per-host rate limiting via Redis
  - Exponential backoff with jitter
  - Structured logging tied to the scraper name

Subclasses should keep their `scrape()` body small and delegate HTTP work
to `self.fetch()` / `self.fetch_browser()` so they automatically inherit
all retry/rate-limit/proxy logic.
"""

import asyncio
import random
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime

import httpx
import structlog

from ..config import settings


# =============================================================================
# Canonical scrape output — the bridge between scrapers and the DB layer
# =============================================================================

@dataclass
class ScrapedOutcome:
    name:           str          # e.g. "Flamengo" or "Over"
    price_decimal:  float
    point:          float | None = None
    deep_link:      str | None   = None


@dataclass
class ScrapedMarket:
    key:      str                # "h2h" | "spreads" | "totals"
    outcomes: list[ScrapedOutcome] = field(default_factory=list)


@dataclass
class ScrapedEvent:
    bookmaker_key: str
    sport_key:     str
    home_team:     str
    away_team:     str
    commence_time: datetime
    markets:       list[ScrapedMarket] = field(default_factory=list)


# =============================================================================
# Base class
# =============================================================================

class BaseScraper(ABC):
    """Subclass and override `scrape()` to add a new bookmaker."""

    # Subclasses MUST set these
    name:        str = ""        # short id, e.g. "betano"
    title:       str = ""        # display name, e.g. "Betano"
    base_url:    str = ""        # e.g. "https://www.betano.bet.br"

    # Tunables — override as needed
    rate_limit_per_minute:  int = 20      # max requests per minute to this site
    retries:                int = 3
    retry_base_delay:       float = 1.5   # seconds; doubled each retry with jitter
    request_timeout:        float = 20.0
    needs_browser:          bool = False  # set True if the site is JS/Cloudflare-protected

    def __init__(self):
        self.log = structlog.get_logger(scraper=self.name)
        self._last_request_at: float = 0.0
        self._min_interval: float    = 60.0 / max(self.rate_limit_per_minute, 1)

    # -------------------------------------------------------------------------
    # Subclass interface
    # -------------------------------------------------------------------------

    @abstractmethod
    async def scrape(self) -> list[ScrapedEvent]:
        """Return all currently-listed events for this bookmaker."""

    # -------------------------------------------------------------------------
    # HTTP helper — used by all subclasses
    # -------------------------------------------------------------------------

    async def fetch(self, url: str, *, headers: dict | None = None,
                    params: dict | None = None) -> httpx.Response:
        """GET `url` with retries, rate limiting, proxy + user-agent rotation."""
        await self._respect_rate_limit()

        merged_headers = self._build_headers(headers or {})
        proxies = settings.proxy_url or None

        last_err: Exception | None = None
        for attempt in range(1, self.retries + 1):
            try:
                async with httpx.AsyncClient(
                    timeout=self.request_timeout,
                    proxies=proxies,
                    follow_redirects=True,
                    http2=True,
                ) as client:
                    response = await client.get(url, headers=merged_headers, params=params)
                    response.raise_for_status()
                    return response
            except (httpx.HTTPStatusError, httpx.TransportError) as e:
                last_err = e
                if attempt < self.retries:
                    delay = self.retry_base_delay * (2 ** (attempt - 1)) + random.uniform(0, 0.5)
                    self.log.warning("fetch_retry", url=url, attempt=attempt, delay=delay, error=str(e))
                    await asyncio.sleep(delay)

        # Exhausted retries
        self.log.error("fetch_failed", url=url, error=str(last_err))
        assert last_err is not None
        raise last_err

    async def fetch_browser(self, url: str) -> str:
        """Render `url` in a real Chromium and return the final HTML.

        Use this for Cloudflare-protected sites (Betano, Bet365). Slower than
        plain HTTP — only use when `fetch()` returns 403/503.

        Logs the final status code and response time so we can diagnose
        scenarios where Playwright returns an empty body or fails silently.
        """
        from playwright.async_api import async_playwright

        await self._respect_rate_limit()
        import time
        t0 = time.time()

        try:
            async with async_playwright() as pw:
                launch_kwargs: dict = {"headless": True}
                if settings.proxy_url:
                    launch_kwargs["proxy"] = self._parse_proxy(settings.proxy_url)

                browser = await pw.chromium.launch(**launch_kwargs)
                try:
                    context = await browser.new_context(
                        user_agent=random.choice(settings.user_agent_pool),
                        locale="pt-BR",
                        viewport={"width": 1366, "height": 768},
                    )
                    page = await context.new_page()
                    response = await page.goto(
                        url, wait_until="networkidle",
                        timeout=int(self.request_timeout * 1000),
                    )
                    status = response.status if response is not None else None
                    html = await page.content()
                    self.log.info(
                        "browser_fetched",
                        url        = url,
                        status     = status,
                        duration_s = round(time.time() - t0, 2),
                        body_len   = len(html or ""),
                    )
                    return html
                finally:
                    await browser.close()
        except Exception as e:
            self.log.error(
                "browser_fetch_failed",
                url        = url,
                duration_s = round(time.time() - t0, 2),
                error      = f"{type(e).__name__}: {e}",
            )
            raise

    # -------------------------------------------------------------------------
    # Internals
    # -------------------------------------------------------------------------

    def _build_headers(self, extra: dict) -> dict:
        ua = random.choice(settings.user_agent_pool)
        return {
            "User-Agent":       ua,
            "Accept":           "application/json, text/plain, */*",
            "Accept-Language":  "pt-BR,pt;q=0.9,en;q=0.8",
            **extra,
        }

    async def _respect_rate_limit(self) -> None:
        """Block until enough time has elapsed since the previous request."""
        now = asyncio.get_event_loop().time()
        elapsed = now - self._last_request_at
        if elapsed < self._min_interval:
            await asyncio.sleep(self._min_interval - elapsed)
        self._last_request_at = asyncio.get_event_loop().time()

    @staticmethod
    def _parse_proxy(url: str) -> dict:
        """Convert PROXY_URL into Playwright's proxy dict shape."""
        from urllib.parse import urlparse
        p = urlparse(url)
        result = {"server": f"{p.scheme}://{p.hostname}:{p.port}"}
        if p.username:
            result["username"] = p.username
        if p.password:
            result["password"] = p.password
        return result
