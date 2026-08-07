from dataclasses import dataclass, field
from typing import Dict, List, Set, Callable, Optional


@dataclass
class PhaseProfile:
    name: str
    hot: Set[str]
    background: Set[str] = field(default_factory=set)
    conditional: Dict[str, Callable] = field(default_factory=dict)


# ── Профили стратегий ───────────────────────────────────────────────
# Каждая стратегия получает свой набор hot (синхронных) и background
# (fire-and-forget) фаз. conditional-фазы добавляются в hot, если
# предикат возвращает True.

PROFILES: Dict[str, PhaseProfile] = {
    "simple": PhaseProfile(
        name="simple",
        hot={
            "safety", "intent",
            "emotion", "impulse",
            "persona", "roots",
            "generate", "response_guard",
        },
        background={
            "save_episode",
            "emotion_update", "impulse_update",
            "events_broadcast", "metrics",
            "memory_maintenance",
        },
    ),
    "retrieval": PhaseProfile(
        name="retrieval",
        hot={
            "safety", "intent",
            "rag", "episodic",
            "emotion", "impulse",
            "persona", "roots",
            "generate",
            "evaluation", "response_guard",
        },
        background={
            "save_episode", "extraction",
            "emotion_update", "impulse_update",
            "persona_evolution",
            "events_broadcast", "health",
            "memory_maintenance",
            "reflection", "dreams", "metrics",
        },
        conditional={
            "knowledge_graph": lambda ctx: any(
                kw in (ctx.user_message or "").lower()
                for kw in ["что такое", "кто такой", "определение", "значение"]
            ),
            "truth_loop": lambda ctx: bool(
                ctx.context.get("sources", {}).get("rag", {}).get("count", 0) > 0
            ),
        },
    ),
    "reasoning": PhaseProfile(
        name="reasoning",
        hot={
            "safety", "intent",
            "rag", "knowledge_graph", "episodic", "semantic",
            "emotion", "impulse",
            "persona", "roots",
            "generate",
            "truth_loop", "evaluation",
            "response_guard",
        },
        background={
            "save_episode", "extraction",
            "emotion_update", "impulse_update",
            "persona_evolution",
            "events_broadcast", "health",
            "reflection", "dreams", "metrics",
            "memory_maintenance",
        },
    ),
    "creative": PhaseProfile(
        name="creative",
        hot={
            "safety", "intent",
            "rag", "knowledge_graph",
            "emotion", "impulse",
            "persona", "roots",
            "generate",
            "truth_loop", "evaluation",
            "response_guard",
        },
        background={
            "save_episode", "extraction",
            "emotion_update", "impulse_update",
            "persona_evolution",
            "events_broadcast", "health",
            "reflection", "dreams", "metrics",
            "memory_maintenance",
        },
    ),
    "reflective": PhaseProfile(
        name="reflective",
        hot={
            "safety", "intent",
            "rag",
            "emotion", "impulse",
            "persona", "roots", "identity",
            "generate",
            "truth_loop", "evaluation",
            "response_guard",
        },
        background={
            "save_episode", "extraction",
            "emotion_update", "impulse_update",
            "persona_evolution",
            "events_broadcast", "health",
            "reflection", "dreams", "metrics",
            "memory_maintenance",
        },
    ),
    "learning": PhaseProfile(
        name="learning",
        hot={
            "safety", "intent",
            "rag", "semantic",
            "emotion", "impulse",
            "persona", "roots",
            "generate",
            "evaluation",
            "response_guard",
        },
        background={
            "save_episode", "extraction",
            "emotion_update", "impulse_update",
            "persona_evolution",
            "events_broadcast", "health",
            "reflection", "dreams", "metrics",
            "memory_maintenance",
        },
    ),
}

# Фазы, которые могут выполняться параллельно (группа retrieval)
INDEPENDENT_GROUP: Set[str] = {
    "rag", "knowledge_graph", "episodic", "semantic", "emotion",
}


def get_profile(strategy: str) -> PhaseProfile:
    return PROFILES.get(strategy, PROFILES["reasoning"])


def get_effective_hot(strategy: str, ctx) -> Set[str]:
    """Возвращает hot-фазы для стратегии с учётом conditional."""
    profile = get_profile(strategy)
    phases = set(profile.hot)
    for name, predicate in profile.conditional.items():
        try:
            if predicate(ctx):
                phases.add(name)
        except Exception:
            pass
    return phases
