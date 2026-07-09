"""Тесты для Knowledge Graph — ядро графа знаний"""
import os
import sys
import json
import pytest
from pathlib import Path
from datetime import datetime
from unittest.mock import MagicMock, patch

project_root = str(Path(__file__).resolve().parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)
backend_path = str(Path(__file__).resolve().parent.parent / "backend")
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)


@pytest.fixture
def kg_with_networkx(tmp_path):
    """KnowledgeGraph с NetworkX (если установлен)"""
    from knowledge.graph import KnowledgeGraph
    db_file = str(tmp_path / "test_knowledge.db")
    kg = KnowledgeGraph(db_path=db_file)
    kg._concepts.clear()
    if kg.graph:
        kg.graph.clear()
    return kg


@pytest.fixture
def populated_kg(kg_with_networkx):
    """KnowledgeGraph с тестовыми данными"""
    kg = kg_with_networkx
    c1 = kg.add_concept("физика", concept_type="concept", confidence=0.9, source="test")
    c2 = kg.add_concept("квантовая механика", concept_type="concept", confidence=0.8, source="test")
    c3 = kg.add_concept("классическая механика", concept_type="concept", confidence=0.7, source="test")
    c4 = kg.add_concept("философия", concept_type="concept", confidence=0.6, source="test")
    kg.add_relation(c1.id, c2.id, relation_type="related", weight=0.9)
    kg.add_relation(c1.id, c3.id, relation_type="related", weight=0.8)
    kg.add_relation(c2.id, c4.id, relation_type="related", weight=0.5)
    return kg


class TestConcept:
    def test_to_dict(self):
        from knowledge.graph import Concept
        now = datetime.now()
        c = Concept(
            id="test123",
            name="тест",
            concept_type="concept",
            confidence=0.75,
            source="user",
            created_at=now,
            metadata={"key": "val"}
        )
        d = c.to_dict()
        assert d["id"] == "test123"
        assert d["name"] == "тест"
        assert d["type"] == "concept"
        assert d["confidence"] == 0.75
        assert d["source"] == "user"
        assert d["created_at"] == now.isoformat()
        assert d["metadata"] == {"key": "val"}


class TestRelation:
    def test_to_dict(self):
        from knowledge.graph import Relation
        now = datetime.now()
        r = Relation(
            source_id="src1",
            target_id="tgt1",
            relation_type="is_a",
            weight=0.5,
            confidence=0.9,
            created_at=now
        )
        d = r.to_dict()
        assert d["source"] == "src1"
        assert d["target"] == "tgt1"
        assert d["type"] == "is_a"
        assert d["weight"] == 0.5
        assert d["confidence"] == 0.9


