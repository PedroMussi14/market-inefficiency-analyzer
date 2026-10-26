# =============================================================================
# providers/planned.py
# Providers on the roadmap whose adapters are not implemented yet.
#
# They are registered so the dashboard can list them under "Add more
# providers", but they raise NotImplementedError until finished.
#
# To finish an adapter:
#   1. Get an API key and capture one real response from each endpoint
#   2. Transform it into the canonical format documented in base.py
#   3. Add tests with the captured response as a fixture
# =============================================================================

import os

from .base import Provider


class OpticOddsProvider(Provider):
    """OpticOdds claims 350+ bookmakers including Betano, with a sport-level
    odds endpoint similar to The Odds API's model."""

    name        = "opticodds"
    label       = "OpticOdds 🌎 (planned)"
    region_hint = "350+ books incl. Betano. Adapter not implemented yet."

    BASE_URL = "https://api.opticodds.com/api/v3"

    def is_configured(self) -> bool:
        return bool(os.getenv("OPTICODDS_KEY"))

    def setup_help(self) -> str:
        return ("Planned provider. Sign up at https://opticodds.com and add "
                "`OPTICODDS_KEY=...` to .env once the adapter is implemented.")

    def get_sports(self) -> list:
        raise NotImplementedError("OpticOdds adapter is planned but not implemented yet.")

    def get_odds(self, sport, markets="h2h", regions="us", odds_format="american",
                 include_links=True, include_sids=True) -> list:
        raise NotImplementedError("OpticOdds adapter is planned but not implemented yet.")
