"""Tests for D'-3 Lifecycle & Forgetting (TTL/quota/importance eviction)."""

import sqlite3
from datetime import datetime, timedelta

import pytest

from memory.lifecycle import (
    MemoryLifecycleConfig, MemoryLifecycleManager, get_lifecycle, reset_lifecycle,
)
from memory import episodic as ep_mod
from memory import semantic as sem_mod


@pytest.fixture(autouse=True)
def _reset():
    reset_lifecycle()
    yield
    reset_lifecycle()


@pytest.fixture
def episodic(tmp_path):
    store = ep_mod.EpisodicMemory(db_path=str(tmp_path / "ep.db"))
    store.clear()
    yield store
    store.clear()


@pytest.fixture
def semantic(tmp_path):
    store = sem_mod.SemanticMemory(db_path=str(tmp_path / "sem.db"))
    store.clear()
    yield store
    store.clear()


def _age_row(db_path, table, column, match_key, match_value, hours):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    old_ts = (datetime.now() - timedelta(hours=hours)).isoformat()
    cur.execute(f"UPDATE {table} SET {column}=? WHERE {match_key}=?", (old_ts, match_value))
    conn.commit()
    conn.close()


class TestLifecycleConfig:
    def test_defaults(self):
        cfg = MemoryLifecycleConfig()
        assert cfg.get_ttl_hours("episodic") == 30 * 24
        assert cfg.get_ttl_hours("roots") is None
        assert cfg.get_strategy("episodic") == "ttl+importance"
        assert cfg.get_max_items("semantic") == 50000

    def test_to_dict(self):
        cfg = MemoryLifecycleConfig()
        d = cfg.to_dict()
        assert "ttl_hours" in d and "max_items" in d and "forgetting_strategy" in d


class TestEpisodicLifecycle:
    def test_delete_expired_protects_important(self, episodic):
        episodic.add_episode(user_message="старый", ai_response="ok", significance=0.2, topic="old")
        episodic.add_episode(user_message="важный", ai_response="ok", significance=0.95, topic="important")
        episodic.add_episode(user_message="свежий", ai_response="ok", significance=0.2, topic="new")

        _age_row(episodic.db_path, "episodes", "timestamp", "topic", "old", 50)
        _age_row(episodic.db_path, "episodes", "timestamp", "topic", "important", 50)

        expired, protected = episodic.delete_expired(max_age_hours=24)
        assert expired == 1
        assert protected == 1
        assert episodic.get_count() == 2

    def test_delete_expired_nothing_stale(self, episodic):
        episodic.add_episode(user_message="свежий", ai_response="ok")
        expired, protected = episodic.delete_expired(max_age_hours=24)
        assert expired == 0
        assert protected == 0

    def test_delete_by_id(self, episodic):
        ep = episodic.add_episode(user_message="x", ai_response="y")
        assert episodic.delete_by_id(ep.id) is True
        assert episodic.get_episode(ep.id) is None
        assert episodic.delete_by_id(ep.id) is False

    def test_get_count(self, episodic):
        episodic.add_episode(user_message="1", ai_response="a")
        episodic.add_episode(user_message="2", ai_response="b")
        assert episodic.get_count() == 2

    def test_get_all(self, episodic):
        episodic.add_episode(user_message="1", ai_response="a")
        episodic.add_episode(user_message="2", ai_response="b")
        assert len(episodic.get_all()) == 2


class TestSemanticLifecycle:
    def test_delete_expired_protects_important(self, semantic):
        semantic.add_knowledge(content="старое", confidence=0.2)
        semantic.add_knowledge(content="важное", confidence=0.95)
        _age_row(semantic.db_path, "semantic_knowledge", "created_at", "content", "старое", 200)
        _age_row(semantic.db_path, "semantic_knowledge", "created_at", "content", "важное", 200)

        expired, protected = semantic.delete_expired(max_age_hours=100)
        assert expired == 1
        assert protected == 1
        assert semantic.get_count() == 1

    def test_delete_by_id(self, semantic):
        k = semantic.add_knowledge(content="тест")
        assert semantic.delete_by_id(k.id) is True
        assert semantic.get_knowledge(k.id) is None

    def test_get_count_get_all(self, semantic):
        semantic.add_knowledge(content="1")
        semantic.add_knowledge(content="2")
        assert semantic.get_count() == 2
        assert len(semantic.get_all()) == 2


class TestLifecycleManager:
    def test_run_maintenance_ttl(self, episodic, semantic):
        episodic.add_episode(user_message="старый", ai_response="ok", significance=0.2, topic="old")
        semantic.add_knowledge(content="старое", confidence=0.2)
        _age_row(episodic.db_path, "episodes", "timestamp", "topic", "old", 50)
        _age_row(semantic.db_path, "semantic_knowledge", "created_at", "content", "старое", 200)

        cfg = MemoryLifecycleConfig()
        cfg.ttl_hours["episodic"] = 24
        cfg.ttl_hours["semantic"] = 100
        cfg.max_items["episodic"] = None
        cfg.max_items["semantic"] = None

        mgr = MemoryLifecycleManager(cfg)
        results = mgr.run_maintenance(episodic=episodic, semantic=semantic)
        assert results["episodic"].expired == 1
        assert results["semantic"].expired == 1

    def test_run_maintenance_quota(self, episodic):
        for i in range(6):
            episodic.add_episode(user_message=f"эпизод {i}", ai_response="ok", significance=0.1 + i * 0.1)

        cfg = MemoryLifecycleConfig()
        cfg.ttl_hours["episodic"] = None
        cfg.max_items["episodic"] = 3
        mgr = MemoryLifecycleManager(cfg)
        results = mgr.run_maintenance(episodic=episodic)
        assert results["episodic"].evicted >= 1
        assert episodic.get_count() <= 3

    def test_stats_and_history(self, episodic):
        cfg = MemoryLifecycleConfig()
        cfg.ttl_hours["episodic"] = None
        cfg.max_items["episodic"] = 1000
        mgr = MemoryLifecycleManager(cfg)
        mgr.run_maintenance(episodic=episodic)
        stats = mgr.get_stats()
        assert stats["total_runs"] == 1
        assert "by_component" in stats
        assert "config" in stats

    def test_global_getter(self):
        lm = get_lifecycle()
        assert isinstance(lm, MemoryLifecycleManager)
        assert get_lifecycle() is lm


class TestImpulseStackLimit:
    def test_stack_limited_to_max(self):
        from core.impulse.core import ImpulseCore
        core = ImpulseCore()
        for _ in range(ImpulseCore.MAX_STACK_DEPTH + 20):
            core.push()
        assert core.stack_depth() <= ImpulseCore.MAX_STACK_DEPTH
