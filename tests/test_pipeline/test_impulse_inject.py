"""CI proof: impulse bias is injected into GeneratePhase system prompt (no live LLM)."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from core.pipeline.context import PipelineContext
from core.pipeline.phases.generate import GeneratePhase


class _FakeResp:
    def __init__(self, text="ok"):
        self.text = text
        self.provider = "mock"
        self.confidence = 0.9
        self.model = "mock-model"
        self.metadata = {}


class _FakeGenResult:
    def __init__(self):
        self.response = _FakeResp()


@pytest.mark.asyncio
async def test_generate_includes_bias_in_system_prompt():
    captured = {}

    async def fake_generate(**kwargs):
        captured["system_prompt"] = kwargs.get("system_prompt", "")
        captured["prompt"] = kwargs.get("prompt", "")
        return _FakeGenResult()

    mock_pm = MagicMock()
    mock_pm.generate = AsyncMock(side_effect=fake_generate)

    ctx = PipelineContext(
        user_message="Что важнее?",
        api_key="test-key",
        provider="openrouter",
        context={
            "impulse_bias": (
                "Твоя когнитивная направленность:\n"
                "- Основной импульс: понять\n"
                "- Активные направления: understand (1.00)\n"
                "- Доминанта: understand → фокус на понимание и анализ"
            ),
            "impulse_primary": "understand",
            "strategy": "simple",
            "emotion_style": {"tone": "neutral"},
            "emotion_state": {},
        },
    )

    with patch("runtime.provider_manager.get_provider_manager", return_value=mock_pm):
        result = await GeneratePhase().execute(ctx)

    assert result.success
    assert "understand" in captured["system_prompt"]
    assert "когнитивная направленность" in captured["system_prompt"]
    assert result.data.get("impulse_used") is True
    assert result.data.get("impulse_primary") == "understand"


@pytest.mark.asyncio
async def test_generate_skips_empty_bias():
    captured = {}

    async def fake_generate(**kwargs):
        captured["system_prompt"] = kwargs.get("system_prompt", "")
        return _FakeGenResult()

    mock_pm = MagicMock()
    mock_pm.generate = AsyncMock(side_effect=fake_generate)

    ctx = PipelineContext(
        user_message="Привет",
        api_key="test-key",
        context={
            "impulse_bias": "",
            "impulse_primary": "unknown",
            "strategy": "simple",
            "emotion_style": {},
            "emotion_state": {},
        },
    )

    with patch("runtime.provider_manager.get_provider_manager", return_value=mock_pm):
        result = await GeneratePhase().execute(ctx)

    assert result.success
    assert "когнитивная направленность" not in captured["system_prompt"]
    assert result.data.get("impulse_used") is False


@pytest.mark.asyncio
async def test_thought_visualizer_impulse():
    from core.xray.thought_visualizer import ThoughtVisualizer, ThoughtType

    tv = ThoughtVisualizer()
    state = {
        "version": 2,
        "primary": {
            "label": "create",
            "question": "Что я могу создать?",
            "dimensions": [
                {"label": "create", "question": "?", "weight": 0.9},
                {"label": "understand", "question": "?", "weight": 0.1},
            ],
        },
    }
    th = tv.impulse_state(state)
    assert th.type == ThoughtType.IMPULSE_READ
    assert "create" in th.content

    th2 = tv.impulse_state(state, updated=True)
    assert th2.type == ThoughtType.IMPULSE_UPDATE
