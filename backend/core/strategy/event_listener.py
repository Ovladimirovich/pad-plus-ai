import logging
from typing import Any, Dict

from core.xray.meta_learner import get_meta_learner

logger = logging.getLogger("padplus.strategy.listener")

_listener_registered = False


async def _on_dialog_completed(data: Dict[str, Any]) -> None:
    try:
        strategy = data.get("strategy", "simple")
        result_dict = data.get("result", {})

        meta = get_meta_learner()
        meta.record_outcome(strategy, result_dict)

        should_change = meta.should_adjust_strategy(strategy)
        if should_change and should_change != strategy:
            try:
                from core.events import get_events
                await get_events().strategy_changed.publish({
                    "previous_strategy": strategy,
                    "recommended_strategy": should_change,
                    "reason": f"success_rate below threshold, recommend {should_change}",
                })
            except Exception:
                pass

    except Exception as e:
        logger.warning("Strategy listener error: %s", e)


def setup_strategy_listener() -> None:
    global _listener_registered
    if _listener_registered:
        return
    try:
        from core.events import get_events
        events = get_events()
        events.dialog_completed.subscribe(_on_dialog_completed)
        _listener_registered = True
        logger.info("Strategy listener registered on dialog_completed")
    except Exception as e:
        logger.warning("Failed to setup strategy listener: %s", e)
