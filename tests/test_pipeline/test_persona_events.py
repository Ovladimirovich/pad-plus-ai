from unittest.mock import MagicMock, patch

import pytest

from core.persona.event_listener import setup_persona_listener, _on_experience_captured


@pytest.fixture(autouse=True)
def reset_events():
    import core.events as mod
    mod._events = None
    yield
    mod._events = None


@pytest.fixture(autouse=True)
def reset_listener_flag():
    import core.persona.event_listener as mod
    mod._listener_registered = False
    yield


@pytest.mark.asyncio
async def test_listener_registers():
    setup_persona_listener()
    from core.events import get_events
    events = get_events()
    assert events.experience_captured.subscriber_count == 1


@pytest.mark.asyncio
async def test_listener_is_idempotent():
    setup_persona_listener()
    setup_persona_listener()
    from core.events import get_events
    events = get_events()
    assert events.experience_captured.subscriber_count == 1


@pytest.mark.asyncio
async def test_adjusts_global_persona_traits():
    mock_persona = MagicMock()
    with patch("memory.persona.get_persona", return_value=mock_persona), \
         patch("memory.user_persona.get_user_persona_manager"):

        await _on_experience_captured({
            "dialog_id": "d1",
            "interaction_type": "praise",
            "significance": 0.8,
            "user_message": "спасибо",
            "ai_response": "пожалуйста",
        })

        assert mock_persona.adjust_trait.call_count == 2
        calls = [(c.args[0], round(c.args[1], 3)) for c in mock_persona.adjust_trait.call_args_list]
        assert ("empathy", 0.08) in calls
        assert ("openness", 0.064) in calls


@pytest.mark.asyncio
async def test_adjusts_user_persona_style():
    mock_persona = MagicMock()
    mock_up = MagicMock()

    with patch("memory.persona.get_persona", return_value=mock_persona), \
         patch("memory.user_persona.get_user_persona_manager") as mock_get_pm:
        mock_pm = MagicMock()
        mock_get_pm.return_value = mock_pm
        mock_pm.get_persona.return_value = mock_up

        await _on_experience_captured({
            "dialog_id": "d1",
            "interaction_type": "praise",
            "significance": 0.8,
            "user_id": "u1",
            "user_message": "спасибо",
            "ai_response": "пожалуйста",
        })

        mock_up.adjust_style.assert_any_call("verbosity", 0.024, reason="praise")
        mock_up.adjust_style.assert_any_call("formality", -0.016, reason="praise")
        mock_pm.save_persona.assert_called_once_with(mock_up)


@pytest.mark.asyncio
async def test_skips_low_significance():
    mock_persona = MagicMock()
    with patch("memory.persona.get_persona", return_value=mock_persona):
        await _on_experience_captured({
            "dialog_id": "d1",
            "interaction_type": "praise",
            "significance": 0.05,
        })

        mock_persona.adjust_trait.assert_not_called()


@pytest.mark.asyncio
async def test_handles_exception_gracefully():
    with patch("memory.persona.get_persona", side_effect=ValueError("fail")), \
         patch("core.persona.event_listener.logger.warning") as mock_logger:
        await _on_experience_captured({
            "dialog_id": "d1",
            "interaction_type": "praise",
            "significance": 0.5,
        })
        mock_logger.assert_called_once()
