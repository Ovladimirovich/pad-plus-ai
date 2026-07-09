from unittest.mock import MagicMock, patch

import pytest

from core.pipeline.cross_memory_sync import CrossMemorySync, get_cross_memory_sync


@pytest.fixture(autouse=True)
def reset():
    import core.pipeline.cross_memory_sync as mod
    mod._cross_memory_sync = None
    yield
    mod._cross_memory_sync = None


class TestCrossMemorySync:
    def test_sync_rag_to_semantic_empty(self):
        with patch("memory.get_rag") as mock_rag, \
             patch("memory.get_semantic_memory") as mock_sem:
            mock_rag.return_value.get_recent.return_value = []
            sync = CrossMemorySync()
            insights = sync.sync_rag_to_semantic()
            assert insights == []

    def test_sync_rag_to_semantic_with_data(self):
        with patch("memory.get_rag") as mock_rag, \
             patch("memory.get_semantic_memory") as mock_sem:
            mock_rag.return_value.get_recent.return_value = [
                {
                    "metadata": {"user_message": "привет", "ai_response": "здравствуй"},
                    "topic": "общее",
                    "timestamp": "2026-01-01",
                }
            ]
            mock_sem_instance = MagicMock()
            mock_sem_instance.search_knowledge.return_value = []
            mock_sem.return_value = mock_sem_instance

            sync = CrossMemorySync()
            insights = sync.sync_rag_to_semantic()
            assert len(insights) == 1
            mock_sem_instance.add_knowledge.assert_called_once()

    def test_sync_rag_to_semantic_skip_existing(self):
        with patch("memory.get_rag") as mock_rag, \
             patch("memory.get_semantic_memory") as mock_sem:
            mock_rag.return_value.get_recent.return_value = [
                {"metadata": {"user_message": "привет", "ai_response": "здравствуй"}, "topic": "общее"}
            ]
            mock_sem_instance = MagicMock()
            mock_sem_instance.search_knowledge.return_value = [MagicMock()]
            mock_sem.return_value = mock_sem_instance

            sync = CrossMemorySync()
            insights = sync.sync_rag_to_semantic()
            assert insights == []

    def test_sync_episodic_to_semantic(self):
        with patch("memory.get_episodic_memory") as mock_ep, \
             patch("memory.get_semantic_memory") as mock_sem:
            mock_episode = MagicMock()
            mock_episode.content = "тестовый эпизод"
            mock_episode.user_message = "привет"
            mock_ep.return_value.get_related_episodes.return_value = [mock_episode]

            mock_sem_instance = MagicMock()
            mock_sem_instance.search_knowledge.return_value = []
            mock_sem.return_value = mock_sem_instance

            sync = CrossMemorySync()
            insights = sync.sync_episodic_to_semantic()
            assert len(insights) == 1
            mock_sem_instance.add_knowledge.assert_called_once()

    def test_sync_semantic_to_roots(self):
        with patch("memory.get_semantic_memory") as mock_sem, \
             patch("memory.get_roots_memory") as mock_roots:
            mock_knowledge = MagicMock()
            mock_knowledge.confidence = 0.9
            mock_knowledge.content = "важное знание"
            mock_knowledge.summary = "важно"
            mock_knowledge.knowledge_type = MagicMock()
            mock_knowledge.knowledge_type.value = "factual"

            mock_sem_instance = MagicMock()
            mock_sem_instance.search_knowledge.return_value = [mock_knowledge]
            mock_sem.return_value = mock_sem_instance

            mock_roots_instance = MagicMock()
            mock_roots_instance.search_knowledge.return_value = []
            mock_roots.return_value = mock_roots_instance

            sync = CrossMemorySync()
            insights = sync.sync_semantic_to_roots(min_confidence=0.8)
            assert len(insights) == 1
            mock_roots_instance.add_knowledge.assert_called_once()

    def test_sync_semantic_to_roots_low_confidence(self):
        with patch("memory.get_semantic_memory") as mock_sem, \
             patch("memory.get_roots_memory") as mock_roots:
            mock_knowledge = MagicMock()
            mock_knowledge.confidence = 0.5

            mock_sem_instance = MagicMock()
            mock_sem_instance.search_knowledge.return_value = [mock_knowledge]
            mock_sem.return_value = mock_sem_instance

            sync = CrossMemorySync()
            insights = sync.sync_semantic_to_roots(min_confidence=0.8)
            assert insights == []

    def test_sync_all(self):
        with patch.object(CrossMemorySync, "sync_rag_to_semantic") as m1, \
             patch.object(CrossMemorySync, "sync_episodic_to_semantic") as m2, \
             patch.object(CrossMemorySync, "sync_semantic_to_roots") as m3:
            m1.return_value = ["a"]
            m2.return_value = ["b"]
            m3.return_value = ["c"]

            sync = CrossMemorySync()
            result = sync.sync_all("user1")
            assert result["rag_to_semantic"] == ["a"]
            assert result["episodic_to_semantic"] == ["b"]
            assert result["semantic_to_roots"] == ["c"]

    def test_singleton(self):
        a = get_cross_memory_sync()
        b = get_cross_memory_sync()
        assert a is b
