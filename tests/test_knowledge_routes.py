"""Тесты для Knowledge Graph API — /api/v1/knowledge/*"""
import os
import sys
import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

project_root = str(Path(__file__).resolve().parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)
backend_path = str(Path(__file__).resolve().parent.parent / "backend")
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)


@pytest.fixture
def mock_graph():
    """Создаёт замокированный KnowledgeGraph с тестовыми данными"""
    from unittest.mock import MagicMock
    graph = MagicMock()

    # Концепции
    concept1 = MagicMock()
    concept1.id = "c1"
    concept1.name = "физика"
    concept1.concept_type = "concept"
    concept1.confidence = 0.9
    concept1.source = "test"
    concept1.to_dict.return_value = {
        "id": "c1", "name": "физика", "type": "concept",
        "confidence": 0.9, "source": "test",
        "created_at": "2024-01-01T00:00:00", "metadata": {}
    }

    concept2 = MagicMock()
    concept2.id = "c2"
    concept2.name = "квантовая механика"
    concept2.concept_type = "concept"
    concept2.confidence = 0.8
    concept2.source = "test"
    concept2.to_dict.return_value = {
        "id": "c2", "name": "квантовая механика", "type": "concept",
        "confidence": 0.8, "source": "test",
        "created_at": "2024-01-01T00:00:00", "metadata": {}
    }

    # Настройка методов
    graph.get_stats.return_value = {
        "nodes": 2, "edges": 1, "density": 0.5,
        "avg_confidence": 0.85, "networkx_available": True
    }
    graph.to_dict.return_value = {
        "nodes": [concept1.to_dict(), concept2.to_dict()],
        "links": [{"source": "c1", "target": "c2", "type": "related", "weight": 0.9}],
        "stats": {"nodes": 2, "edges": 1, "density": 0.5}
    }
    graph.find_concepts.return_value = [concept1]
    graph.get_concept.return_value = concept1
    graph.get_related.return_value = [concept2]

    return graph


@pytest.mark.api
class TestKnowledgeStats:
    def test_stats_success(self, test_app, mock_graph):
        with patch("knowledge.graph.get_knowledge_graph", return_value=mock_graph):
            response = test_app.get("/api/v1/knowledge/stats")
        assert response.status_code == 200
        data = response.json()
        assert data["nodes"] == 2
        assert data["edges"] == 1
        assert data["avg_confidence"] == 0.85
        assert "density" in data

    def test_stats_fallback(self, test_app):
        with patch("knowledge.graph.get_knowledge_graph", side_effect=Exception("no graph")):
            response = test_app.get("/api/v1/knowledge/stats")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "unavailable"
        assert "error" in data


@pytest.mark.api
class TestKnowledgeGraph:
    def test_graph_success(self, test_app, mock_graph):
        with patch("knowledge.graph.get_knowledge_graph", return_value=mock_graph):
            response = test_app.get("/api/v1/knowledge/graph?limit=10")
        assert response.status_code == 200
        data = response.json()
        assert "nodes" in data
        assert "edges" in data
        assert len(data["nodes"]) == 2
        assert len(data["edges"]) == 1
        # Проверка, что это правильные ключи (баг: раньше было "concepts" и "relations")
        assert data["nodes"][0]["id"] == "c1"
        assert data["nodes"][0]["name"] == "физика"
        assert data["edges"][0]["source"] == "c1"
        assert data["edges"][0]["target"] == "c2"

    def test_graph_fallback(self, test_app):
        with patch("knowledge.graph.get_knowledge_graph", side_effect=Exception("no graph")):
            response = test_app.get("/api/v1/knowledge/graph")
        assert response.status_code == 200
        data = response.json()
        assert data["nodes"] == []
        assert data["edges"] == []
        assert "error" in data


@pytest.mark.api
class TestKnowledgeSearch:
    def test_search_found(self, test_app, mock_graph):
        with patch("knowledge.graph.get_knowledge_graph", return_value=mock_graph):
            response = test_app.get("/api/v1/knowledge/search?q=физика")
        assert response.status_code == 200
        data = response.json()
        assert data["query"] == "физика"
        assert len(data["concepts"]) == 1
        assert data["concepts"][0]["name"] == "физика"

    def test_search_empty(self, test_app, mock_graph):
        mock_graph.find_concepts.return_value = []
        with patch("knowledge.graph.get_knowledge_graph", return_value=mock_graph):
            response = test_app.get("/api/v1/knowledge/search?q=nonexistent")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0

    def test_search_missing_query(self, test_app):
        response = test_app.get("/api/v1/knowledge/search")
        assert response.status_code == 422  # Validation error

    def test_search_fallback(self, test_app):
        with patch("knowledge.graph.get_knowledge_graph", side_effect=Exception("fail")):
            response = test_app.get("/api/v1/knowledge/search?q=test")
        assert response.status_code == 200
        data = response.json()
        assert data["concepts"] == []
        assert data["total"] == 0
        assert "error" in data


@pytest.mark.api
class TestKnowledgeRelated:
    def test_related_success(self, test_app, mock_graph):
        with patch("knowledge.graph.get_knowledge_graph", return_value=mock_graph):
            response = test_app.get("/api/v1/knowledge/related/c1")
        assert response.status_code == 200
        data = response.json()
        assert data["concept"]["id"] == "c1"
        assert len(data["related"]) == 1
        assert data["related"][0]["id"] == "c2"

    def test_related_not_found(self, test_app, mock_graph):
        mock_graph.get_concept.return_value = None
        mock_graph.get_related.return_value = []
        with patch("knowledge.graph.get_knowledge_graph", return_value=mock_graph):
            response = test_app.get("/api/v1/knowledge/related/nonexistent")
        assert response.status_code == 200
        data = response.json()
        assert data["concept"] is None

    def test_related_fallback(self, test_app):
        with patch("knowledge.graph.get_knowledge_graph", side_effect=Exception("fail")):
            response = test_app.get("/api/v1/knowledge/related/c1")
        assert response.status_code == 200
        data = response.json()
        assert "error" in data
