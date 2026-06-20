import logging
from typing import Any, Dict

from emotion.pad_model import get_pad_model

logger = logging.getLogger("padplus.emotion.listener")

_listener_registered = False

_INTERACTION_TO_PAD_EVENT = {
    "new_knowledge": "new_knowledge",
    "contradiction": "contradiction",
    "praise": "user_praise",
    "criticism": "user_criticism",
    "exploration": "new_knowledge",
    "error_recovery": "fallback",
    "repetition": "self_reflection",
}


async def _on_experience_captured(data: Dict[str, Any]) -> None:
    try:
        interaction_type = data.get("interaction_type", "new_knowledge")
        significance = data.get("significance", 0.3)

        pad_event = _INTERACTION_TO_PAD_EVENT.get(interaction_type, "self_reflection")
        pad = get_pad_model()
        pad.apply_event(pad_event, intensity=significance)

        try:
            from core.event_bus import get_event_bus, EventType
            bus = get_event_bus()
            bus.emit(EventType.EMOTION_CHANGED, {
                "state": pad.get_state().to_dict(),
                "trigger": pad_event,
                "interaction_type": interaction_type,
            })
        except Exception:
            pass

    except Exception as e:
        logger.warning("Emotion listener error: %s", e)


def setup_emotion_listener() -> None:
    global _listener_registered
    if _listener_registered:
        return
    try:
        from core.events import get_events
        events = get_events()
        events.experience_captured.subscribe(_on_experience_captured)
        _listener_registered = True
        logger.info("Emotion listener registered on experience_captured")
    except Exception as e:
        logger.warning("Failed to setup emotion listener: %s", e)
