import logging

from ..base import PipelinePhase
from ..context import PipelineContext
from ..models import PhaseResult
from ..registry import register_phase

logger = logging.getLogger("padplus.pipeline.semantic")


@register_phase("semantic", order=6)
class SemanticPhase(PipelinePhase):
    name = "semantic"

    async def execute(self, ctx: PipelineContext) -> PhaseResult:
        try:
            session_id = ctx.session_id
            from memory.session_store import get_session_semantic_store
            semantic_store = get_session_semantic_store()
            procedure = semantic_store.find_applicable_procedure(session_id, ctx.user_message)

            procedure_context = ""
            procedure_name = None
            procedure_id = None

            if procedure:
                procedure_name = procedure.name
                procedure_id = procedure.id
                procedure_context = f"\n\n🔧 Процедура '{procedure.name}':\n"
                for i, step in enumerate(procedure.procedure_steps[:3], 1):
                    procedure_context += f"  {i}. {step}\n"

            return PhaseResult(
                success=True,
                data={
                    "procedure_context": procedure_context,
                    "procedure_name": procedure_name,
                    "procedure_id": procedure_id,
                },
            )
        except Exception as e:
            logger.warning("Ошибка в SemanticPhase: %s", e, exc_info=True)
            return PhaseResult(
                success=True,
                data={"procedure_context": "", "procedure_name": None, "procedure_id": None},
            )
