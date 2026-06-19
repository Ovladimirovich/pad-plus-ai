"""
🎯 Strategy Layer — выбор стратегии обработки запроса.

Определяет, как pipeline будет обрабатывать запрос:
simple / retrieval / reasoning / creative / reflective / learning

Фаза 0: заглушка. Реализация — в Фазе 3.
"""

from .selector import StrategySelector

__all__ = ["StrategySelector"]
