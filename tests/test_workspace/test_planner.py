"""
Тесты для CognitivePlanner и LearningCoordinator (Phase D'-4).
"""

import pytest
from backend.core.workspace.schemas import TurnWorkspace, ConversationWorkspace, ConversationCore
from backend.core.workspace.planner import CognitivePlanner, LearningCoordinator


def test_cognitive_planner_steps():
    conv = ConversationWorkspace(
        core=ConversationCore(session_id="plan-sess", dialog_id="diag-1")
    )
    ws = TurnWorkspace(session_id="plan-sess", turn_id=1, user_message="Help me code", intent="coding")

    # Без активных целей — стандартный пайплайн
    steps = CognitivePlanner.plan_next_steps(ws, conv)
    assert "safety" in steps
    assert "generate" in steps

    # С активной целью — добавляется рефлексия и truth loop
    conv.push_goal("Написать безопасный код", turn_id=1)
    steps_with_goals = CognitivePlanner.plan_next_steps(ws, conv)
    assert "reflection" in steps_with_goals
    assert "truth_loop" in steps_with_goals


def test_learning_coordinator_signal():
    ws = TurnWorkspace(session_id="learn-sess", turn_id=1, user_message="Test")
    reflection_result = {
        "coherence_score": 0.5,
        "unsupported_count": 2
    }

    signal = LearningCoordinator.coordinate_learning(ws, reflection_result)
    assert signal["reinforcement"] == 0.5
    assert signal["requires_consolidation"] is True
    assert "learning_signal" in ws.phase_outputs
