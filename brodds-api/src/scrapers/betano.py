"""Betano (Brazil) scraper.

Calibrated against live Betano traffic captured via DevTools (Network → XHR).

Endpoint pattern (Kaizen Gaming platform):
    GET /api/sport/{sport_slug}/{country_slug}/{league_slug}/{league_id}/?req=s,stnf,c,mb,mbl

The `?req=` parameter is a comma-separated compact key requesting specific
blocks of data:
    s    = sport info
    stnf = standings
    c    = competition info
    mb   = main betting markets
    mbl  = market builder list

Cloudflare-protected: must use Playwright (`needs_browser = True`) and ideally
a residential proxy. Direct httpx fetches return 403/503.

Response structure (sample observed):
    {
      ... nested layout ...
      selections: [
        {id: "...", name: "1", fullName: "<home team>", price: 1.82, ...},
        {id: "...", name: "X", fullName: "Empate",       price: 3.45, ...},
        {id: "...", name: "2", fullName: "<away team>", price: 4.85, ...},
      ],
      type: "MRES",        # Match Result (Moneyline / 1X2)
      typeId: 1,
      name: "Home - Away",
      participants: [{name: "<home>", ...}, {name: "<away>", ...}],
      regionId: "10004",
      regionName: "Brasil",
    }

The top-level response wraps these event-shaped objects inside one or more
layout blocks. We walk the full response recursively rather than assuming
a fixed shape, so the parser is robust to layout changes.
"""

from datetime import datetime, timezone
from typing import Iterator

from .base import BaseScraper, ScrapedEvent, ScrapedMarket, ScrapedOutcome


# Map our canonical sport keys → Betano league URL paths.
# Add more leagues by inspecting their URL in Betano's DevTools Network tab
# (look for the request matching the pattern in the module docstring).
LEAGUE_URLS: dict[str, str] = {
    "soccer_brazil_serie_a":
        "/api/sport/futebol/brasil/brasileirao-serie-a-betano/10016/?req=s,stnf,c,mb,mbl",
    # Examples — uncomment + verify the real slugs/IDs once you've captured them:
    # "soccer_brazil_serie_b":
    #     "/api/sport/futebol/brasil/brasileirao-serie-b/<league_id>/?req=s,stnf,c,mb,mbl",
    # "soccer_brazil_copa_brasil":
    #     "/api/sport/futebol/brasil/copa-do-brasil/<league_id>/?req=s,stnf,c,mb,mbl",
}


