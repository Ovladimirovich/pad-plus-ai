from unittest.mock import MagicMock, patch, PropertyMock
from datetime import datetime, timezone

import pytest

from memory.semantic_postgres import SemanticMemory, KnowledgeType


@pytest.fixture
def mock_semantic():
    with patch("memory.semantic_postgres.psycopg2.connect") as mock_conn, \
         patch("memory.semantic_postgres.SemanticMemory._get_conn") as mock_get_conn:
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []
        mock_conn.return_value.cursor.return_value = mock_cursor
        mock_conn.return_value.closed = False
        mock_get_conn.return_value.cursor.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn.return_value
        sem = SemanticMemory()
        sem._procedures_cache = {}
        sem.cursor = mock_cursor
        sem.conn = mock_conn.return_value
        yield sem


def test_learn_procedure(mock_semantic):
    sem = mock_semantic
    with patch.object(sem, "add_knowledge") as mock_add:
        mock_knowledge = MagicMock()
        mock_knowledge.id = "proc_1"
        mock_knowledge.triggers = ["hello", "greeting"]
        mock_knowledge.confidence = 0.7
        mock_knowledge.success_rate = 0.5
        mock_knowledge.access_count = 0
        mock_add.return_value = mock_knowledge

        result = sem.learn_procedure("greet", ["say hi"], ["hello"], "general", 0.7)

        assert result.id == "proc_1"
        assert "proc_1" in sem._procedures_cache


def test_find_applicable_procedure(mock_semantic):
    sem = mock_semantic
    proc = MagicMock()
    proc.id = "proc_1"
    proc.triggers = ["hello", "greeting"]
    proc.confidence = 0.8
    proc.success_rate = 0.9

    sem._procedures_cache = {"proc_1": proc}

    result = sem.find_applicable_procedure("hello world")
    assert result is not None
    assert result.id == "proc_1"


def test_find_applicable_procedure_no_match(mock_semantic):
    sem = mock_semantic
    proc = MagicMock()
    proc.triggers = ["bye", "goodbye"]
    proc.confidence = 0.8
    proc.success_rate = 0.9
    sem._procedures_cache = {"proc_1": proc}

    result = sem.find_applicable_procedure("hello world")
    assert result is None


def test_apply_procedure(mock_semantic):
    sem = mock_semantic
    proc = MagicMock()
    proc.id = "proc_1"
    proc.knowledge_type = KnowledgeType.PROCEDURAL
    proc.procedure_steps = ["step1"]
    proc.confidence = 0.8
    proc.success_rate = 0.5
    proc.access_count = 0

    with patch.object(sem, "get_knowledge", return_value=proc), \
         patch.object(sem, "record_procedure_application") as mock_record:
        sem.cursor.fetchone.return_value = [0.9]

        result = sem.apply_procedure("proc_1", "context", True, "good")

        assert result["success_rate"] == 0.9
        assert result["procedure_id"] == "proc_1"
        mock_record.assert_called_once_with("proc_1", "context", True, "good")


def test_improve_procedure(mock_semantic):
    sem = mock_semantic
    proc = MagicMock()
    proc.id = "proc_1"
    proc.procedure_steps = ["step1"]
    proc.triggers = ["hello"]
    proc.last_modified = datetime.now(timezone.utc)

    with patch.object(sem, "get_knowledge", return_value=proc), \
         patch.object(sem, "_save_knowledge") as mock_save:
        result = sem.improve_procedure("proc_1", new_steps=["new_step"], new_triggers=["new_trigger"])

        assert result.procedure_steps == ["new_step"]
        assert "new_trigger" in result.triggers
        mock_save.assert_called_once()


def test_add_concept(mock_semantic):
    sem = mock_semantic
    with patch.object(sem, "add_knowledge") as mock_add:
        mock_add.return_value = MagicMock(id="concept_1")

        result = sem.add_concept("AI", "Artificial Intelligence", ["example"], ["ML"], "tech")

        assert result.id == "concept_1"
        mock_add.assert_called_once_with(
            content="Artificial Intelligence",
            knowledge_type=KnowledgeType.CONCEPTUAL,
            summary="Концепция: AI",
            examples=["example"],
            related_concepts=["ML"],
            domain="tech",
            tags=["AI"],
        )


def test_add_self_knowledge(mock_semantic):
    sem = mock_semantic
    with patch.object(sem, "add_knowledge") as mock_add:
        mock_add.return_value = MagicMock(id="self_1")

        result = sem.add_self_knowledge("I am helpful", 0.8)

        assert result.id == "self_1"
        mock_add.assert_called_once_with(
            content="I am helpful",
            knowledge_type=KnowledgeType.METACOGNITIVE,
            source="self_reflection",
            confidence=0.8,
        )


def test_get_self_knowledge(mock_semantic):
    sem = mock_semantic
    with patch.object(sem, "search_knowledge") as mock_search:
        mock_search.return_value = [MagicMock(), MagicMock()]

        result = sem.get_self_knowledge()

        assert len(result) == 2
        mock_search.assert_called_once_with(
            knowledge_type=KnowledgeType.METACOGNITIVE.value,
            limit=50,
        )
