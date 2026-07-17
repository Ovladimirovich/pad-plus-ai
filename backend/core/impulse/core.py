"""
Impulse Core — многомерное ядро когнитивной направленности.

4 измерения: understand / improve / protect / create.
Канонический wire format: ImpulseCore.to_dict() version 2.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Impulse:
    """Импульс сознания — точка зарождения (legacy single-question)."""

    question: str = "Что я могу понять?"
    layer: str = "roots"
    depth: int = 0
    source: str = "impulse"
    immutable: bool = True
    created_at: Optional[str] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()

    def to_dict(self) -> dict:
        return {
            "question": self.question,
            "layer": self.layer,
            "depth": self.depth,
            "source": self.source,
            "immutable": self.immutable,
            "created_at": self.created_at,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


@dataclass
class ImpulseDimension:
    label: str
    question: str
    weight: float = 0.0

    def to_dict(self) -> dict:
        return {"label": self.label, "question": self.question, "weight": self.weight}

    @staticmethod
    def from_dict(d: dict) -> ImpulseDimension:
        return ImpulseDimension(
            label=d["label"],
            question=d.get("question", "?"),
            weight=float(d.get("weight", 0.0)),
        )

    def __eq__(self, other):
        if not isinstance(other, ImpulseDimension):
            return NotImplemented
        return (
            self.label == other.label
            and self.question == other.question
            and self.weight == other.weight
        )

    def __hash__(self):
        return hash((self.label, self.question))


_QUESTIONS = {
    "understand": "Что я могу понять?",
    "improve": "Что я могу улучшить?",
    "protect": "Что я могу защитить?",
    "create": "Что я могу создать?",
}

IMPULSE_LABELS = _QUESTIONS

_HUMAN_LABELS = {
    "understand": "понять",
    "improve": "улучшить",
    "protect": "защитить",
    "create": "создать",
}

_DOMINANT_HINTS = {
    "understand": "фокус на понимание и анализ",
    "improve": "фокус на улучшение и оптимизацию",
    "protect": "фокус на защиту и устойчивость",
    "create": "фокус на создание и генерацию идей",
}


def default_dimensions() -> list[ImpulseDimension]:
    return [ImpulseDimension(label=k, question=v) for k, v in _QUESTIONS.items()]


@dataclass
class ImpulseState:
    """DTO-снимок (не source of truth; канон — ImpulseCore.to_dict())."""

    question: str = ""
    label: str = ""
    dimensions: list[ImpulseDimension] = field(default_factory=list)
    stack: list[dict] = field(default_factory=list)
    created_at: str = ""
    modified_at: str = ""


class ImpulseCore:
    def __init__(self, dimensions: list[ImpulseDimension] | None = None):
        self.dimensions = dimensions or default_dimensions()
        self._stack: list[dict] = []
        self.created_at = datetime.now().isoformat()
        self.modified_at = self.created_at

    def get_primary_label(self) -> str:
        if not self.dimensions:
            return "unknown"
        best = max(self.dimensions, key=lambda d: d.weight)
        return best.label if best.weight > 0 else "unknown"

    def get_primary_question(self) -> str:
        label = self.get_primary_label()
        if label == "unknown":
            return "познать"
        return _QUESTIONS.get(label, "познать")

    def get_prompt_line(self) -> str:
        active = [d for d in self.dimensions if d.weight > 0]
        if not active:
            return "познать"
        if len(active) == 1:
            q = active[0].question.lower()
            return q.replace("что я могу ", "").replace("?", "").strip()
        parts = []
        for d in active:
            q = d.question.lower().replace("что я могу ", "").replace("?", "").strip()
            parts.append(q)
        return " и ".join(parts)

    def get_bias_block(self, active_threshold: float = 0.3) -> str:
        """
        Структурированный блок для инъекции в system prompt.
        Пустая строка, если primary == unknown (не шумим в prompt).
        """
        primary = self.get_primary_label()
        if primary == "unknown":
            return ""

        active = sorted(
            [d for d in self.dimensions if d.weight >= active_threshold],
            key=lambda d: d.weight,
            reverse=True,
        )
        if not active:
            active = [max(self.dimensions, key=lambda d: d.weight)]

        human_parts = [_HUMAN_LABELS.get(d.label, d.label) for d in active[:3]]
        main_impulse = " и ".join(human_parts)
        active_line = ", ".join(f"{d.label} ({d.weight:.2f})" for d in active[:4])
        hint = _DOMINANT_HINTS.get(primary, "смещённая когнитивная направленность")

        block = (
            "Твоя когнитивная направленность:\n"
            f"- Основной импульс: {main_impulse}\n"
            f"- Активные направления: {active_line}\n"
            f"- Доминанта: {primary} → {hint}"
        )
        if len(block) > 400:
            block = block[:397] + "..."
        return block

    def set_from_labels(self, weights: dict[str, float]):
        for dim in self.dimensions:
            dim.weight = float(weights.get(dim.label, 0.0))
        self.modified_at = datetime.now().isoformat()

    def set_from_question(self, question: str):
        q_lower = question.lower()
        best_label = None
        best_score = 0
        for label, q in _QUESTIONS.items():
            score = 0
            if q_lower == q.lower():
                score = 10
            else:
                for word in q_lower.split():
                    if word in q.lower():
                        score += 1
            if score > best_score:
                best_score = score
                best_label = label
        weights = {label: 1.0 if label == best_label else 0.0 for label in _QUESTIONS}
        if best_label is None:
            weights["understand"] = 1.0
        self.set_from_labels(weights)

    def get_active_questions(self, threshold: float = 0.5) -> list[ImpulseDimension]:
        return [d for d in self.dimensions if d.weight >= threshold]

    def push(self):
        self._stack.append([d.to_dict() for d in self.dimensions])

    def pop(self) -> bool:
        if not self._stack:
            return False
        state = self._stack.pop()
        self.dimensions = [ImpulseDimension.from_dict(d) for d in state]
        self.modified_at = datetime.now().isoformat()
        return True

    def stack_depth(self) -> int:
        return len(self._stack)

    def to_dict(self) -> dict:
        return {
            "version": 2,
            "scope": "system",
            "primary": {
                "question": self.get_primary_question(),
                "label": self.get_primary_label(),
                "dimensions": [d.to_dict() for d in self.dimensions],
            },
            "stack": list(self._stack),
            "created_at": self.created_at,
            "modified_at": self.modified_at,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    @staticmethod
    def from_dict(data: dict) -> ImpulseCore:
        if not data:
            return ImpulseCore()

        # V1 compatibility
        if "version" not in data:
            dims = default_dimensions()
            question = data.get("question", "")
            if question:
                for d in dims:
                    if d.question == question:
                        d.weight = 1.0
            return ImpulseCore(dimensions=dims)

        # V2
        primary = data.get("primary", {})
        dims = [ImpulseDimension.from_dict(d) for d in primary.get("dimensions", [])]
        core = ImpulseCore(dimensions=dims if dims else None)
        core._stack = list(data.get("stack", []))
        core.created_at = data.get("created_at", core.created_at)
        core.modified_at = data.get("modified_at", core.modified_at)
        return core
