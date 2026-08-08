"""
SessionEmotionStore — per-session хранение эмоций.

Вместо глобального синглтона get_pad_model():
  store = get_session_emotion_store()
  pad = store.get_or_create(session_id)
"""

from __future__ import annotations

import logging
import os
import threading
import time
from datetime import datetime
from typing import Dict, Optional

from .pad_model import PADModel
from core.xray.memory_trace import (
    emit_memory_event, MemoryOperation, MemoryComponent, MemoryObjectType, MemoryResult
)

logger = logging.getLogger("padplus.emotion.store")

SESSION_EMOTION_DATA_DIR = "data"


class SessionEmotionStore:
    """Per-session EmotionState store с TTL/LRU eviction."""

    MAX_SESSIONS = 500
    MAX_AGE_HOURS = 24
    CLEANUP_INTERVAL = 100

    def __init__(self, base_path: str | None = None):
        if base_path is None:
            base_path = str(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            )
        self.base_path = base_path
        self._sessions: Dict[str, PADModel] = {}
        self._last_access: Dict[str, datetime] = {}
        self._lock = threading.RLock()
        self._access_count = 0

    def get_or_create(self, session_id: str) -> PADModel:
        """Возвращает PADModel для сессии, создаёт если нет."""
        start_time = time.perf_counter()
        
        if not session_id:
            return self._get_fallback()
        with self._lock:
            self._maybe_cleanup()
            if session_id not in self._sessions:
                state_file = os.path.join(self.base_path, "data", f"emotion_state_{session_id}.json")
                self._sessions[session_id] = PADModel(state_file=state_file)
            self._last_access[session_id] = datetime.now()
            
            duration_ms = (time.perf_counter() - start_time) * 1000
            
            emit_memory_event(
                operation=MemoryOperation.READ,
                component=MemoryComponent.EMOTION_ENGINE,
                object_type=MemoryObjectType.EMOTION_STATE,
                object_id=session_id,
                result=MemoryResult.FOUND if session_id in self._sessions else MemoryResult.CREATED,
                duration_ms=duration_ms,
                phase="get_or_create",
            )
            
            return self._sessions[session_id]

    def _get_fallback(self) -> PADModel:
        """Fallback для сессий без session_id (тесты, legacy)."""
        key = "__fallback__"
        with self._lock:
            if key not in self._sessions:
                state_file = os.path.join(self.base_path, "data", "emotion_state.json")
                self._sessions[key] = PADModel(state_file=state_file)
            return self._sessions[key]

    def save(self, session_id: str) -> None:
        """Сохраняет состояние эмоций для сессии."""
        start_time = time.perf_counter()
        
        with self._lock:
            pad = self._sessions.get(session_id)
            if pad:
                pad.save()
                
                duration_ms = (time.perf_counter() - start_time) * 1000
                
                emit_memory_event(
                    operation=MemoryOperation.WRITE,
                    component=MemoryComponent.EMOTION_ENGINE,
                    object_type=MemoryObjectType.EMOTION_STATE,
                    object_id=session_id,
                    result=MemoryResult.UPDATED,
                    duration_ms=duration_ms,
                    phase="save",
                )

    def save_all(self) -> None:
        """Сохраняет все активные сессии."""
        with self._lock:
            for session_id, pad in list(self._sessions.items()):
                try:
                    pad.save()
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

    def get_all_states(self) -> dict:
        """Возвращает состояния всех сессий (для админки)."""
        with self._lock:
            return {
                sid: pad.get_state().to_dict()
                for sid, pad in self._sessions.items()
            }

    def get_aggregate(self) -> PADModel:
        """Возвращает агрегатную PAD-модель (среднее по всем сессиям).
        Используется для dashboard-эндпоинтов без session_id."""
        with self._lock:
            if not self._sessions:
                return self._get_fallback()
            states = [pad.get_state() for pad in self._sessions.values()]
            if not states:
                return self._get_fallback()
            # Среднее по всем измерениям
            n = len(states)
            sum_state = states[0]
            for s in states[1:]:
                sum_state.pleasure += s.pleasure
                sum_state.arousal += s.arousal
                sum_state.dominance += s.dominance
                sum_state.curiosity += s.curiosity
                sum_state.confidence += s.confidence
                sum_state.social_connection += s.social_connection
            # Делим на n
            sum_state.pleasure /= n
            sum_state.arousal /= n
            sum_state.dominance /= n
            sum_state.curiosity /= n
            sum_state.confidence /= n
            sum_state.social_connection /= n
            aggregated = PADModel(session_id="__aggregate__")
            aggregated._state = sum_state
            return aggregated

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
                try:
                    self._sessions[sid].save()
                except Exception:
                    pass
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
                try:
                    self._sessions[sid].save()
                except Exception:
                    pass
                del self._sessions[sid]
                del self._last_access[sid]


_module_store: Optional[SessionEmotionStore] = None
_module_lock = threading.Lock()


def get_session_emotion_store() -> SessionEmotionStore:
    global _module_store
    with _module_lock:
        if _module_store is None:
            _module_store = SessionEmotionStore()
        return _module_store


def reset_store():
    """Сброс для тестов."""
    global _module_store
    with _module_lock:
        _module_store = None
