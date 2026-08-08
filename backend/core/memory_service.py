"""
🏗️ Unified Memory Service (D'-4)

Единая типизированная точка доступа ко всей памяти для pipeline-фаз.

Объединяет разрозненные хранилища под единый contract:
- SessionRAGStore / SessionSemanticStore / SessionEpisodicStore (кэш-слои)
- SessionEmotionStore (эмоции)
- SessionImpulseStore (импульсы)
- UserPersonaManager (персона пользователя)
- RootsMemory (корневая память)

Типизированные методы чтения/записи.
Синхронный интерфейс (хранилища синхронные), асинхронные обёртки — для фаз.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from core.xray.memory_trace import (
    emit_memory_event, MemoryOperation, MemoryComponent, MemoryObjectType, MemoryResult
)

logger = logging.getLogger("padplus.memory.service")


@dataclass
class MemorySnapshot:
    """Типизированный снимок всей памяти одной сессии."""
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    rag_context: str = ""
    episodic_context: str = ""
    procedure_context: str = ""
    procedure_name: Optional[str] = None
    emotion_state: Dict[str, Any] = field(default_factory=dict)
    emotion_style: Dict[str, Any] = field(default_factory=dict)
    impulse_state: Dict[str, Any] = field(default_factory=dict)
    impulse_bias: str = ""
    impulse_primary: str = ""
    persona_context: str = ""
    roots_context: str = ""
    sources: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "rag_context": self.rag_context,
            "episodic_context": self.episodic_context,
            "procedure_context": self.procedure_context,
            "procedure_name": self.procedure_name,
            "emotion_state": self.emotion_state,
            "emotion_style": self.emotion_style,
            "impulse_state": self.impulse_state,
            "impulse_bias": self.impulse_bias,
            "impulse_primary": self.impulse_primary,
            "persona_context": self.persona_context,
            "roots_context": self.roots_context,
            "sources": self.sources,
        }


class MemoryService:
    """
    Единая типised точка доступа ко всей памяти сессии.

    Использование:
        svc = MemoryService(session_id="...", user_id="...")
        snap = svc.snapshot()          # типизированный снимок всей памяти
        context = svc.to_memory_context()   # словарь для MemoryContext/PipelineContext
    """

    def __init__(
        self,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ):
        self.session_id = session_id
        self.user_id = user_id

        from memory.session_store import (
            get_session_rag_store, get_session_semantic_store, get_session_episodic_store,
        )
        self.rag_store = get_session_rag_store()
        self.semantic_store = get_session_semantic_store()
        self.episodic_store = get_session_episodic_store()

        from emotion.session_store import get_session_emotion_store
        self.emotion_store = get_session_emotion_store()

        from core.impulse.session_store import get_session_impulse_store
        self.impulse_store = get_session_impulse_store()

        self._user_persona = None
        self._roots = None

    # === Ленивые синглтоны глобальной памяти ===

    def _get_user_persona(self):
        if self._user_persona is None and self.user_id:
            try:
                from memory.user_persona import get_user_persona_manager
                self._user_persona = get_user_persona_manager()
            except Exception as e:
                logger.debug("UserPersona недоступен: %s", e)
        return self._user_persona

    def _get_roots(self):
        if self._roots is None:
            try:
                from memory.roots import get_roots_memory
                self._roots = get_roots_memory()
            except Exception as e:
                logger.debug("RootsMemory недоступен: %s", e)
        return self._roots

    # === Typed reads ===

    def get_recent_episodes(self, limit: int = 10) -> List[Any]:
        """Возвращает последние эпизоды сессии."""
        if not self.session_id:
            from memory import get_episodic_memory
            ep = get_episodic_memory()
            return ep.get_all_episodes(limit=limit, user_id=self.user_id)
        return self.episodic_store.get(self.session_id, "_recent", default=[])

    def search_episodes(self, query: str, limit: int = 3) -> List[Any]:
        """Ищет похожие эпизоды."""
        return self.episodic_store.search_episodes(self.session_id, query, limit=limit, user_id=self.user_id)

    def get_rag_context(self, query: str) -> str:
        """Возвращает RAG-контекст с per-session кэшем."""
        return self.rag_store.get_context(self.session_id, query, user_id=self.user_id)

    def search_semantic(self, query: str) -> List[Any]:
        """Возвращает знания из семантической памяти / процедуру."""
        return self.semantic_store.find_applicable_procedure(self.session_id, query)

    def get_emotion_state(self) -> Dict[str, Any]:
        """Возвращает типизированное эмоциональное состояние сессии."""
        pad = self.emotion_store.get_or_create(self.session_id)
        state = pad.get_state()
        return {
            "emotion_state": state.to_dict(),
            "emotion_style": state.get_style(),
        }

    def get_impulse_state(self) -> Dict[str, Any]:
        """Возвращает типизироваnное импульсное состояние сессии."""
        core = self.impulse_store.get_or_create(self.session_id)
        return {
            "impulse_state": core.to_dict(),
            "impulse_bias": core.get_bias_block(),
            "impulse_primary": core.get_primary_label(),
            "impulse_prompt_line": core.get_prompt_line(),
        }

    def get_persona_context(self) -> str:
        """Возвращает контекст персона пользователя."""
        mgr = self._get_user_persona()
        if mgr and self.user_id:
            try:
                persona = mgr.get_persona(self.user_id)
                return persona.get_context_for_prompt()
            except Exception as e:
                logger.debug("get_persona_context: %s", e)
        return ""

    def get_roots_context(self, max_items: int = 20) -> str:
        """Возвращает контекст из Roots (корневая память)."""
        roots = self._get_roots()
        if roots:
            try:
                return roots.export_for_context(max_items=max_items)
            except Exception as e:
                logger.debug("get_roots_context: %s", e)
        return ""

    def get_sources(self, query: str) -> Dict[str, Any]:
        """Возвращает источники RAG для данного запроса."""
        context = self.get_rag_context(query)
        return {
            "count": 1 if context else 0,
            "confidence": 0.8 if context else 0.0,
        }

    # === Typed writes ===

    def add_episode(
        self,
        user_message: str,
        ai_response: str,
        intent: str = "unknown",
        topic: str = "общее",
        significance: float = 0.5,
        user_id: Optional[str] = None,
    ) -> Optional[str]:
        """Сохраняет эпизод диалога."""
        try:
            from memory import get_episodic_memory
            ep = get_episodic_memory().add_episode(
                user_message=user_message,
                ai_response=ai_response,
                intent=intent,
                topic=topic,
                significance=significance,
                user_id=user_id or self.user_id,
            )
            return ep.id
        except Exception as e:
            logger.warning("add_episode: %s", e, exc_info=True)
            return None

    def add_fact(self, content: str, confidence: float = 0.5) -> Optional[str]:
        """Добавляет декларативное знание (факт)."""
        try:
            from memory import get_semantic_memory
            k = get_semantic_memory().add_knowledge(
                content=content,
                confidence=confidence,
            )
            return k.id
        except Exception as e:
            logger.warning("add_fact: %s", e, exc_info=True)
            return None

    def add_procedure(
        self,
        name: str,
        steps: List[str],
        triggers: List[str],
        domain: str = "general",
    ) -> Optional[str]:
        """Добавляет процедурное знание (навык)."""
        try:
            from memory import get_semantic_memory
            k = get_semantic_memory().learn_procedure(
                name=name,
                steps=steps,
                triggers=triggers,
                domain=domain,
            )
            return k.id
        except Exception as e:
            logger.warning("add_procedure: %s", e, exc_info=True)
            return None

    def apply_emotion_event(self, event_type: str, intensity: float = 0.1) -> None:
        """Применяет эмоциональное событие к модели сессии."""
        pad = self.emotion_store.get_or_create(self.session_id)
        pad.apply_event(event_type, intensity=intensity)
        self.emotion_store.save(self.session_id)

    def apply_impulse_delta(self, weights: Dict[str, float]) -> None:
        """Применяет дельта-изменение импульсов сессии."""
        core = self.impulse_store.get_or_create(self.session_id)
        core.set_from_labels(weights)
        self.impulse_store.save(self.session_id)

    # === Типизированный снимок ===

    def snapshot(self) -> MemorySnapshot:
        """Собирает типизированный снимок всей памяти сессии."""
        user_id = self.user_id
        snap = MemorySnapshot(
            session_id=self.session_id,
            user_id=user_id,
        )
        try:
            snap.rag_context = self.get_rag_context("")
        except Exception as e:
            logger.debug("snapshot rag: %s", e)
        try:
            emotion = self.get_emotion_state()
            snap.emotion_state = emotion.get("emotion_state", {})
            snap.emotion_style = emotion.get("emotion_style", {})
        except Exception as e:
            logger.debug("snapshot emotion: %s", e)
        try:
            imp = self.get_impulse_state()
            snap.impulse_state = imp.get("impulse_state", {})
            snap.impulse_bias = imp.get("impulse_bias", "")
            snap.impulse_primary = imp.get("impulse_primary", "")
        except Exception as e:
            logger.debug("snapshot impulse: %s", e)
        try:
            snap.persona_context = self.get_persona_context()
        except Exception:
            pass
        try:
            snap.roots_context = self.get_roots_context()
        except Exception:
            pass

        snap.sources = self.get_sources("")

        emit_memory_event(
            operation=MemoryOperation.READ,
            component=MemoryComponent.UNKNOWN,
            object_type=MemoryObjectType.CONTEXT,
            object_id=self.session_id,
            result=MemoryResult.FOUND,
            phase="memory_service.snapshot",
            session_id=self.session_id,
            metadata={"user_id": user_id},
        )
        return snap

    def to_memory_context(self, snapshot: Optional[MemorySnapshot] = None) -> Dict[str, Any]:
        """Формирует MemoryContext-flavored словарь для PipelineContext."""
        snap = snapshot or self.snapshot()
        return {
            "rag_context": snap.rag_context or "",
            "rag_used": bool(snap.rag_context),
            "episodic_context": snap.episodic_context or "",
            "procedure_name": snap.procedure_name,
            "procedure_context": snap.procedure_context,
            "emotion_state": snap.emotion_state,
            "emotion_style": snap.emotion_style,
            "impulse_state": snap.impulse_state,
            "impulse_bias": snap.impulse_bias,
            "impulse_primary": snap.impulse_primary,
            "persona_context": snap.persona_context,
            "roots_context": snap.roots_context,
            "sources": snap.sources,
        }


def get_memory_service(session_id: Optional[str] = None, user_id: Optional[str] = None) -> MemoryService:
    """Factory — создаёт MemoryService для сессии."""
    return MemoryService(session_id=session_id, user_id=user_id)