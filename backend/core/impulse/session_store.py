"""
SessionImpulseStore — per-session хранение импульсов.

Вместо глобального синглтона get_impulse_core():
    from core.impulse.session_store import get_session_impulse_store
    store = get_session_impulse_store()
    core = store.get_or_create(session_id)
"""

from __future__ import annotations

import json
import logging
import os
import threading
import time
from datetime import datetime
from typing import Dict, Optional

from .core import ImpulseCore
from core.xray.memory_trace import (
    emit_memory_event, MemoryOperation, MemoryComponent, MemoryObjectType, MemoryResult
)

logger = logging.getLogger("padplus.impulse.store")

SESSION_IMPULSE_DATA_DIR = "data"


class SessionImpulseStore:
    """Per-session ImpulseCore store с TTL/LRU eviction."""

    MAX_SESSIONS = 500
    MAX_AGE_HOURS = 24
    CLEANUP_INTERVAL = 100

    def __init__(self, base_path: str | None = None):
        if base_path is None:
            # По умолчанию — каталог данных проекта (data/), как у остальных storage
            base_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(
                    os.path.dirname(__file__)
                ))),
                SESSION_IMPULSE_DATA_DIR,
            )
        self.base_path = base_path
        self._sessions: Dict[str, ImpulseCore] = {}
        self._last_access: Dict[str, datetime] = {}
        self._lock = threading.RLock()
        self._access_count = 0

    def get_or_create(self, session_id: str) -> ImpulseCore:
        """Возвращает ImpulseCore для сессии, создаёт если нет."""
        import time
        start_time = time.perf_counter()
        
        if not session_id:
            return self._get_fallback()
        with self._lock:
            self._maybe_cleanup()
            if session_id not in self._sessions:
                self._sessions[session_id] = self._load(session_id)
            self._last_access[session_id] = datetime.now()
            
            duration_ms = (time.perf_counter() - start_time) * 1000
            
            emit_memory_event(
                operation=MemoryOperation.READ,
                component=MemoryComponent.IMPULSE_CORE,
                object_type=MemoryObjectType.IMPULSE_STATE,
                object_id=session_id,
                result=MemoryResult.FOUND if session_id in self._sessions else MemoryResult.CREATED,
                duration_ms=duration_ms,
                phase="get_or_create",
            )
            
            return self._sessions[session_id]

    def _get_fallback(self) -> ImpulseCore:
        """Fallback для сессий без session_id (тесты, legacy)."""
        key = "__fallback__"
        with self._lock:
            if key not in self._sessions:
                self._sessions[key] = ImpulseCore()
            return self._sessions[key]

    def save(self, session_id: str) -> None:
        """Сохраняет состояние импульса для сессии."""
        import time
        start_time = time.perf_counter()
        
        with self._lock:
            core = self._sessions.get(session_id)
            if core:
                self._persist(session_id, core)
                
                duration_ms = (time.perf_counter() - start_time) * 1000
                
                emit_memory_event(
                    operation=MemoryOperation.WRITE,
                    component=MemoryComponent.IMPULSE_CORE,
                    object_type=MemoryObjectType.IMPULSE_STATE,
                    object_id=session_id,
                    result=MemoryResult.UPDATED,
                    duration_ms=duration_ms,
                    phase="save",
                )

    def _persist(self, session_id: str, core: ImpulseCore) -> None:
        """Сохраняет ImpulseCore в JSON-файл сессии."""
        try:
            os.makedirs(self.base_path, exist_ok=True)
            path = os.path.join(self.base_path, f"impulse_state_{session_id}.json")
            with open(path, "w", encoding="utf-8") as f:
                f.write(core.to_json())
        except Exception as e:
            logger.warning("Persist failed for %s: %s", session_id, e)

    def _load(self, session_id: str) -> ImpulseCore:
        """Загружает ImpulseCore из JSON-файла сессии."""
        path = os.path.join(self.base_path, f"impulse_state_{session_id}.json")
        try:
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    return ImpulseCore.from_dict(json.load(f))
        except Exception as e:
            logger.warning("Load failed for %s: %s", session_id, e)
        return ImpulseCore()

    def save_all(self) -> None:
        """Сохраняет все активные сессии."""
        with self._lock:
            for session_id, core in list(self._sessions.items()):
                try:
                    self._persist(session_id, core)
                except Exception as e:
                    logger.warning("Save failed for %s: %s", session_id, e)

    def remove(self, session_id: str) -> None:
        """Удаляет сессию из памяти."""
        with self._lock:
            self._sessions.pop(session_id, None)
            self._last_access.pop(session_id, None)

    def get_active_count(self) -> int:
        with self._lock:
            return len(self._sessions)

    def get_stats(self) -> dict:
        with self._lock:
            return {
                "active_sessions": len(self._sessions),
                "max_sessions": self.MAX_SESSIONS,
                "max_age_hours": self.MAX_AGE_HOURS,
            }

    def _maybe_cleanup(self):
        self._access_count += 1
        if self._access_count >= self.CLEANUP_INTERVAL:
            self._access_count = 0
            self._evict_expired()
            self._evict_lru()

    def _evict_expired(self):
        now = datetime.now()
        expired = [
            sid
            for sid, last in self._last_access.items()
            if (now - last).total_seconds() > self.MAX_AGE_HOURS * 3600
        ]
        for sid in expired:
            if sid in self._sessions:
                del self._sessions[sid]
                del self._last_access[sid]

    def _evict_lru(self):
        if len(self._sessions) <= self.MAX_SESSIONS:
            return
        sorted_by_access = sorted(
            self._last_access.items(), key=lambda x: x[1]
        )
        to_remove = len(self._sessions) - self.MAX_SESSIONS
        for sid, _ in sorted_by_access[:to_remove]:
            if sid in self._sessions:
                del self._sessions[sid]
                del self._last_access[sid]


_module_store: Optional[SessionImpulseStore] = None
_module_lock = threading.Lock()


def get_session_impulse_store() -> SessionImpulseStore:
    global _module_store
    with _module_lock:
        if _module_store is None:
            _module_store = SessionImpulseStore()
        return _module_store


def reset_impulse_store():
    """Сброс для тестов."""
    global _module_store
    with _module_lock:
        _module_store = None
