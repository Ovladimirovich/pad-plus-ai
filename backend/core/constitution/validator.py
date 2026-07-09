"""
ConstitutionValidator — проверяет изменения стратегии на соответствие правилам.

Используется Evolution Layer перед применением любого изменения поведения.
"""

from typing import Dict, Any, Optional
import logging

from core.anti_directive import ANTI_DIRECTIVE

logger = logging.getLogger("padplus.constitution")


class ValidationResult:
    """Результат проверки конституцией."""

    def __init__(
        self,
        passed: bool,
        reason: str = "",
        layer: str = "",
        confidence: float = 1.0,
    ):
        self.passed = passed
        self.reason = reason
        self.layer = layer
        self.confidence = confidence

    def to_dict(self) -> dict:
        return {
            "passed": self.passed,
            "reason": self.reason,
            "layer": self.layer,
            "confidence": self.confidence,
        }


class ConstitutionValidator:
    """
    Проверяет изменения стратегии и поведения.

    Слои проверки (в порядке применения):
    1. anti_directive — запрет абсолютизма
    2. roots — корневые принципы (заглушка, будет подключено в Фазе 4)
    3. bounds — границы допустимых значений
    """

    # Допустимые границы для trait-изменений
    TRAIT_BOUNDS = {
        "min": -0.5,
        "max": 1.0,
        "max_delta_per_step": 0.2,
    }

    def validate_strategy_change(
        self,
        proposed_strategy: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> ValidationResult:
        """Проверяет смену стратегии."""
        # AntiDirective: стратегия не должна содержать абсолютизм
        if not ANTI_DIRECTIVE.validate(proposed_strategy):
            return ValidationResult(
                passed=False,
                reason=f"Стратегия '{proposed_strategy}' нарушает AntiDirective",
                layer="anti_directive",
            )

        return ValidationResult(passed=True, layer="constitution")

    def validate_trait_change(
        self,
        trait_name: str,
        current_value: float,
        delta: float,
    ) -> ValidationResult:
        """Проверяет изменение черты личности."""
        new_value = current_value + delta

        # Проверка границ
        if new_value < self.TRAIT_BOUNDS["min"]:
            return ValidationResult(
                passed=False,
                reason=f"Черта '{trait_name}' выходит за нижнюю границу "
                       f"({new_value:.2f} < {self.TRAIT_BOUNDS['min']})",
                layer="bounds",
            )

        if new_value > self.TRAIT_BOUNDS["max"]:
            return ValidationResult(
                passed=False,
                reason=f"Черта '{trait_name}' выходит за верхнюю границу "
                       f"({new_value:.2f} > {self.TRAIT_BOUNDS['max']})",
                layer="bounds",
            )

        # Проверка дельты
        if abs(delta) > self.TRAIT_BOUNDS["max_delta_per_step"]:
            return ValidationResult(
                passed=False,
                reason=f"Изменение черты '{trait_name}' слишком большое "
                       f"({delta:.2f} > {self.TRAIT_BOUNDS['max_delta_per_step']})",
                layer="bounds",
                confidence=0.7,
            )

        # AntiDirective: проверяем, не приводит ли изменение к абсолютизму
        if new_value >= 0.95:
            test_knowledge = f"Я {trait_name} на {new_value:.0%}"
            if not ANTI_DIRECTIVE.validate(test_knowledge):
                return ValidationResult(
                    passed=False,
                    reason=f"Черта '{trait_name}' приближается к абсолютизму",
                    layer="anti_directive",
                    confidence=0.8,
                )

        return ValidationResult(passed=True, layer="constitution")

    def validate_all(
        self,
        changes: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> list[ValidationResult]:
        """Проверяет набор изменений."""
        results = []

        strategy = changes.get("strategy")
        if strategy:
            results.append(self.validate_strategy_change(strategy, context))

        traits = changes.get("traits", {})
        for trait_name, delta in traits.items():
            current = (context or {}).get("traits", {}).get(trait_name, 0.0)
            results.append(self.validate_trait_change(trait_name, current, delta))

        return results
