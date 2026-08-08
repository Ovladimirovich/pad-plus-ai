"""
Тесты для SessionManager ↔ Supabase deduplication (Phase C4).

Политика:
- Supabase Auth — source of truth для auth-сессий.
- SessionManager — кэш: `user_id` = `session_id`, валидность сверяется с Supabase.
"""

import pytest
from backend.core.session_manager import SessionManager


def test_session_manager_user_id_mapping(tmp_path):
    sessions_file = tmp_path / "sessions.json"
    manager = SessionManager(data_path=str(sessions_file))

    supabase_user_id = "sup-user-uuid-12345"
    
    # Создаем сессию по Supabase user_id
    session = manager.get_or_create(user_id=supabase_user_id)
    assert session.session_id == supabase_user_id

    # Повторный запрос должен вернуть ту же сессию без создания новой
    session_again = manager.get_or_create(user_id=supabase_user_id)
    assert session_again.session_id == supabase_user_id
    assert manager.get_stats()["active_sessions"] == 1


def test_session_lifecycle_consistency_with_supabase(tmp_path):
    """C4: если пользователь удалён в Supabase, кэш-сессия инвалидируется."""
    sessions_file = tmp_path / "sessions.json"

    # Статус пользователя в "Supabase" (source of truth)
    active_users = {"user-alive", "user-deleted"}

    def fake_auth_validator(user_id: str) -> bool:
        return user_id in active_users

    manager = SessionManager(
        data_path=str(sessions_file),
        auth_validator=fake_auth_validator,
        auth_cache_ttl_seconds=60,
    )

    # Создаём две сессии для активного и удалённого пользователя
    alive = manager.get_or_create(user_id="user-alive")
    deleted = manager.get_or_create(user_id="user-deleted")
    assert alive.session_id == "user-alive"
    assert deleted.session_id == "user-deleted"
    assert manager.get_stats()["active_sessions"] == 2

    # Пользователь "user-deleted" удаляется в Supabase
    active_users.discard("user-deleted")

    # Живой пользователь остаётся активным
    assert manager.get_session("user-alive") is not None

    # Удалённый пользователь — сессия инвалидируется (кэш-слой отдаёт None)
    assert manager.get_session("user-deleted") is None
    assert manager.get_stats()["active_sessions"] == 1


def test_anonymous_session_not_validated_against_supabase(tmp_path):
    """C4: анонимные сессии не проходят через Supabase-валидацию."""
    sessions_file = tmp_path / "sessions.json"

    calls = []
    def fake_auth_validator(user_id: str) -> bool:
        calls.append(user_id)
        return True

    manager = SessionManager(
        data_path=str(sessions_file),
        auth_validator=fake_auth_validator,
    )

    anon = manager.get_or_create(ip_address="127.0.0.1")
    assert anon.session_id.startswith("sess_")
    assert manager.get_session(anon.session_id) is not None
    assert calls == [], "Анонимные сессии не должны вызывать auth-валидатор"

