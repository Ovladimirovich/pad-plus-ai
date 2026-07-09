import logging

from ..base import PipelinePhase
from ..context import PipelineContext
from ..models import PhaseResult

logger = logging.getLogger("padplus.pipeline.knowledge_graph")


class KnowledgeGraphPhase(PipelinePhase):
    name = "knowledge_graph"

    async def execute(self, ctx: PipelineContext) -> PhaseResult:
        try:
            from knowledge.search import find_related_triples, search_concepts

            concept_names, graph_context = find_related_triples(
                query=ctx.user_message,
                concept_limit=5,
                relation_limit=8,
            )

            return PhaseResult(
                success=True,
                data={
                    "concepts": concept_names,
                    "graph_context": graph_context,
                    "confidence": 0.7 if concept_names else 0.0,
                },
            )
        except Exception as e:
            logger.warning("Ошибка в KnowledgeGraphPhase: %s", e, exc_info=True)
            return PhaseResult(
                success=True,
                data={"concepts": [], "graph_context": "", "confidence": 0.0},
            )
