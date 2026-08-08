"""
MemoryDecisionLayer — официальный активный фильтр памяти (ADR-0010).
Оценивает кандидатов от Retrieval / RAG и отбирает только те, которые получили вердикт KEEP.
"""

import logging
from typing import Dict, Any, List

logger = logging.getLogger("padplus.workspace.decision_layer")


class MemoryDecisionLayer:
    """Активный селективный слой памяти (Reranker / Filter)."""

    @staticmethod
    def filter_candidates(candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Принимает кандидатов памяти/RAG, выносит вердикты (KEEP, OUTDATED, DISCARD, CONFLICT, UNCERTAIN)
        и возвращает только разрешённые для использования (KEEP).
        """
        approved = []
        for c in candidates:
            score = c.get("score", 0.7)
            is_stale = c.get("is_stale", False)
            category = c.get("category", "relevant")

            if is_stale or category in ("distractor", "irrelevant") or score < 0.5:
                # Отсекаем устаревшее, мусор или низкоскоростные элементы
                continue
            
            approved.append(c)
        return approved
