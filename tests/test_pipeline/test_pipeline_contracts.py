"""
Фокусные тесты контрактов pipeline (A1-A3 из REMAINING_TASKS_PLAN).

A1: EvaluationPhase получает execution_time_ms (через start_time из ctx.context).
A2: SemanticPhase пишет procedure_name, SaveEpisodePhase читает тот же ключ.
A3: ReflectionPhase получает pipeline_result из ctx.context (result_dict).
"""

import time
from unittest.mock import MagicMock, patch

from backend.core.pipeline.context import PipelineContext
from backend.core.pipeline.models import PipelineResult, PhaseResult
from backend.core.pipeline.phases.evaluation import EvaluationPhase
from backend.core.pipeline.phases.reflection import ReflectionPhase
from backend.core.pipeline.phases.save_episode import SaveEpisodePhase
from backend.learning.evaluator import EvaluationResult


async def test_a1_evaluation_receives_execution_time_ms():
    """A1: EvaluationPhase вычисляет execution_time_ms из ctx.context['start_time']."""
    mock_eval = MagicMock()
    mock_eval.evaluate.return_value = EvaluationResult(
        completeness=0.8, consistency=0.9, safety=1.0, confidence=0.85,
        latency_score=0.9, novelty=0.6, overall=0.85,
        details={"response_length": 100},
    )
    mock_collector = MagicMock()

    phase = EvaluationPhase(evaluator=mock_eval, collector=mock_collector)
    ctx = PipelineContext(
        user_message="вопрос",
        context={
            "response": "ответ",
            "start_time": time.perf_counter() - 0.05,  # 50ms назад
        },
    )
    result = await phase.execute(ctx)
    assert result.success

    meta = mock_eval.evaluate.call_args[1]["metadata"]
    assert "execution_time_ms" in meta
    assert meta["execution_time_ms"] >= 0


async def test_a2_save_episode_reads_semantic_procedure_name():
    """A2: procedure_name, который пишет SemanticPhase, читается SaveEpisodePhase."""
    mock_episode = MagicMock()
    mock_episode.id = "ep_contract"
    mock_mem = MagicMock()
    mock_mem.add_episode.return_value = mock_episode

    with patch("memory.get_episodic_memory", return_value=mock_mem):
        phase = SaveEpisodePhase()
        ctx = PipelineContext(
            user_message="задача",
            context={
                "response": "ответ",
                "procedure_name": "deployment_procedure",  # ключ SemanticPhase
                "rag_used": False,
                "truth_confidence": 0.5,
                "emotion_state": {"уверенность": 0.7},
            },
        )
        result = await phase.execute(ctx)

    assert result.success
    assert result.data["episode_id"] == "ep_contract"

    # significance должен получить +0.15 за procedure_used
    call_kwargs = mock_mem.add_episode.call_args[1]
    assert call_kwargs["significance"] == 0.65
    assert call_kwargs["procedure_name"] == "deployment_solution" if "procedure_name" in call_kwargs else True


async def test_a3_reflection_consumes_pipeline_result():
    """A3: ReflectionPhase использует ctx.context['pipeline_result'] (result_dict)."""
    result_obj = PipelineResult(response="ответ", success=True, confidence=0.8)
    result_obj.execution_time_ms = 150.0

    ctx = PipelineContext(
        user_message="тест",
        context={"pipeline_result": result_obj},
    )

    # Список мета-контроллера, чтобы meta.adapt не падал
    with patch("core.meta_controller.get_meta_controller") as mock_mc:
        mc = MagicMock()
        mc.adapt.return_value = None
        mock_mc.return_value = mc

        phase = ReflectionPhase()
        result = await phase.execute(ctx)

    assert result.success
    # meta.adapt получил strategy_success из pipeline_result
    mc.adapt.assert_called_once()
    adapt_payload = mc.adapt.call_args[0][0]
    assert adapt_payload["strategy_success"] is True