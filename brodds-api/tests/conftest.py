"""Test configuration for the BrOdds service.

`src.config.Settings` requires DATABASE_URL at import time. Tests never touch a
real database, so point it at an in-memory SQLite engine before any import.
"""

import os

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite://")
