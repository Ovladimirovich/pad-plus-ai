"""
Эволюционный слой PAD+ AI.

Отвечает за:
- Reflection — анализ накопленного опыта и эмоциональных трендов
- MetaLearner — принятие решений об изменении личности
- Constitution — безопасное применение изменений
"""

from .constitution import Constitution
from .meta_learner import EvolutionDecision, MetaLearner
from .reflection import ReflectionEngine, ReflectionInsight

__all__ = [
    "Constitution",
    "EvolutionDecision",
    "MetaLearner",
    "ReflectionEngine",
    "ReflectionInsight",
]
