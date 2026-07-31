import logging

from ..base import PipelinePhase
from ..context import PipelineContext
from ..models import PhaseResult
from ..registry import register_phase

logger = logging.getLogger("padplus.pipeline.emotion_update")


@register_phase("emotion_update", order=17)
class EmotionUpdatePhase(PipelinePhase):
    name = "emotion_update"

    async def execute(self, ctx: PipelineContext) -> PhaseResult:
        try:
            user_message = ctx.user_message
            response = ctx.context.get("response", "")
            from emotion.session_store import get_session_emotion_store
            from emotion.emotion_learner import get_emotion_learner

            store = get_session_emotion_store()
            pad = store.get_or_create(ctx.session_id)
            learner = get_emotion_learner()
            analysis = learner.learn_from_dialog(user_message, response)
            pad.apply_event(analysis["event"], analysis["intensity"])
            store.save(ctx.session_id)

            return PhaseResult(success=True, data={
                "emotion_event": analysis["event"],
                "emotion_intensity": analysis["intensity"],
            })
        except Exception as e:
            logger.warning("Ошибка в EmotionUpdatePhase: %s", e, exc_info=True)
            return PhaseResult(success=True)
