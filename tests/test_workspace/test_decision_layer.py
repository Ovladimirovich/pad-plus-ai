"""
Тесты для MemoryDecisionLayer (ADR-0010, Active Path).
"""

import pytest
from backend.core.workspace.decision_layer import MemoryDecisionLayer


def test_memory_decision_layer_filtering():
    candidates = [
        {"id": "1", "text": "Relevant active fact", "score": 0.9, "is_stale": False, "category": "relevant"},
        {"id": "2", "text": "Outdated fact", "score": 0.85, "is_stale": True, "category": "stale"},
        {"id": "3", "text": "Low score fact", "score": 0.3, "is_stale": False, "category": "relevant"},
        {"id": "4", "text": "Noise distractor", "score": 0.7, "is_stale": False, "category": "distractor"}
    ]

    approved = MemoryDecisionLayer.filter_candidates(candidates)

    assert len(approved) == 1
    assert approved[0]["id"] == "1"
    assert approved[0]["text"] == "Relevant active fact"
