from unittest.mock import patch

import pytest


def test_get_user_persona_manager_postgres():
    """Postgres path: production + DATABASE_URL (см. get_user_persona_manager)."""
    env = {
        "APP_ENV": "production",
        "DATABASE_URL": "postgresql://localhost:5432/test",
    }
    with patch.dict("os.environ", env, clear=False):
        # clear=False сохраняет PATH; сбросим только кэш env-хелпера если есть
        with patch("memory.user_persona.UserPersonaManager") as mock_json, \
             patch("memory.user_persona_postgres.UserPersonaPostgresManager") as mock_pg:
            mock_pg.return_value.get_persona.return_value = None

            import memory.user_persona as mod

            mod._persona_manager = None

            mgr = mod.get_user_persona_manager()
            mock_pg.assert_called_once()
            mock_json.assert_not_called()
            assert mgr is mock_pg.return_value

            # cleanup cache so other tests don't get postgres manager
            mod._persona_manager = None


def test_get_user_persona_manager_json():
    """Development (default) always uses JSON even if DATABASE_URL is set."""
    env = {
        "APP_ENV": "development",
    }
    with patch.dict("os.environ", env, clear=False):
        with patch("memory.user_persona.UserPersonaManager") as mock_json:
            mock_json.return_value.get_persona.return_value = None

            import memory.user_persona as mod

            mod._persona_manager = None
            # remove production triggers for this process
            with patch.dict("os.environ", {"APP_ENV": "development", "RENDER": ""}, clear=False):
                mgr = mod.get_user_persona_manager()
            mock_json.assert_called_once()
            assert mgr is mock_json.return_value
            mod._persona_manager = None


def test_get_user_persona_manager_dev_ignores_database_url():
    """В development DATABASE_URL не переключает на Postgres."""
    with patch.dict(
        "os.environ",
        {
            "APP_ENV": "development",
            "DATABASE_URL": "postgresql://localhost:5432/test",
            "RENDER": "",
        },
        clear=False,
    ):
        with patch("memory.user_persona.UserPersonaManager") as mock_json, \
             patch("memory.user_persona_postgres.UserPersonaPostgresManager") as mock_pg:
            mock_json.return_value.get_persona.return_value = None

            import memory.user_persona as mod

            mod._persona_manager = None
            mod.get_user_persona_manager()
            mock_json.assert_called_once()
            mock_pg.assert_not_called()
            mod._persona_manager = None
