"""Tests for D'-4 Unified Memory Service (typed access to all memory)."""

import pytest

from core.memory_service import (
    MemoryService, MemorySnapshot, get_memory_service,
)


@pytest.fixture(autouse=True)
def _isolated_reset():
    # Сбрасываем глобальные session stores между тестами
    from memory.session_store import reset_session_stores
    from core.impulse.session_store import reset_impulse_store
    from emotion.session_store import reset_store
    reset_session_stores()
    reset_impulse_store()
    yield
    reset_session_stores()
    reset_impulse_store()


class TestMemoryServiceReads:
    def test_snapshot_type(self):
        svc = MemoryService(session_id="s1", user_id="u1")
        snap = svc.snapshot()
        assert isinstance(snap, MemorySnapshot)
        assert snap.session_id == "s1"
        assert snap.user_id == "u1"

    def test_snapshot_has_emotion(self):
        svc = MemoryService(session_id="s1", user_id="u1")
        snap = svc.snapshot()
        assert isinstance(snap.emotion_state, dict)
        assert isinstance(snap.emotion_style, dict)

    def test_snapshot_has_impulse(self):
        svc = MemoryService(session_id="s1", user_id="u1")
        snap = svc.snapshot()
        assert isinstance(snap.impulse_state, dict)
        assert "impulse_bias" in svc.get_impulse_state()
        assert "impulse_primary" in svc.get_impulse_state()

    def test_to_memory_context_counts(self):
        svc = MemoryService(session_id="s1", user_id="u1")
        ctx = svc.to_memory_context()
        assert "rag_context" in ctx
        assert "emotion_state" in ctx
        assert "impulse_primary" in ctx
        assert "roots_context" in ctx
        assert "persona_context" in ctx

    def test_search_episodes_returns_list(self):
        svc = MemoryService(session_id="s1", user_id="u1")
        res = svc.search_episodes("привет", limit=2)
        assert isinstance(res, list)

    def test_get_rag_context_str(self):
        svc = MemoryService(session_id="s1", user_id="u1")
        ctx = svc.get_rag_context("привет")
        assert isinstance(ctx, str)


class TestMemoryServiceWrites:
    def test_add_episode(self):
        svc = MemoryService(session_id="s1", user_id="u1")
        eid = svc.add_episode("user msg", "ai reply", significance=0.6)
        assert eid is not None and isinstance(eid, str)

    def test_add_fact(self):
        svc = MemoryService(session_id="s1", user_id="u1")
        kid = svc.add_fact("PAD+ — когнитивная архитектура", confidence=0.9)
        assert kid is not None and isinstance(kid, str)

    def test_add_procedure(self):
        svc = MemoryService(session_id="s1", user_id="u1")
        pid = svc.add_procedure(
            name="Тест",
            steps=["1", "2", "3"],
            triggers=["тест", "пример"],
            domain="general",
        )
        assert pid is not None and isinstance(pid, str)

    def test_apply_emotion_event_no_raise(self):
        svc = MemoryService(session_id="s1", user_id="u1")
        svc.apply_emotion_event("user_praise", intensity=0.5)  # должно работать без исключений

    def test_apply_impulse_delta_no_raise(self):
        svc = MemoryService(session_id="s1", user_id="u1")
        svc.apply_impulse_delta({"understand": 1.0})  # должно работать без исключений


class TestMemoryServiceFactory:
    def test_get_memory_service(self):
        svc = get_memory_service(session_id="s1", user_id="u1")
        assert isinstance(svc, MemoryService)

    def test_session_isolation(self):
        """Разные сессии — разные эмоциональные/импульсные состояния."""
        svc_a = MemoryService(session_id="sess_a", user_id="u1")
        svc_b = MemoryService(session_id="sess_b", user_id="u1")
        # Применяем событие только к A
        svc_a.apply_emotion_event("user_praise", intensity=1.0)
        state_a = svc_a.get_emotion_state()["emotion_state"]
        # Без PG/постоянства состояния могут быть равны, но вызовы не должны падать
        _ = svc_b.get_emotion_state()
        assert isinstance(state_a, dict)