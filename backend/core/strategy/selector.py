"""
StrategySelector — выбор стратегии на основе контекста и MetaLearner.

Фаза 0: заглушка. Использует статический keyword-matching.
Фаза 3: будет добавлен MetaLearner + Constitution.
"""

from typing import Optional
import logging

logger = logging.getLogger("padplus.strategy")


class StrategySelector:
    """
    Выбирает стратегию обработки запроса.

    Вход:
    - user_message
    - context (intent, history, etc.)
    - MetaLearner (Фаза 3)

    Выход:
    - стратегия: simple / retrieval / reasoning / creative / reflective / learning
    """

    def select(
        self,
        user_message: str,
        context: Optional[dict] = None,
    ) -> str:
        """
        Определяет стратегию.

        Фаза 0: статический keyword-matching (как было в executor.py).
        Фаза 3: будет советоваться с MetaLearner.
        """
        text_lower = user_message.lower().strip()

        if any(kw in text_lower for kw in ["почему ты", "как ты", "что ты думаешь о себе"]):
            return "reflective"
        if any(kw in text_lower for kw in ["запомни", "выучи", "новый факт"]):
            return "learning"
        if any(kw in text_lower for kw in ["придумай", "сочини", "креативно"]):
            return "creative"
        if len(user_message) < 20:
            return "simple"
        if len(user_message) < 100:
            return "retrieval"

        return "reasoning"