class TestKnowledgeGraph:
    def test_add_concept(self, kg_with_networkx):
        kg = kg_with_networkx
        c = kg.add_concept("тестовая концепция", concept_type="concept", confidence=0.8)
        assert c.id is not None
        assert c.name == "тестовая концепция"
        assert c.concept_type == "concept"
        assert c.confidence == 0.8
        # Проверка что в кэше
        assert kg.get_concept(c.id) is c
        # Проверка что в графе NetworkX
        if kg.graph:
            assert kg.graph.has_node(c.id)

    def test_add_duplicate_name(self, kg_with_networkx):
        """add_concept создаёт новый ID даже при том же имени"""
        kg = kg_with_networkx
        c1 = kg.add_concept("дубль")
        c2 = kg.add_concept("дубль")
        assert c1.id != c2.id
        assert len(kg._concepts) == 2

    def test_add_relation(self, populated_kg):
        kg = populated_kg
        concepts = list(kg._concepts.values())
        existing = kg.add_relation(concepts[0].id, concepts[1].id)
        assert existing is not None
        # Несуществующие ID
        nonexistent = kg.add_relation("no_such_id", concepts[0].id)
        assert nonexistent is None

    def test_get_concept(self, populated_kg):
        kg = populated_kg
        concepts = list(kg._concepts.values())
        assert kg.get_concept(concepts[0].id) is concepts[0]
        assert kg.get_concept("no_such_id") is None

    def test_find_concepts(self, populated_kg):
        kg = populated_kg
        results = kg.find_concepts("физика", limit=10)
        names = [c.name for c in results]
        assert "физика" in names
        assert len(results) >= 1

    def test_find_concepts_substring(self, populated_kg):
        kg = populated_kg
        results = kg.find_concepts("механика", limit=10)
        names = [c.name for c in results]
        assert "квантовая механика" in names
        assert "классическая механика" in names
        assert len(results) == 2

    def test_find_concepts_limit(self, populated_kg):
        kg = populated_kg
        results = kg.find_concepts("механика", limit=1)
        assert len(results) <= 1

    def test_find_concepts_no_match(self, populated_kg):
        kg = populated_kg
        results = kg.find_concepts("zxywq_nonexistent_12345")
        assert len(results) == 0

    def test_get_related(self, populated_kg):
        kg = populated_kg
        concepts = list(kg._concepts.values())
        related = kg.get_related(concepts[0].id)
        if kg.graph:
            assert len(related) > 0
        else:
            assert len(related) == 0
        # Несуществующий ID
        empty = kg.get_related("no_such_id")
        assert empty == []

    def test_get_related_no_networkx(self, populated_kg):
        """Без NetworkX get_related всегда пуст"""
        kg = populated_kg
        saved = kg.graph
        kg.graph = None
        concepts = list(kg._concepts.values())
        related = kg.get_related(concepts[0].id)
        kg.graph = saved
        assert related == []

    def test_get_stats_keys(self, populated_kg):
        kg = populated_kg
        stats = kg.get_stats()
        assert "nodes" in stats
        assert "edges" in stats
        assert "density" in stats
        assert "avg_confidence" in stats

    def test_get_stats_values(self, populated_kg):
        kg = populated_kg
        stats = kg.get_stats()
        assert stats["nodes"] == 4
        if kg.graph:
            assert stats["edges"] == 3
        else:
            assert stats["edges"] == 0
        assert stats["avg_confidence"] == pytest.approx(0.75, abs=0.01)

    def test_get_stats_empty(self, kg_with_networkx):
        kg = kg_with_networkx
        stats = kg.get_stats()
        assert stats["nodes"] == 0
        assert stats["edges"] == 0
        assert stats["density"] == 0
        assert stats["avg_confidence"] == 0.0

    def test_to_dict_keys(self, populated_kg):
        kg = populated_kg
        d = kg.to_dict()
        assert "nodes" in d
        assert "links" in d
        assert "stats" in d
        # Проверка структуры ноды
        if d["nodes"]:
            node = d["nodes"][0]
            assert "id" in node
            assert "name" in node
        # Проверка структуры линка
        if d["links"]:
            link = d["links"][0]
            assert "source" in link
            assert "target" in link

    def test_find_path(self, populated_kg):
        kg = populated_kg
        concepts = list(kg._concepts.values())
        if len(concepts) >= 3 and kg.graph:
            path = kg.find_path(concepts[0].id, concepts[2].id)
            assert len(path) > 0
            assert path[0] == concepts[0].id

    def test_find_path_no_path(self, populated_kg):
        kg = populated_kg
        # Несуществующие узлы
        path = kg.find_path("no_src", "no_tgt")
        assert path == []

    def test_networkx_available(self, populated_kg):
        stats = populated_kg.get_stats()
        assert isinstance(stats["networkx_available"], bool)

    def test_add_relation_updates_concepts(self, populated_kg):
        """Relation добавляется даже без NetworkX (проверка _concepts)"""
        kg = populated_kg
        concepts = list(kg._concepts.values())
        # Relation уже создана в populated_kg, проверяем что она в БД
        conn = __import__("sqlite3").connect(kg.db_path)
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM relations")
        count = cur.fetchone()[0]
        conn.close()
        assert count == 3


class TestSearch:
    """Тесты для knowledge/search.py — Graph RAG"""

    def test_find_related_triples_no_match(self, populated_kg):
        from knowledge.search import find_related_triples
        names, context = find_related_triples("nonexistent_xyz", concept_limit=5, graph=populated_kg)
        assert names == []
        assert context == ""

    def test_find_related_triples_returns_context(self, populated_kg):
        from knowledge.search import find_related_triples
        names, context = find_related_triples("физика", concept_limit=5, relation_limit=10, graph=populated_kg)
        assert "физика" in names
        assert context.startswith("Знания из графа:")
        assert "→" in context

    def test_find_related_triples_relation_count(self, populated_kg):
        from knowledge.search import find_related_triples
        names, context = find_related_triples("физика", concept_limit=5, relation_limit=3, graph=populated_kg)
        lines = [l for l in context.split("\n") if l.startswith("- ")]
        assert len(lines) <= 3

    def test_search_concepts(self, populated_kg):
        from knowledge.search import search_concepts
        names = search_concepts("механика", limit=10, graph=populated_kg)
        assert "квантовая механика" in names
        assert "классическая механика" in names

    def test_search_concepts_no_match(self, populated_kg):
        from knowledge.search import search_concepts
        names = search_concepts("nonexistent", graph=populated_kg)
        assert names == []
