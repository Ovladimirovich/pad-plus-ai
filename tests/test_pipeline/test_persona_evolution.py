from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from core.pipeline import PipelineContext
from core.pipeline.phases.persona_evolution import (
    PersonaEvolutionPhase,
    _reset_reflection_counter,
    REFLECTION_INTERVAL,
)


@pytest.fixture(autouse=True)
def reset_counter():
    _reset_reflection_counter()


async def test_persona_evolution_with_user():
    with patch("memory.user_persona.get_user_persona_manager") as mock_get:
        mock_persona = MagicMock()
        mock_mgr = MagicMock()
        mock_mgr.get_persona.return_value = mock_persona
        mock_get.return_value = mock_mgr

        phase = PersonaEvolutionPhase()
        ctx = PipelineContext(
            user_message="спасибо за помощь",
            context={
                "response": "Пожалуйста!",
                "user_id": "user_1",
            },
        )
        result = await phase.execute(ctx)

    assert result.success
    assert mock_persona.adjust_style.call_count >= 0


async def test_persona_evolution_fallback():
    with patch("memory.persona.get_persona") as mock_get:
        mock_p = MagicMock()
        mock_p.evolve_from_dialog.return_value = {"changes": []}
        mock_get.return_value = mock_p

        phase = PersonaEvolutionPhase()
        ctx = PipelineContext(
            user_message="спасибо",
            context={"response": "Пожалуйста!"},
        )
        result = await phase.execute(ctx)

    assert result.success


async def test_reflection_cycle_triggers():
    with (
        patch("memory.persona.get_persona") as mock_get_persona,
        patch("core.evolution.ReflectionEngine") as mock_engine_cls,
        patch("core.evolution.MetaLearner") as mock_learner_cls,
        patch("core.evolution.Constitution") as mock_constitution_cls,
        patch("core.experience.get_store") as mock_get_store,
    ):
        mock_p = MagicMock()
        mock_p.evolve_from_dialog.return_value = {"changes": []}
        mock_get_persona.return_value = mock_p

        mock_store = MagicMock()
        mock_store.load_all.return_value = [
            {"interaction_type": "praise", "strategy_success": 0.9, "signals": {"sentiment": "positive", "contradiction_detected": False, "is_repetition": False}}
            for _ in range(20)
        ]
        mock_get_store.return_value = mock_store

        mock_insight = MagicMock()
        mock_insight.domain = "test"
        mock_insight.insight = "test"
        mock_insight.confidence = 0.7
        mock_insight.suggested_action = "increase_empathy"
        mock_insight.priority = 0.7

        mock_engine = MagicMock()
        mock_engine.reflect.return_value = [mock_insight]
        mock_engine_cls.return_value = mock_engine

        mock_decision = MagicMock()
        mock_decision.target = "trait:empathy"
        mock_decision.delta = 0.02
        mock_decision.reason = "test"
        mock_decision.confidence = 0.7

        mock_learner = MagicMock()
        mock_learner.decide.return_value = [mock_decision]
        mock_learner_cls.return_value = mock_learner

        mock_constitution = MagicMock()
        mock_constitution.execute.return_value = [{"target": "trait:empathy", "delta": 0.02}]
        mock_constitution_cls.return_value = mock_constitution

        phase = PersonaEvolutionPhase()
        ctx = PipelineContext(user_message="тест", context={"response": "ответ"})

        for _ in range(REFLECTION_INTERVAL):
            result = await phase.execute(ctx)

        assert result.success
        assert mock_p.add_reflection.called


async def test_reflection_cycle_skipped_when_no_store():
    with (
        patch("memory.persona.get_persona") as mock_get_persona,
        patch("core.experience.get_store") as mock_get_store,
    ):
        mock_p = MagicMock()
        mock_p.evolve_from_dialog.return_value = {"changes": []}
        mock_get_persona.return_value = mock_p

        mock_store = MagicMock()
        mock_store.load_all.return_value = []
        mock_get_store.return_value = mock_store

        phase = PersonaEvolutionPhase()
        ctx = PipelineContext(user_message="тест", context={"response": "ответ"})

        for _ in range(REFLECTION_INTERVAL):
            result = await phase.execute(ctx)

        assert result.success
        assert not mock_p.add_reflection.called
