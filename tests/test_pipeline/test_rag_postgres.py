from unittest.mock import MagicMock, patch, PropertyMock
from datetime import datetime, timedelta
import json

import pytest

from memory.rag_postgres import (
    RAGMemory,
    calculate_keyword_score,
    calculate_recency_score,
    summarize_text_sync,
    CONTEXT_WINDOW,
)


class TestRagFunctions:
    def test_calculate_keyword_score(self):
        assert calculate_keyword_score(["hello", "world"], ["hello", "foo"]) == pytest.approx(1 / 3)
        assert calculate_keyword_score([], ["hello"]) == 0.0
        assert calculate_keyword_score(["hello"], []) == 0.0
        assert calculate_keyword_score(["a", "b"], ["a", "b"]) == 1.0

    def test_calculate_recency_score(self):
        now = datetime.now()
        recent = (now - timedelta(hours=1)).isoformat()
        old = (now - timedelta(days=30)).isoformat()
        assert calculate_recency_score(recent) > 0.9
        assert calculate_recency_score(old) == pytest.approx(0.1, abs=0.01)
        assert calculate_recency_score("") == 0.5
        assert calculate_recency_score("invalid") == 0.5

    def test_summarize_text_sync(self):
        assert summarize_text_sync("short") == "short"
        long_text = "A" * 300
        result = summarize_text_sync(long_text, max_length=200)
        assert len(result) < len(long_text)


@pytest.fixture
def mock_rag():
    with patch("memory.rag_postgres.psycopg2.connect") as mock_conn:
        mock_cursor = MagicMock()
        mock_conn.return_value.cursor.return_value = mock_cursor
        rag = RAGMemory()
        rag._keywords_cache = {}
        yield rag


class TestRAGMemoryPostgres:
    def test_search_by_topic(self, mock_rag):
        rag = mock_rag
        with patch.object(rag, "hybrid_search") as mock_search:
            mock_search.return_value = [{"id": "1"}]
            result = rag.search_by_topic("tech")
            mock_search.assert_called_once_with("", n_results=5, topic_filter="tech")
            assert len(result) == 1

    def test_search_by_keywords(self, mock_rag):
        rag = mock_rag
        with patch.object(rag, "hybrid_search") as mock_search:
            mock_search.return_value = [{"id": "1"}]
            result = rag.search_by_keywords(["hello", "world"])
            mock_search.assert_called_once_with("hello world", CONTEXT_WINDOW, use_keywords=True, use_recency=False)
            assert len(result) == 1

    def test_search_by_keywords_empty(self, mock_rag):
        rag = mock_rag
        result = rag.search_by_keywords([])
        assert result == []

    def test_get_recent(self, mock_rag):
        rag = mock_rag
        rag.cursor.fetchall.return_value = [
            ("id1", "user msg", "ai msg", json.dumps({"topic": "tech"}), datetime.now()),
        ]
        result = rag.get_recent(days=7, n_results=10)
        assert len(result) == 1
        assert result[0]["id"] == "id1"
        assert result[0]["topic"] == "tech"

    def test_get_recent_empty(self, mock_rag):
        rag = mock_rag
        rag.cursor.fetchall.return_value = []
        result = rag.get_recent()
        assert result == []

    def test_get_topic_stats(self, mock_rag):
        rag = mock_rag
        rag.cursor.fetchall.return_value = [("tech", 10), ("science", 5)]
        result = rag.get_topic_stats()
        assert result == {"tech": 10, "science": 5}

    def test_get_entity_index(self, mock_rag):
        rag = mock_rag
        rag.cursor.fetchall.return_value = [
            ("id1", json.dumps([{"value": "Python"}, {"value": "AI"}])),
            ("id2", json.dumps([{"value": "Python"}])),
        ]
        result = rag.get_entity_index()
        assert "Python" in result
        assert "AI" in result
        assert len(result["Python"]) == 2
        assert len(result["AI"]) == 1

    def test_clear(self, mock_rag):
        rag = mock_rag
        rag.clear()
        rag.cursor.execute.assert_called_with("TRUNCATE TABLE rag_dialogs RESTART IDENTITY")
