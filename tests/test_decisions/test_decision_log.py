"""Тесты для Decision Log системы."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.core.decisions.models import DecisionRecord
from backend.core.decisions.store import DecisionStore, get_decision_store
from backend.core.decisions.recorder import DecisionRecorder, get_decision_recorder


def test_record_and_get():
    rec = get_decision_recorder()
    record = rec.record(
        component="provider_selector",
        decision_type="provider_selection",
        selected="gigachat",
        confidence=0.85,
        reason="Тест",
        input_factors={"intent": "chat"},
        candidates=[{"name": "gigachat", "score": 0.85}],
    )
    assert record.id
    loaded = rec.get(record.id)
    assert loaded is not None
    assert loaded.selected == "gigachat"
    assert loaded.confidence == 0.85
    assert loaded.input_factors["intent"] == "chat"


def test_query_by_component():
    rec = get_decision_recorder()
    rec.record(component="strategy_selector", decision_type="strategy_selection", selected="reasoning", confidence=0.8, reason="x")
    results = rec.query(component="strategy_selector", limit=10)
    assert len(results) > 0
    assert all(r.component == "strategy_selector" for r in results)


def test_query_by_session():
    rec = get_decision_recorder()
    sid = "session-test-123"
    rec.record(component="evaluator", decision_type="confidence", selected="0.7", confidence=0.7, reason="y", session_id=sid)
    results = rec.query(session_id=sid, limit=10)
    assert len(results) >= 1
    assert results[0].session_id == sid


def test_stats():
    rec = get_decision_recorder()
    rec.record(component="meta_learner", decision_type="strategy_change", selected="simple", confidence=0.6, reason="z")
    stats = rec.stats()
    assert "total" in stats
    assert "by_component" in stats
    assert stats["total"] > 0


def test_model_roundtrip():
    r = DecisionRecord(
        id="test-1",
        timestamp=123.0,
        component="test",
        decision_type="test_type",
        selected="val",
        confidence=0.5,
        reason="reason",
        input_factors={"a": 1},
        candidates=[{"name": "x", "score": 0.5}],
    )
    d = r.to_dict()
    r2 = DecisionRecord.from_dict(d)
    assert r2.id == r.id
    assert r2.input_factors == r.input_factors
    assert r2.candidates == r.candidates
