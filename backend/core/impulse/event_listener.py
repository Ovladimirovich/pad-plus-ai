"""
Impulse event listener.

V1 note (single writer):
  Phase ImpulseUpdatePhase владеет мутацией весов.
  Listener подписан для observability / future multi-process, но
  НЕ применяет deltas, пока env IMPULSE_LISTENER_WRITE != true.

  По умолчанию write отключён (IMPULSE_LISTENER_WRITE=false).
  Для legacy-тестов dual-path можно включить явно.
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict

logger = logging.getLogger("padplus.impulse.listener")

_listener_registered = False

# V1 default: phase owns writes. Set true only for legacy/debug.
_LISTENER_WRITE = os.getenv("IMPULSE_LISTENER_WRITE", "false").lower() in (
    "1",
    "true",
    "yes",
)


async def _on_experience_captured(data: Dict[str, Any]) -> None:
    """
    Handler experience_captured.

    V1: no-op write (single writer = ImpulseUpdatePhase).
    Legacy write path: IMPULSE_LISTENER_WRITE=true.
    """
    try:
        if not _LISTENER_WRITE:
            logger.debug(
                "impulse listener: write skipped (phase owns updates); type=%s sig=%s",
                data.get("interaction_type"),
                data.get("significance"),
            )
            return

        interaction_type = data.get("interaction_type", "new_knowledge")
        significance = float(data.get("significance", 0.0) or 0.0)

        from .deltas import apply_deltas
        from .manager import get_impulse_core, get_manager

        core = get_impulse_core()
        changed = apply_deltas(core, interaction_type, significance)
        if changed:
            get_manager().save(core)
            logger.info(
                "impulse listener applied deltas: type=%s sig=%.2f",
                interaction_type,
                significance,
            )
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
        mode = "write" if _LISTENER_WRITE else "observe-only"
        logger.info(
            "Impulse listener registered on experience_captured (mode=%s)", mode
        )
    except Exception as e:
        logger.warning("Failed to setup impulse listener: %s", e)