class BetanoScraper(BaseScraper):
    name           = "betano"
    title          = "Betano"
    base_url       = "https://www.betano.bet.br"
    needs_browser  = True   # Cloudflare-protected; direct httpx is blocked

    # Conservative — each league is just one request, no need to hammer.
    rate_limit_per_minute = 10

    async def scrape(self) -> list[ScrapedEvent]:
        """Pull all currently-listed events from Betano across known leagues."""
        all_events: list[ScrapedEvent] = []

        for sport_key, path in LEAGUE_URLS.items():
            try:
                events = await self._scrape_league(sport_key, path)
                all_events.extend(events)
                self.log.info("scraped_league", sport=sport_key, count=len(events))
            except Exception as e:
                # One league's failure shouldn't abort the whole scrape
                self.log.error("scrape_league_failed", sport=sport_key, error=str(e))

        self.log.info("scrape_done", total_events=len(all_events))
        return all_events

    # -------------------------------------------------------------------------
    # Per-league fetch
    # -------------------------------------------------------------------------

    async def _scrape_league(self, sport_key: str, path: str) -> list[ScrapedEvent]:
        url = self.base_url + path
        self.log.info("fetching", url=url)
        body = await self.fetch_browser(url)
        body_len = len(body or "")
        payload = self._extract_json(body)
        events = list(self._iter_events(payload, sport_key))

        # Diagnostic — when extraction fails, walk the payload and log every
        # path in the JSON tree that resembles an event/market/widget so we
        # can see exactly where in the structure the real data lives.
        if not events:
            paths = self._find_event_paths(payload)[:30]
            widgets = self._find_widget_urls(payload)[:20]
            preview = (body or "")[:600].replace("\n", " ")
            self.log.warning(
                "no_events_extracted",
                url             = url,
                body_length     = body_len,
                body_preview    = preview,
                payload_type    = type(payload).__name__,
                payload_keys    = (list(payload.keys())[:12] if isinstance(payload, dict) else None),
                interesting_paths = paths,
                widget_urls       = widgets,
            )
        return events

    # -------------------------------------------------------------------------
    # Structure inspector — used only when extraction fails, to find where
    # the events live in the JSON tree.
    # -------------------------------------------------------------------------

    def _find_event_paths(self, node, path: str = "$",
                          out: list | None = None, depth: int = 0) -> list:
        """Walk `node` and return a list of paths that look like events,
        markets, or odds. Helps locate where the real data sits."""
        if out is None:
            out = []
        if depth > 8 or len(out) >= 60:
            return out

        if isinstance(node, dict):
            keys = set(node.keys())
            hits = []
            if "selections" in keys:
                hits.append("has_selections")
            if "markets" in keys and isinstance(node.get("markets"), list):
                hits.append("has_markets_list")
            if {"homeTeam", "awayTeam"} <= keys or {"home", "away"} <= keys:
                hits.append("has_teams")
            if "participants" in keys and isinstance(node.get("participants"), list):
                hits.append("has_participants")
            if "price" in keys and ("name" in keys or "label" in keys):
                hits.append("has_priced_outcome")
            if hits:
                out.append({"path": path, "hits": hits, "keys": sorted(keys)[:12]})
            for k, v in node.items():
                self._find_event_paths(v, f"{path}.{k}", out, depth + 1)
        elif isinstance(node, list):
            # Sample the first element only — keeps the log size manageable
            if node and isinstance(node[0], (dict, list)):
                self._find_event_paths(node[0], f"{path}[0]", out, depth + 1)
        return out

    def _find_widget_urls(self, node, out: list | None = None, depth: int = 0) -> list:
        """Collect any `url` strings that look like Betano API endpoints —
        these are the sub-endpoints the layout response points to."""
        if out is None:
            out = []
        if depth > 8 or len(out) >= 40:
            return out

        if isinstance(node, dict):
            url = node.get("url")
            if isinstance(url, str) and url.startswith("/api/"):
                out.append(url)
            for v in node.values():
                self._find_widget_urls(v, out, depth + 1)
        elif isinstance(node, list):
            for item in node:
                self._find_widget_urls(item, out, depth + 1)
        return out

    # -------------------------------------------------------------------------
    # Body → JSON
    # -------------------------------------------------------------------------

    def _extract_json(self, body: str) -> dict:
        """Best-effort: Betano's API returns application/json, but when Playwright
        navigates to it, the browser sometimes wraps the body in HTML (<pre>...</pre>
        or document.body innerHTML). Handle both cases."""
        import json
        import re

        s = (body or "").strip()
        if not s:
            return {}

        # Plain JSON body
        if s.startswith("{") or s.startswith("["):
            try:
                return json.loads(s)
            except json.JSONDecodeError:
                pass

        # JSON inside a <pre> tag (Chrome's default JSON viewer)
        match = re.search(r"<pre[^>]*>(.*?)</pre>", s, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass

        # JSON inside a <body> with no wrapping
        match = re.search(r"<body[^>]*>(.*?)</body>", s, re.DOTALL)
        if match:
            inner = match.group(1).strip()
            try:
                return json.loads(inner)
            except json.JSONDecodeError:
                pass

        self.log.warning("response_not_json", preview=s[:200])
        return {}

    # -------------------------------------------------------------------------
    # Walk the response and yield events
    # -------------------------------------------------------------------------

    def _iter_events(self, node, sport_key: str) -> Iterator[ScrapedEvent]:
        """Recursively walk `node`, yielding a ScrapedEvent for every
        event-shaped object encountered. This is more robust than assuming a
        fixed top-level structure, which Kaizen Gaming changes frequently."""
        if isinstance(node, dict):
            if self._looks_like_event(node):
                event = self._parse_event(node, sport_key)
                if event is not None:
                    yield event
                # Don't recurse into a parsed event's children
                return
            for value in node.values():
                yield from self._iter_events(value, sport_key)
        elif isinstance(node, list):
            for item in node:
                yield from self._iter_events(item, sport_key)

    @staticmethod
    def _looks_like_event(obj: dict) -> bool:
        """Betano event shape (verified via DevTools diagnostic):
            {
              participants: [{name: "<home>", ...}, {name: "<away>", ...}],
              markets:      [{type: "MRES", selections: [...], ...}, ...],
              name:         "Home - Away",
              ...
            }

        Selections live INSIDE markets[], not on the event itself — so we
        match on `participants + markets`, not on `selections` directly.
        """
        parts = obj.get("participants")
        if not isinstance(parts, list) or len(parts) < 2:
            return False
        markets = obj.get("markets")
        if not isinstance(markets, list) or not markets:
            return False
        return True

    # -------------------------------------------------------------------------
    # Parse one event
    # -------------------------------------------------------------------------

    def _parse_event(self, obj: dict, sport_key: str) -> ScrapedEvent | None:
        # ── teams ────────────────────────────────────────────────────────────
        parts = obj["participants"]
        if not (isinstance(parts[0], dict) and isinstance(parts[1], dict)):
            return None
        home = parts[0].get("name") or "Unknown"
        away = parts[1].get("name") or "Unknown"

        # ── find the MRES (Match Result / 1X2) market ────────────────────────
        # Betano emits many markets per event (handicap, totals, score, etc.);
        # we only care about MRES for h2h. Identified by type="MRES" or typeId=1.
        mres_market = None
        for m in obj.get("markets", []):
            if not isinstance(m, dict):
                continue
            if m.get("type") == "MRES" or m.get("typeId") == 1:
                mres_market = m
                break

        if mres_market is None:
            return None

        # ── start time ───────────────────────────────────────────────────────
        # The event object doesn't expose a startTime field directly (verified
        # via diagnostic). Use the MRES market's `marketCloseTimeMillis` —
        # for pre-match markets this equals the event kickoff.
        commence = None
        raw_ms = mres_market.get("marketCloseTimeMillis")
        if isinstance(raw_ms, (int, float)) and raw_ms > 0:
            commence = datetime.fromtimestamp(raw_ms / 1000, tz=timezone.utc)
        if commence is None:
            # Fallback: try a handful of event-level keys in case Kaizen adds one.
            for k in ("eventStartTimeMillis", "startTimeMillis",
                      "startTime", "startDate", "eventTime"):
                commence = self._parse_time(obj.get(k))
                if commence:
                    break
        if commence is None:
            return None

        # ── parse MRES selections → h2h outcomes ─────────────────────────────
        h2h_outcomes: list[ScrapedOutcome] = []
        for sel in mres_market.get("selections", []):
            if not isinstance(sel, dict):
                continue
            try:
                price = float(sel["price"])
            except (KeyError, TypeError, ValueError):
                continue

            sel_name  = sel.get("name", "")
            full_name = sel.get("fullName", "")
            outcome_name = self._map_outcome(sel_name, full_name, home, away)
            if outcome_name is None:
                continue

            h2h_outcomes.append(ScrapedOutcome(
                name          = outcome_name,
                price_decimal = price,
            ))

        # Sanity check: a valid soccer market has 3 outcomes (1/X/2);
        # tennis/MMA has 2. Anything less than 2 means we mis-parsed.
        if len(h2h_outcomes) < 2:
            return None

        return ScrapedEvent(
            bookmaker_key = self.name,
            sport_key     = sport_key,
            home_team     = home,
            away_team     = away,
            commence_time = commence,
            markets       = [ScrapedMarket(key="h2h", outcomes=h2h_outcomes)],
        )

    # -------------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------------

    @staticmethod
    def _parse_time(raw) -> datetime | None:
        if not raw:
            return None
        try:
            if isinstance(raw, (int, float)):
                # Unix timestamp — guess ms vs seconds by magnitude
                ts = raw / 1000 if raw > 1e12 else raw
                return datetime.fromtimestamp(ts, tz=timezone.utc)
            s = str(raw).replace("Z", "+00:00")
            dt = datetime.fromisoformat(s)
            return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _map_outcome(sel_name: str, full_name: str, home: str, away: str) -> str | None:
        """Map Betano's 1/X/2 selection naming to canonical outcome names."""
        # Soccer 1X2
        if sel_name == "1":
            return home
        if sel_name == "2":
            return away
        if sel_name == "X" or full_name.strip().lower() == "empate":
            return "Draw"
        # Two-way markets (tennis, MMA) — Betano sometimes uses team names directly
        if full_name:
            return full_name
        return None
