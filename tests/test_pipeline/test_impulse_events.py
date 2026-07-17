from unittest.mock import MagicMock, patch

import pytest

from core.impulse.event_listener import setup_impulse_listener, _on_experience_captured


@pytest.fixture(autouse=True)
def reset_events():
    import core.events as mod

    mod._events = None
    yield
    mod._events = None


@pytest.fixture(autouse=True)
def reset_listener_flag():
    import core.impulse.event_listener as mod

    mod._listener_registered = False
    yield


@pytest.mark.asyncio
async def test_listener_registers():
    setup_impulse_listener()
    from core.events import get_events

    events = get_events()
    assert events.experience_captured.subscriber_count == 1


@pytest.mark.asyncio
async def test_listener_is_idempotent():
    setup_impulse_listener()
    setup_impulse_listener()
    from core.events import get_events

    events = get_events()
    assert events.experience_captured.subscriber_count == 1


@pytest.mark.asyncio
async def test_listener_does_not_write_by_default():
    """V1 single writer: listener observe-only unless IMPULSE_LISTENER_WRITE=true."""
    mock_core = MagicMock()
    mock_manager = MagicMock()

    with patch("core.impulse.event_listener._LISTENER_WRITE", False), patch(
        "core.impulse.manager.get_impulse_core", return_value=mock_core
    ), patch("core.impulse.manager.get_manager", return_value=mock_manager):
        await _on_experience_captured(
            {
                "dialog_id": "d1",
                "interaction_type": "criticism",
                "significance": 0.7,
            }
        )

        mock_core.get_primary_label.assert_not_called()
        mock_manager.save.assert_not_called()


@pytest.mark.asyncio
async def test_applies_impulse_deltas_when_write_enabled():
    mock_core = MagicMock()
    mock_core.get_primary_label.return_value = "understand"
    dim_understand = MagicMock()
    dim_understand.label = "understand"
    dim_understand.weight = 0.5
    dim_improve = MagicMock()
    dim_improve.label = "improve"
    dim_improve.weight = 0.3
    mock_core.dimensions = [dim_understand, dim_improve]
    mock_manager = MagicMock()

    with patch("core.impulse.event_listener._LISTENER_WRITE", True), patch(
        "core.impulse.manager.get_impulse_core", return_value=mock_core
    ), patch("core.impulse.manager.get_manager", return_value=mock_manager):
        await _on_experience_captured(
            {
                "dialog_id": "d1",
                "interaction_type": "criticism",
                "significance": 0.7,
                "strategy_success": 0.0,
            }
        )

        assert dim_improve.weight == pytest.approx(0.3 + 0.20 * 0.7)
        mock_manager.save.assert_called_once_with(mock_core)


@pytest.mark.asyncio
async def test_skips_low_significance_when_write_enabled():
    mock_core = MagicMock()
    with patch("core.impulse.event_listener._LISTENER_WRITE", True), patch(
        "core.impulse.manager.get_impulse_core", return_value=mock_core
    ), patch("core.impulse.manager.get_manager"):
        await _on_experience_captured(
            {
                "dialog_id": "d1",
                "interaction_type": "praise",
                "significance": 0.1,
            }
        )

        mock_core.get_primary_label.assert_not_called()


@pytest.mark.asyncio
async def test_skips_unknown_type_when_write_enabled():
    mock_core = MagicMock()
    with patch("core.impulse.event_listener._LISTENER_WRITE", True), patch(
        "core.impulse.manager.get_impulse_core", return_value=mock_core
    ), patch("core.impulse.manager.get_manager"):
        await _on_experience_captured(
            {
                "dialog_id": "d1",
                "interaction_type": "unknown",
                "significance": 0.5,
            }
        )

        mock_core.get_primary_label.assert_not_called()


@pytest.mark.asyncio
async def test_handles_exception_gracefully_when_write_enabled():
    with patch("core.impulse.event_listener._LISTENER_WRITE", True), patch(
        "core.impulse.manager.get_impulse_core", side_effect=ValueError("fail")
    ), patch("core.impulse.event_listener.logger.warning") as mock_logger:
        await _on_experience_captured(
            {
                "dialog_id": "d1",
                "interaction_type": "praise",
                "significance": 0.5,
            }
        )
        mock_logger.assert_called_once()
