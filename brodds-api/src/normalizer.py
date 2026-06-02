"""Cross-bookmaker entity unification.

Different sportsbooks list the same team/match under different names:
    Betano       "Flamengo"
    KTO          "C.R. Flamengo"
    Sportingbet  "Flamengo RJ"
    Pinnacle     "Flamengo Rio de Janeiro"

If we don't unify these, the same match shows up as multiple "events" in the
DB and arbitrage detection breaks (you can't compare prices across books for
what looks like different events).

Strategy:
  1. Apply a deterministic alias table for the obvious cases (curated)
  2. Fall back to fuzzy matching (rapidfuzz) above a similarity threshold
  3. Build a stable canonical_key for each event from
     normalize(home) + "_" + normalize(away) + "_" + start_date

The canonical_key is unique-indexed in the DB, so duplicates collapse.
"""

import re
import unicodedata
from datetime import datetime

from rapidfuzz import fuzz, process


# =============================================================================
# Curated aliases — extend as you encounter more variants
# =============================================================================

TEAM_ALIASES: dict[str, str] = {
    # --- Brazilian football ---
    "flamengo":               "flamengo",
    "c.r. flamengo":          "flamengo",
    "cr flamengo":            "flamengo",
    "flamengo rj":            "flamengo",
    "flamengo rio de janeiro":"flamengo",

    "palmeiras":              "palmeiras",
    "se palmeiras":           "palmeiras",
    "sociedade esportiva palmeiras": "palmeiras",

    "corinthians":            "corinthians",
    "sc corinthians paulista":"corinthians",

    "sao paulo":              "sao paulo",
    "são paulo":              "sao paulo",
    "sao paulo fc":           "sao paulo",

    "santos":                 "santos",
    "santos fc":              "santos",

    "gremio":                 "gremio",
    "grêmio":                 "gremio",

    "internacional":          "internacional",
    "sc internacional":       "internacional",

    "atletico mineiro":       "atletico mineiro",
    "atlético mineiro":       "atletico mineiro",
    "atletico-mg":            "atletico mineiro",

    "fluminense":             "fluminense",
    "vasco":                  "vasco",
    "cr vasco da gama":       "vasco",
    "botafogo":               "botafogo",
    "botafogo fr":            "botafogo",
}

# Cache of known canonical names — used by fuzzy matching as the candidate pool
_KNOWN_CANONICAL: set[str] = set(TEAM_ALIASES.values())


# =============================================================================
# Public API
# =============================================================================

def normalize_team(name: str) -> str:
    """Map any spelling/variant of a team name to its canonical form.

    Resolution order:
      1. Strip accents + lowercase
      2. Direct alias lookup
      3. Fuzzy match against known canonicals (>= 88% similar)
      4. Fall back to the cleaned input (and remember it as a new canonical)
    """
    cleaned = _clean(name)

    if cleaned in TEAM_ALIASES:
        return TEAM_ALIASES[cleaned]

    if _KNOWN_CANONICAL:
        match = process.extractOne(cleaned, _KNOWN_CANONICAL, scorer=fuzz.WRatio)
        if match and match[1] >= 88:
            return match[0]

    # First time seeing this name — add to cache so future variants can match it
    _KNOWN_CANONICAL.add(cleaned)
    return cleaned


def canonical_event_key(home: str, away: str, commence_time: datetime) -> str:
    """Build a stable string identifying a match across bookmakers.

    Same home + away + same calendar day → same key, even if the listed start
    time varies by ±30 min between books.
    """
    h = normalize_team(home).replace(" ", "_")
    a = normalize_team(away).replace(" ", "_")
    day = commence_time.date().isoformat()
    return f"{h}__vs__{a}__{day}"


# =============================================================================
# Internals
# =============================================================================

def _clean(name: str) -> str:
    """Strip accents, lowercase, collapse whitespace, drop punctuation."""
    decomposed = unicodedata.normalize("NFKD", name)
    no_accents = "".join(c for c in decomposed if not unicodedata.combining(c))
    no_punct   = re.sub(r"[^\w\s]", "", no_accents)
    return re.sub(r"\s+", " ", no_punct).strip().lower()
