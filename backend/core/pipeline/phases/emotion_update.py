import logging

from ..base import PipelinePhase
from ..context import PipelineContext
from ..models import PhaseResult

logger = logging.getLogger("padplus.pipeline.emotion_update")


class EmotionUpdatePhase(PipelinePhase):
    name = "emotion_update"

    async def execute(self, ctx: PipelineContext) -> PhaseResult:
        try:
            user_message = ctx.user_message
            response = ctx.context.get("response", "")
            from emotion.pad_model import get_pad_model
            from emotion.emotion_learner import get_emotion_learner

            pad = get_pad_model()
            learner = get_emotion_learner()
            analysis = learner.learn_from_dialog(user_message, response)
            pad.apply_event(analysis["event"], analysis["intensity"])
            pad.save()

            return PhaseResult(success=True, data={
                "emotion_event": analysis["event"],
                "emotion_intensity": analysis["intensity"],
            })
        except Exception as e:
            logger.warning("Ошибка в EmotionUpdatePhase: %s", e, exc_info=True)
            return PhaseResult(success=True)
