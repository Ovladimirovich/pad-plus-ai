import logging
from typing import Any, Dict
import uuid

from .experience import capture_experience

logger = logging.getLogger("padplus.experience.listener")

_listener_registered = False


async def _on_dialog_completed(data: Dict[str, Any]) -> None:
    try:
        user_message = data.get("user_message", "")
        result_dict = data.get("result", {})

        dialog_id = data.get("session_id") or str(uuid.uuid4())
        ai_response = result_dict.get("answer", "") if isinstance(result_dict, dict) else ""
        strategy = data.get("strategy", "simple")
        success = data.get("success", False)

        truth = result_dict.get("truth", {}) if isinstance(result_dict, dict) else {}
        truth_confidence = truth.get("confidence")

        meta = result_dict.get("meta", {}) if isinstance(result_dict, dict) else {}
        intent = meta.get("intent", "")

        strategy_success = 1.0 if success else 0.0

        record = capture_experience(
            dialog_id=dialog_id,
            user_message=user_message,
            ai_response=ai_response,
            truth_confidence=truth_confidence,
            intent=intent,
            strategy=strategy,
            strategy_success=strategy_success,
            lessons=[],
        )

        if record:
            from core.events import get_events
            await get_events().experience_captured.publish({
                "dialog_id": dialog_id,
                "user_message": user_message,
                "ai_response": ai_response,
                "user_id": data.get("user_id"),
                "interaction_type": record.interaction_type.value,
                "significance": record.significance,
                "strategy_success": strategy_success,
            })
            logger.debug("Experience captured: %s sig=%.3f", record.interaction_type.value, record.significance)

    except Exception as e:
        logger.warning("Experience listener error: %s", e)


def setup_experience_listener() -> None:
    global _listener_registered
    if _listener_registered:
        return
    try:
        from core.events import get_events
        events = get_events()
        events.dialog_completed.subscribe(_on_dialog_completed)
        _listener_registered = True
        logger.info("Experience listener registered on dialog_completed")
    except Exception as e:
        logger.warning("Failed to setup experience listener: %s", e)
