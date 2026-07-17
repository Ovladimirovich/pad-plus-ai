"""
Импульс (seed) — CLI и compat re-export.

Каноническая реализация: backend/core/impulse/
Этот модуль сохраняет импорт `from scripts.impulse import ...` для тестов и CLI.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# backend/ на path (для `from core.impulse ...`)
_ROOT = Path(__file__).resolve().parent.parent
_BACKEND = _ROOT / "backend"
for _p in (str(_ROOT), str(_BACKEND)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from core.impulse.core import (  # noqa: E402
    IMPULSE_LABELS,
    Impulse,
    ImpulseCore,
    ImpulseDimension,
    ImpulseState,
    default_dimensions,
)
from core.impulse.deltas import (  # noqa: E402
    IMPULSE_DELTAS,
    MIN_SIGNIFICANCE,
    apply_deltas,
)
from core.impulse.manager import (  # noqa: E402
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

__all__ = [
    "Impulse",
    "ImpulseDimension",
    "ImpulseState",
    "ImpulseCore",
    "ImpulseManager",
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
]


if __name__ == "__main__":
    result = start_impulse()
    print("\n📄 Импульс сохранён:")
    print(json.dumps(result, ensure_ascii=False, indent=2))
