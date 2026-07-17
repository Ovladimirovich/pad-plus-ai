import logging

from ..base import PipelinePhase
from ..context import PipelineContext
from ..models import PhaseResult

logger = logging.getLogger("padplus.pipeline.impulse_update")


class ImpulseUpdatePhase(PipelinePhase):
    """
    Post-generate: единственный writer deltas (V1).

    1. ensure experience_* via signals.infer_experience
    2. apply_deltas + save
    """

    name = "impulse_update"

    async def execute(self, ctx: PipelineContext) -> PhaseResult:
        try:
            from core.impulse import apply_deltas, get_impulse_core, get_manager
            from core.impulse.signals import ensure_experience_in_context

            interaction_type, significance = ensure_experience_in_context(
                ctx.context,
                user_message=ctx.user_message or "",
            )

            if significance < 0.2:
                return PhaseResult(
                    success=True,
                    data={
                        "impulse_updated": False,
                        "experience_interaction_type": interaction_type,
                        "experience_significance": significance,
                        "reason": "low_significance",
                    },
                )

            core = get_impulse_core()
            before = core.get_primary_label()
            changed = apply_deltas(core, interaction_type, significance)
            if not changed:
                return PhaseResult(
                    success=True,
                    data={
                        "impulse_updated": False,
                        "experience_interaction_type": interaction_type,
                        "experience_significance": significance,
                        "reason": "no_delta_change",
                    },
                )

            get_manager().save(core)
            after_state = core.to_dict()
            after_primary = core.get_primary_label()

            ctx.context["impulse_updated"] = True
            ctx.context["impulse_state"] = after_state
            ctx.context["impulse_primary"] = after_primary

            logger.info(
                "ImpulseUpdate: type=%s sig=%.2f primary %s → %s",
                interaction_type,
                significance,
                before,
                after_primary,
            )

            return PhaseResult(
                success=True,
                data={
                    "impulse_updated": True,
                    "impulse_state": after_state,
                    "impulse_primary": after_primary,
                    "experience_interaction_type": interaction_type,
                    "experience_significance": significance,
                },
            )
        except Exception as e:
            logger.warning("Ошибка в ImpulseUpdatePhase: %s", e, exc_info=True)
            return PhaseResult(success=True, data={"impulse_updated": False})
