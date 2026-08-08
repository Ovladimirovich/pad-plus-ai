"""
Shadow Mode Monitor для Memory Decision Layer (ADR-0010).
Анализирует кандидатов памяти в фоновом режиме, логирует решения (KEEP, OUTDATED, DISCARD, CONFLICT, UNCERTAIN)
и собирает метрики на реальном трафике без изменения продакшен-ответов.
"""

import logging
from typing import Dict, Any, List

logger = logging.getLogger("padplus.workspace.shadow_monitor")


class ShadowMemoryMonitor:
    """Монитор памяти в режиме shadow mode для сбора аналитики решений."""

    @staticmethod
    def evaluate_shadow_decision(candidates: List[Dict[str, Any]], query: str) -> Dict[str, Any]:
        """
        Прогоняет кандидатов через логику Decision Layer в фоновом режиме.
        Не влияет на отправляемый клиенту ответ.
        """
        decisions = []
        stats = {
            "total_candidates": len(candidates),
            "keep": 0,
            "outdated": 0,
            "discard": 0,
            "conflict": 0,
            "uncertain": 0
        }

        for c in candidates:
            score = c.get("score", 0.7)
            is_stale = c.get("is_stale", False)
            category = c.get("category", "relevant")

            if is_stale:
                verdict = "OUTDATED"
                stats["outdated"] += 1
            elif score < 0.5:
                verdict = "UNCERTAIN"
                stats["uncertain"] += 1
            elif category in ("distractor", "irrelevant"):
                verdict = "DISCARD"
                stats["discard"] += 1
            else:
                verdict = "KEEP"
                stats["keep"] += 1

            decisions.append({
                "id": c.get("id"),
                "verdict": verdict,
                "score": score
            })

        # Логируем статистику shadow mode для аналитики
        logger.info(
            "[SHADOW MODE] Query: '%s' | Candidates: %d | Decisions: KEEP=%d, OUTDATED=%d, DISCARD=%d, UNCERTAIN=%d",
            query[:40],
            stats["total_candidates"],
            stats["keep"],
            stats["outdated"],
            stats["discard"],
            stats["uncertain"]
        )

        return {
            "stats": stats,
            "decisions": decisions
        }
