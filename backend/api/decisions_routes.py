"""Decision Log API — просмотр решений системы."""

import logging
from typing import Optional

from fastapi import APIRouter, Query

logger = logging.getLogger("padplus.api.decisions")

router = APIRouter(prefix="/api/v1/decisions", tags=["decisions"])


@router.get("")
async def list_decisions(
    component: Optional[str] = Query(None),
    decision_type: Optional[str] = Query(None),
    session_id: Optional[str] = Query(None),
    trace_id: Optional[str] = Query(None),
    since: Optional[float] = Query(None),
    limit: int = Query(100, le=500),
):
    from backend.core.decisions import get_decision_recorder
    rec = get_decision_recorder()
    records = rec.query(
        component=component,
        decision_type=decision_type,
        session_id=session_id,
        trace_id=trace_id,
        since=since,
        limit=limit,
    )
    return {"decisions": [r.to_dict() for r in records], "total": len(records)}


@router.get("/stats")
async def decisions_stats():
    from backend.core.decisions import get_decision_recorder
    rec = get_decision_recorder()
    return rec.stats()


@router.get("/{decision_id}")
async def get_decision(decision_id: str):
    from backend.core.decisions import get_decision_recorder
    rec = get_decision_recorder()
    record = rec.get(decision_id)
    if not record:
        from fastapi import HTTPException
        raise HTTPException(404, f"Decision '{decision_id}' not found")
    return record.to_dict()


@router.get("/session/{session_id}")
async def session_decisions(session_id: str, limit: int = Query(100, le=500)):
    from backend.core.decisions import get_decision_recorder
    rec = get_decision_recorder()
    records = rec.query(session_id=session_id, limit=limit)
    return {"decisions": [r.to_dict() for r in records], "total": len(records)}
