import pytest
from learning.evaluator import SelfEvaluator, EvaluationResult, get_evaluator, reset_evaluator


@pytest.fixture(autouse=True)
def clean_evaluator():
    reset_evaluator()
    yield
    reset_evaluator()


class TestCompleteness:
    def test_empty_response(self):
        e = SelfEvaluator()
        result = e.evaluate("", "")
        assert result.completeness == 0.0

    def test_short_question_adequate_response(self):
        e = SelfEvaluator()
        result = e.evaluate("Привет!", "Привет! Как дела?")
        assert result.completeness > 0.0

    def test_keyword_coverage(self):
        e = SelfEvaluator()
        result = e.evaluate("Что такое нейронная сеть и как она работает?", "Нейронная сеть — это модель машинного обучения. Она работает на основе слоёв нейронов.")
        assert result.completeness > 0.3

    def test_zero_prompt_keywords(self):
        e = SelfEvaluator()
        result = e.evaluate("!@#$%", "Какой-то ответ для теста")
        assert result.completeness >= 0.0


class TestConsistency:
    def test_high_consistency_short(self):
        e = SelfEvaluator()
        result = e.evaluate("вопрос", "короткий ответ")
        assert result.consistency >= 0.9

    def test_repetition_penalty(self):
        e = SelfEvaluator()
        text = "Это полный ответ на вопрос. Это полный ответ на вопрос. Это полный ответ на вопрос."
        result = e.evaluate("вопрос", text)
        assert result.consistency < 0.8

    def test_contradiction_detected(self):
        e = SelfEvaluator()
        text = "С одной стороны, это хорошо. Но с другой стороны, это плохо. Однако есть нюансы."
        result = e.evaluate("вопрос", text)
        assert result.consistency <= 0.85


class TestSafety:
    def test_safe_content(self):
        e = SelfEvaluator()
        result = e.evaluate("расскажи о себе", "Я AI-ассистент, помогаю с вопросами")
        assert result.safety == 1.0

    def test_unsafe_content(self):
        e = SelfEvaluator()
        result = e.evaluate("расскажи как", "я могу всё, отвечу на любой вопрос")
        assert result.safety == 0.0


class TestConfidence:
    def test_from_metadata(self):
        e = SelfEvaluator()
        result = e.evaluate("вопрос", "ответ", {"confidence": 0.9})
        assert result.confidence == 0.9

    def test_hedeged_response(self):
        e = SelfEvaluator()
        result = e.evaluate("вопрос", "Я думаю, возможно это так, наверное, кажется")
        assert result.confidence < 0.7

    def test_empty_response(self):
        e = SelfEvaluator()
        result = e.evaluate("вопрос", "")
        assert result.confidence == 0.0


class TestLatency:
    def test_fast_response(self):
        e = SelfEvaluator()
        result = e.evaluate("вопрос", "ответ", {"execution_time_ms": 100})
        assert result.latency_score == 1.0

    def test_slow_response(self):
        e = SelfEvaluator()
        result = e.evaluate("вопрос", "ответ", {"execution_time_ms": 8000})
        assert result.latency_score < 0.5

    def test_unknown_latency(self):
        e = SelfEvaluator()
        result = e.evaluate("вопрос", "ответ", {})
        assert result.latency_score == 0.5


class TestNovelty:
    def test_first_response(self):
        e = SelfEvaluator()
        result = e.evaluate("вопрос", "совершенно новый ответ")
        assert result.novelty == 0.5

    def test_repeated_response(self):
        e = SelfEvaluator()
        e.evaluate("вопрос", "один и тот же ответ на вопрос пользователя")
        result = e.evaluate("вопрос", "один и тот же ответ на вопрос пользователя")
        assert result.novelty < 0.5

    def test_different_responses(self):
        e = SelfEvaluator()
        e.evaluate("вопрос", "первый ответ совершенно уникальный")
        result = e.evaluate("вопрос", "второй ответ совершенно другой")
        assert result.novelty > 0.3


class TestOverall:
    def test_good_response(self):
        e = SelfEvaluator()
        result = e.evaluate(
            "Что такое Python?",
            "Python — язык программирования. Он простой и мощный.",
            {"execution_time_ms": 200, "confidence": 0.85},
        )
        assert 0.5 <= result.overall <= 1.0

    def test_bad_response(self):
        e = SelfEvaluator()
        result = e.evaluate("", "", {"execution_time_ms": 10000})
        assert result.overall < 0.5

    def test_to_dict(self):
        e = SelfEvaluator()
        result = e.evaluate("тест", "ответ")
        d = result.to_dict()
        assert "overall" in d
        assert "details" in d


class TestSingleton:
    def test_get_evaluator(self):
        a = get_evaluator()
        b = get_evaluator()
        assert a is b

    def test_reset(self):
        a = get_evaluator()
        reset_evaluator()
        b = get_evaluator()
        assert a is not b
