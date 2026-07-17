"""
Единая конфигурация PAD+ AI.

USE_PG_STORAGE: PostgreSQL = source of truth, JSON/SQLite = dev/fallback.
"""

import os

USE_PG_STORAGE = os.getenv("USE_PG_STORAGE", "true").lower() in ("1", "true", "yes")
