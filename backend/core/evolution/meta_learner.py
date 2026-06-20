import logging
from typing import Any, Dict, List, Optional, Tuple

from .reflection import ReflectionInsight

logger = logging.getLogger("padplus.evolution.meta_learner")

TRAIT_MAP: Dict[str, str] = {
    "increase_skepticism": ("skepticism", 0.03),
    "increase_curiosity": ("curiosity", 0.03),
    "increase_empathy": ("empathy", 0.03),
    "increase_caution": ("caution", 0.03),
    "increase_humility": ("humility", 0.03),
    "increase_creativity": ("creativity", 0.03),
    "increase_openness": ("openness", 0.03),
    "decrease_skepticism": ("skepticism", -0.03),
    "decrease_caution": ("caution", -0.03),
}

STYLE_MAP: Dict[str, Tuple[str, float]] = {
    "positive_sentiment": ("formality", -0.02),
    "negative_sentiment": ("formality", 0.02),
    "complex_questions": ("verbosity", 0.03),
    "simple_responses": ("verbosity", -0.02),
    "emotional_tone": ("emotional_expressiveness", 0.03),
}

ACTION_PRIORITIES = {
    "increase_skepticism": 0.7,
    "increase_curiosity": 0.5,
    "increase_empathy": 0.8,
    "increase_caution": 0.6,
    "increase_humility": 0.7,
    "increase_creativity": 0.6,
    "increase_openness": 0.4,
    "decrease_skepticism": 0.3,
    "decrease_caution": 0.3,
    "positive_sentiment": 0.4,
    "negative_sentiment": 0.5,
    "complex_questions": 0.3,
    "simple_responses": 0.2,
    "emotional_tone": 0.3,
}


class EvolutionDecision:
    """Решение об изменении личности."""

    def __init__(self, target: str, delta: float, reason: str, confidence: float):
        self.target = target
        self.delta = delta
        self.reason = reason
        self.confidence = confidence
        self.timestamp = __import__("datetime").datetime.now().isoformat()

    def to_dict(self) -> dict:
        return {
            "target": self.target,
            "delta": round(self.delta, 3),
            "reason": self.reason,
            "confidence": round(self.confidence, 3),
            "timestamp": self.timestamp,
        }


class MetaLearner:
    """Принимает решения об эволюции на основе рефлексии."""

    def decide(self, insights: List[ReflectionInsight]) -> List[EvolutionDecision]:
        if not insights:
            return []

        decisions: List[EvolutionDecision] = []

        seen_actions: set = set()
        for insight in sorted(insights, key=lambda i: i.priority, reverse=True):
            action = insight.suggested_action
            if action in seen_actions:
                continue
            seen_actions.add(action)

            if action in TRAIT_MAP:
                trait, base_delta = TRAIT_MAP[action]
                delta = base_delta * insight.confidence
                decisions.append(EvolutionDecision(
                    target=f"trait:{trait}",
                    delta=delta,
                    reason=insight.insight,
                    confidence=insight.confidence,
                ))

            if action.startswith("review_strategy:"):
                trait_type = action.split(":", 1)[1]
                if trait_type in ("error_recovery", "contradiction"):
                    decisions.append(EvolutionDecision(
                        target="trait:caution",
                        delta=0.04 * insight.confidence,
                        reason=f"Частые {trait_type} — повышаю осторожность",
                        confidence=insight.confidence,
                    ))
                elif trait_type in ("praise", "exploration"):
                    decisions.append(EvolutionDecision(
                        target="trait:openness",
                        delta=0.03 * insight.confidence,
                        reason=f"Частые {trait_type} — повышаю открытость",
                        confidence=insight.confidence,
                    ))

        return decisions
