import logging
from typing import Any, Dict, List, Optional

from .meta_learner import EvolutionDecision

logger = logging.getLogger("padplus.evolution.constitution")

TRAIT_BOUNDS: Dict[str, tuple[float, float]] = {}
STYLE_BOUNDS: Dict[str, tuple[float, float]] = {
    "verbosity": (0.1, 0.9),
    "formality": (0.1, 0.9),
    "emotional_expressiveness": (0.1, 0.9),
}

MAX_TRAIT_CHANGE_PER_CYCLE = 0.1
MAX_STYLE_CHANGE_PER_CYCLE = 0.1


class Constitution:
    """Безопасно применяет изменения к личности."""

    def apply_trait(
        self,
        current_value: float,
        delta: float,
        trait_name: str,
    ) -> tuple[float, float]:
        applied_delta = max(-MAX_TRAIT_CHANGE_PER_CYCLE, min(MAX_TRAIT_CHANGE_PER_CYCLE, delta))
        new_value = max(0.0, min(1.0, current_value + applied_delta))
        actual_delta = round(new_value - current_value, 4)
        return new_value, actual_delta

    def apply_style(
        self,
        current_value: float,
        delta: float,
        style_name: str,
    ) -> tuple[float, float]:
        applied_delta = max(-MAX_STYLE_CHANGE_PER_CYCLE, min(MAX_STYLE_CHANGE_PER_CYCLE, delta))
        bounds = STYLE_BOUNDS.get(style_name, (0.0, 1.0))
        new_value = max(bounds[0], min(bounds[1], current_value + applied_delta))
        actual_delta = round(new_value - current_value, 4)
        return new_value, actual_delta

    def execute(
        self,
        decisions: List[EvolutionDecision],
        persona,
    ) -> List[dict]:
        if not decisions:
            return []

        applied: List[dict] = []

        for decision in decisions:
            try:
                target = decision.target
                if target.startswith("trait:"):
                    trait_key = target.split(":", 1)[1]
                    trait = persona.get_trait(trait_key)
                    if trait is not None:
                        new_val, actual_delta = self.apply_trait(trait.value, decision.delta, trait_key)
                        if actual_delta != 0.0:
                            persona.adjust_trait(trait_key, actual_delta)
                            applied.append({
                                "target": target,
                                "delta": actual_delta,
                                "reason": decision.reason,
                                "confidence": decision.confidence,
                            })
                            logger.info("Конституция: %s %+.4f — %s", trait_key, actual_delta, decision.reason)
                    else:
                        logger.debug("Конституция: черта %s не найдена", trait_key)

                elif target.startswith("style:"):
                    style_key = target.split(":", 1)[1]
                    if style_key in persona.style_preferences:
                        current = persona.style_preferences[style_key]
                        new_val, actual_delta = self.apply_style(current, decision.delta, style_key)
                        if actual_delta != 0.0:
                            persona.style_preferences[style_key] = new_val
                            applied.append({
                                "target": target,
                                "delta": actual_delta,
                                "reason": decision.reason,
                                "confidence": decision.confidence,
                            })
                            logger.info("Конституция: стиль %s %+.4f — %s", style_key, actual_delta, decision.reason)
                else:
                    logger.debug("Конституция: неизвестный target %s", target)

            except Exception as e:
                logger.warning("Конституция: ошибка при применении %s: %s", decision.target, e)

        if applied:
            try:
                persona._save()
            except Exception as e:
                logger.warning("Конституция: ошибка сохранения: %s", e)

        return applied
