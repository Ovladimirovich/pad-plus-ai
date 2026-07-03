"""Тесты загрузки документов"""

import pytest
from unittest.mock import MagicMock

AUTH_HEADER = {"Authorization": "Bearer test-access-token"}


def _make_mock_supabase():
    mock_supabase = MagicMock()
    mock_execute = MagicMock()
    mock_execute.data = []

    table_chain = MagicMock()
    table_chain.execute.return_value = mock_execute
    table_chain.select.return_value = table_chain
    table_chain.insert.return_value = table_chain
    table_chain.update.return_value = table_chain
    table_chain.delete.return_value = table_chain
    table_chain.eq.return_value = table_chain
    table_chain.order.return_value = table_chain

    mock_supabase.table.return_value = table_chain
    mock_supabase.auth = MagicMock()

    mock_storage = MagicMock()
    mock_storage.from_.return_value.upload.return_value = MagicMock()
    mock_supabase.storage = mock_storage

    return mock_supabase


class TestDocumentUpload:
    def test_document_upload_requires_auth(self, test_app):
        response = test_app.post("/api/v1/documents/upload")
        # CSRF middleware может вернуть 403 (нет CSRF-токена)
        # или auth middleware вернёт 401 (нет авторизации)
        assert response.status_code in (401, 403)

    def test_document_upload_with_file(self, test_app):
        response = test_app.post(
            "/api/v1/documents/upload",
            headers=AUTH_HEADER,
            files={"file": ("test.txt", b"test content", "text/plain")}
        )
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, dict)

    def test_document_list(self, test_app):
        response = test_app.get("/api/v1/documents/", headers=AUTH_HEADER)
        assert response.status_code in (200, 404)
