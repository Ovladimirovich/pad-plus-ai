from fastapi import APIRouter
from typing import Dict, Any, List
import logging

logger = logging.getLogger("padplus.admin_routes")

router = APIRouter(prefix="/api/v1/admin", tags=["Admin"])


@router.get("/emotion")
async def get_emotion_stats():
    result: Dict[str, Any] = {}
    try:
        from emotion.emotion_learner import get_emotion_learner
        learner = get_emotion_learner()
        result["learner"] = learner.get_stats()
    except Exception as e:
        result["learner"] = {"status": "unavailable", "error": str(e)[:100]}

    try:
        from emotion.pad_model import get_pad_model
        pad = get_pad_model()
        result["pad"] = {
            "pleasure": pad.pleasure,
            "arousal": pad.arousal,
            "dominance": pad.dominance,
        }
    except Exception as e:
        result["pad"] = {"status": "unavailable", "error": str(e)[:100]}

    return result


@router.get("/sync")
async def get_sync_status():
    try:
        from core.pipeline.cross_memory_sync import get_cross_memory_sync
        sync = get_cross_memory_sync()
        return {"sync_count": sync._sync_count}
    except Exception as e:
        return {"status": "unavailable", "error": str(e)[:100]}


@router.post("/sync/trigger")
async def trigger_sync():
    try:
        from core.pipeline.cross_memory_sync import get_cross_memory_sync
        sync = get_cross_memory_sync()
        result = sync.sync_all()
        total = sum(len(v) for v in result.values())
        return {
            "success": True,
            "total_insights": total,
            "details": {k: len(v) for k, v in result.items()},
        }
    except Exception as e:
        return {"success": False, "error": str(e)[:200]}


@router.get("/health")
async def get_cognitive_health():
    """Когнитивное здоровье системы: общий score + рекомендации"""
    result: Dict[str, Any] = {}
    suggestions: List[str] = []

    try:
        from memory.consolidation import get_consolidator
        cons = get_consolidator()
        stats = cons.get_consolidation_stats()
        result["consolidation"] = stats
        if stats.get("total_consolidations", 0) == 0:
            suggestions.append("Запустите консолидацию памяти: POST /api/v1/memory/consolidation/trigger")
        elif stats.get("success_rate", 0) < 0.5:
            suggestions.append("Низкий успех консолидации — проверьте целостность memory слоёв")
    except Exception as e:
        result["consolidation"] = {"error": str(e)[:100]}

    try:
        from memory import get_rag
        rag = get_rag()
        rag_stats = rag.get_stats() if hasattr(rag, "get_stats") else {}
        total_dialogs = rag_stats.get("total_dialogs", 0)
        result["rag"] = {"total_dialogs": total_dialogs}
        if total_dialogs == 0:
            suggestions.append("RAG пуст — добавьте диалоги через чат")
    except Exception as e:
        result["rag"] = {"error": str(e)[:100]}

    try:
        from emotion.emotion_learner import get_emotion_learner
        learner = get_emotion_learner()
        learner_stats = learner.get_stats()
        result["emotion_learner"] = learner_stats
        if learner_stats.get("total_dialogs_analyzed", 0) == 0:
            suggestions.append("EmotionLearner не анализировал диалоги")
    except Exception as e:
        result["emotion_learner"] = {"error": str(e)[:100]}

    try:
        from emotion.pad_model import get_pad_model
        pad = get_pad_model()
        pad_state = {
            "pleasure": pad.pleasure,
            "arousal": pad.arousal,
            "dominance": pad.dominance,
        }
        result["pad"] = pad_state
    except Exception as e:
        result["pad"] = {"error": str(e)[:100]}

    try:
        from core.pipeline.cross_memory_sync import get_cross_memory_sync
        r = get_cross_memory_sync()
        result["cross_memory_sync"] = {"sync_count": r._sync_count}
    except Exception as e:
        result["cross_memory_sync"] = {"error": str(e)[:100]}

    health_score = _compute_health_score(result)
    result["health_score"] = health_score
    result["suggestions"] = suggestions
    return result


def _compute_health_score(data: Dict[str, Any]) -> float:
    score = 0.0
    metrics = 0

    cons = data.get("consolidation", {})
    if "total_consolidations" in cons:
        score += 0.3 if cons["total_consolidations"] > 0 else 0
        metrics += 1

    rag = data.get("rag", {})
    if "total_dialogs" in rag:
        score += min(rag["total_dialogs"] / 10, 0.3)
        metrics += 1

    el = data.get("emotion_learner", {})
    if "total_dialogs_analyzed" in el:
        score += 0.2 if el["total_dialogs_analyzed"] > 0 else 0
        metrics += 1

    pad = data.get("pad", {})
    if "pleasure" in pad:
        score += 0.2
        metrics += 1

    if metrics == 0:
        return 0.0
    return round(score / metrics, 2)
