"""
🗄️ Session Stores — per-session cache-слои над глобальной памятью.

D'-2 Session Isolation: RAG / Semantic / Episodic остаются глобальным
источником данных (SQLite/PostgreSQL), а поверх них работает per-session
кэш-слой с TTL/LRU eviction. Это гарантирует, что результаты поиска
одной сессии не «протекают» в другую, и снижает нагрузку на БД.

Базовый класс: BaseSessionStore (dict session_id -> dict key -> value).
Конкретные: SessionRAGStore, SessionSemanticStore, SessionEpisodicStore.
"""

from __future__ import annotations

import logging
import threading
import time
from datetime import datetime
from typing import Any, Dict, Optional

from core.xray.memory_trace import (
    emit_memory_event, MemoryOperation, MemoryComponent, MemoryObjectType, MemoryResult
)

logger = logging.getLogger("padplus.memory.session_store")


class BaseSessionStore:
    """Базовый per-session кэш-слой с TTL/LRU eviction.

    Структура: session_id -> {key: value}. Каждая сессия изолирована.
    """

    MAX_SESSIONS = 500
    MAX_AGE_HOURS = 24
    CLEANUP_INTERVAL = 100
    COMPONENT = MemoryComponent.UNKNOWN
    OBJECT_TYPE = MemoryObjectType.CONTEXT

    def __init__(self):
        self._sessions: Dict[str, Dict[str, Any]] = {}
        self._last_access: Dict[str, datetime] = {}
        self._lock = threading.RLock()
        self._access_count = 0

    def get(self, session_id: str, key: str, default: Any = None) -> Any:
        """Возвращает значение из кэша сессии (или default)."""
        with self._lock:
            self._maybe_cleanup()
            data = self._sessions.get(session_id)
            if data is None:
                emit_memory_event(
                    operation=MemoryOperation.READ,
                    component=self.COMPONENT,
                    object_type=self.OBJECT_TYPE,
                    object_id=session_id,
                    result=MemoryResult.NOT_FOUND,
                    phase=f"{self.__class__.__name__}.get",
                )
                return default
            self._last_access[session_id] = datetime.now()
            return data.get(key, default)

    def set(self, session_id: str, key: str, value: Any) -> None:
        """Сохраняет значение в кэш сессии."""
        start_time = time.perf_counter()
        with self._lock:
            self._maybe_cleanup()
            data = self._sessions.setdefault(session_id, {})
            data[key] = value
            self._last_access[session_id] = datetime.now()

            duration_ms = (time.perf_counter() - start_time) * 1000
            emit_memory_event(
                operation=MemoryOperation.WRITE,
                component=self.COMPONENT,
                object_type=self.OBJECT_TYPE,
                object_id=session_id,
                result=MemoryResult.UPDATED,
                duration_ms=duration_ms,
                phase=f"{self.__class__.__name__}.set",
                payload_size_bytes=len(key),
            )

    def delete(self, session_id: str, key: str) -> None:
        """Удаляет ключ из кэша сессии."""
        with self._lock:
            data = self._sessions.get(session_id)
            if data and key in data:
                del data[key]

    def clear_session(self, session_id: str) -> None:
        """Полностью очищает кэш сессии."""
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
            self._sessions.pop(sid, None)
            self._last_access.pop(sid, None)
        if expired:
            emit_memory_event(
                operation=MemoryOperation.EVICT,
                component=self.COMPONENT,
                object_type=self.OBJECT_TYPE,
                result=MemoryResult.EXPIRED,
                phase=f"{self.__class__.__name__}.evict_expired",
                payload_size_bytes=len(expired),
            )

    def _evict_lru(self):
        if len(self._sessions) <= self.MAX_SESSIONS:
            return
        sorted_by_access = sorted(self._last_access.items(), key=lambda x: x[1])
        to_remove = len(self._sessions) - self.MAX_SESSIONS
        removed = 0
        for sid, _ in sorted_by_access[:to_remove]:
            if sid in self._sessions:
                del self._sessions[sid]
                del self._last_access[sid]
                removed += 1
        if removed:
            emit_memory_event(
                operation=MemoryOperation.EVICT,
                component=self.COMPONENT,
                object_type=self.OBJECT_TYPE,
                result=MemoryResult.EVICTED,
                phase=f"{self.__class__.__name__}.evict_lru",
                payload_size_bytes=removed,
            )


