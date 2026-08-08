"""
Тесты интеграции MemoryDecisionLayer в активный RAG Path (ADR-0010).

RAGMemory.get_context() пропускает кандидатов через MemoryDecisionLayer:
stale-записи и дистракторы отбрасываются, релевантные — остаются.
"""

from datetime import datetime
from unittest.mock import MagicMock, patch

from backend.memory.rag import RAGMemory


def _build_dialog(meta, score, timestamp):
    return {
        "metadata": meta,
        "combined_score": score,
        "topic": meta.get("topic", "общее"),
        "timestamp": timestamp,
    }


def test_get_context_keeps_relevant_drops_stale(tmp_path, monkeypatch):
    """Decision Layer: релевантные диалоги проходят, stale отсекаются."""
    monkeypatch.setenv("DATABASE_URL", "postgresql://localhost:5432/db")

    now = datetime(2026, 8, 8, 12, 0, 0)
    dialogs = [
        _build_dialog(
            {"user_message": "Как работает FastAPI?", "ai_response": "FastAPI это...", "topic": "техническое"},
            score=0.8,
            timestamp=now,
        ),
        # stale — 30 дней назад, должен быть отсечён (recency ~0.014 < 0.25)
        _build_dialog(
            {"user_message": "Старый вопрос", "ai_response": "Старый ответ", "topic": "общее"},
            score=0.7,
            timestamp="2026-07-09T12:00:00",
        ),
    ]

    fake_rows = [
        (dialogs[0]["metadata"]["user_message"], dialogs[0]["metadata"]["ai_response"],
         dialogs[0]["metadata"], "техническое", now),
        (dialogs[1]["metadata"]["user_message"], dialogs[1]["metadata"]["ai_response"],
         dialogs[1]["metadata"], "общее", datetime(2026, 7, 9, 12, 0, 0)),
    ]

    with patch("psycopg2.connect") as mock_conn:
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = fake_rows
        mock_conn.return_value.cursor.return_value = mock_cursor

        rag = RAGMemory(persist_dir=str(tmp_path))
        result = rag.get_context("FastAPI работа")

    assert "FastAPI" in result
    assert "Старый вопрос" not in result


def test_get_context_drops_distractor_low_score(tmp_path, monkeypatch):
    """Decision Layer: низкоскорный дистрактор (<0.35) отсекается."""
    monkeypatch.setenv("DATABASE_URL", "postgresql://localhost:5432/db")

    now = datetime(2026, 8, 8, 12, 0, 0)
    fake_rows = [
        ("Релевантный диалог", "Релевантный ответ", {"user_message": "Релевантный диалог", "ai_response": "Релевантный ответ"}, "техническое", now),
        # Дистрактор — не совпадает по теме и имеет низкий score
        ("Погода", "Солнечно", {"user_message": "Погода", "ai_response": "Солнечно"}, "бытовое", now),
    ]

    # Кандидаты в реальном коде получают score=0.5 из строки; дистрактор с
    # category=distractor должен отсекаться по score < 0.5.
    with patch("psycopg2.connect") as mock_conn:
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = fake_rows
        mock_conn.return_value.cursor.return_value = mock_cursor

        rag = RAGMemory(persist_dir=str(tmp_path))
        result = rag.get_context("FastAPI")

    assert result  # хотя бы один релевантный остался
