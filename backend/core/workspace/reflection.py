"""
ReflectionEngine — движок рефлексии для анализа гипотез и evidence в WorkingScratchpad (D'-3).
"""

from typing import Dict, Any, List
from .schemas import TurnWorkspace, WorkingScratchpad, PhaseName


class ReflectionEngine:
    """Движок рефлексии для проверки выводов текущего хода."""

    @staticmethod
    def reflect_on_turn(workspace: TurnWorkspace) -> Dict[str, Any]:
        """
        Анализирует scratchpad воркспейса текущего хода:
        - Проверяет обоснованность гипотез доказательствами (evidence).
        - Вычисляет общую уверенность.
        - Формирует краткий отчёт рефлексии.
        """
        scratchpad = workspace.scratchpad
        total_hypotheses = len(scratchpad.hypotheses)
        supported_count = 0
        unsupported_count = 0

        evaluations = []
        for hyp in scratchpad.hypotheses:
            has_evidence = len(hyp.supporting_evidence) > 0
            if has_evidence:
                supported_count += 1
                evaluations.append({
                    "hypothesis_id": hyp.id,
                    "statement": hyp.statement,
                    "status": "supported",
                    "evidence_count": len(hyp.supporting_evidence)
                })
            else:
                unsupported_count += 1
                evaluations.append({
                    "hypothesis_id": hyp.id,
                    "statement": hyp.statement,
                    "status": "unsupported_needs_evidence",
                    "evidence_count": 0
                })

        # Общая оценка рефлексии
        coherence_score = 1.0
        if total_hypotheses > 0:
            coherence_score = supported_count / total_hypotheses

        reflection_result = {
            "total_hypotheses": total_hypotheses,
            "supported_count": supported_count,
            "unsupported_count": unsupported_count,
            "coherence_score": coherence_score,
            "evaluations": evaluations,
            "summary": f"Проверено гипотез: {total_hypotheses}. Обосновано: {supported_count}."
        }

        # Сохраняем результат в фазовый воркспейс
        workspace.update_phase(PhaseName.REFLECTION, reflection_result)
        return reflection_result
