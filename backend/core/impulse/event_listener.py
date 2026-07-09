import logging
from typing import Any, Dict

logger = logging.getLogger("padplus.impulse.listener")

_listener_registered = False

_IMPULSE_DELTAS = {
    "contradiction": {"current": -0.20, "improve": 0.15},
    "criticism":    {"current": -0.25, "improve": 0.20},
    "praise":       {"current":  0.20},
    "exploration":  {"understand": 0.15},
    "error_recovery": {"protect": 0.20, "improve": 0.10},
    "repetition":   {"current": -0.08},
    "new_knowledge": {},
}


async def _on_experience_captured(data: Dict[str, Any]) -> None:
    try:
        interaction_type = data.get("interaction_type", "new_knowledge")
        significance = data.get("significance", 0.0)

        if significance < 0.2:
            return

        deltas = _IMPULSE_DELTAS.get(interaction_type, {})
        if not deltas:
            return

        from scripts.impulse import get_impulse_core, get_manager
        core = get_impulse_core()
        current_label = core.get_primary_label()
        dims = {d.label: d for d in core.dimensions}

        for target, base_delta in deltas.items():
            if target == "current":
                if current_label in dims:
                    dims[current_label].weight = max(0.0, dims[current_label].weight + base_delta * significance)
            elif target in dims:
                dims[target].weight = max(0.0, min(1.0, dims[target].weight + base_delta * significance))

        get_manager().save(core)

    except Exception as e:
        logger.warning("Impulse listener error: %s", e)


def setup_impulse_listener() -> None:
    global _listener_registered
    if _listener_registered:
        return
    try:
        from core.events import get_events
        events = get_events()
        events.experience_captured.subscribe(_on_experience_captured)
        _listener_registered = True
        logger.info("Impulse listener registered on experience_captured")
    except Exception as e:
        logger.warning("Failed to setup impulse listener: %s", e)
