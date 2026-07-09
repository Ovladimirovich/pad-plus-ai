import pytest
from unittest.mock import MagicMock, patch

from core.pipeline.context import PipelineContext
from core.pipeline.phases.evaluation import EvaluationPhase
from learning.evaluator import EvaluationResult


@pytest.fixture
def mock_evaluator():
    m = MagicMock()
    m.evaluate.return_value = EvaluationResult(
        completeness=0.8,
        consistency=0.9,
        safety=1.0,
        confidence=0.85,
        latency_score=0.9,
        novelty=0.6,
        overall=0.85,
        details={"response_length": 100},
    )
    return m


@pytest.fixture
def mock_collector():
    m = MagicMock()
    m.record_dialog.return_value = "test-dialog-id"
    return m


class TestEvaluationPhase:
    @pytest.mark.asyncio
    async def test_evaluates_response(self, mock_evaluator, mock_collector):
        phase = EvaluationPhase(evaluator=mock_evaluator, collector=mock_collector)
        ctx = PipelineContext(
            user_message="Что такое Python?",
            context={
                "response": "Python — это язык программирования.",
                "strategy": "retrieval",
            },
        )
        result = await phase.execute(ctx)

        assert result.success is True
        assert result.data["evaluation_skipped"] is False
        assert "evaluation" in result.data
        assert result.data["evaluation"]["overall"] == 0.85

    @pytest.mark.asyncio
    async def test_skips_when_no_response(self, mock_evaluator, mock_collector):
        phase = EvaluationPhase(evaluator=mock_evaluator, collector=mock_collector)
        ctx = PipelineContext(
            user_message="вопрос",
            context={"response": ""},
        )
        result = await phase.execute(ctx)

        assert result.success is True
        assert result.data["evaluation_skipped"] is True

    @pytest.mark.asyncio
    async def test_records_dialog(self, mock_evaluator, mock_collector):
        phase = EvaluationPhase(evaluator=mock_evaluator, collector=mock_collector)
        ctx = PipelineContext(
            user_message="Расскажи про ИИ",
            context={
                "response": "Искусственный интеллект — это...",
                "strategy": "reasoning",
            },
        )
        await phase.execute(ctx)

        mock_collector.record_dialog.assert_called_once()
        call_kwargs = mock_collector.record_dialog.call_args[1]
        assert call_kwargs["prompt"] == "Расскажи про ИИ"
        assert call_kwargs["response"] == "Искусственный интеллект — это..."
        assert "evaluation" in call_kwargs

    @pytest.mark.asyncio
    async def test_passes_metadata(self, mock_evaluator, mock_collector):
        phase = EvaluationPhase(evaluator=mock_evaluator, collector=mock_collector)
        ctx = PipelineContext(
            user_message="вопрос",
            context={
                "response": "ответ",
                "strategy": "creative",
                "provider": "openrouter",
            },
        )
        await phase.execute(ctx)

        call_kwargs = mock_collector.record_dialog.call_args[1]
        assert call_kwargs["metadata"]["strategy"] == "creative"
        assert call_kwargs["metadata"]["provider"] == "openrouter"

    @pytest.mark.asyncio
    async def test_evaluate_called_with_metadata(self, mock_evaluator, mock_collector):
        phase = EvaluationPhase(evaluator=mock_evaluator, collector=mock_collector)
        ctx = PipelineContext(
            user_message="вопрос",
            context={
                "response": "ответ",
                "execution_time_ms": 1500,
            },
        )
        await phase.execute(ctx)

        mock_evaluator.evaluate.assert_called_once()
        meta = mock_evaluator.evaluate.call_args[1]["metadata"]
        assert meta["execution_time_ms"] == 1500

    @pytest.mark.asyncio
    async def test_evaluator_error_handling(self, mock_collector):
        broken_evaluator = MagicMock()
        broken_evaluator.evaluate.side_effect = Exception("evaluation failed")

        phase = EvaluationPhase(evaluator=broken_evaluator, collector=mock_collector)
        ctx = PipelineContext(
            user_message="вопрос",
            context={"response": "ответ"},
        )
        result = await phase.execute(ctx)

        assert not result.success
        assert result.errors
