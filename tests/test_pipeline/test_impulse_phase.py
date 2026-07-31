"""Tests for ImpulsePhase (pre-generate read)."""

import pytest

from core.pipeline.context import PipelineContext
from core.pipeline.phases.impulse import ImpulsePhase


def _build_mock_core(label="understand", bias="", state=None, active=None):
    """Строит MagicMock, имитирующий ImpulseCore из session store."""
    from unittest.mock import MagicMock

    core = MagicMock()
    core.get_primary_label.return_value = label
    core.get_bias_block.return_value = bias
    core.get_prompt_line.return_value = f"primary_impulse: {label}"
    core.to_dict.return_value = state or {"version": 2}
    if active is not None:
        from core.impulse.core import ImpulseCore as _IC, default_dimensions

        dims = default_dimensions()
        real_dims = []
        for d in dims:
            d.weight = 0.0
            real_dims.append(d)
        for item in active:
            d = next(x for x in real_dims if x.label == item["label"])
            d.weight = item["weight"]
        core.get_active_questions.return_value = [d for d in real_dims if d.weight >= 0.3]
    else:
        core.get_active_questions.return_value = []
    return core


@pytest.mark.asyncio
async def test_impulse_phase_merges_keys(monkeypatch):
    from unittest.mock import patch

    core = _build_mock_core(
        label="understand",
        bias={"understand": "Понимать"},
        state={"version": 2},
        active=[{"label": "understand", "weight": 1.0, "question": "Как устроен мир?"}],
    )

    with patch("core.impulse.session_store.get_session_impulse_store") as mock_store:
        mock_store.return_value.get_or_create.return_value = core
        phase = ImpulsePhase()
        result = await phase.execute(PipelineContext(user_message="test"))

    assert result.success
    assert result.data["impulse_primary"] == "understand"
    assert result.data["impulse_state"]["version"] == 2
    assert isinstance(result.data["impulse_active"], list)


@pytest.mark.asyncio
async def test_impulse_phase_unknown_empty_bias(monkeypatch):
    from unittest.mock import patch

    core = _build_mock_core(label="unknown", bias="")

    with patch("core.impulse.session_store.get_session_impulse_store") as mock_store:
        mock_store.return_value.get_or_create.return_value = core
        phase = ImpulsePhase()
        result = await phase.execute(PipelineContext(user_message="hi"))

    assert result.data["impulse_primary"] == "unknown"
    assert result.data["impulse_bias"] == ""
