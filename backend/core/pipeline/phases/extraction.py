import logging

from ..base import PipelinePhase
from ..context import PipelineContext
from ..models import PhaseResult

logger = logging.getLogger("padplus.pipeline.extraction")


class ExtractionPhase(PipelinePhase):
    """Фаза извлечения концепций из сообщения пользователя.
    Работает без LLM — только частотный анализ + шаблоны.
    Занимает <1мс. Никак не влияет на ответ пользователю."""

    name = "extraction"

    async def execute(self, ctx: PipelineContext) -> PhaseResult:
        try:
            from knowledge.graph import get_knowledge_graph
            from knowledge.extractor import extract_and_add

            result = extract_and_add(ctx.user_message, get_knowledge_graph())

            if result["concepts_added"] or result["relations_added"]:
                logger.info(
                    "Извлечено из сообщения: +%d концепций, +%d связей",
                    result["concepts_added"],
                    result["relations_added"],
                )

            return PhaseResult(
                success=True,
                data={
                    "concepts_added": result["concepts_added"],
                    "relations_added": result["relations_added"],
                },
            )
        except Exception as e:
            logger.warning("Ошибка в ExtractionPhase: %s", e, exc_info=True)
            return PhaseResult(
                success=True,
                data={"concepts_added": 0, "relations_added": 0},
            )
