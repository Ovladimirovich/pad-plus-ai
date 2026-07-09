import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

logger = logging.getLogger("padplus.evolution.reflection")


class ReflectionInsight:
    """Инсайт, полученный из анализа опыта"""

    def __init__(
        self,
        domain: str,
        insight: str,
        confidence: float,
        suggested_action: str,
        priority: float = 0.5,
    ):
        self.domain = domain
        self.insight = insight
        self.confidence = confidence
        self.suggested_action = suggested_action
        self.priority = priority
        self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> dict:
        return {
            "domain": self.domain,
            "insight": self.insight,
            "confidence": self.confidence,
            "suggested_action": self.suggested_action,
            "priority": self.priority,
            "timestamp": self.timestamp,
        }


class ReflectionEngine:
    """Анализирует накопленный опыт и эмоциональные тренды."""

    def reflect(self, experiences: List[dict], emotion_history: Optional[List[dict]] = None) -> List[ReflectionInsight]:
        if not experiences:
            return []

        insights: List[ReflectionInsight] = []

        recent = experiences[-30:] if len(experiences) > 30 else experiences

        interaction_types = [e.get("interaction_type", "unknown") for e in recent]
        strategy_scores = [e.get("strategy_success", 0.0) for e in recent if e.get("strategy_success") is not None]
        sentiments = [e.get("signals", {}).get("sentiment", "neutral") for e in recent]

        type_counts: Dict[str, int] = {}
        for t in interaction_types:
            type_counts[t] = type_counts.get(t, 0) + 1

        total = len(recent)
        for t, count in type_counts.items():
            ratio = count / total
            if ratio > 0.3:
                insights.append(ReflectionInsight(
                    domain="interaction_pattern",
                    insight=f"Частый тип взаимодействия: {t} ({ratio:.0%})",
                    confidence=min(ratio, 0.9),
                    suggested_action=f"review_strategy:{t}",
                    priority=ratio,
                ))

        if strategy_scores:
            avg_strategy = sum(strategy_scores) / len(strategy_scores)
            if avg_strategy < 0.3:
                insights.append(ReflectionInsight(
                    domain="strategy_effectiveness",
                    insight="Стратегии показывают низкую эффективность",
                    confidence=0.7,
                    suggested_action="increase_skepticism",
                    priority=0.8,
                ))
            elif avg_strategy > 0.8:
                insights.append(ReflectionInsight(
                    domain="strategy_effectiveness",
                    insight="Стратегии показывают высокую эффективность",
                    confidence=0.6,
                    suggested_action="increase_curiosity",
                    priority=0.4,
                ))

        positive = sentiments.count("positive")
        negative = sentiments.count("negative")
        if total > 0 and positive / total > 0.4:
            insights.append(ReflectionInsight(
                domain="sentiment_trend",
                insight="Преобладает позитивный сентимент пользователей",
                confidence=min(positive / total, 0.85),
                suggested_action="increase_empathy",
                priority=positive / total,
            ))
        if total > 0 and negative / total > 0.3:
            insights.append(ReflectionInsight(
                domain="sentiment_trend",
                insight="Заметен негативный сентимент пользователей",
                confidence=min(negative / total, 0.7),
                suggested_action="increase_caution",
                priority=negative / total,
            ))

        contradictions = sum(1 for e in recent if e.get("signals", {}).get("contradiction_detected"))
        if contradictions > 2:
            insights.append(ReflectionInsight(
                domain="contradiction_pattern",
                insight=f"Обнаружено {contradictions} противоречий в последних диалогах",
                confidence=min(contradictions / len(recent) * 2, 0.8),
                suggested_action="increase_humility",
                priority=min(contradictions / len(recent), 0.7),
            ))

        repetitions = sum(1 for e in recent if e.get("signals", {}).get("is_repetition"))
        if repetitions > 3:
            insights.append(ReflectionInsight(
                domain="repetition_pattern",
                insight="Много повторяющихся диалогов — требуется новый подход",
                confidence=0.6,
                suggested_action="increase_creativity",
                priority=0.5,
            ))

        return insights
