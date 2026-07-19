"""Тесты для API Decision Log."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)
AUTH_HEADERS = {"Authorization": "Bearer test-token"}


def test_list_decisions():
    res = client.get("/api/v1/decisions", headers=AUTH_HEADERS)
    assert res.status_code == 200
    data = res.json()
    assert "decisions" in data
    assert "total" in data


def test_decisions_stats():
    res = client.get("/api/v1/decisions/stats", headers=AUTH_HEADERS)
    assert res.status_code == 200
    data = res.json()
    assert "total" in data
    assert "by_component" in data


def test_get_decision_not_found():
    res = client.get("/api/v1/decisions/nonexistent-xyz", headers=AUTH_HEADERS)
    assert res.status_code == 404
