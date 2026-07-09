from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
import logging

logger = logging.getLogger("padplus.memory_hooks")


class MemoryHookManager:
    def __init__(self):
        self._hooks: Dict[str, List[Callable]] = {
            "before_pipeline": [],
            "after_phase": [],
            "before_response": [],
            "after_process": [],
        }
        logger.info("MemoryHookManager initialized")

    def register(self, hook_point: str, handler: Callable) -> None:
        if hook_point not in self._hooks:
            logger.warning(f"Unknown hook point: {hook_point}")
            return
        self._hooks[hook_point].append(handler)
        logger.debug(f"Hook registered: {hook_point} -> {handler.__name__}")

    def execute(self, hook_point: str, context: Dict[str, Any]) -> None:
        for handler in self._hooks.get(hook_point, []):
            try:
                handler(context)
            except Exception as e:
                logger.warning(f"Hook {hook_point}/{handler.__name__} error: {e}")

    def reset(self) -> None:
        for key in self._hooks:
            self._hooks[key].clear()


def _before_pipeline_impl(ctx):
    user_id = ctx.get("user_id")
    if not user_id:
        return
    try:
        from memory import get_user_persona_manager
        pm = get_user_persona_manager()
        persona = pm.get_persona(user_id)
        ctx["user_persona"] = persona
        ctx["style_preferences"] = persona.style_preferences
    except Exception as e:
        logger.warning(f"before_pipeline: user_persona error: {e}")


def _after_phase_impl(ctx):
    phase_name = ctx.get("phase_name")
    phase_result = ctx.get("phase_result", {})
    user_id = ctx.get("user_id")
    if not user_id:
        return
    if phase_name == "generate":
        response = phase_result.get("response", "")
        if response:
            ctx.setdefault("_generated_response", response)
    elif phase_name == "rag":
        rag_context = phase_result.get("rag_context", "")
        if rag_context:
            ctx.setdefault("_rag_contexts", []).append(rag_context)
    elif phase_name == "emotion":
        emotion_data = phase_result.get("emotion_state", {})
        if emotion_data:
            ctx["_last_emotion"] = emotion_data


def _before_response_impl(ctx):
    user_id = ctx.get("user_id")
    persona = ctx.get("user_persona")
    if not user_id or not persona:
        return
    user_message = ctx.get("user_message", "")
    response = ctx.get("_generated_response", "")
    try:
        from memory.rag_postgres import classify_topic
        topic, confidence = classify_topic(f"{user_message} {response}")
        persona.frequent_topics[topic] = persona.frequent_topics.get(topic, 0) + 1
        persona.total_interactions += 1
    except Exception as e:
        logger.warning(f"before_response: topic update error: {e}")


def _after_process_impl(ctx):
    user_id = ctx.get("user_id")
    user_message = ctx.get("user_message", "")
    response = ctx.get("_generated_response", "")
    if not user_id or not user_message or not response:
        return
    try:
        from memory import get_user_persona_manager
        pm = get_user_persona_manager()
        persona = pm.get_persona(user_id)
        persona.last_interaction = datetime.now().isoformat()
        pm.save_persona(persona)
    except Exception as e:
        logger.warning(f"after_process: save persona error: {e}")
    try:
        from memory import get_rag
        rag = get_rag()
        rag.add_dialog(user_message, response, user_id=user_id)
    except Exception as e:
        logger.warning(f"after_process: save dialog error: {e}")

    # Lightweight cross-memory sync every 5 dialogs
    sync_key = "_dialog_count"
    count = ctx.get(sync_key, 0) + 1
    ctx[sync_key] = count
    if count % 5 == 0:
        try:
            from core.pipeline.cross_memory_sync import get_cross_memory_sync
            sync = get_cross_memory_sync()
            result = sync.sync_all(user_id)
            total = sum(len(v) for v in result.values())
            if total:
                logger.info(f"Cross-memory sync: {total} insights ({', '.join(f'{k}={len(v)}' for k, v in result.items())})")
        except Exception as e:
            logger.warning(f"after_process: cross-memory sync error: {e}")

    # Batch consolidation every 20 dialogs
    if count % 20 == 0:
        try:
            from memory.consolidation import get_consolidator
            consolidator = get_consolidator()
            results = consolidator.consolidate_all(user_id=user_id)
            total = sum(r.items_consolidated for r in results.values())
            if total:
                logger.info(f"Batch consolidation: {total} items consolidated ({', '.join(f'{k}={v.items_consolidated}' for k, v in results.items())})")
        except Exception as e:
            logger.warning(f"after_process: batch consolidation error: {e}")


def register_default_hooks() -> MemoryHookManager:
    """Регистрирует стандартные memory hooks."""
    mgr = get_memory_hooks()
    mgr.register("before_pipeline", _before_pipeline_impl)
    mgr.register("after_phase", _after_phase_impl)
    mgr.register("before_response", _before_response_impl)
    mgr.register("after_process", _after_process_impl)
    logger.info("Default memory hooks registered")
    return mgr


_memory_hooks: Optional[MemoryHookManager] = None


def get_memory_hooks() -> MemoryHookManager:
    global _memory_hooks
    if _memory_hooks is None:
        _memory_hooks = MemoryHookManager()
    return _memory_hooks
