"""Tests for ImpulsePhase (pre-generate read)."""

import pytest

from core.pipeline.context import PipelineContext
from core.pipeline.phases.impulse import ImpulsePhase


@pytest.mark.asyncio
async def test_impulse_phase_merges_keys(tmp_path, monkeypatch):
    monkeypatch.setenv("IMPULSE_USE_PG", "false")
    from core.impulse.manager import ImpulseManager, reset_manager
    from core.impulse.core import ImpulseCore

    reset_manager()
    mgr = ImpulseManager(base_path=str(tmp_path), use_pg=False)
    core = ImpulseCore()
    core.set_from_labels({"understand": 1.0})
    mgr.save(core)

    # point global manager to tmp
    import core.impulse.manager as m

    m._manager = mgr

    phase = ImpulsePhase()
    ctx = PipelineContext(user_message="test")
    result = await phase.execute(ctx)

    assert result.success
    assert result.data["impulse_primary"] == "understand"
    assert "understand" in result.data["impulse_bias"]
    assert result.data["impulse_state"]["version"] == 2
    assert isinstance(result.data["impulse_active"], list)


@pytest.mark.asyncio
async def test_impulse_phase_unknown_empty_bias(tmp_path, monkeypatch):
    monkeypatch.setenv("IMPULSE_USE_PG", "false")
    from core.impulse.manager import ImpulseManager, reset_manager
    from core.impulse.core import ImpulseCore

    reset_manager()
    mgr = ImpulseManager(base_path=str(tmp_path), use_pg=False)
    mgr.save(ImpulseCore())
    import core.impulse.manager as m

    m._manager = mgr

    phase = ImpulsePhase()
    result = await phase.execute(PipelineContext(user_message="hi"))
    assert result.data["impulse_primary"] == "unknown"
    assert result.data["impulse_bias"] == ""
