"""Tests for D'-2 Session Stores (per-session cache isolation)."""

import pytest

from memory.session_store import (
    SessionRAGStore, SessionSemanticStore, SessionEpisodicStore,
    reset_session_stores,
)


@pytest.fixture(autouse=True)
def _reset_stores():
    reset_session_stores()
    yield
    reset_session_stores()


class TestSessionRAGStore:
    def test_set_get_isolated(self):
        store = SessionRAGStore()
        store.set("sess_a", "ctx::hello", "context A")
        assert store.get("sess_a", "ctx::hello") == "context A"
        assert store.get("sess_b", "ctx::hello", "EMPTY") == "EMPTY"

    def test_clear_session(self):
        store = SessionRAGStore()
        store.set("sess_a", "k", "v")
        store.clear_session("sess_a")
        assert store.get("sess_a", "k", "EMPTY") == "EMPTY"
        assert store.get_active_count() == 0

    def test_delete_key(self):
        store = SessionRAGStore()
        store.set("sess_a", "k", "v")
        store.delete("sess_a", "k")
        assert store.get("sess_a", "k", "EMPTY") == "EMPTY"

    def test_get_context_fallback_without_session(self):
        store = SessionRAGStore()
        # Без session_id падает на глобальный RAG (без DATABASE_URL -> "")
        ctx = store.get_context("", "привет")
        assert isinstance(ctx, str)

    def test_stats(self):
        store = SessionRAGStore()
        store.set("sess_a", "k", "v")
        store.set("sess_b", "k", "v2")
        stats = store.get_stats()
        assert stats["active_sessions"] == 2
        assert stats["max_sessions"] == 500


class TestSessionSemanticStore:
    def test_isolated(self):
        store = SessionSemanticStore()
        store.set("sess_a", "proc::hello", "proc1")
        assert store.get("sess_a", "proc::hello") == "proc1"
        assert store.get("sess_b", "proc::hello", "EMPTY") == "EMPTY"

    def test_fallback_without_session(self):
        store = SessionSemanticStore()
        proc = store.find_applicable_procedure("", "привет")
        assert proc is None or hasattr(proc, "name")


class TestSessionEpisodicStore:
    def test_isolated(self):
        store = SessionEpisodicStore()
        store.set("sess_a", "ep::hello", [{"id": 1}])
        assert store.get("sess_a", "ep::hello") == [{"id": 1}]
        assert store.get("sess_b", "ep::hello", "EMPTY") == "EMPTY"

    def test_fallback_without_session(self):
        store = SessionEpisodicStore()
        eps = store.search_episodes("", "привет", limit=2)
        assert isinstance(eps, list)


class TestEviction:
    def test_lru_evicts_oldest(self):
        store = SessionRAGStore()
        store.MAX_SESSIONS = 2
        store.set("sess_1", "k", "v")
        store.set("sess_2", "k", "v")
        # Трогаем sess_1, чтобы sess_2 стал самым старым
        store.get("sess_1", "k")
        store._evict_lru()
        assert store.get_active_count() == 2
        store.set("sess_3", "k", "v")
        store._evict_lru()
        # sess_2 должен быть вытеснен
        assert "sess_2" not in store._sessions
        assert store.get_active_count() == 2

    def test_expired_evicted(self):
        import time as _time
        store = SessionRAGStore()
        store.set("sess_1", "k", "v")
        store._last_access["sess_1"] = store._last_access["sess_1"].replace(
            year=store._last_access["sess_1"].year - 1
        )
        store._evict_expired()
        assert store.get_active_count() == 0