class SessionRAGStore(BaseSessionStore):
    """Per-session кэш контекста RAG.

    Кэширует результат get_context(query) на ключ сессии, чтобы
    повторные похожие запросы в рамках одной сессии не били в БД.
    """

    COMPONENT = MemoryComponent.RAG_MEMORY
    OBJECT_TYPE = MemoryObjectType.DIALOG

    def get_context(self, session_id: str, query: str, user_id: Optional[str] = None) -> str:
        """Возвращает RAG-контекст с per-session кэшированием."""
        start_time = time.perf_counter()

        if not session_id:
            from memory import get_rag
            return get_rag().get_context(query, user_id=user_id)

        cache_key = f"ctx::{query}"
        cached = self.get(session_id, cache_key)
        if cached is not None:
            duration_ms = (time.perf_counter() - start_time) * 1000
            emit_memory_event(
                operation=MemoryOperation.READ,
                component=self.COMPONENT,
                object_type=self.OBJECT_TYPE,
                object_id=session_id,
                result=MemoryResult.FOUND,
                duration_ms=duration_ms,
                phase="session_rag.get_context_cached",
            )
            return cached

        from memory import get_rag
        context = get_rag().get_context(query, user_id=user_id)
        self.set(session_id, cache_key, context)
        return context


class SessionSemanticStore(BaseSessionStore):
    """Per-session кэш семантической памяти.

    Кэширует найденные процедуры и результаты поиска знаний по ключу
    сессии, изолируя «горячий» контекст одной сессии от другой.
    """

    COMPONENT = MemoryComponent.SEMANTIC_MEMORY
    OBJECT_TYPE = MemoryObjectType.PROCEDURE

    def find_applicable_procedure(self, session_id: str, text: str):
        """Возвращает применимую процедуру с per-session кэшированием."""
        if not session_id:
            from memory import get_semantic_memory
            return get_semantic_memory().find_applicable_procedure(text)

        cache_key = f"proc::{text[:80]}"
        cached = self.get(session_id, cache_key)
        if cached is not None:
            return cached

        from memory import get_semantic_memory
        procedure = get_semantic_memory().find_applicable_procedure(text)
        self.set(session_id, cache_key, procedure)
        return procedure


class SessionEpisodicStore(BaseSessionStore):
    """Per-session кэш эпизодической памяти.

    Кэширует результаты поиска похожих ситуаций для сессии, чтобы
    каждый turn не дублировал дорогой поиск по БД.
    """

    COMPONENT = MemoryComponent.EPISODIC_MEMORY
    OBJECT_TYPE = MemoryObjectType.EPISODE

    def search_episodes(self, session_id: str, query: str, limit: int = 2, user_id: Optional[str] = None):
        """Возвращает похожие эпизоды с per-session кэшированием."""
        if not session_id:
            from memory import get_episodic_memory
            return get_episodic_memory().search_episodes(query, limit=limit, user_id=user_id)

        cache_key = f"ep::{query[:80]}::{limit}"
        cached = self.get(session_id, cache_key)
        if cached is not None:
            return cached

        from memory import get_episodic_memory
        episodes = get_episodic_memory().search_episodes(query, limit=limit, user_id=user_id)
        self.set(session_id, cache_key, episodes)
        return episodes


# === Глобальные экземпляры ===
_rag_store: Optional[SessionRAGStore] = None
_semantic_store: Optional[SessionSemanticStore] = None
_episodic_store: Optional[SessionEpisodicStore] = None
_module_lock = threading.Lock()


def get_session_rag_store() -> SessionRAGStore:
    global _rag_store
    with _module_lock:
        if _rag_store is None:
            _rag_store = SessionRAGStore()
        return _rag_store


def get_session_semantic_store() -> SessionSemanticStore:
    global _semantic_store
    with _module_lock:
        if _semantic_store is None:
            _semantic_store = SessionSemanticStore()
        return _semantic_store


def get_session_episodic_store() -> SessionEpisodicStore:
    global _episodic_store
    with _module_lock:
        if _episodic_store is None:
            _episodic_store = SessionEpisodicStore()
        return _episodic_store


def reset_session_stores():
    """Сброс для тестов."""
    global _rag_store, _semantic_store, _episodic_store
    with _module_lock:
        _rag_store = None
        _semantic_store = None
        _episodic_store = None
