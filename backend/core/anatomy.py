"""
Anatomy — живая анатомия когнитивной архитектуры PAD+ AI.

Агрегирует live-статус всех когнитивных модулей в единое дерево:
Brain → Memory, Reasoning, Identity, Emotion, Reflection, Dreams,
Truth, Safety, Healer, Research, X-Ray.

Каждый узел содержит: status, metrics, last_activity, children.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger("padplus.anatomy")

# Маппинг модулей анатомии → компоненты Decision Log (для кросс-ссылок)
MODULE_TO_COMPONENT = {
    "provider_selector": "provider_selector",
    "strategy_selector": "strategy_selector",
    "reasoning": "strategy_selector",
    "reflection": "reflection",
    "dreams": "reflection",
    "healer": "healing",
    "research": "provider_selector",
    "memory": None,
    "identity": None,
    "emotion": None,
    "truth": None,
    "safety": None,
    "xray": None,
}


def _safe(fn, default=None):
    """Безопасно вызывает fn, возвращает default при ошибке."""
    try:
        return fn()
    except Exception as e:
        logger.debug("anatomy._safe failed: %s", e)
        return default


def get_module_status() -> Dict[str, Any]:
    """Возвращает статус всех модулей архитектуры."""

    # ─── Memory ───
    memory_children = {}

    episodic = _safe(lambda: __import__("backend.memory.episodic", fromlist=["get_episodic_memory"]).get_episodic_memory().get_stats())
    if episodic:
        memory_children["episodic"] = {
            "label": "Episodic", "status": "active",
            "metrics": {"episodes": episodic.get("total_episodes", 0)},
        }

    semantic = _safe(lambda: __import__("backend.memory.semantic", fromlist=["get_semantic_memory"]).get_semantic_memory().get_stats())
    if semantic:
        memory_children["semantic"] = {
            "label": "Semantic", "status": "active",
            "metrics": {"knowledge": semantic.get("total_knowledge", 0), "avg_confidence": semantic.get("avg_confidence", 0)},
        }

    rag = _safe(lambda: __import__("backend.memory.rag", fromlist=["get_rag"]).get_rag().get_stats())
    if rag:
        memory_children["rag"] = {
            "label": "RAG", "status": "active",
            "metrics": {"dialogs": rag.get("total_dialogs", 0)},
        }

    persona = _safe(lambda: __import__("backend.memory.persona", fromlist=["get_persona"]).get_persona().get_stats())
    if persona:
        memory_children["persona"] = {
            "label": "Persona", "status": "active",
            "metrics": {"traits": persona.get("traits_count", 0), "interactions": persona.get("total_interactions", 0)},
        }

    roots = _safe(lambda: __import__("backend.memory.roots", fromlist=["get_roots_memory"]).get_roots_memory().get_stats())
    if roots:
        memory_children["roots"] = {
            "label": "Roots", "status": "active",
            "metrics": {"roots": roots.get("total_roots", 0)},
        }

    memory_total = sum(
        c.get("metrics", {}).get(k, 0)
        for c in memory_children.values()
        for k in c.get("metrics", {})
    )
    memory = {
        "label": "Memory", "status": "active" if memory_children else "unknown",
        "metrics": {"modules": len(memory_children), "items": memory_total},
        "children": memory_children,
    }

    # ─── Reasoning ───
    ml = _safe(lambda: __import__("backend.core.xray.meta_learner", fromlist=["get_meta_learner"]).get_meta_learner().get_stats())
    strategy = "unknown"
    ml_metrics = {}
    if ml:
        strategy = ml.get("best_strategy") or "reasoning"
        ml_metrics = {
            "success_rate": ml.get("overall_success_rate", 0),
            "decisions": ml.get("total_decisions", 0),
        }
    reasoning = {
        "label": "Reasoning", "status": "active",
        "metrics": {"strategy": strategy, **ml_metrics},
    }

    # ─── Identity ───
    identity_metrics = {}
    if persona:
        identity_metrics = {
            "dominant_traits": persona.get("dominant_traits", [])[:3],
            "reflections": persona.get("reflections_count", 0),
        }
    identity = {
        "label": "Identity", "status": "active",
        "metrics": identity_metrics,
    }

    # ─── Emotion ───
    emotion_metrics = {}
    pad_state = _safe(lambda: __import__("backend.emotion.pad_model", fromlist=["get_pad_model"]).get_pad_model().get_state())
    if pad_state:
        d = pad_state.to_dict() if hasattr(pad_state, "to_dict") else {}
        emotion_metrics = {
            "pleasure": d.get("удовольствие", d.get("pleasure", 0)),
            "arousal": d.get("возбуждение", d.get("arousal", 0)),
            "dominance": d.get("доминирование", d.get("dominance", 0)),
            "curiosity": d.get("любопытство", d.get("curiosity", 0)),
            "confidence": d.get("уверенность", d.get("confidence", 0)),
        }
    emotion = {
        "label": "Emotion", "status": "active",
        "metrics": emotion_metrics,
    }

    # ─── Reflection ───
    refl = _safe(lambda: __import__("backend.core.xray.reflection", fromlist=["get_reflection_loop"]).get_reflection_loop().get_stats())
    reflection_metrics = {}
    if refl:
        reflection_metrics = {
            "count": refl.get("reflection_count", 0),
            "adjustments": refl.get("adjustment_count", 0),
        }
    reflection = {
        "label": "Reflection", "status": "active",
        "metrics": reflection_metrics,
    }

    # ─── Dreams ───
    dreams = _safe(lambda: __import__("backend.core.dreams", fromlist=["get_dream_system"]).get_dream_system().get_dream_stats())
    dream_metrics = {}
    if dreams:
        dream_metrics = {
            "total_dreams": dreams.get("total_dreams", 0),
            "consolidated": dreams.get("total_episodes_consolidated", 0),
            "is_dreaming": dreams.get("is_dreaming", False),
        }
    dreams_node = {
        "label": "Dreams", "status": "active" if dreams else "unknown",
        "metrics": dream_metrics,
    }

    # ─── Truth ───
    truth = _safe(lambda: __import__("backend.core.truth_loop", fromlist=["get_truth_loop"]).get_truth_loop().get_stats())
    truth_metrics = {}
    if truth:
        truth_metrics = {
            "claims": truth.get("total_claims", 0),
            "avg_confidence": truth.get("average_confidence", 0),
        }
    truth_node = {
        "label": "Truth", "status": "active" if truth else "unknown",
        "metrics": truth_metrics,
    }

    # ─── Safety ───
    safety = _safe(lambda: __import__("backend.core.safety_layer", fromlist=["get_safety_layer"]).get_safety_layer().get_stats())
    safety_metrics = {}
    if safety:
        safety_metrics = {
            "autonomy": safety.get("autonomy_enabled", False),
            "strict_mode": safety.get("strict_mode", False),
            "requests_1m": safety.get("requests_last_minute", 0),
        }
    safety_node = {
        "label": "Safety", "status": "active" if safety else "unknown",
        "metrics": safety_metrics,
    }

    # ─── Healer ───
    healer = _safe(lambda: __import__("backend.healing.listener", fromlist=["get_healer"]).get_healer().get_status())
    healer_metrics = {}
    if healer:
        healer_metrics = {
            "mode": healer.get("mode", "unknown"),
            "remediations": healer.get("remediation_applied", 0),
            "cycles": healer.get("cycle_count", 0),
        }
    healer_node = {
        "label": "Healer", "status": "active" if healer else "unknown",
        "metrics": healer_metrics,
    }

    # ─── Research ───
    from backend.core.decisions import get_decision_recorder
    dec_stats = _safe(lambda: get_decision_recorder().stats())
    research_metrics = {}
    if dec_stats:
        research_metrics = {
            "decisions": dec_stats.get("total", 0),
            "components": len(dec_stats.get("by_component", {})),
        }
    research_node = {
        "label": "Research", "status": "active",
        "metrics": research_metrics,
    }

    # ─── X-Ray ───
    xray = _safe(lambda: __import__("backend.core.xray.history_recorder", fromlist=["get_xray_history"]).get_xray_history())
    xray_metrics = {}
    if xray:
        try:
            sessions = xray.list_sessions(limit=1)
            xray_metrics = {"traces": len(sessions) if sessions else 0}
        except Exception:
            pass
        # recent session time
        try:
            if sessions:
                xray_metrics["last_trace"] = sessions[0].get("timestamp") or sessions[0].get("created_at")
        except Exception:
            pass
    xray_node = {
        "label": "X-Ray", "status": "active" if xray else "unknown",
        "metrics": xray_metrics,
    }

    # ─── Brain (root) ───
    brain = {
        "label": "Brain", "status": "active",
        "metrics": {
            "modules": 11,
            "strategy": strategy,
        },
        "children": {
            "memory": memory,
            "reasoning": reasoning,
            "identity": identity,
            "emotion": emotion,
            "reflection": reflection,
            "dreams": dreams_node,
            "truth": truth_node,
            "safety": safety_node,
            "healer": healer_node,
            "research": research_node,
            "xray": xray_node,
        },
    }

    return {
        "brain": brain,
        "timestamp": datetime.now().isoformat(),
    }


def _find_nested(d: Dict, key: str, depth: int = 0) -> Optional[Dict]:
    """Рекурсивный поиск модуля во вложенных children."""
    if not isinstance(d, dict):
        return None
    for k, v in d.items():
        if k == key and isinstance(v, dict):
            return v
        if isinstance(v, dict) and "children" in v:
            found = _find_nested(v["children"], key, depth + 1)
            if found:
                return found
    return None


def get_module_detail(module_id: str) -> Optional[Dict[str, Any]]:
    """Детальный статус конкретного модуля."""
    status = get_module_status()
    brain = status.get("brain", {})
    children = brain.get("children", {})
    if module_id == "brain":
        detail = dict(brain)
    else:
        detail = children.get(module_id)
        if detail is None:
            detail = _find_nested(children, module_id)
        if detail is None:
            return None

    # Кросс-ссылка: какой компонент Decision Log соответствует модулю
    detail = dict(detail)
    detail["component"] = MODULE_TO_COMPONENT.get(module_id)

    # Количество решений по этому компоненту
    comp = detail["component"]
    if comp:
        try:
            from backend.core.decisions import get_decision_recorder
            recs = get_decision_recorder().query(component=comp, limit=1000)
            detail["decision_count"] = len(recs)
        except Exception:
            detail["decision_count"] = 0
    else:
        detail["decision_count"] = 0

    return detail
