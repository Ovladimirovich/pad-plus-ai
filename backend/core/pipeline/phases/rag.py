import logging

from ..base import PipelinePhase
from ..context import PipelineContext
from ..models import PhaseResult
from ..registry import register_phase

logger = logging.getLogger("padplus.pipeline.rag")


@register_phase("rag", order=3)
class RagPhase(PipelinePhase):
    name = "rag"

    async def execute(self, ctx: PipelineContext) -> PhaseResult:
        try:
            from memory import get_rag
            rag = get_rag()
            user_id = ctx.context.get("user_id") if ctx.context else None
            context_data = rag.get_context(ctx.user_message, user_id=user_id)

            sources = {"count": 1 if context_data else 0, "confidence": 0.8 if context_data else 0.0}

            # Поиск по документам пользователя
            document_context = ""
            if user_id:
                try:
                    from core.document_processor import search_document_chunks
                    doc_results = await search_document_chunks(
                        query=ctx.user_message,
                        user_id=user_id,
                        limit=3,
                        similarity_threshold=0.4,
                    )
                    if doc_results:
                        doc_parts = []
                        for r in doc_results:
                            doc_parts.append(
                                f"[{r['document_title']} (сходство: {r['similarity']:.2f})]\n{r['content'][:500]}"
                            )
                        document_context = "📄 Контекст из документов:\n" + "\n\n".join(doc_parts)
                        sources["count"] += len(doc_results)
                except Exception as doc_e:
                    logger.debug("Ошибка поиска по документам: %s", doc_e)

            full_context = context_data or ""
            if document_context:
                if full_context:
                    full_context += "\n\n" + document_context
                else:
                    full_context = document_context

            return PhaseResult(
                success=True,
                data={
                    "rag_context": full_context,
                    "rag_used": bool(full_context),
                    "sources": sources,
                },
            )
        except Exception as e:
            logger.warning("Ошибка в RagPhase: %s", e, exc_info=True)
            return PhaseResult(
                success=True,
                data={"rag_context": "", "rag_used": False, "sources": {"count": 0, "confidence": 0.0}},
            )
