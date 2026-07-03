"""
Общие фикстуры для всех тестов
"""

import sys
import os
import pytest
import asyncio
from pathlib import Path
from unittest.mock import Mock, AsyncMock, MagicMock

project_root = str(Path(__file__).resolve().parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)
backend_path = str(Path(__file__).resolve().parent.parent / "backend")
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)


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
    mock_supabase.auth.get_user.return_value = MagicMock()
    mock_supabase.auth.get_user.return_value.user = MagicMock()
    mock_supabase.auth.get_user.return_value.user.id = "test-user-id"
    mock_supabase.auth.get_user.return_value.user.email = "test@test.com"
    return mock_supabase


def _patch_module_functions(module, mock_supabase):
    """Подменяет функции supabase_client в указанном модуле"""
    module.get_supabase = lambda: mock_supabase
    module.get_supabase_service = lambda: mock_supabase
    module.get_db_client = lambda current_user=None: mock_supabase
    module.check_database_connection = lambda: True
    module.create_supabase_client_with_access_token = lambda token: mock_supabase
    module.get_database_url = lambda: os.environ.get("DATABASE_URL")


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_app():
    os.environ["TEST_MODE"] = "true"
    os.environ["DATABASE_URL"] = "postgresql://test:test@localhost:5432/test"
    os.environ["SUPABASE_URL"] = "http://localhost:8000"
    os.environ["SUPABASE_KEY"] = "test-key"
    os.environ["CSRF_SECRET_KEY"] = "test-csrf-key-for-testing"

    mock_supabase = _make_mock_supabase()

    from backend.main import app

    # Шаг 1: патенчим core.supabase_client (базовый модуль)
    import core.supabase_client
    core.supabase_client._supabase = mock_supabase
    _patch_module_functions(core.supabase_client, mock_supabase)

    # Шаг 2: патенчим ВСЕ копии api.frontend_routes в sys.modules
    modules_to_patch = set()
    for mod_name, mod in list(sys.modules.items()):
        if mod_name.endswith("frontend_routes") or mod_name.endswith("document_routes") or mod_name.endswith("dialog_routes"):
            modules_to_patch.add(id(mod))

    for mod_name, mod in list(sys.modules.items()):
        if id(mod) in modules_to_patch:
            _patch_module_functions(mod, mock_supabase)

    # Шаг 3: патенчим get_current_user_safe
    import core.auth_manager
    from fastapi import HTTPException

    async def _mock_get_current_user_safe(authorization=None, x_refresh_token=None):
        if not authorization:
            raise HTTPException(
                status_code=401,
                detail={"error": "authorization_required", "message": "Требуется заголовок Authorization"}
            )
        return {
            "auth_user": MagicMock(),
            "profile": {"id": "test-user-id", "email": "test@test.com", "full_name": "Test User"},
            "id": "test-user-id",
            "email": "test@test.com",
            "access_token": "test-access-token",
            "authorization": "Bearer test-access-token",
        }

    core.auth_manager.get_current_user_safe = _mock_get_current_user_safe

    from fastapi.testclient import TestClient
    client = TestClient(app)
    yield client


@pytest.fixture
def mock_current_user():
    return {
        "auth_user": MagicMock(),
        "profile": {"id": "test-user-id", "email": "test@test.com", "full_name": "Test User"},
        "id": "test-user-id",
        "email": "test@test.com",
        "access_token": "test-access-token",
        "authorization": "Bearer test-access-token",
    }


@pytest.fixture
def mock_llm_response():
    return {
        "response": "Тестовый ответ",
        "provider": "test",
        "quality_score": 0.8,
        "quality_factors": {"relevance": 0.9, "coherence": 0.8},
        "concepts_extracted": ["тест", "концепт"],
        "rag_used": False
    }


@pytest.fixture
def mock_memory_record():
    record = Mock()
    record.id = "test_id"
    record.content = "Тестовый контент"
    record.metadata = {"type": "test"}
    record.timestamp = "2024-01-01T00:00:00Z"
    return record


@pytest.fixture
def sample_text():
    return "Это тестовый текст для проверки функциональности"


@pytest.fixture
def sample_dialog():
    return {
        "prompt": "Тестовый вопрос",
        "response": "Тестовый ответ",
        "timestamp": "2024-01-01T00:00:00Z",
        "metadata": {"provider": "test"}
    }


@pytest.fixture
def temp_dir(tmp_path):
    return tmp_path


@pytest.fixture
def mock_http_client():
    client = AsyncMock()
    client.post.return_value = Mock()
    client.post.return_value.status_code = 200
    client.post.return_value.json.return_value = {"status": "ok"}
    client.get.return_value = Mock()
    client.get.return_value.status_code = 200
    client.get.return_value.json.return_value = {"status": "ok"}
    return client


@pytest.fixture
def mock_websocket():
    ws = AsyncMock()
    ws.send_text = AsyncMock()
    ws.receive_text = AsyncMock(return_value="test message")
    ws.close = AsyncMock()
    return ws


@pytest.fixture(autouse=True)
def mock_env_vars(monkeypatch):
    monkeypatch.setenv("TEST_MODE", "true")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("DATABASE_URL", ":memory:")


@pytest.fixture
def sample_knowledge_graph():
    return {
        "nodes": [
            {"id": "concept1", "label": "Концепт 1", "type": "concept"},
            {"id": "concept2", "label": "Концепт 2", "type": "concept"}
        ],
        "edges": [
            {"source": "concept1", "target": "concept2", "relation": "related_to"}
        ]
    }


@pytest.fixture
def sample_persona_traits():
    return {
        "openness": 0.8,
        "conscientiousness": 0.7,
        "extraversion": 0.6,
        "agreeableness": 0.9,
        "neuroticism": 0.3
    }


@pytest.fixture
def sample_emotion_state():
    return {
        "pleasure": 0.7,
        "arousal": 0.5,
        "dominance": 0.6,
        "mood": "positive"
    }
