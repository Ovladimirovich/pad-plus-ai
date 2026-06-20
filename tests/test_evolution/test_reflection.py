from core.evolution.reflection import ReflectionEngine


def _make_exp(
    interaction_type: str = "exploration",
    strategy_success: float = 0.5,
    sentiment: str = "neutral",
    contradiction: bool = False,
    repetition: bool = False,
) -> dict:
    return {
        "interaction_type": interaction_type,
        "strategy_success": strategy_success,
        "signals": {
            "sentiment": sentiment,
            "contradiction_detected": contradiction,
            "is_repetition": repetition,
        },
    }


def test_empty_experiences():
    engine = ReflectionEngine()
    insights = engine.reflect([])
    assert insights == []


def test_dominant_interaction_type():
    engine = ReflectionEngine()
    exps = [_make_exp(interaction_type="praise") for _ in range(15)]
    exps += [_make_exp(interaction_type="exploration") for _ in range(5)]
    insights = engine.reflect(exps)
    interaction_insights = [i for i in insights if i.domain == "interaction_pattern"]
    assert len(interaction_insights) >= 1
    praise_insights = [i for i in interaction_insights if "praise" in i.insight]
    assert len(praise_insights) >= 1


def test_low_strategy_effectiveness():
    engine = ReflectionEngine()
    exps = [_make_exp(strategy_success=0.1) for _ in range(20)]
    insights = engine.reflect(exps)
    strategy_insights = [i for i in insights if i.domain == "strategy_effectiveness"]
    assert len(strategy_insights) >= 1
    assert "низкую" in strategy_insights[0].insight
    assert strategy_insights[0].suggested_action == "increase_skepticism"


def test_high_strategy_effectiveness():
    engine = ReflectionEngine()
    exps = [_make_exp(strategy_success=0.9) for _ in range(20)]
    insights = engine.reflect(exps)
    strategy_insights = [i for i in insights if i.domain == "strategy_effectiveness"]
    assert len(strategy_insights) >= 1
    assert "высокую" in strategy_insights[0].insight
    assert strategy_insights[0].suggested_action == "increase_curiosity"


def test_positive_sentiment():
    engine = ReflectionEngine()
    exps = [_make_exp(sentiment="positive") for _ in range(15)]
    exps += [_make_exp(sentiment="neutral") for _ in range(10)]
    insights = engine.reflect(exps)
    sentiment_insights = [i for i in insights if i.domain == "sentiment_trend"]
    assert len(sentiment_insights) >= 1
    assert "позитивный" in sentiment_insights[0].insight


def test_negative_sentiment():
    engine = ReflectionEngine()
    exps = [_make_exp(sentiment="negative") for _ in range(10)]
    exps += [_make_exp(sentiment="neutral") for _ in range(20)]
    insights = engine.reflect(exps)
    sentiment_insights = [i for i in insights if i.domain == "sentiment_trend"]
    negative_insights = [i for i in sentiment_insights if "негативный" in i.insight]
    assert len(negative_insights) >= 1


def test_contradictions():
    engine = ReflectionEngine()
    exps = [_make_exp(contradiction=True) for _ in range(5)]
    exps += [_make_exp(contradiction=False) for _ in range(25)]
    insights = engine.reflect(exps)
    contradiction_insights = [i for i in insights if i.domain == "contradiction_pattern"]
    assert len(contradiction_insights) >= 1


def test_repetitions():
    engine = ReflectionEngine()
    exps = [_make_exp(repetition=True) for _ in range(6)]
    exps += [_make_exp(repetition=False) for _ in range(24)]
    insights = engine.reflect(exps)
    repetition_insights = [i for i in insights if i.domain == "repetition_pattern"]
    assert len(repetition_insights) >= 1
