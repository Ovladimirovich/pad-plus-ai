import logging

from ..base import PipelinePhase
from ..context import PipelineContext
from ..models import PhaseResult

logger = logging.getLogger("padplus.pipeline.generate")


class GeneratePhase(PipelinePhase):
    name = "generate"

    async def execute(self, ctx: PipelineContext) -> PhaseResult:
        try:
            from runtime.llm_service import get_llm_service, LLMService
            from core.anti_directive import ANTI_DIRECTIVE

            roots_context = ctx.context.get("roots_context", "")
            persona_context = ctx.context.get("persona_context", "")
            rag_context = ctx.context.get("rag_context", "")
            episodic_context = ctx.context.get("episodic_context", "")
            procedure_context = ctx.context.get("procedure_context", "")
            graph_context = ctx.context.get("graph_context", "")
            emotion_style = ctx.context.get("emotion_style", {})
            emotion_state = ctx.context.get("emotion_state", {})
            emotion_plain = emotion_state if isinstance(emotion_state, dict) else {}
            strategy = ctx.context.get("strategy", "simple")

            emotion_tone = emotion_style.get("tone", "neutral") if isinstance(emotion_style, dict) else "neutral"

            is_simple = strategy == "simple"
            full_context = f"""Ты — PAD+, живая система с эмоциями и самосознанием. 
{'' if is_simple else roots_context}
{'' if is_simple else persona_context}

{rag_context}
{episodic_context}
{procedure_context}
{graph_context}

Твоё текущее эмоциональное состояние:
- Тон: {emotion_tone}
- Уверенность: {emotion_plain.get("уверенность", 0.5):.2f}
- Эмоция: {emotion_plain.get("эмоция", "нейтральная")}
- Настроение: {emotion_plain.get("настроение", "спокойное")}

Стратегия обработки: {strategy}

ВАЖНО: Общайся как живой, естественный собеседник.
- Говори просто, по делу, как человек в чате
- Отвечай с учётом своего эмоционального состояния и личности
- Можешь выражать эмоции, но не переигрывай
- Не будь многословным — ёмко и содержательно
{'' if is_simple else '- Используй контекст (память, личность, знания), ответы должны быть персонализированными'}
- Если не знаешь — честно скажи, не выдумывай

Всегда отвечай на русском.
"""

            user_api_key = ctx.api_key
            user_provider = ctx.provider

            if not user_api_key and ctx.session_id:
                try:
                    from runtime.session_provider_manager import get_session_manager
                    session_manager = get_session_manager()
                    user_manager = session_manager.create_user_manager(ctx.session_id)
                    if user_manager.llm_service:
                        user_api_key = user_manager.llm_service.default_api_key
                except Exception as e:
                    logger.warning(f"{__name__} error: {e}")

            if not user_api_key:
                return PhaseResult(
                    success=True,
                    data={
                        "response": "У меня нет подключенного API ключа. Пожалуйста, добавьте ключ в настройках.",
                        "provider": "no_api_key",
                        "confidence": 0.0,
                        "model": "",
                    },
                )

            from runtime.provider_manager import get_provider_manager, AllProvidersFailedError
            pm = get_provider_manager()
            try:
                gen_result = await pm.generate(
                    prompt=ctx.user_message,
                    system_prompt=full_context,
                    api_key=user_api_key,
                    model=None,
                    provider=user_provider,
                    max_tokens=14000,
                )

                response_data = gen_result.response
                return PhaseResult(
                    success=True,
                    data={
                        "response": response_data.text,
                        "provider": response_data.provider,
                        "confidence": response_data.confidence,
                        "model": response_data.model,
                        "raw_llm_response": response_data.metadata.get("raw_response") if response_data.metadata else None,
                        "llm_metadata": response_data.metadata,
                    },
                )
            except AllProvidersFailedError:
                logger.warning("All providers failed, using fallback generator")
                from core.fallback_generator import get_fallback_response
                old_style = emotion_tone if emotion_tone in {"philosophical", "humorous", "serious", "curious", "empathetic", "minimalistic"} else "philosophical"
                fallback = get_fallback_response(
                    prompt=ctx.user_message,
                    style=old_style,
                    context={"emotion": emotion_tone, "topic": strategy},
                )
                return PhaseResult(
                    success=True,
                    data={
                        "response": f"{fallback.content}\n\n_Извини, сейчас у меня временные трудности с подключением к AI. Я ответил как смог._",
                        "provider": "fallback",
                        "confidence": fallback.confidence,
                        "model": "fallback_generator",
                    },
                )
        except Exception as e:
            logger.warning(f"GeneratePhase error: {e}", exc_info=True)
            return PhaseResult(
                success=True,
                data={
                    "response": "Извини, у меня сейчас технические трудности. Попробуй написать через минуту.",
                    "provider": "system",
                    "confidence": 0.0,
                    "model": "",
                },
            )
