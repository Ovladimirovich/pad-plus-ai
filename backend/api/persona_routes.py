from fastapi import APIRouter
import logging
from typing import Dict, List, Tuple, Any

logger = logging.getLogger("padplus.experience")

router = APIRouter(prefix="/api/v1/admin/persona", tags=["Persona"])


def _build_persona_system_deltas() -> Dict[str, List[Tuple[str, float]]]:
    """Собирает текущие черты персоны и триггеры эволюции для отображения в UI."""
    from memory.persona import get_persona
    try:
        persona = get_persona()
        traits = persona.traits
    except Exception:
        return {}

    result: Dict[str, List[Tuple[str, float]]] = {}

    trait_labels = {
        "curiosity": "Любопытство",
        "skepticism": "Скептицизм",
        "empathy": "Эмпатия",
        "creativity": "Креативность",
        "caution": "Осторожность",
        "openness": "Открытость",
        "humility": "Смирение",
    }

    current = []
    for key, trait in traits.items():
        label = trait_labels.get(key, key)
        current.append((label, round(trait.value, 2)))
    if current:
        result["Текущие черты"] = current

    result["Триггеры эволюции"] = [
        ("caution+", "вопрос о фактах"),
        ("creativity+", "философский вопрос"),
        ("empathy++", "благодарность"),
        ("humility++", "ошибка / проблема"),
        ("curiosity+", "длинный вопрос"),
    ]

    return result


@router.get("/deltas")
async def get_persona_deltas():
    from core.impulse.deltas import _IMPULSE_DELTAS

    return {
        "emotion": {
            "deltas": {
                "new_knowledge": {"pleasure": 0.1, "curiosity": 0.2, "confidence": 0.05},
                "contradiction": {"pleasure": -0.1, "confidence": -0.2, "arousal": 0.1},
                "user_praise": {"pleasure": 0.3, "social_connection": 0.2, "confidence": 0.1},
                "user_criticism": {"pleasure": -0.2, "social_connection": -0.1, "confidence": -0.1},
                "fallback": {"pleasure": -0.3, "anxiety": 0.2},
                "self_reflection": {"curiosity": 0.1, "arousal": 0.05},
            },
            "note": "определено в emotion.pad_model.PADModel.apply_event. intensity = base * significance.",
        },
        "impulse": {
            "deltas": {k: v for k, v in sorted(_IMPULSE_DELTAS.items())},
            "note": "delta умножается на significance. 'current' = метка с макс. весом.",
        },
        "persona_system": {
            "deltas": _build_persona_system_deltas(),
            "note": "Триггеры и текущие значения черт. Эволюция через evolve_from_dialog (анализ тональности и ключевых слов).",
        },
        "persona_user_style": {
            "deltas": {
                "factual_question": [["technical_level", 0.01]],
                "philosophical_question": [["formality", -0.01]],
                "positive_feedback": [["verbosity", 0.01]],
            },
            "note": "adjust_style клипирует в ±0.1. delta умножается на significance. Определено в PersonaEvolutionPhase.execute.",
        },
    }
