"""
Единая конфигурация PAD+ AI.

USE_PG_STORAGE: PostgreSQL = source of truth, JSON/SQLite = dev/fallback.
"""

import os

_val = os.getenv("USE_PG_STORAGE") or os.getenv("IMPULSE_USE_PG") or "true"
USE_PG_STORAGE = _val.lower() in ("1", "true", "yes")
