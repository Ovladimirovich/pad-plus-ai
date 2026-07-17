"""
DTO для impulse (не source of truth).

Каноническое состояние: ImpulseCore.to_dict() v2.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class BiasBlock:
    """Готовый блок для инъекции + метаданные."""

    text: str
    primary: str = "unknown"
    active: list[dict[str, Any]] = field(default_factory=list)

    @property
    def is_empty(self) -> bool:
        return not self.text

    def to_dict(self) -> dict[str, Any]:
        return {
            "text": self.text,
            "primary": self.primary,
            "active": self.active,
            "empty": self.is_empty,
        }
