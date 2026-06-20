from unittest.mock import MagicMock, patch

import pytest

from core.strategy.event_listener import setup_strategy_listener, _on_dialog_completed


@pytest.fixture(autouse=True)
def reset_events():
    import core.events as mod
    mod._events = None
    yield
    mod._events = None


@pytest.fixture(autouse=True)
def reset_listener_flag():
    import core.strategy.event_listener as mod
    mod._listener_registered = False
    yield


@pytest.mark.asyncio
async def test_listener_registers_on_dialog_completed():
    setup_strategy_listener()
    from core.events import get_events
    events = get_events()
    assert events.dialog_completed.subscriber_count >= 1


@pytest.mark.asyncio
async def test_listener_is_idempotent():
    setup_strategy_listener()
    setup_strategy_listener()
    from core.events import get_events
    events = get_events()
    assert events.dialog_completed.subscriber_count == 1


@pytest.mark.asyncio
async def test_calls_record_outcome():
    mock_meta = MagicMock()
    mock_meta.should_adjust_strategy.return_value = "simple"

    with patch("core.strategy.event_listener.get_meta_learner", return_value=mock_meta):
        await _on_dialog_completed({
            "strategy": "reasoning",
            "result": {"success": True, "confidence": 0.85},
            "user_message": "тест",
        })

        mock_meta.record_outcome.assert_called_once_with("reasoning", {"success": True, "confidence": 0.85})


@pytest.mark.asyncio
async def test_publishes_strategy_changed_when_recommended():
    mock_meta = MagicMock()
    mock_meta.should_adjust_strategy.return_value = "simple"

    with patch("core.strategy.event_listener.get_meta_learner", return_value=mock_meta), \
         patch("core.events.get_events") as mock_get_events:
        mock_events = MagicMock()
        mock_events.strategy_changed = MagicMock()
        mock_get_events.return_value = mock_events

        await _on_dialog_completed({
            "strategy": "reasoning",
            "result": {"success": True, "confidence": 0.3},
        })

        call_data = mock_events.strategy_changed.publish.call_args[0][0]
        assert call_data["previous_strategy"] == "reasoning"
        assert call_data["recommended_strategy"] == "simple"


@pytest.mark.asyncio
async def test_does_not_publish_if_same_strategy():
    mock_meta = MagicMock()
    mock_meta.should_adjust_strategy.return_value = "reasoning"

    with patch("core.strategy.event_listener.get_meta_learner", return_value=mock_meta), \
         patch("core.events.get_events") as mock_get_events:
        mock_events = MagicMock()
        mock_events.strategy_changed = MagicMock()
        mock_get_events.return_value = mock_events

        await _on_dialog_completed({
            "strategy": "reasoning",
            "result": {"success": True, "confidence": 0.9},
        })

        mock_events.strategy_changed.publish.assert_not_called()


@pytest.mark.asyncio
async def test_handles_exception_gracefully():
    with patch("core.strategy.event_listener.get_meta_learner", side_effect=ValueError("fail")), \
         patch("core.strategy.event_listener.logger.warning") as mock_logger:
        await _on_dialog_completed({
            "strategy": "simple",
            "result": {"success": True},
        })
        mock_logger.assert_called_once()
