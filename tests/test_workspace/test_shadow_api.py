"""
Тесты для Shadow Mode API эндпоинта (ADR-0010).
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_shadow_stats_endpoint():
    # Импортируем функцию записи из динамически подключенного модуля
    import sys
    shadow_mod = sys.modules.get("api.shadow_routes")
    if not shadow_mod:
        import api.shadow_routes as shadow_mod

    shadow_mod.record_shadow_event(
        query="Test query for shadow analytics",
        stats={"keep": 2, "outdated": 1, "discard": 0, "conflict": 0, "uncertain": 1},
        latency_ms=2.5
    )

    response = client.get("/api/v1/memory/shadow/stats")
    assert response.status_code == 200
    data = response.json()

    assert data["total_queries"] >= 1
    assert data["verdicts_aggregate"]["keep"] >= 2
    assert data["verdicts_aggregate"]["outdated"] >= 1
    assert data["abstention_rate"] >= 0.0
    assert data["avg_latency_ms"] >= 0.0
    assert isinstance(data["recent_events"], list)
