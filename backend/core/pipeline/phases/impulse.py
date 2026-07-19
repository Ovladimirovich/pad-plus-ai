import logging

from ..base import PipelinePhase
from ..context import PipelineContext
from ..models import PhaseResult
from ..registry import register_phase

logger = logging.getLogger("padplus.pipeline.impulse")


@register_phase("impulse", order=8)
class ImpulsePhase(PipelinePhase):
    """Pre-generate: читает impulse state и кладёт bias в ctx.context."""

    name = "impulse"

    async def execute(self, ctx: PipelineContext) -> PhaseResult:
        try:
            from core.impulse import get_impulse_core

            core = get_impulse_core()
            state = core.to_dict()
            bias = core.get_bias_block()
            primary = core.get_primary_label()
            active = [
                {"label": d.label, "weight": d.weight, "question": d.question}
                for d in core.get_active_questions(threshold=0.3)
            ]
            return PhaseResult(
                success=True,
                data={
                    "impulse_state": state,
                    "impulse_bias": bias,
                    "impulse_primary": primary,
                    "impulse_prompt_line": core.get_prompt_line(),
                    "impulse_active": active,
                },
            )
        except Exception as e:
            logger.warning("Ошибка в ImpulsePhase: %s", e, exc_info=True)
            return PhaseResult(
                success=True,
                data={
                    "impulse_state": {},
                    "impulse_bias": "",
                    "impulse_primary": "unknown",
                    "impulse_prompt_line": "",
                    "impulse_active": [],
                },
            )
