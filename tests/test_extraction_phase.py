"""Тесты для ExtractionPhase — авто-экстракция из сообщений"""
import os
import sys
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

project_root = str(Path(__file__).resolve().parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)
backend_path = str(Path(__file__).resolve().parent.parent / "backend")
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)


@pytest.mark.pipeline
class TestExtractionPhase:
    async def test_extracts_concepts(self):
        mock_result = {"concepts_added": 2, "relations_added": 1, "total_concepts": 2, "total_relations": 1}

        with patch("knowledge.extractor.extract_and_add") as mock_extract:
            with patch("knowledge.graph.get_knowledge_graph") as mock_get:
                mock_extract.return_value = mock_result
                mock_get.return_value = MagicMock()

                from core.pipeline import PipelineContext
                from core.pipeline.phases.extraction import ExtractionPhase

                phase = ExtractionPhase()
                ctx = PipelineContext(user_message="нейронные сети используют трансформеры")
                result = await phase.execute(ctx)

        assert result.success
        assert result.data["concepts_added"] == 2
        assert result.data["relations_added"] == 1

    async def test_empty_message(self):
        mock_result = {"concepts_added": 0, "relations_added": 0, "total_concepts": 0, "total_relations": 0}

        with patch("knowledge.extractor.extract_and_add") as mock_extract:
            with patch("knowledge.graph.get_knowledge_graph") as mock_get:
                mock_extract.return_value = mock_result
                mock_get.return_value = MagicMock()

                from core.pipeline import PipelineContext
                from core.pipeline.phases.extraction import ExtractionPhase

                phase = ExtractionPhase()
                ctx = PipelineContext(user_message="привет")
                result = await phase.execute(ctx)

        assert result.success
        assert result.data["concepts_added"] == 0

    async def test_fallback_on_error(self):

        with patch("knowledge.extractor.extract_and_add") as mock_extract:
            with patch("knowledge.graph.get_knowledge_graph") as mock_get:
                mock_extract.side_effect = Exception("extraction failed")
                mock_get.return_value = MagicMock()

                from core.pipeline import PipelineContext
                from core.pipeline.phases.extraction import ExtractionPhase

                phase = ExtractionPhase()
                ctx = PipelineContext(user_message="тест")
                result = await phase.execute(ctx)

        assert result.success
        assert result.data["concepts_added"] == 0
        assert result.data["relations_added"] == 0
