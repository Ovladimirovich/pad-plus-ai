"""Tests for ImpulseUpdatePhase + signals producer (single writer)."""

import pytest

from core.impulse.core import ImpulseCore
from core.impulse.signals import infer_experience, ensure_experience_in_context
from core.pipeline.context import PipelineContext
from core.pipeline.phases.impulse_update import ImpulseUpdatePhase


class TestSignals:
    def test_praise(self):
        t, s = infer_experience("Спасибо, отлично!")
        assert t == "praise"
        assert s >= 0.2

    def test_criticism(self):
        t, s = infer_experience("Это плохо и неверно")
        assert t == "criticism"
        assert s >= 0.2

    def test_exploration(self):
        t, s = infer_experience("Почему небо голубое?")
        assert t == "exploration"
        assert s >= 0.2

    def test_fallback_error(self):
        t, s = infer_experience("hi", {"provider": "fallback"})
        assert t == "error_recovery"

    def test_default_low_sig(self):
        t, s = infer_experience("просто фраза")
        assert t == "new_knowledge"
        assert s < 0.2

    def test_ensure_preserves_existing(self):
        ctx = {"experience_interaction_type": "praise", "experience_significance": 0.9}
        t, s = ensure_experience_in_context(ctx, "ignored")
        assert t == "praise"
        assert s == 0.9


@pytest.mark.asyncio
async def test_impulse_update_applies_on_criticism(monkeypatch):
    from unittest.mock import patch

    core = ImpulseCore()
    core.set_from_labels({"understand": 0.5, "improve": 0.3})
    improve_before = next(d.weight for d in core.dimensions if d.label == "improve")

    with patch("core.impulse.session_store.get_session_impulse_store") as mock_store:
        store = mock_store.return_value
        store.get_or_create.return_value = core

        phase = ImpulseUpdatePhase()
        ctx = PipelineContext(
            user_message="Это плохо и ошибка",
            context={},
        )
        result = await phase.execute(ctx)

    assert result.success
    assert result.data["impulse_updated"] is True
    assert result.data["experience_interaction_type"] == "criticism"
    improve_after = next(d.weight for d in core.dimensions if d.label == "improve")
    assert improve_after > improve_before
    store.save.assert_called_once_with(ctx.session_id)


@pytest.mark.asyncio
async def test_impulse_update_noop_low_significance():
    from unittest.mock import patch

    core = ImpulseCore()
    core.set_from_labels({"understand": 0.5})

    with patch("core.impulse.session_store.get_session_impulse_store") as mock_store:
        mock_store.return_value.get_or_create.return_value = core

        phase = ImpulseUpdatePhase()
        result = await phase.execute(
            PipelineContext(user_message="просто фраза без маркеров", context={})
        )
    assert result.success
    assert result.data["impulse_updated"] is False
    assert result.data.get("reason") == "low_significance"


@pytest.mark.asyncio
async def test_impulse_update_uses_explicit_context():
    from unittest.mock import patch

    core = ImpulseCore()
    core.set_from_labels({"understand": 0.5})

    with patch("core.impulse.session_store.get_session_impulse_store") as mock_store:
        mock_store.return_value.get_or_create.return_value = core

        phase = ImpulseUpdatePhase()
        result = await phase.execute(
            PipelineContext(
                user_message="нейтрально",
                context={
                    "experience_interaction_type": "exploration",
                    "experience_significance": 0.5,
                },
            )
        )
    assert result.success
    assert result.data["impulse_updated"] is True
    assert result.data["experience_interaction_type"] == "exploration"
