from unittest.mock import MagicMock, patch

from core.pipeline import PipelineContext
from core.pipeline.phases.emotion_update import EmotionUpdatePhase


async def test_emotion_update_success():
    mock_pad = MagicMock()

    with patch("emotion.session_store.get_session_emotion_store") as mock_store:
        mock_store.return_value.get_or_create.return_value = mock_pad

        phase = EmotionUpdatePhase()
        ctx = PipelineContext(
            user_message="расскажи подробнее про квантовую физику",
            context={"response": "квантовая физика изучает микромир"},
        )
        result = await phase.execute(ctx)

    assert result.success
    mock_pad.apply_event.assert_called_once_with("new_knowledge", 0.2)


async def test_emotion_update_error():
    with patch("emotion.session_store.get_session_emotion_store") as mock_store:
        mock_store.side_effect = Exception("store unavailable")

        phase = EmotionUpdatePhase()
        ctx = PipelineContext(user_message="тест", context={})
        result = await phase.execute(ctx)

    assert result.success
