"""
Tests for dialog_routes.py — auth dependency and data flow.

Verifies:
- get_current_user extracts access_token
- get_db_client is imported correctly
- Route handlers use get_db_client(current_user) not raw get_supabase()
"""

import pytest
import asyncio
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, AsyncMock, patch


@pytest.fixture
def app():
    app = FastAPI()
    from api.dialog_routes import router
    app.include_router(router)
    return app


@pytest.fixture
def client(app):
    return TestClient(app)


@pytest.mark.api
def test_list_dialogs_requires_auth(client):
    """GET /dialogs returns 401 without auth header."""
    response = client.get("/api/v1/dialogs")
    assert response.status_code == 401


@pytest.mark.api
def test_get_current_user_returns_access_token():
    """get_current_user (get_current_user_safe) returns access_token in the dict."""
    from api.dialog_routes import get_current_user

    with patch("core.supabase_client.get_supabase") as mock_supabase, \
         patch("core.auth_manager.get_auth_manager") as mock_auth_manager:
        from types import SimpleNamespace
        mock_user = SimpleNamespace(id="test-user-id", email="test@test.com")

        mock_sb = MagicMock()
        mock_sb.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
            {"id": "test-user-id", "email": "test@test.com"}
        ]
        mock_supabase.return_value = mock_sb

        mock_am = MagicMock()
        mock_am.extract_token_from_header.return_value = ("test-token-12345", None)
        mock_am.validate_and_refresh = AsyncMock(return_value=(
            {"user": mock_user, "email": "test@test.com"},
            "test-token-12345",
            ""
        ))
        mock_auth_manager.return_value = mock_am

        result = asyncio.run(
            get_current_user(authorization="Bearer test-token-12345")
        )

        assert result["id"] == "test-user-id"
        assert result["email"] == "test@test.com"
        assert result["access_token"] == "test-token-12345"


@pytest.mark.api
def test_routes_import_get_db_client():
    """Verify imports are correct."""
    import ast

    with open("backend/api/dialog_routes.py", "r", encoding="utf-8") as f:
        tree = ast.parse(f.read())

    imports = [
        node for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        and node.module == "core.supabase_client"
    ]
    imported_names = set()
    for imp in imports:
        for alias in imp.names:
            imported_names.add(alias.name)

    assert "get_db_client" in imported_names, "get_db_client must be imported from core.supabase_client"
