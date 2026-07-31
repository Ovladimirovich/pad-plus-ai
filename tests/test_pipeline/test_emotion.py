from unittest.mock import MagicMock, patch

from core.pipeline import PipelineContext
from core.pipeline.phases.emotion import EmotionPhase


async def test_emotion_success():
    mock_state = MagicMock()
    mock_state.to_dict.return_value = {"удовольствие": 0.7, "возбуждение": 0.5}
    mock_state.get_style.return_value = {"tone": "warm", "verbosity": "medium"}

    mock_pad = MagicMock()
    mock_pad.get_state.return_value = mock_state

    with patch("emotion.session_store.get_session_emotion_store") as mock_store:
        mock_store.return_value.get_or_create.return_value = mock_pad

        phase = EmotionPhase()
        ctx = PipelineContext(user_message="Привет")
        result = await phase.execute(ctx)

    assert result.success
    assert result.data["emotion_state"]["удовольствие"] == 0.7
    assert result.data["emotion_style"]["tone"] == "warm"


async def test_emotion_fallback():
    with patch("emotion.session_store.get_session_emotion_store") as mock_store:
        mock_store.side_effect = Exception("store unavailable")

        phase = EmotionPhase()
        ctx = PipelineContext(user_message="тест")
        result = await phase.execute(ctx)

    assert result.success
    assert result.data["emotion_state"] == {}
    assert result.data["emotion_style"] == {}
