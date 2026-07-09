import pytest
from learning.active import ActiveLearningPolicy, get_active_policy, reset_active_policy


@pytest.fixture(autouse=True)
def reset():
    reset_active_policy()
    yield
    reset_active_policy()


class TestShouldAsk:
    def test_short_response_skipped(self):
        policy = get_active_policy()
        evaluation = {"confidence": 0.2, "novelty": 0.8}
        result = policy.should_ask_feedback(evaluation, response="OK")
        assert result is False

    def test_high_confidence_skipped(self):
        policy = get_active_policy()
        evaluation = {"confidence": 0.8, "novelty": 0.8}
        result = policy.should_ask_feedback(
            evaluation,
            response="Длинный ответ с информацией по теме вопроса"
        )
        assert result is False

    def test_low_novelty_skipped(self):
        policy = get_active_policy()
        evaluation = {"confidence": 0.2, "novelty": 0.1}
        result = policy.should_ask_feedback(
            evaluation,
            response="Длинный ответ с информацией по теме вопроса"
        )
        assert result is False

    def test_triggers_ask(self):
        policy = get_active_policy()
        evaluation = {"confidence": 0.3, "novelty": 0.7}
        result = policy.should_ask_feedback(
            evaluation,
            response="Длинный ответ с информацией по теме вопроса с достаточным количеством слов"
        )
        assert result is True

    def test_min_dialogs_respected(self):
        policy = get_active_policy()
        evaluation = {"confidence": 0.3, "novelty": 0.7}
        response = "Длинный ответ с информацией по теме вопроса с достаточным количеством слов"
        assert policy.should_ask_feedback(evaluation, response) is True
        assert policy.should_ask_feedback(evaluation, response) is False
        assert policy.should_ask_feedback(evaluation, response) is False
        assert policy.should_ask_feedback(evaluation, response) is False

    def test_resets_after_ask(self):
        policy = get_active_policy()
        evaluation = {"confidence": 0.3, "novelty": 0.7}
        response = "Длинный ответ с информацией по теме вопроса с достаточным количеством слов"
        policy.should_ask_feedback(evaluation, response)
        state = policy.get_policy_state()
        assert state["dialogs_since_last_ask"] == 0
        assert state["total_asks"] == 1


class TestPolicyState:
    def test_default_state(self):
        policy = get_active_policy()
        state = policy.get_policy_state()
        assert state["confidence_threshold"] == 0.4
        assert state["novelty_threshold"] == 0.3
        assert state["min_dialogs_between"] == 3
        assert state["total_asks"] == 0
        assert state["dialogs_since_last_ask"] == 3

    def test_state_updates_after_ask(self):
        policy = get_active_policy()
        evaluation = {"confidence": 0.2, "novelty": 0.9}
        policy.should_ask_feedback(
            evaluation,
            response="Длинный ответ с информацией по теме вопроса который превышает порог"
        )
        state = policy.get_policy_state()
        assert state["total_asks"] == 1
        assert state["dialogs_since_last_ask"] == 0
        assert state["last_ask_time"] is not None

    def test_reset(self):
        policy = get_active_policy()
        evaluation = {"confidence": 0.2, "novelty": 0.9}
        policy.should_ask_feedback(
            evaluation,
            response="Длинный ответ с информацией по теме вопроса который превышает порог"
        )
        policy.reset()
        state = policy.get_policy_state()
        assert state["total_asks"] == 0
        assert state["dialogs_since_last_ask"] == 3
        assert state["last_ask_time"] is None


class TestCustomThreshold:
    def test_custom_confidence_threshold(self):
        policy = ActiveLearningPolicy(confidence_threshold=0.6)
        evaluation = {"confidence": 0.5, "novelty": 0.8}
        result = policy.should_ask_feedback(
            evaluation,
            response="Длинный ответ с информацией по теме для проверки работы порогов уверенности"
        )
        assert result is True

    def test_custom_novelty_threshold(self):
        policy = ActiveLearningPolicy(novelty_threshold=0.5)
        evaluation = {"confidence": 0.2, "novelty": 0.4}
        result = policy.should_ask_feedback(
            evaluation,
            response="Длинный ответ с информацией по теме для проверки работы порогов новизны"
        )
        assert result is False


class TestSingleton:
    def test_singleton(self):
        p1 = get_active_policy()
        p2 = get_active_policy()
        assert p1 is p2

    def test_reset_singleton(self):
        p1 = get_active_policy()
        reset_active_policy()
        p2 = get_active_policy()
        assert p1 is not p2
