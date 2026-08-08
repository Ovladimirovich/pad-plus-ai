"""
Load-test: 50 конкурентных сессий (Phase C, DoD).

Цель: проверить, что SessionManager при параллельных операциях:
- не теряет сессии (no race on _sessions dict),
- не кладёт cross-session состояние (изоляция контекста),
- не портит файл sessions.json при конкурентных _save(),
- не оставляет утечек (active_sessions == создано).

Политика: аuth-сессии валидируются против Supabase (source of truth),
поэтому для теста инжектим поддельный auth_validator.
"""

import json
import threading

import pytest

from backend.core.session_manager import SessionManager


class FakeAuthStack:
    """Потокобезопасный auth-стек: True для всех известных user id."""

    def __init__(self):
        self._lock = threading.Lock()
        self._users = set()

    def add(self, user_id):
        with self._lock:
            self._users.add(user_id)

    def __call__(self, user_id: str) -> bool:
        with self._lock:
            return user_id in self._users


def _make_manager(tmp_path, auth_stack=None):
    return SessionManager(
        data_path=str(tmp_path / "sessions.json"),
        auth_validator=auth_stack,
        auth_cache_ttl_seconds=5,
    )


def _run_concurrently(worker, n: int = 50):
    """Запускает worker(i) в n потоках, собирает исключения."""
    barrier = threading.Barrier(n)
    errors = []
    results = [None] * n

    def target(i):
        try:
            barrier.wait()  # синхронный старт всех потоков
            results[i] = worker(i)
        except Exception as e:
            errors.append((i, e))

    threads = [threading.Thread(target=target, args=(i,)) for i in range(n)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=30)
    return errors, results


class TestConcurrentSessions:

    def test_50_concurrent_session_creation_no_loss(self, tmp_path):
        auth = FakeAuthStack()
        # Объявляем 50 пользователей валидными в "Supabase"
        users = [f"user-{i:03d}" for i in range(50)]
        for u in users:
            auth.add(u)

        manager = _make_manager(tmp_path, auth)
        errors, _ = _run_concurrently(lambda i: manager.get_or_create(user_id=users[i]))

        assert errors == [], f"Конкурентные создания не должны падать: {errors}"
        assert manager.get_stats()["active_sessions"] == 50

    def test_concurrent_get_or_create_returns_same_session(self, tmp_path):
        """Гонка get_or_create для одного user_id не должна плодить дубликаты."""
        auth = FakeAuthStack()
        auth.add("user-single")
        manager = _make_manager(tmp_path, auth)

        errors, results = _run_concurrently(
            lambda i: manager.get_or_create(user_id="user-single"), n=30
        )
        assert errors == [], f"Нет ошибок, но гонки могли дать None: {errors}"
        for sess in results:
            assert sess.session_id == "user-single"
        assert manager.get_stats()["active_sessions"] == 1

    def test_records_are_isolated_per_session(self, tmp_path):
        """Контексты 50 сессий не должны пересекаться."""
        auth = FakeAuthStack()
        users = [f"user-{i:03d}" for i in range(50)]
        for u in users:
            auth.add(u)
        manager = _make_manager(tmp_path, auth)

        def work(i):
            sid = manager.get_or_create(user_id=users[i]).session_id
            # Каждая сессия пишет СВОЮ тему
            manager.record_message(sid, intent=f"intent-{i}", topic=f"topic-{i}")

        errors, _ = _run_concurrently(work)
        assert not errors

        for i in range(50):
            sess = manager.get_session(users[i])
            assert sess is not None
            assert sess.context.last_intent == f"intent-{i}", f"Сессия {i} засорена"
            assert sess.context.topics_discussed == [f"topic-{i}"]

        assert manager.get_stats()["active_sessions"] == 50

    def test_concurrent_save_keeps_file_valid(self, tmp_path):
        """После конкурентных write/delete файл sessions.json остаётся валидным JSON."""
        auth = FakeAuthStack()
        users = [f"user-{i:03d}" for i in range(50)]
        for u in users:
            auth.add(u)
        manager = _make_manager(tmp_path, auth)
        sessions_file = tmp_path / "sessions.json"

        def work(i):
            sid = manager.get_or_create(user_id=users[i]).session_id
            manager.record_message(sid, topic=f"t-{i}")
            if i % 2 == 0:
                manager.end_session(sid)

        errors, _ = _run_concurrently(work)
        assert not errors

        with open(sessions_file, "r", encoding="utf-8") as f:
            payload = json.load(f)  # падение = испорченный файл
        assert isinstance(payload, dict)
        assert "sessions" in payload