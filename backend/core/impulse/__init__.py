"""
Impulse Core — public API.

Использование:
    from core.impulse import get_impulse_core, set_impulse, get_bias_block
"""

from .core import (
    IMPULSE_LABELS,
    Impulse,
    ImpulseCore,
    ImpulseDimension,
    ImpulseState,
    default_dimensions,
)
from .deltas import IMPULSE_DELTAS, MIN_SIGNIFICANCE, apply_deltas
from .event_listener import setup_impulse_listener
from .manager import (
    ImpulseManager,
    get_impulse_core,
    get_manager,
    is_impulse_initialized,
    pop_impulse,
    push_impulse,
    reset_manager,
    set_impulse,
    set_impulse_by_question,
    start_impulse,
)
from .models import BiasBlock
from .signals import ensure_experience_in_context, infer_experience

__all__ = [
    "Impulse",
    "ImpulseDimension",
    "ImpulseState",
    "ImpulseCore",
    "ImpulseManager",
    "BiasBlock",
    "IMPULSE_LABELS",
    "IMPULSE_DELTAS",
    "MIN_SIGNIFICANCE",
    "default_dimensions",
    "apply_deltas",
    "get_manager",
    "get_impulse_core",
    "set_impulse",
    "set_impulse_by_question",
    "push_impulse",
    "pop_impulse",
    "start_impulse",
    "is_impulse_initialized",
    "reset_manager",
    "setup_impulse_listener",
    "get_bias_block",
    "infer_experience",
    "ensure_experience_in_context",
]


def get_bias_block(active_threshold: float = 0.3) -> str:
    """Удобный accessor: bias block текущего ядра."""
    return get_impulse_core().get_bias_block(active_threshold=active_threshold)
