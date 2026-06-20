from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from core.pipeline import PipelineContext
from core.pipeline.phases.dreams import DreamsPhase, _reset_dream_counter, DREAM_INTERVAL


@pytest.fixture(autouse=True)
def reset_counter():
    _reset_dream_counter()


async def test_dreams_success():
    with patch("core.dreams.get_dream_system") as mock_get:
        mock_dreams = MagicMock()
        mock_get.return_value = mock_dreams

        phase = DreamsPhase()
        ctx = PipelineContext(user_message="тест")
        result = await phase.execute(ctx)

    assert result.success
    mock_dreams.record_activity.assert_called_once()
    mock_dreams.dream.assert_not_called()


async def test_dreams_triggers_after_interval():
    with patch("core.dreams.get_dream_system") as mock_get:
        mock_dreams = MagicMock()
        mock_dreams.dream = AsyncMock()
        mock_get.return_value = mock_dreams

        phase = DreamsPhase()
        ctx = PipelineContext(user_message="тест")

        for _ in range(DREAM_INTERVAL - 1):
            await phase.execute(ctx)

        mock_dreams.dream.assert_not_called()

        await phase.execute(ctx)
        mock_dreams.dream.assert_called_once()


async def test_dreams_resets_counter_after_trigger():
    with patch("core.dreams.get_dream_system") as mock_get:
        mock_dreams = MagicMock()
        mock_dreams.dream = AsyncMock()
        mock_get.return_value = mock_dreams

        phase = DreamsPhase()
        ctx = PipelineContext(user_message="тест")

        for _ in range(DREAM_INTERVAL):
            await phase.execute(ctx)

        assert mock_dreams.dream.call_count == 1

        mock_dreams.dream.reset_mock()

        for _ in range(DREAM_INTERVAL - 1):
            await phase.execute(ctx)
        mock_dreams.dream.assert_not_called()


async def test_dreams_fallback():
    with patch("core.dreams.get_dream_system") as mock_get:
        mock_get.side_effect = Exception("dreams unavailable")

        phase = DreamsPhase()
        ctx = PipelineContext(user_message="тест")
        result = await phase.execute(ctx)

    assert result.success
