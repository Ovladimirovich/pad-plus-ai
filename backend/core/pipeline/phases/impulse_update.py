import logging

from ..base import PipelinePhase
from ..context import PipelineContext
from ..models import PhaseResult
from ..registry import register_phase

logger = logging.getLogger("padplus.pipeline.impulse_update")


@register_phase("impulse_update", order=18)
class ImpulseUpdatePhase(PipelinePhase):
    """
    Post-generate: единственный writer deltas (V1).

    1. ensure experience_* via signals.infer_experience
    2. apply_deltas + save
    """

    name = "impulse_update"

    async def execute(self, ctx: PipelineContext) -> PhaseResult:
        try:
            from core.impulse import apply_deltas
            from core.impulse.session_store import get_session_impulse_store
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

            store = get_session_impulse_store()
            core = store.get_or_create(ctx.session_id)
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

            store.save(ctx.session_id)
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
