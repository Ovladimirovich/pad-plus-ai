"""
Эвристический producer experience signals для ImpulseUpdatePhase.

Без LLM: keyword / context flags → (interaction_type, significance).
Порог применения deltas: significance >= 0.2 (см. deltas.MIN_SIGNIFICANCE).
"""

from __future__ import annotations

import re
from typing import Any, Dict, Tuple

# (type, base_significance)
_PRAISE_RE = re.compile(
    r"\b(спасибо|благодар|отлично|класс|супер|👍|хорошо\s+сработал|helpful)\b",
    re.IGNORECASE,
)
_CRITICISM_RE = re.compile(
    r"\b(плохо|ошиб|неверно|бред|глупо|👎|не\s+так|wrong|useless)\b",
    re.IGNORECASE,
)
_CONTRADICTION_RE = re.compile(
    r"\b(противореч|наоборот|ты\s+сам|contradict)\b",
    re.IGNORECASE,
)
_EXPLORATION_RE = re.compile(
    r"\b(почему|как\s+работа|зачем|что\s+если|explain|how\s+does)\b",
    re.IGNORECASE,
)


def infer_experience(
    user_message: str = "",
    ctx: Dict[str, Any] | None = None,
) -> Tuple[str, float]:
    """
    Возвращает (interaction_type, significance).

    Приоритет:
      1. Явные ctx flags (user_feedback, pipeline_error, fallback, anti_loop)
      2. Эвристики по тексту user_message
      3. intent / strategy hints
      4. new_knowledge с низкой significance (no-op для deltas)
    """
    ctx = ctx or {}
    msg = (user_message or "").strip()

    # Explicit feedback from API / UI
    feedback = ctx.get("user_feedback") or ctx.get("feedback")
    if feedback is not None:
        if isinstance(feedback, (int, float)):
            if feedback >= 4:
                return "praise", 0.6
            if feedback <= 2:
                return "criticism", 0.7
        if isinstance(feedback, str):
            fl = feedback.lower()
            if fl in ("up", "positive", "like", "good", "1", "true"):
                return "praise", 0.6
            if fl in ("down", "negative", "dislike", "bad", "0", "false"):
                return "criticism", 0.7

    if ctx.get("pipeline_error") or ctx.get("fallback_used") or ctx.get("provider") == "fallback":
        return "error_recovery", 0.55

    if ctx.get("anti_loop_near") or ctx.get("repetition_detected"):
        return "repetition", 0.35

    if msg:
        if _CONTRADICTION_RE.search(msg):
            return "contradiction", 0.65
        if _CRITICISM_RE.search(msg):
            return "criticism", 0.6
        if _PRAISE_RE.search(msg):
            return "praise", 0.55
        if _EXPLORATION_RE.search(msg):
            return "exploration", 0.4

    intent = (ctx.get("intent") or "").lower()
    if intent in ("explore", "question", "learning", "research"):
        return "exploration", 0.35

    strategy = (ctx.get("strategy") or "").lower()
    if strategy in ("deep", "reflective", "learning"):
        return "exploration", 0.3

    # Default: weak new_knowledge — below MIN_SIGNIFICANCE → no-op for deltas
    return "new_knowledge", 0.15


def ensure_experience_in_context(ctx_dict: Dict[str, Any], user_message: str = "") -> Tuple[str, float]:
    """
    Гарантирует experience_interaction_type / experience_significance в ctx.
    Не перезаписывает, если уже заданы осмысленно.
    """
    existing_type = ctx_dict.get("experience_interaction_type") or ""
    existing_sig = ctx_dict.get("experience_significance")

    if existing_type and existing_sig is not None:
        try:
            return str(existing_type), float(existing_sig)
        except (TypeError, ValueError):
            pass

    itype, sig = infer_experience(user_message, ctx_dict)
    ctx_dict["experience_interaction_type"] = itype
    ctx_dict["experience_significance"] = sig
    return itype, sig
