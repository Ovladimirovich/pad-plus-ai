"""Тесты для KnowledgeGraphPhase — фаза pipeline"""
import os
import sys
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

project_root = str(Path(__file__).resolve().parent.parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)
backend_path = str(Path(__file__).resolve().parent.parent.parent / "backend")
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from core.pipeline import PipelineContext
from core.pipeline.phases.knowledge_graph import KnowledgeGraphPhase


@pytest.mark.pipeline
class TestKnowledgeGraphPhase:
    async def test_with_concepts(self):
        mock_concept = MagicMock()
        mock_concept.name = "физика"

        with patch("knowledge.graph.get_knowledge_graph") as mock_get:
            mock_graph = MagicMock()
            mock_graph.find_concepts.return_value = [mock_concept]
            mock_get.return_value = mock_graph

            phase = KnowledgeGraphPhase()
            ctx = PipelineContext(user_message="физика частиц")
            result = await phase.execute(ctx)

        assert result.success
        assert result.data["concepts"] == ["физика"]
        assert result.data["confidence"] == 0.7

    async def test_empty(self):
        with patch("knowledge.graph.get_knowledge_graph") as mock_get:
            mock_graph = MagicMock()
            mock_graph.find_concepts.return_value = []
            mock_get.return_value = mock_graph

            phase = KnowledgeGraphPhase()
            ctx = PipelineContext(user_message="тест")
            result = await phase.execute(ctx)

        assert result.success
        assert result.data["concepts"] == []
        assert result.data["confidence"] == 0.0

    async def test_fallback(self):
        with patch("knowledge.graph.get_knowledge_graph") as mock_get:
            mock_get.side_effect = Exception("graph unavailable")

            phase = KnowledgeGraphPhase()
            ctx = PipelineContext(user_message="тест")
            result = await phase.execute(ctx)

        assert result.success
        assert result.data["concepts"] == []

    async def test_multiple_concepts(self):
        mock_c1 = MagicMock()
        mock_c1.name = "квантовая физика"
        mock_c2 = MagicMock()
        mock_c2.name = "классическая физика"

        with patch("knowledge.graph.get_knowledge_graph") as mock_get:
            mock_graph = MagicMock()
            mock_graph.find_concepts.return_value = [mock_c1, mock_c2]
            mock_get.return_value = mock_graph

            phase = KnowledgeGraphPhase()
            ctx = PipelineContext(user_message="физика")
            result = await phase.execute(ctx)

        assert result.success
        assert len(result.data["concepts"]) == 2
        assert result.data["concepts"] == ["квантовая физика", "классическая физика"]

    async def test_long_message_truncation(self):
        """find_related_triples ограничивает концепции до concept_limit"""
        mock_concepts = [MagicMock(name=f"концепт{i}") for i in range(10)]
        concepts_dict = {}
        for i, mc in enumerate(mock_concepts):
            mc.name = f"концепт{i}"
            mc.id = f"id{i}"
            concepts_dict[mc.id] = mc

        def limited_find(q, limit=10):
            return mock_concepts[:limit]

        with patch("knowledge.graph.get_knowledge_graph") as mock_get:
            mock_graph = MagicMock()
            mock_graph.find_concepts.side_effect = limited_find
            mock_graph._concepts = concepts_dict
            mock_graph._relations = []
            mock_get.return_value = mock_graph

            phase = KnowledgeGraphPhase()
            ctx = PipelineContext(user_message="концепт")
            result = await phase.execute(ctx)

        assert result.success
        assert len(result.data["concepts"]) <= 5
