"""Тесты запуска приложения"""

import pytest


class TestAppStartup:
    def test_app_imports(self):
        import os
        os.environ["TEST_MODE"] = "true"

        import backend.core.supabase_client as sc
        from unittest.mock import MagicMock
        sc._supabase = MagicMock()
        sc._supabase.table.return_value.select.return_value.execute.return_value.data = []

        from backend.main import app
        assert app is not None
        assert app.title == "PAD+ AI"
        assert app.version == "4.0.0"

    def test_health_endpoint(self, test_app):
        response = test_app.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_cors_headers(self, test_app):
        response = test_app.get(
            "/health",
            headers={"Origin": "http://localhost:5173"}
        )
        assert response.status_code == 200
        assert "access-control-allow-origin" in response.headers
