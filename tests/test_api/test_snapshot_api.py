"""Тесты для API снэпшотов."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from fastapi.testclient import TestClient
from backend.main import app


client = TestClient(app)

# CSRF middleware пропускает запросы с Bearer токеном
AUTH_HEADERS = {"Authorization": "Bearer test-token"}


def test_create_snapshot():
    res = client.post("/api/v1/experiments/snapshot?label=test-snapshot-api", headers=AUTH_HEADERS)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "created"
    assert "snapshot" in data
    assert data["snapshot"]["id"]
    return data["snapshot"]["id"]


def test_list_snapshots():
    res = client.get("/api/v1/experiments/snapshots", headers=AUTH_HEADERS)
    assert res.status_code == 200
    data = res.json()
    assert "snapshots" in data
    assert "total" in data
    assert isinstance(data["snapshots"], list)


def test_get_snapshot():
    snap_id = test_create_snapshot()
    res = client.get(f"/api/v1/experiments/snapshots/{snap_id}", headers=AUTH_HEADERS)
    assert res.status_code == 200
    data = res.json()
    assert data["snapshot"]["id"] == snap_id


def test_get_snapshot_not_found():
    res = client.get("/api/v1/experiments/snapshots/nonexistent-xyz", headers=AUTH_HEADERS)
    assert res.status_code == 404


def test_link_snapshot_to_run_missing():
    res = client.post("/api/v1/experiments/snapshots/abc123/link-to-run/nonexistent-run", headers=AUTH_HEADERS)
    assert res.status_code == 404
