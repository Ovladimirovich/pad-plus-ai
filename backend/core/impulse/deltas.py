"""
Единый источник дельт импульса.

apply_deltas — единственная функция мутации весов (writer logic).
Кто вызывает apply_deltas, тот и writer (V1: ImpulseUpdatePhase).
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .core import ImpulseCore

logger = logging.getLogger("padplus.impulse.deltas")

# Дельта-изменения весов (умножаются на significance)
#   - criticism/contradiction сильнее — improve может догнать understand
#   - praise усиливает текущий primary
#   - error_recovery → protect
IMPULSE_DELTAS: dict[str, dict[str, float]] = {
    "contradiction": {"current": -0.20, "improve": 0.15},
    "criticism": {"current": -0.25, "improve": 0.20},
    "praise": {"current": 0.20},
    "exploration": {"understand": 0.15},
    "error_recovery": {"protect": 0.20, "improve": 0.10},
    "repetition": {"current": -0.08},
    "new_knowledge": {},
}

# backward-compat alias
_IMPULSE_DELTAS = IMPULSE_DELTAS

MIN_SIGNIFICANCE = 0.2


def apply_deltas(
    core: ImpulseCore,
    interaction_type: str,
    significance: float,
) -> bool:
    """
    Мутирует core.dimensions по таблице IMPULSE_DELTAS.

    Returns:
        True если веса изменились, False если no-op.
    """
    if significance < MIN_SIGNIFICANCE:
        return False

    deltas = IMPULSE_DELTAS.get(interaction_type)
    if not deltas:
        return False

    current_label = core.get_primary_label()
    dims = {d.label: d for d in core.dimensions}
    changed = False

    for target, base_delta in deltas.items():
        delta = base_delta * significance
        if target == "current":
            if current_label in dims:
                old = dims[current_label].weight
                dims[current_label].weight = max(0.0, old + delta)
                if dims[current_label].weight != old:
                    changed = True
        elif target in dims:
            old = dims[target].weight
            dims[target].weight = max(0.0, min(1.0, old + delta))
            if dims[target].weight != old:
                changed = True

    if changed:
        from datetime import datetime

        core.modified_at = datetime.now().isoformat()

    return changed
