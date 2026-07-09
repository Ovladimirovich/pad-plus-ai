from core.evolution.meta_learner import MetaLearner
from core.evolution.reflection import ReflectionInsight


def test_empty_insights():
    learner = MetaLearner()
    decisions = learner.decide([])
    assert decisions == []


def test_trait_decisions():
    learner = MetaLearner()
    insights = [
        ReflectionInsight(
            domain="strategy_effectiveness",
            insight="Стратегии показывают низкую эффективность",
            confidence=0.8,
            suggested_action="increase_skepticism",
            priority=0.8,
        ),
    ]
    decisions = learner.decide(insights)
    assert len(decisions) == 1
    assert decisions[0].target == "trait:skepticism"
    assert decisions[0].delta > 0


def test_multiple_trait_decisions():
    learner = MetaLearner()
    insights = [
        ReflectionInsight(
            domain="sentiment_trend",
            insight="Преобладает позитивный сентимент",
            confidence=0.7,
            suggested_action="increase_empathy",
            priority=0.7,
        ),
        ReflectionInsight(
            domain="contradiction_pattern",
            insight="Обнаружены противоречия",
            confidence=0.6,
            suggested_action="increase_humility",
            priority=0.6,
        ),
    ]
    decisions = learner.decide(insights)
    assert len(decisions) == 2
    targets = {d.target for d in decisions}
    assert "trait:empathy" in targets
    assert "trait:humility" in targets


def test_delta_scales_with_confidence():
    learner = MetaLearner()
    insights_high = [
        ReflectionInsight(
            domain="test", insight="test", confidence=1.0,
            suggested_action="increase_caution", priority=0.5,
        ),
    ]
    insights_low = [
        ReflectionInsight(
            domain="test", insight="test", confidence=0.1,
            suggested_action="increase_caution", priority=0.5,
        ),
    ]
    high_decisions = learner.decide(insights_high)
    low_decisions = learner.decide(insights_low)
    assert high_decisions[0].delta > low_decisions[0].delta


def test_duplicate_actions_deduplicated():
    learner = MetaLearner()
    insights = [
        ReflectionInsight(
            domain="test1", insight="test1", confidence=0.8,
            suggested_action="increase_empathy", priority=0.8,
        ),
        ReflectionInsight(
            domain="test2", insight="test2", confidence=0.6,
            suggested_action="increase_empathy", priority=0.6,
        ),
    ]
    decisions = learner.decide(insights)
    empathy_decisions = [d for d in decisions if d.target == "trait:empathy"]
    assert len(empathy_decisions) == 1


def test_review_strategy_contradiction():
    learner = MetaLearner()
    insights = [
        ReflectionInsight(
            domain="interaction_pattern",
            insight="Частый тип: contradiction",
            confidence=0.7,
            suggested_action="review_strategy:contradiction",
            priority=0.7,
        ),
    ]
    decisions = learner.decide(insights)
    caution_decisions = [d for d in decisions if d.target == "trait:caution"]
    assert len(caution_decisions) >= 1


def test_review_strategy_praise():
    learner = MetaLearner()
    insights = [
        ReflectionInsight(
            domain="interaction_pattern",
            insight="Частый тип: praise",
            confidence=0.7,
            suggested_action="review_strategy:praise",
            priority=0.7,
        ),
    ]
    decisions = learner.decide(insights)
    openness_decisions = [d for d in decisions if d.target == "trait:openness"]
    assert len(openness_decisions) >= 1
