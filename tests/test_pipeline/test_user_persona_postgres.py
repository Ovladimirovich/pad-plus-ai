from unittest.mock import MagicMock, patch

import pytest

from memory.user_persona import UserPersona
from memory.user_persona_postgres import UserPersonaPostgresManager


@pytest.fixture
def mock_supabase():
    with patch("memory.user_persona_postgres.get_supabase") as mock_get:
        mock_client = MagicMock()
        mock_client.table.return_value.select.return_value.execute.return_value.data = []
        mock_get.return_value = mock_client
        yield mock_get


def test_init_loads_personas(mock_supabase):
    mock_client = mock_supabase.return_value
    mock_client.table.return_value.select.return_value.execute.return_value.data = [
        {
            "user_id": "user1",
            "data": {
                "user_id": "user1",
                "style_preferences": {"verbosity": 0.7},
                "interests": [],
                "frequent_topics": {},
                "total_interactions": 5,
                "preferred_providers": [],
                "preferred_models": {},
                "evolution_history": [],
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-01T00:00:00",
            },
        }
    ]
    mgr = UserPersonaPostgresManager()
    persona = mgr.get_persona("user1")
    assert persona.style_preferences["verbosity"] == 0.7
    assert persona.total_interactions == 5


def test_get_persona_creates_new(mock_supabase):
    mgr = UserPersonaPostgresManager()
    persona = mgr.get_persona("new_user")
    assert persona.user_id == "new_user"
    assert persona.style_preferences["verbosity"] == 0.5


def test_save_persona_upserts(mock_supabase):
    mgr = UserPersonaPostgresManager()
    persona = mgr.get_persona("test_user")
    persona.style_preferences["verbosity"] = 0.9
    mgr.save_persona(persona)

    mock_client = mock_supabase.return_value
    mock_client.table.return_value.upsert.assert_called_once()
    call_args = mock_client.table.return_value.upsert.call_args[0][0]
    assert call_args["user_id"] == "test_user"
    assert call_args["data"]["style_preferences"]["verbosity"] == 0.9


def test_save_persona_updates_timestamp(mock_supabase):
    mgr = UserPersonaPostgresManager()
    persona = mgr.get_persona("t")
    old_updated = persona.updated_at
    mgr.save_persona(persona)
    assert persona.updated_at != old_updated


def test_get_stats_empty(mock_supabase):
    mgr = UserPersonaPostgresManager()
    stats = mgr.get_stats()
    assert stats["total_users"] == 0


def test_get_stats_with_users(mock_supabase):
    mgr = UserPersonaPostgresManager()
    p1 = mgr.get_persona("u1")
    p1.total_interactions = 10
    mgr.save_persona(p1)
    p2 = mgr.get_persona("u2")
    p2.total_interactions = 5
    mgr.save_persona(p2)

    stats = mgr.get_stats()
    assert stats["total_users"] == 2
    assert stats["total_interactions"] == 15
    assert stats["avg_interactions_per_user"] == 7.5
    assert stats["storage"] == "postgres"
