from unittest.mock import MagicMock, patch, AsyncMock

import pytest

from core.pipeline import PipelineContext
from core.pipeline.phases.generate import GeneratePhase


class TestProviderFallback:
    @pytest.mark.asyncio
    async def test_generate_success(self):
        with patch("runtime.provider_manager.get_provider_manager") as mock_pm:
            mock_instance = MagicMock()
            mock_result = MagicMock()
            mock_result.response.text = "нормальный ответ"
            mock_result.response.provider = "openrouter"
            mock_result.response.confidence = 0.9
            mock_result.response.model = "test-model"
            mock_result.response.metadata = None
            mock_instance.generate = AsyncMock(return_value=mock_result)
            mock_pm.return_value = mock_instance

            phase = GeneratePhase()
            ctx = PipelineContext(
                user_message="привет",
                context={"strategy": "simple", "response": ""},
                api_key="sk-test",
            )
            result = await phase.execute(ctx)
            assert result.success
            assert result.data["response"] == "нормальный ответ"
            assert result.data["provider"] == "openrouter"

    @pytest.mark.asyncio
    async def test_generate_fallback_all_providers_failed(self):
        with patch("runtime.provider_manager.get_provider_manager") as mock_pm, \
             patch("core.fallback_generator.get_fallback_response") as mock_fallback:
            mock_instance = MagicMock()
            from runtime.provider_manager import AllProvidersFailedError
            mock_instance.generate = AsyncMock(side_effect=AllProvidersFailedError(
                errors={"openrouter": "timeout"},
            ))
            mock_pm.return_value = mock_instance

            mock_fallback.return_value.content = "философский ответ"
            mock_fallback.return_value.confidence = 0.6

            phase = GeneratePhase()
            ctx = PipelineContext(
                user_message="привет",
                context={"strategy": "simple", "emotion_style": {"tone": "philosophical"}, "response": ""},
                api_key="sk-test",
            )
            result = await phase.execute(ctx)
            assert result.success
            assert "философский ответ" in result.data["response"]
            assert result.data["provider"] == "fallback"
            assert result.data["model"] == "fallback_generator"

    @pytest.mark.asyncio
    async def test_generate_fallback_generic_error(self):
        with patch("runtime.provider_manager.get_provider_manager") as mock_pm:
            mock_instance = MagicMock()
            mock_instance.generate = AsyncMock(side_effect=RuntimeError("network error"))
            mock_pm.return_value = mock_instance

            phase = GeneratePhase()
            ctx = PipelineContext(
                user_message="привет",
                context={"strategy": "simple", "response": ""},
                api_key="sk-test",
            )
            result = await phase.execute(ctx)
            assert result.success
            assert "технические трудности" in result.data["response"]

    @pytest.mark.asyncio
    async def test_generate_no_api_key(self):
        phase = GeneratePhase()
        ctx = PipelineContext(
            user_message="привет",
            context={"strategy": "simple", "response": ""},
            api_key=None,
        )
        result = await phase.execute(ctx)
        assert result.success
        assert "API ключа" in result.data["response"]
        assert result.data["provider"] == "no_api_key"
