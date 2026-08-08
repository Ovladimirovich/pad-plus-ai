"""
Тесты для ShadowMemoryMonitor (ADR-0010).
"""

import pytest
from backend.core.workspace.shadow_monitor import ShadowMemoryMonitor


def test_shadow_monitor_evaluation():
    candidates = [
        {"id": "1", "text": "Valid fact", "score": 0.9, "is_stale": False, "category": "relevant"},
        {"id": "2", "text": "Old fact", "score": 0.8, "is_stale": True, "category": "stale"},
        {"id": "3", "text": "Low score fact", "score": 0.3, "is_stale": False, "category": "relevant"},
        {"id": "4", "text": "Noise", "score": 0.7, "is_stale": False, "category": "distractor"}
    ]

    result = ShadowMemoryMonitor.evaluate_shadow_decision(candidates, "Test query")
    
    assert result["stats"]["total_candidates"] == 4
    assert result["stats"]["keep"] == 1
    assert result["stats"]["outdated"] == 1
    assert result["stats"]["uncertain"] == 1
    assert result["stats"]["discard"] == 1
