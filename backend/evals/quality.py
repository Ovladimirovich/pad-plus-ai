from typing import Any, Dict, Optional

from ..learning.evaluator import SelfEvaluator, get_evaluator
from .base import BaseEvaluator, EvalScore


class QualityEvaluator(BaseEvaluator):
    def __init__(self, source: Optional[SelfEvaluator] = None):
        self._source = source

    def _get(self) -> SelfEvaluator:
        return self._source or get_evaluator()

    async def evaluate(
        self,
        response: str,
        expected: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> EvalScore:
        ctx = context or {}
        prompt = ctx.get("prompt", "")
        metadata = ctx.get("metadata", {})

        result = self._get().evaluate(prompt=prompt, response=response, metadata=metadata)

        return EvalScore(
            name="quality",
            value=result.overall,
            weight=1.0,
            details={
                "completeness": result.completeness,
                "consistency": result.consistency,
                "safety": result.safety,
                "confidence": result.confidence,
                "latency_score": result.latency_score,
                "novelty": result.novelty,
            },
        )
