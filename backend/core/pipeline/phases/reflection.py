import logging

from ..base import PipelinePhase
from ..context import PipelineContext
from ..models import PhaseResult

logger = logging.getLogger("padplus.pipeline.phases.reflection")


class ReflectionPhase(PipelinePhase):
    name = "reflection"

    async def execute(self, ctx: PipelineContext) -> PhaseResult:
        try:
            from core.xray.reflection import get_reflection_loop
            from core.xray.system_state import get_system_state_manager

            reflection = get_reflection_loop()
            state_manager = get_system_state_manager()
            state_manager.update(ctx.context.get("result_dict", {}))
        except Exception as e:
            logger.warning(f"{__name__} error: {e}")

        try:
            from core.meta_controller import get_meta_controller
            meta = get_meta_controller()
            meta.adapt({
                "strategy_success": ctx.context.get("pipeline_result", {}).get("success", False),
                "interaction_type": ctx.context.get("experience_interaction_type", "new_knowledge"),
                "significance": ctx.context.get("experience_significance", 0.0),
                "emotion": ctx.context.get("emotion_style", {}),
                "impulse_primary": ctx.context.get("impulse_primary", ""),
            })
        except Exception as e:
            logger.warning(f"{__name__} error: {e}")

        return PhaseResult(success=True)
