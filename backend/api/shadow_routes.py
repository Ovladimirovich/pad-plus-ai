"""
Shadow Routes — API для мониторинга и аналитики Memory Decision Layer в режиме Shadow Mode (ADR-0010).
"""

import logging
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException

logger = logging.getLogger("padplus.api.shadow")

router = APIRouter(prefix="/api/v1/memory/shadow", tags=["Shadow Memory Analytics"])

# In-memory буфер для сбора shadow-статистики в рантайме (с лимитом на последние 1000 записей)
_SHADOW_STATS_BUFFER: List[Dict[str, Any]] = []
_MAX_BUFFER_SIZE = 1000


def record_shadow_event(query: str, stats: Dict[str, int], latency_ms: float) -> None:
    """Записывает событие shadow-оценки в рантайм-буфер."""
    global _SHADOW_STATS_BUFFER
    event = {
        "query": query,
        "stats": stats,
        "latency_ms": latency_ms
    }
    _SHADOW_STATS_BUFFER.append(event)
    if len(_SHADOW_STATS_BUFFER) > _MAX_BUFFER_SIZE:
        _SHADOW_STATS_BUFFER.pop(0)


@router.get("/stats")
async def get_shadow_stats() -> Dict[str, Any]:
    """
    Возвращает агрегированную статистику работы Memory Decision Layer в режиме Shadow Mode:
    - Общее количество запросов
    - Суммарное распределение вердиктов (KEEP, OUTDATED, DISCARD, CONFLICT, UNCERTAIN)
    - Среднюю латентность
    - Abstention Rate (долю неопределённых решений)
    """
    total_events = len(_SHADOW_STATS_BUFFER)
    if total_events == 0:
        return {
            "total_queries": 0,
            "verdicts_aggregate": {"keep": 0, "outdated": 0, "discard": 0, "conflict": 0, "uncertain": 0},
            "abstention_rate": 0.0,
            "avg_latency_ms": 0.0,
            "recent_events": []
        }

    agg = {"keep": 0, "outdated": 0, "discard": 0, "conflict": 0, "uncertain": 0}
    total_latency = 0.0
    total_candidates = 0

    for ev in _SHADOW_STATS_BUFFER:
        total_latency += ev.get("latency_ms", 0.0)
        st = ev.get("stats", {})
        for k in agg:
            agg[k] += st.get(k, 0)
            total_candidates += st.get(k, 0)

    abstention_rate = (agg["uncertain"] / total_candidates * 100) if total_candidates > 0 else 0.0
    avg_latency = total_latency / total_events

    return {
        "total_queries": total_events,
        "verdicts_aggregate": agg,
        "abstention_rate": round(abstention_rate, 2),
        "avg_latency_ms": round(avg_latency, 3),
        "recent_events": _SHADOW_STATS_BUFFER[-10:]  # последние 10 событий
    }
