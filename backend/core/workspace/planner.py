"""
Planner и Learning Coordinator для управления целями и сигналами обучения в воркспейсе (D'-4).
"""

import logging
from typing import Dict, Any, List
from .schemas import ConversationWorkspace, TurnWorkspace

logger = logging.getLogger("padplus.workspace.planner")


class CognitivePlanner:
    """Динамический планировщик шагов на основе активных целей сессии."""

    @staticmethod
    def plan_next_steps(workspace: TurnWorkspace, conversation: ConversationWorkspace) -> List[str]:
        """
        Формирует план подзадач/фаз для текущего хода на основе:
        - Сообщения пользователя
        - Активных целей сессии (active_goals)
        - Интента
        """
        active_goals = conversation.core.active_goals

        steps = ["safety", "intent", "rag", "knowledge_graph"]

        # Если есть активные цели, требующие глубокого анализа
        if active_goals:
            steps.append("reflection")
            steps.append("truth_loop")

        steps.extend(["generate", "evaluation", "save_episode"])
        
        workspace.phase_outputs["planned_steps"] = steps
        logger.debug("Сформирован план шагов: %s", steps)
        return steps


class LearningCoordinator:
    """Координатор обучения — единый центр сбора сигналов от рефлексии и воркспейса."""

    @staticmethod
    def coordinate_learning(workspace: TurnWorkspace, reflection_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Собирает метрики обучения из хода и рефлексии:
        - Оценивает качество (coherence_score)
        - Формирует обучающий сигнал для Experience/Meta-Learner
        """
        coherence = reflection_result.get("coherence_score", 1.0)
        unsupported = reflection_result.get("unsupported_count", 0)

        learning_signal = {
            "significance": 1.0 if unsupported > 0 else 0.5,
            "reinforcement": coherence,
            "requires_consolidation": unsupported > 0,
            "metrics": {
                "coherence_score": coherence,
                "unsupported_hypotheses": unsupported
            }
        }

        workspace.phase_outputs["learning_signal"] = learning_signal
        return learning_signal
