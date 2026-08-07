"""
Тесты для воркспейса хода и чекпоинтера (Phase D'-1).
"""

import pytest
from datetime import datetime
from backend.core.workspace.schemas import TurnWorkspace, PhaseName, WorkingScratchpad
from backend.core.workspace.checkpointer import SQLiteCheckpointer


def test_scratchpad_evidence_and_hypotheses():
    scratch = WorkingScratchpad()
    ev = scratch.add_evidence("Test fact from memory", source="rag", confidence=0.95)
    assert len(scratch.evidence) == 1
    assert ev.content == "Test fact from memory"

    hyp = scratch.propose_hypothesis("User is asking about quantum physics")
    assert len(scratch.hypotheses) == 1

    assert scratch.link_evidence(ev.id, hyp.id) is True
    assert hyp.supporting_evidence == [ev.id]


def test_turn_workspace_checkpoint_json():
    ws = TurnWorkspace(
        session_id="session-123",
        turn_id=1,
        user_message="Hello AI"
    )
    ws.update_phase(PhaseName.INTENT, {"intent": "greeting"})

    json_str = ws.to_checkpoint_json()
    loaded = TurnWorkspace.from_checkpoint_json(json_str)

    assert loaded.session_id == "session-123"
    assert loaded.turn_id == 1
    assert loaded.phase_outputs["intent"] == {"intent": "greeting"}


def test_sqlite_checkpointer_save_and_load():
    cp = SQLiteCheckpointer(":memory:")
    
    ws = TurnWorkspace(session_id="test-sess", turn_id=1, user_message="Check checkpointer")
    ws.update_phase(PhaseName.SAFETY, {"passed": True})
    cp.save_after_phase(ws, PhaseName.SAFETY)

    ws.update_phase(PhaseName.INTENT, {"intent": "question"})
    cp.save_after_phase(ws, PhaseName.INTENT)

    # load_latest должен вернуть с наивысшим приоритетом (INTENT > SAFETY)
    latest = cp.load_latest("test-sess", 1)
    assert latest is not None
    assert "intent" in latest.phase_outputs
    assert latest.phase_outputs["safety"]["passed"] is True

    # load_at_phase (time-travel)
    at_safety = cp.load_at_phase("test-sess", 1, PhaseName.SAFETY)
    assert at_safety is not None
    assert at_safety.phase_outputs["safety"]["passed"] is True
    assert "intent" not in at_safety.phase_outputs


def test_sqlite_checkpointer_branching():
    cp = SQLiteCheckpointer(":memory:")
    
    ws = TurnWorkspace(session_id="branch-sess", turn_id=1, user_message="Original")
    ws.update_phase(PhaseName.SAFETY, {"passed": True})
    cp.save_after_phase(ws, PhaseName.SAFETY)

    ws.update_phase(PhaseName.RAG, {"context": "secret knowledge"})
    cp.save_after_phase(ws, PhaseName.RAG)

    # Branch from RAG to new turn 5
    branched = cp.branch("branch-sess", 1, PhaseName.RAG, new_turn_id=5)
    assert branched.turn_id == 5
    assert branched.phase_outputs["rag"]["context"] == "secret knowledge"
    assert branched.current_phase is None
    assert branched.current_phase is None
