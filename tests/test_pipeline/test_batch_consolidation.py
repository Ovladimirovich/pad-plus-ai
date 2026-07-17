from unittest.mock import MagicMock, patch

import pytest


class TestMemoryConsolidator:
    @pytest.fixture
    def consolidator(self):
        with patch("memory.consolidation.get_episodic_memory"), \
             patch("memory.consolidation.get_semantic_memory"), \
             patch("memory.consolidation.get_roots_memory"), \
             patch("memory.consolidation.get_rag_memory"):
            from memory.consolidation import MemoryConsolidator
            c = MemoryConsolidator()
            c.episodic = MagicMock()
            c.semantic = MagicMock()
            c.roots = MagicMock()
            c.rag = MagicMock()
            return c

    def test_consolidate_episodes_to_semantic_empty(self, consolidator):
        consolidator.episodic.get_significant_episodes.return_value = []
        consolidator.episodic.search_episodes.return_value = []

        result = consolidator.consolidate_episodes_to_semantic()
        assert result.items_processed == 0
        assert result.items_consolidated == 0
        assert len(result.insights) == 0

    def test_consolidate_all_empty(self, consolidator):
        consolidator.episodic.get_significant_episodes.return_value = []
        consolidator.episodic.search_episodes.return_value = []
        consolidator.rag.get_recent.return_value = []
        consolidator.semantic.search_knowledge.return_value = []

        results = consolidator.consolidate_all()
        assert "episodic_to_semantic" in results
        assert "rag_to_semantic" in results
        assert "semantic_to_roots" in results
        assert "update_connections" in results

    def test_run_scheduled_consolidation(self, consolidator):
        consolidator.episodic.get_significant_episodes.return_value = []
        consolidator.episodic.search_episodes.return_value = []
        consolidator.rag.get_recent.return_value = []
        consolidator.semantic.search_knowledge.return_value = []

        summary = consolidator.run_scheduled_consolidation()
        assert "timestamp" in summary
        assert "results" in summary

    def test_emotion_integration(self, consolidator):
        from datetime import datetime, timedelta, timezone
        mock_ep = MagicMock()
        mock_ep.id = "ep1"
        mock_ep.topic = "тест"
        mock_ep.user_message = "тестовое сообщение"
        mock_ep.concepts = ["тест"]
        mock_ep.keywords = ["тест"]
        mock_ep.intent = "test"
        mock_ep.success = True
        mock_ep.access_count = 5
        mock_ep.emotion_impact = 0.5
        # Старше min_age_hours (1ч): и naive local, и aware UTC должны проходить
        mock_ep.timestamp = datetime.now(timezone.utc) - timedelta(hours=2)

        consolidator.episodic.get_significant_episodes.return_value = [mock_ep]
        consolidator.episodic.search_episodes.return_value = []

        with patch.object(consolidator, "_extract_procedures", return_value=[]):
            result = consolidator.consolidate_episodes_to_semantic()
        assert result.items_processed >= 1

    def test_emotion_integration_naive_local_timestamp(self, consolidator):
        """Регрессия: naive local timestamp не должен отфильтровываться из‑за UTC-сдвига."""
        from datetime import datetime, timedelta
        mock_ep = MagicMock()
        mock_ep.id = "ep2"
        mock_ep.topic = "тест"
        mock_ep.user_message = "сообщение"
        mock_ep.concepts = ["тест"]
        mock_ep.keywords = ["тест"]
        mock_ep.intent = "test"
        mock_ep.success = True
        mock_ep.access_count = 5
        mock_ep.emotion_impact = 0.5
        mock_ep.timestamp = datetime.now() - timedelta(hours=3)

        consolidator.episodic.get_significant_episodes.return_value = [mock_ep]
        consolidator.episodic.search_episodes.return_value = []

        with patch.object(consolidator, "_extract_procedures", return_value=[]):
            result = consolidator.consolidate_episodes_to_semantic()
        assert result.items_processed >= 1

    def test_consolidation_stats(self, consolidator):
        consolidator.episodic.get_significant_episodes.return_value = []
        consolidator.episodic.search_episodes.return_value = []
        consolidator.rag.get_recent.return_value = []
        consolidator.semantic.search_knowledge.return_value = []

        consolidator.consolidate_all()
        stats = consolidator.get_consolidation_stats()
        assert stats["total_consolidations"] == 4
        assert "total_items_processed" in stats

    def test_singleton(self):
        with patch("memory.consolidation.get_episodic_memory"), \
             patch("memory.consolidation.get_semantic_memory"), \
             patch("memory.consolidation.get_roots_memory"), \
             patch("memory.consolidation.get_rag_memory"):
            from memory.consolidation import get_consolidator
            a = get_consolidator()
            b = get_consolidator()
            assert a is b
