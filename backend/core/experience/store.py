import logging
import os
from typing import Optional, List, Dict, Any

from .models import ExperienceRecord
from .postgres_store import ExperiencePostgresStore, postgres_available

logger = logging.getLogger("padplus.experience")

_POSTGRES_STORE: Optional[ExperiencePostgresStore] = None
_SQLITE_STORE = None


def _is_dev_mode() -> bool:
    return os.getenv("APP_ENV", "").strip().lower() == "development"


def _get_store():
    global _POSTGRES_STORE, _SQLITE_STORE

    if _is_dev_mode() or not postgres_available:
        if _SQLITE_STORE is None:
            from .sqlite_store import ExperienceSQLiteStore
            _SQLITE_STORE = ExperienceSQLiteStore()
            logger.info("Experience: использую SQLite (локальный режим)")
        return _SQLITE_STORE
    else:
        if _POSTGRES_STORE is None:
            _POSTGRES_STORE = ExperiencePostgresStore()
            logger.info("Experience: использую PostgreSQL (продакшн)")
        return _POSTGRES_STORE


class ExperienceStore:
    def save(self, record: ExperienceRecord) -> str:
        return _get_store().save(record)

    def load_all(self) -> List[Dict[str, Any]]:
        return _get_store().load_all()

    def count(self) -> int:
        return _get_store().count()

    def get_session_records(self, session_id: str, limit: int = 0) -> list:
        store = _get_store()
        if hasattr(store, "get_session_records"):
            return store.get_session_records(session_id, limit)
        return []

    def clear_session(self, session_id: str):
        store = _get_store()
        if hasattr(store, "clear_session"):
            store.clear_session(session_id)

    def get_stats(self) -> Dict[str, Any]:
        store = _get_store()
        if hasattr(store, "get_stats"):
            return store.get_stats()
        return {"total": 0, "by_type": {}}
