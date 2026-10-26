# =============================================================================
# providers
# Registry of odds data providers.
#
# To add a provider:
#   1. Subclass `Provider` (base.py) in a new module
#   2. Return events in the canonical format documented in base.py
#   3. Add an instance to `_PROVIDER_INSTANCES` below
# =============================================================================

# Load .env so is_configured() sees keys from the file, not only OS env vars.
from dotenv import load_dotenv

from .base import Provider
from .brodds import BroddsLocalProvider
from .demo import DemoProvider
from .odds_api import OddsApiProvider
from .planned import OpticOddsProvider

load_dotenv()

# Order matters: the first configured provider is the default in the dashboard
# and CLI. The demo provider is always configured, so without any API key the
# project still runs end to end on bundled sample data.
_PROVIDER_INSTANCES: list[Provider] = [
    OddsApiProvider(),
    DemoProvider(),
    BroddsLocalProvider(),
    OpticOddsProvider(),
]

PROVIDERS: dict[str, Provider] = {p.name: p for p in _PROVIDER_INSTANCES}


def get_provider(name: str) -> Provider:
    """Resolve a provider by its `name`. Raises KeyError if unknown."""
    return PROVIDERS[name]


def list_providers() -> list[Provider]:
    """Return all registered providers (configured or not)."""
    return list(PROVIDERS.values())


def list_configured_providers() -> list[Provider]:
    """Return only providers that are ready to use."""
    return [p for p in PROVIDERS.values() if p.is_configured()]


__all__ = [
    "PROVIDERS",
    "Provider",
    "get_provider",
    "list_configured_providers",
    "list_providers",
]
