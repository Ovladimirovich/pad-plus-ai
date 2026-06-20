from unittest.mock import patch

import pytest


def test_get_user_persona_manager_postgres():
    with patch.dict("os.environ", {"DATABASE_URL": "postgresql://localhost:5432/test"}, clear=True):
        with patch("memory.user_persona.UserPersonaManager") as mock_json, \
             patch("memory.user_persona_postgres.UserPersonaPostgresManager") as mock_pg:
            mock_pg_instance = mock_pg.return_value
            mock_pg_instance.get_persona.return_value = None

            from memory.user_persona import _persona_manager, get_user_persona_manager

            # Cброс глобального кэша
            import memory.user_persona as mod
            mod._persona_manager = None

            mgr = get_user_persona_manager()
            mock_pg.assert_called_once()
            mock_json.assert_not_called()


def test_get_user_persona_manager_json():
    with patch.dict("os.environ", {}, clear=True):
        with patch("memory.user_persona.UserPersonaManager") as mock_json:
            mock_json_instance = mock_json.return_value
            mock_json_instance.get_persona.return_value = None

            from memory.user_persona import _persona_manager, get_user_persona_manager

            import memory.user_persona as mod
            mod._persona_manager = None

            mgr = get_user_persona_manager()
            mock_json.assert_called_once()
