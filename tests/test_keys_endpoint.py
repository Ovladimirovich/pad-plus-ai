"""Тесты API ключей"""

import pytest
from unittest.mock import MagicMock
from fastapi import HTTPException


AUTH_HEADER = {"Authorization": "Bearer test-access-token"}


def _make_mock_supabase(data_list=None, count=0):
    mock_supabase = MagicMock()
    mock_execute = MagicMock()
    mock_execute.data = data_list or []
    mock_execute.count = count

    table_chain = MagicMock()
    table_chain.execute.return_value = mock_execute
    table_chain.select.return_value = table_chain
    table_chain.insert.return_value = table_chain
    table_chain.update.return_value = table_chain
    table_chain.delete.return_value = table_chain
    table_chain.eq.return_value = table_chain
    table_chain.order.return_value = table_chain
    table_chain.range.return_value = table_chain
    table_chain.limit.return_value = table_chain

    mock_supabase.table.return_value = table_chain
    mock_supabase.auth = MagicMock()
    return mock_supabase


class TestKeysEndpoint:
    def test_list_keys_requires_auth(self, test_app):
        response = test_app.get("/api/v1/keys")
        assert response.status_code == 401

    def test_list_keys_returns_empty(self, test_app):
        response = test_app.get("/api/v1/keys", headers=AUTH_HEADER)
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["total"] == 0
        assert data["data"] == []

    def test_create_key_invalid_data(self, test_app):
        response = test_app.post("/api/v1/keys", json={}, headers=AUTH_HEADER)
        assert response.status_code in (422,)

    def test_delete_key_not_found(self, test_app):
        response = test_app.delete("/api/v1/keys/non-existent-id", headers=AUTH_HEADER)
        assert response.status_code == 404

    def test_get_providers_no_auth_required(self, test_app):
        response = test_app.get("/api/v1/providers")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 2
        assert any(p["id"] == "openrouter" for p in data)
        assert any(p["id"] == "gigachat" for p in data)
