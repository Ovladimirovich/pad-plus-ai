import logging
from typing import Optional

from core.pipeline.base import PipelinePhase
from core.pipeline.models import PhaseResult
from core.pipeline.context import PipelineContext
from learning.evaluator import SelfEvaluator, get_evaluator
from learning.collector import DataCollector, get_collector

logger = logging.getLogger("padplus.pipeline.evaluation")


class EvaluationPhase(PipelinePhase):
    name = "evaluation"

    def __init__(self, evaluator: Optional[SelfEvaluator] = None, collector: Optional[DataCollector] = None):
        self._evaluator = evaluator
        self._collector = collector

    def _get_evaluator(self) -> SelfEvaluator:
        return self._evaluator or get_evaluator()

    def _get_collector(self) -> DataCollector:
        return self._collector or get_collector()

    async def execute(self, ctx: PipelineContext) -> PhaseResult:
        # TEMPORARILY DISABLED FOR PERFORMANCE
        return PhaseResult(success=True, data={"evaluation_skipped": True, "reason": "disabled_for_performance"})

        response = ctx.context.get("response", "")
        if not response:
            return PhaseResult(success=True, data={"evaluation_skipped": True, "reason": "no_response"})

        try:
            evaluator = self._get_evaluator()
            collector = self._get_collector()
            user_message = ctx.user_message

            evaluation = evaluator.evaluate(
                prompt=user_message,
                response=response,
                metadata={
                    "confidence": ctx.context.get("confidence"),
                    "execution_time_ms": ctx.context.get("execution_time_ms"),
                },
            )

            eval_dict = evaluation.to_dict()

            metadata = {
                "strategy": ctx.context.get("strategy"),
                "intent": ctx.context.get("intent"),
                "provider": ctx.context.get("provider"),
                "model": ctx.context.get("model"),
            }

            collector.record_dialog(
                prompt=user_message,
                response=response,
                evaluation=eval_dict,
                metadata=metadata,
            )

            return PhaseResult(
                success=True,
                data={
                    "evaluation": eval_dict,
                    "evaluation_skipped": False,
                },
            )
        except Exception as e:
            logger.warning("Evaluation failed: %s", str(e))
            return PhaseResult(
                success=False,
                errors=[f"Evaluation error: {str(e)}"],
            )
