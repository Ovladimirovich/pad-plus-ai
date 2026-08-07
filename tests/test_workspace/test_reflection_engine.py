"""
Тесты для ReflectionEngine (Phase D'-3).
"""

import pytest
from backend.core.workspace.schemas import TurnWorkspace, PhaseName
from backend.core.workspace.reflection import ReflectionEngine


def test_reflection_engine_analysis():
    ws = TurnWorkspace(
        session_id="refl-sess",
        turn_id=1,
        user_message="Are black holes real?"
    )
    
    # Добавляем факты и гипотезы в scratchpad
    ev = ws.scratchpad.add_evidence("Gravitational waves detected from black hole mergers", source="rag", confidence=0.99)
    hyp1 = ws.scratchpad.propose_hypothesis("Black holes exist")
    ws.scratchpad.link_evidence(ev.id, hyp1.id)

    hyp2 = ws.scratchpad.propose_hypothesis("Black holes lead to other universes") # без evidence

    # Запускаем рефлексию
    result = ReflectionEngine.reflect_on_turn(ws)

    assert result["total_hypotheses"] == 2
    assert result["supported_count"] == 1
    assert result["unsupported_count"] == 1
    assert result["coherence_score"] == 0.5
    assert "reflection" in ws.phase_outputs
    assert ws.phase_outputs["reflection"]["summary"] == "Проверено гипотез: 2. Обосновано: 1."
