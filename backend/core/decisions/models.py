"""
Decision Log — структурированное логирование решений системы.

Вместо текстовых логов «что произошло» фиксируем «почему»:
- какие факторы повлияли на решение
- какие альтернативы рассматривались
- какой вариант выбран и с какой уверенностью
- человекочитаемая причина

Хранилище: data/decisions.db (SQLite)
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Dict, List, Optional
import json
import uuid


@dataclass
class DecisionRecord:
    id: str
    timestamp: float
    component: str
    decision_type: str
    selected: str
    confidence: float
    reason: str
    input_factors: Dict[str, Any] = field(default_factory=dict)
    candidates: List[Dict[str, Any]] = field(default_factory=list)
    trace_id: Optional[str] = None
    session_id: Optional[str] = None
    meta: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "DecisionRecord":
        return cls(
            id=d.get("id", uuid.uuid4().hex[:12]),
            timestamp=d.get("timestamp", datetime.now().timestamp()),
            component=d.get("component", "unknown"),
            decision_type=d.get("decision_type", "unknown"),
            selected=d.get("selected", ""),
            confidence=d.get("confidence", 0.0),
            reason=d.get("reason", ""),
            input_factors=d.get("input_factors", {}),
            candidates=d.get("candidates", []),
            trace_id=d.get("trace_id"),
            session_id=d.get("session_id"),
            meta=d.get("meta", {}),
        )
