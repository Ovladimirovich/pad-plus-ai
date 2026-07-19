from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class EvalScore:
    name: str
    value: float
    weight: float = 1.0
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EvaluationReport:
    evaluator: str
    scores: List[EvalScore] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def weighted_total(self) -> float:
        if not self.scores:
            return 0.0
        total_weight = sum(s.weight for s in self.scores)
        if total_weight == 0:
            return 0.0
        return sum(s.value * s.weight for s in self.scores) / total_weight

    def to_dict(self) -> dict:
        return {
            "evaluator": self.evaluator,
            "scores": [
                {"name": s.name, "value": round(s.value, 3), "weight": s.weight}
                for s in self.scores
            ],
            "weighted_total": round(self.weighted_total, 3),
            "metadata": self.metadata,
        }


class BaseEvaluator(ABC):
    @abstractmethod
    async def evaluate(
        self,
        response: str,
        expected: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> EvalScore:
        ...
