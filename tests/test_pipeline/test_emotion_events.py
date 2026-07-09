from unittest.mock import MagicMock, patch

import pytest

from emotion.event_listener import setup_emotion_listener, _on_experience_captured


@pytest.fixture(autouse=True)
def reset_events():
    import core.events as mod
    mod._events = None
    yield
    mod._events = None


@pytest.fixture(autouse=True)
def reset_listener_flag():
    import emotion.event_listener as mod
    mod._listener_registered = False
    yield


@pytest.mark.asyncio
async def test_listener_registers_on_experience_captured():
    setup_emotion_listener()
    from core.events import get_events
    events = get_events()
    assert events.experience_captured.subscriber_count == 1


@pytest.mark.asyncio
async def test_listener_is_idempotent():
    setup_emotion_listener()
    setup_emotion_listener()
    from core.events import get_events
    events = get_events()
    assert events.experience_captured.subscriber_count == 1


@pytest.mark.asyncio
async def test_calls_pad_apply_event_with_mapping():
    mock_pad = MagicMock()
    with patch("emotion.event_listener.get_pad_model", return_value=mock_pad):
        await _on_experience_captured({
            "dialog_id": "d1",
            "interaction_type": "praise",
            "significance": 0.7,
            "strategy_success": 1.0,
        })

        mock_pad.apply_event.assert_called_once_with("user_praise", intensity=0.7)


@pytest.mark.asyncio
async def test_all_interaction_types_map():
    cases = [
        ("new_knowledge", "new_knowledge"),
        ("contradiction", "contradiction"),
        ("praise", "user_praise"),
        ("criticism", "user_criticism"),
        ("exploration", "new_knowledge"),
        ("error_recovery", "fallback"),
        ("repetition", "self_reflection"),
        ("unknown_type", "self_reflection"),
    ]
    for interaction_type, expected_event in cases:
        mock_pad = MagicMock()
        with patch("emotion.event_listener.get_pad_model", return_value=mock_pad):
            await _on_experience_captured({
                "dialog_id": "d1",
                "interaction_type": interaction_type,
                "significance": 0.5,
            })
            mock_pad.apply_event.assert_called_with(expected_event, intensity=0.5)


@pytest.mark.asyncio
async def test_emits_emotion_changed_to_old_event_bus():
    mock_pad = MagicMock()
    mock_pad.get_state.return_value.to_dict.return_value = {"pleasure": 0.3}

    with patch("emotion.event_listener.get_pad_model", return_value=mock_pad), \
         patch("core.event_bus.get_event_bus") as mock_get_bus:
        mock_bus = MagicMock()
        mock_get_bus.return_value = mock_bus

        await _on_experience_captured({
            "dialog_id": "d1",
            "interaction_type": "criticism",
            "significance": 0.6,
        })

        mock_bus.emit.assert_called_once()
        event_type_arg = mock_bus.emit.call_args[0][0]
        data_arg = mock_bus.emit.call_args[0][1]
        assert event_type_arg.value == "emotion.changed"
        assert data_arg["trigger"] == "user_criticism"


@pytest.mark.asyncio
async def test_handles_exception_gracefully():
    with patch("emotion.event_listener.get_pad_model", side_effect=ValueError("fail")), \
         patch("emotion.event_listener.logger.warning") as mock_logger:
        await _on_experience_captured({
            "dialog_id": "d1",
            "interaction_type": "praise",
            "significance": 0.5,
        })
        mock_logger.assert_called_once()
