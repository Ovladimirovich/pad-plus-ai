import logging
from typing import Any, Dict

logger = logging.getLogger("padplus.persona.listener")

_listener_registered = False

_PERSONA_TRAIT_DELTAS = {
    "contradiction": {"skepticism": 0.08, "humility": 0.08},
    "praise":        {"empathy": 0.10, "openness": 0.08},
    "criticism":     {"humility": 0.10, "skepticism": 0.05},
    "exploration":   {"curiosity": 0.10, "creativity": 0.08},
    "error_recovery": {"caution": 0.10, "humility": 0.08},
    "repetition":    {"curiosity": -0.03},
    "new_knowledge": {"curiosity": 0.03},
}

_PERSONA_STYLE_DELTAS = {
    "contradiction": {"technical_level": 0.03},
    "praise":        {"verbosity": 0.03, "formality": -0.02},
    "criticism":     {"technical_level": 0.02},
    "exploration":   {"formality": -0.03},
    "error_recovery": {"technical_level": -0.02},
    "repetition":    {"verbosity": -0.02},
    "new_knowledge": {},
}


async def _on_experience_captured(data: Dict[str, Any]) -> None:
    try:
        interaction_type = data.get("interaction_type", "new_knowledge")
        significance = data.get("significance", 0.0)

        if significance < 0.1:
            return

        trait_deltas = _PERSONA_TRAIT_DELTAS.get(interaction_type, {})
        style_deltas = _PERSONA_STYLE_DELTAS.get(interaction_type, {})

        if not trait_deltas and not style_deltas:
            return

        user_message = data.get("user_message", "")
        ai_response = data.get("ai_response", "")

        from memory.persona import get_persona
        persona = get_persona()
        for trait, delta in trait_deltas.items():
            persona.adjust_trait(trait, delta * significance)

        from memory.user_persona import get_user_persona_manager
        user_id = data.get("user_id")
        if user_id:
            pm = get_user_persona_manager()
            up = pm.get_persona(user_id)
            for style, delta in style_deltas.items():
                up.adjust_style(style, delta * significance, reason=interaction_type)
            pm.save_persona(up)

    except Exception as e:
        logger.warning("Persona listener error: %s", e)


def setup_persona_listener() -> None:
    global _listener_registered
    if _listener_registered:
        return
    try:
        from core.events import get_events
        events = get_events()
        events.experience_captured.subscribe(_on_experience_captured)
        _listener_registered = True
        logger.info("Persona listener registered on experience_captured")
    except Exception as e:
        logger.warning("Failed to setup persona listener: %s", e)
