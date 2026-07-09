from unittest.mock import MagicMock, patch, PropertyMock

import pytest

from emotion.emotion_learner import EmotionLearner, get_emotion_learner


@pytest.fixture(autouse=True)
def reset_learner():
    # Reset singleton for each test
    import emotion.emotion_learner as mod
    mod._emotion_learner = None
    yield
    mod._emotion_learner = None


class TestEmotionLearner:
    def test_analyze_praise(self):
        learner = EmotionLearner()
        result = learner.analyze_sentiment("ты лучший, спасибо!", "пожалуйста")
        assert result["event"] == "user_praise"
        assert result["intensity"] > 0

    def test_analyze_criticism(self):
        learner = EmotionLearner()
        result = learner.analyze_sentiment("ты не прав, это ерунда", "извините")
        assert result["event"] == "user_criticism"
        assert result["intensity"] > 0

    def test_analyze_error(self):
        learner = EmotionLearner()
        result = learner.analyze_sentiment("объясни", "произошла ошибка")
        assert result["event"] == "fallback"

    def test_analyze_new_knowledge(self):
        learner = EmotionLearner()
        result = learner.analyze_sentiment("расскажи подробнее про квантовую физику", "квантовая физика изучает...")
        assert result["event"] == "new_knowledge"
        assert result["intensity"] > 0

    def test_analyze_self_reflection(self):
        learner = EmotionLearner()
        result = learner.analyze_sentiment("да", "хорошо")
        assert result["event"] == "self_reflection"

    def test_learn_from_dialog_tracks_history(self):
        learner = EmotionLearner()
        learner.learn_from_dialog("ты лучший, спасибо!", "пожалуйста")
        assert len(learner._dialog_history) == 1
        assert learner._dialog_history[0]["event"] == "user_praise"

    def test_learn_from_dialog_caps_history(self):
        learner = EmotionLearner()
        for i in range(150):
            learner.learn_from_dialog(f"msg {i}", "ok")
        assert len(learner._dialog_history) == 100

    def test_get_stats(self):
        learner = EmotionLearner()
        stats = learner.get_stats()
        assert stats["total_dialogs_analyzed"] == 0
        assert stats["event_distribution"] == {}

        learner.learn_from_dialog("спасибо!", "ok")
        learner.learn_from_dialog("плохо", "извините")
        stats = learner.get_stats()
        assert stats["total_dialogs_analyzed"] == 2

    def test_learn_from_history_empty(self):
        with patch("memory.get_rag") as mock_rag:
            mock_rag.return_value.get_recent.return_value = []
            learner = EmotionLearner()
            count = learner.learn_from_history()
            assert count == 0

    def test_learn_from_history_with_data(self):
        with patch("memory.get_rag") as mock_rag, \
             patch("emotion.pad_model.get_pad_model") as mock_pad:
            mock_pad_instance = MagicMock()
            mock_pad.return_value = mock_pad_instance
            mock_rag.return_value.get_recent.return_value = [
                {
                    "metadata": {"user_message": "спасибо!", "ai_response": "пожалуйста"},
                    "timestamp": "2026-01-01T00:00:00",
                },
                {
                    "metadata": {"user_message": "плохо", "ai_response": "извините"},
                    "timestamp": "2026-01-01T00:00:01",
                },
            ]
            learner = EmotionLearner()
            count = learner.learn_from_history()
            assert count == 2
            assert mock_pad_instance.apply_event.call_count == 2
            mock_pad_instance.save.assert_called_once()

    def test_singleton(self):
        a = get_emotion_learner()
        b = get_emotion_learner()
        assert a is b
