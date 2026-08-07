"""
Интеграционные тесты для WorkspaceOrchestrator (Phase D'-5).
"""

import pytest
from backend.core.workspace.integration import WorkspaceOrchestrator
from backend.core.workspace.checkpointer import SQLiteCheckpointer


def test_workspace_orchestrator_turn_flow():
    cp = SQLiteCheckpointer(":memory:")
    orchestrator = WorkspaceOrchestrator(checkpointer=cp)

    session_id = "orch-session-1"
    turn_id = 1

    # 1. Инициализация хода
    ws = orchestrator.init_turn(session_id, turn_id, "Как работает гравитация?")
    assert ws.session_id == session_id

    # 2. Чекпоинтинг фазы
    orchestrator.checkpoint_phase(ws, "intent", {"intent": "science_question"})
    assert "intent" in ws.phase_outputs

    # 3. Наполнение scratchpad и рефлексия
    ev = ws.scratchpad.add_evidence("Mass curves spacetime", source="rag", confidence=0.98)
    hyp = ws.scratchpad.propose_hypothesis("Gravity is spacetime curvature")
    ws.scratchpad.link_evidence(ev.id, hyp.id)
    
    reflection = orchestrator.run_reflection(ws)
    assert reflection["total_hypotheses"] == 1
    assert reflection["supported_count"] == 1

    # 4. Проверка сохранения в чекпоинтер
    loaded = cp.load_latest(session_id, turn_id)
    assert loaded is not None
    assert "reflection" in loaded.phase_outputs

    # 5. Сессионный воркспейс
    conv = orchestrator.get_or_create_conversation(session_id, dialog_id="diag-100")
    conv.add_turn(turn_id, ws.user_message, "science_question")
    orchestrator.save_conversation(conv)

    loaded_conv = cp.load_conversation(session_id)
    assert loaded_conv is not None
    assert loaded_conv.core.turn_count == 1
    assert loaded_conv.core.current_topic == "science_question"
