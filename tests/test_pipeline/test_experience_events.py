from unittest.mock import MagicMock, patch, AsyncMock

import pytest

from core.events import get_events
from core.experience.listener import setup_experience_listener, _on_dialog_completed


@pytest.fixture(autouse=True)
def reset_events():
    import core.events as mod
    mod._events = None
    yield
    mod._events = None


@pytest.fixture(autouse=True)
def reset_listener_flag():
    import core.experience.listener as mod
    mod._listener_registered = False
    yield


@pytest.mark.asyncio
async def test_listener_registers_on_dialog_completed():
    setup_experience_listener()
    events = get_events()
    assert events.dialog_completed.subscriber_count == 1


@pytest.mark.asyncio
async def test_listener_is_idempotent():
    setup_experience_listener()
    setup_experience_listener()
    events = get_events()
    assert events.dialog_completed.subscriber_count == 1


@pytest.mark.asyncio
async def test_listener_calls_capture_experience():
    with patch("core.experience.listener.capture_experience") as mock_capture, \
         patch("core.events.get_events") as mock_get_events:
        mock_capture.return_value = MagicMock(
            interaction_type=MagicMock(value="new_knowledge"),
            significance=0.5,
        )

        mock_events = MagicMock()
        mock_events.experience_captured = AsyncMock()
        mock_get_events.return_value = mock_events

        await _on_dialog_completed({
            "user_message": "привет",
            "result": {
                "answer": "и тебе привет",
                "truth": {"confidence": 0.9},
                "meta": {"intent": "chat_general"},
            },
            "strategy": "simple",
            "success": True,
            "session_id": "sess-1",
        })

        mock_capture.assert_called_once()
        _, kwargs = mock_capture.call_args
        assert kwargs["dialog_id"] == "sess-1"
        assert kwargs["user_message"] == "привет"
        assert kwargs["ai_response"] == "и тебе привет"
        assert kwargs["strategy"] == "simple"
        assert kwargs["strategy_success"] == 1.0

        mock_events.experience_captured.publish.assert_called_once()
        call_data = mock_events.experience_captured.publish.call_args[0][0]
        assert call_data["dialog_id"] == "sess-1"
        assert call_data["interaction_type"] == "new_knowledge"
        assert call_data["significance"] == 0.5


@pytest.mark.asyncio
async def test_listener_handles_failed_pipeline():
    with patch("core.experience.listener.capture_experience") as mock_capture, \
         patch("core.events.get_events") as mock_get_events:
        mock_capture.return_value = MagicMock(
            interaction_type=MagicMock(value="error_recovery"),
            significance=0.7,
        )
        mock_events = MagicMock()
        mock_events.experience_captured = AsyncMock()
        mock_get_events.return_value = mock_events

        await _on_dialog_completed({
            "user_message": "сломалось",
            "result": {"answer": ""},
            "strategy": "simple",
            "success": False,
            "session_id": "sess-2",
        })

        mock_capture.assert_called_once()
        _, kwargs = mock_capture.call_args
        assert kwargs["strategy_success"] == 0.0


@pytest.mark.asyncio
async def test_listener_handles_missing_result():
    with patch("core.experience.listener.capture_experience") as mock_capture:
        mock_capture.return_value = None

        await _on_dialog_completed({
            "user_message": "тест",
            "strategy": "simple",
            "success": True,
            "session_id": "sess-3",
        })

        mock_capture.assert_called_once()


@pytest.mark.asyncio
async def test_listener_handles_exception_gracefully():
    with patch("core.experience.listener.capture_experience", side_effect=ValueError("fail")):
        with patch("core.experience.listener.logger.warning") as mock_logger:
            await _on_dialog_completed({
                "user_message": "x",
                "result": {"answer": "y"},
                "strategy": "simple",
                "success": True,
                "session_id": "s-x",
            })

            mock_logger.assert_called_once()



