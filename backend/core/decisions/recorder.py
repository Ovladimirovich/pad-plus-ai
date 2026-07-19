"""
DecisionRecorder — сервис для записи решений системы.

Используется в точках принятия решений (выбор провайдера, стратегии и т.д.):
    recorder.record(
        component="provider_selector",
        decision_type="provider_selection",
        selected="gigachat",
        confidence=0.85,
        reason="Высокая важность запроса → качественный провайдер",
        input_factors={"message_length": 120, "intent": "knowledge"},
        candidates=[
            {"name": "gigachat", "score": 0.85},
            {"name": "openrouter", "score": 0.6},
        ],
        trace_id=...,
        session_id=...,
    )
"""

import logging
import time
import uuid
from typing import Any, Dict, List, Optional

from backend.core.decisions.models import DecisionRecord
from backend.core.decisions.store import get_decision_store

logger = logging.getLogger("padplus.decisions.recorder")


class DecisionRecorder:
    def __init__(self):
        self._store = get_decision_store()

    def record(
        self,
        component: str,
        decision_type: str,
        selected: str,
        confidence: float = 0.0,
        reason: str = "",
        input_factors: Optional[Dict[str, Any]] = None,
        candidates: Optional[List[Dict[str, Any]]] = None,
        trace_id: Optional[str] = None,
        session_id: Optional[str] = None,
        meta: Optional[Dict[str, Any]] = None,
    ) -> DecisionRecord:
        record = DecisionRecord(
            id=uuid.uuid4().hex[:12],
            timestamp=time.time(),
            component=component,
            decision_type=decision_type,
            selected=selected,
            confidence=confidence,
            reason=reason,
            input_factors=input_factors or {},
            candidates=candidates or [],
            trace_id=trace_id,
            session_id=session_id,
            meta=meta or {},
        )
        try:
            self._store.save(record)
        except Exception as e:
            logger.warning("Failed to save decision record: %s", e)
        return record

    def get(self, decision_id: str):
        return self._store.get(decision_id)

    def query(self, **kwargs):
        return self._store.query(**kwargs)

    def stats(self):
        return self._store.stats()


_recorder: Optional[DecisionRecorder] = None


def get_decision_recorder() -> DecisionRecorder:
    global _recorder
    if _recorder is None:
        _recorder = DecisionRecorder()
    return _recorder
