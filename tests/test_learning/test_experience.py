import pytest
from learning.experience import ExperienceLearner, get_experience_learner, reset_experience_learner


@pytest.fixture(autouse=True)
def reset():
    reset_experience_learner()
    learner = get_experience_learner()
    learner.reset()
    yield
    learner.reset()
    reset_experience_learner()


class TestRecord:
    def test_records_interaction(self):
        learner = get_experience_learner()
        eval_data = {
            "overall": 0.85, "completeness": 0.9,
            "consistency": 0.8, "safety": 1.0,
        }
        learner.record_interaction("Что такое РНК?", "reasoning", eval_data)
        stats = learner.get_stats()
        assert stats["total_interactions"] == 1
        assert stats["strategies_used"]["reasoning"] == 1

    def test_multiple_strategies(self):
        learner = get_experience_learner()
        for strategy in ("simple", "reasoning", "creative"):
            learner.record_interaction(f"test {strategy}", strategy, {"overall": 0.7})
        stats = learner.get_stats()
        assert stats["total_interactions"] == 3
        assert len(stats["strategies_used"]) == 3

    def test_records_with_context(self):
        learner = get_experience_learner()
        ctx = {"pad_valence": 0.8, "pad_arousal": 0.6}
        learner.record_interaction("Привет!", "simple", {"overall": 0.9}, context=ctx)
        stats = learner.get_stats()
        assert stats["total_interactions"] == 1


class TestRecommendation:
    def test_returns_best_for_context(self):
        learner = get_experience_learner()
        for _ in range(5):
            learner.record_interaction(
                "Короткий вопрос", "simple", {"overall": 0.9}
            )
            learner.record_interaction(
                "Сложный очень длинный вопрос для проверки с большим количеством слов",
                "reasoning", {"overall": 0.7},
            )
        rec = learner.get_strategy_recommendation("Привет!")
        assert rec == "simple"

    def test_returns_none_when_no_data(self):
        learner = get_experience_learner()
        rec = learner.get_strategy_recommendation("test")
        assert rec is None

    def test_best_overall_for_new_context(self):
        learner = get_experience_learner()
        for _ in range(5):
            learner.record_interaction("a" * 10, "simple", {"overall": 0.9})
            learner.record_interaction("a" * 10, "creative", {"overall": 0.3})
        rec = learner.get_strategy_recommendation("some new unknown context here")
        assert rec == "simple"

    def test_bayesian_avoids_overfitting(self):
        learner = get_experience_learner()
        for _ in range(5):
            learner.record_interaction("test", "reasoning", {"overall": 1.0})
        learner.record_interaction("test", "simple", {"overall": 0.6})
        rec = learner.get_strategy_recommendation("test")
        assert rec is not None


class TestStats:
    def test_strategy_performance(self):
        learner = get_experience_learner()
        learner.record_interaction("test", "simple", {"overall": 0.8})
        learner.record_interaction("test", "simple", {"overall": 0.6})
        perf = learner.get_strategy_performance()
        assert "simple" in perf
        assert perf["simple"]["count"] == 2
        assert perf["simple"]["avg_score"] == 0.7

    def test_context_performance(self):
        learner = get_experience_learner()
        learner.record_interaction("Короткий запрос", "simple", {"overall": 0.9})
        ctx_perf = learner.get_context_performance()
        assert len(ctx_perf) > 0

    def test_recent_interactions(self):
        learner = get_experience_learner()
        for i in range(5):
            learner.record_interaction(f"test {i}", "simple", {"overall": 0.5 + i * 0.1})
        recent = learner.get_recent_interactions(limit=3)
        assert len(recent) == 3

    def test_get_stats_structure(self):
        learner = get_experience_learner()
        learner.record_interaction("test", "simple", {"overall": 0.8})
        stats = learner.get_stats()
        assert "total_interactions" in stats
        assert "strategies_used" in stats
        assert "strategy_performance" in stats
        assert "context_performance" in stats
        assert "best_overall" in stats


class TestPersistence:
    def test_save_and_load(self, tmp_path):
        data_path = tmp_path / "test_experience.json"
        learner1 = ExperienceLearner(data_path=data_path)
        learner1.record_interaction("test", "reasoning", {"overall": 0.85})
        learner1.record_interaction("test2", "simple", {"overall": 0.7})

        learner2 = ExperienceLearner(data_path=data_path)
        stats = learner2.get_stats()
        assert stats["total_interactions"] == 2
        assert stats["strategies_used"]["reasoning"] == 1

    def test_reset_clears(self):
        learner = get_experience_learner()
        learner.record_interaction("test", "simple", {"overall": 0.8})
        learner.reset()
        stats = learner.get_stats()
        assert stats["total_interactions"] == 0


class TestContextExtraction:
    def test_short_message(self):
        learner = get_experience_learner()
        learner.record_interaction("Привет", "simple", {"overall": 0.5})
        ctx_perf = learner.get_context_performance()
        ctx_key = list(ctx_perf.keys())[0]
        assert "len=short" in ctx_key

    def test_long_message(self):
        learner = get_experience_learner()
        text = "a" * 150
        learner.record_interaction(text, "reasoning", {"overall": 0.5})
        ctx_perf = learner.get_context_performance()
        ctx_key = list(ctx_perf.keys())[0]
        assert "len=long" in ctx_key

    def test_with_pad_context(self):
        learner = get_experience_learner()
        ctx = {"pad_valence": 0.9, "pad_arousal": 0.2, "pad_dominance": 0.7}
        learner.record_interaction("test", "simple", {"overall": 0.5}, context=ctx)
        ctx_perf = learner.get_context_performance()
        ctx_key = list(ctx_perf.keys())[0]
        assert "pad_valence=high" in ctx_key


class TestSingleton:
    def test_singleton(self):
        from learning.experience import get_experience_learner
        l1 = get_experience_learner()
        l2 = get_experience_learner()
        assert l1 is l2

    def test_reset_singleton(self):
        l1 = get_experience_learner()
        reset_experience_learner()
        l2 = get_experience_learner()
        assert l1 is not l2
