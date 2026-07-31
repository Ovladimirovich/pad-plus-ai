import logging

from ..base import PipelinePhase
from ..context import PipelineContext
from ..models import PhaseResult
from ..registry import register_phase

logger = logging.getLogger("padplus.pipeline.emotion")


@register_phase("emotion", order=7)
class EmotionPhase(PipelinePhase):
    name = "emotion"

    async def execute(self, ctx: PipelineContext) -> PhaseResult:
        try:
            from emotion.session_store import get_session_emotion_store

            store = get_session_emotion_store()
            pad = store.get_or_create(ctx.session_id)
            state = pad.get_state()
            return PhaseResult(
                success=True,
                data={
                    "emotion_state": state.to_dict(),
                    "emotion_style": state.get_style(),
                },
            )
        except Exception as e:
            logger.warning("Ошибка в EmotionPhase: %s", e, exc_info=True)
            return PhaseResult(
                success=True,
                data={"emotion_state": {}, "emotion_style": {}},
            )
