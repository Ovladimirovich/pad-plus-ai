from unittest.mock import MagicMock

from core.evolution.constitution import Constitution
from core.evolution.meta_learner import EvolutionDecision


def _make_persona():
    p = MagicMock()
    p.traits = {}
    p.style_preferences = {
        "verbosity": 0.5,
        "formality": 0.3,
        "emotional_expressiveness": 0.6,
    }
    return p


def test_empty_decisions():
    constitution = Constitution()
    persona = _make_persona()
    result = constitution.execute([], persona)
    assert result == []


def test_trait_adjustment():
    constitution = Constitution()
    persona = _make_persona()

    def get_trait(name):
        if name == "skepticism":
            trait = MagicMock()
            trait.value = 0.5
            return trait
        return None

    persona.get_trait.side_effect = get_trait

    decisions = [
        EvolutionDecision(
            target="trait:skepticism",
            delta=0.03,
            reason="need more skepticism",
            confidence=0.8,
        ),
    ]

    result = constitution.execute(decisions, persona)
    assert len(result) == 1
    assert result[0]["target"] == "trait:skepticism"
    persona.adjust_trait.assert_called_once()


def test_trait_bounds():
    constitution = Constitution()
    persona = _make_persona()

    def get_trait(name):
        if name == "skepticism":
            trait = MagicMock()
            trait.value = 0.99
            return trait
        return None

    persona.get_trait.side_effect = get_trait

    decisions = [
        EvolutionDecision(
            target="trait:skepticism",
            delta=1.0,
            reason="max skepticism",
            confidence=1.0,
        ),
    ]

    new_val, actual_delta = constitution.apply_trait(0.99, 1.0, "skepticism")
    assert new_val <= 1.0
    assert abs(actual_delta) <= 0.1


def test_style_adjustment():
    constitution = Constitution()
    persona = _make_persona()

    decisions = [
        EvolutionDecision(
            target="style:verbosity",
            delta=0.05,
            reason="more detail needed",
            confidence=0.7,
        ),
    ]

    result = constitution.execute(decisions, persona)
    assert len(result) == 1
    assert result[0]["target"] == "style:verbosity"


def test_style_bounds():
    constitution = Constitution()
    persona = _make_persona()

    new_val, actual_delta = constitution.apply_style(0.05, -0.5, "verbosity")
    assert new_val >= 0.1
    assert actual_delta != -0.5


def test_unknown_trait_skipped():
    constitution = Constitution()
    persona = _make_persona()
    persona.get_trait.return_value = None

    decisions = [
        EvolutionDecision(
            target="trait:unknown_trait",
            delta=0.03,
            reason="test",
            confidence=0.5,
        ),
    ]

    result = constitution.execute(decisions, persona)
    assert result == []


def test_unknown_target_skipped():
    constitution = Constitution()
    persona = _make_persona()

    decisions = [
        EvolutionDecision(
            target="unknown:target",
            delta=0.03,
            reason="test",
            confidence=0.5,
        ),
    ]

    result = constitution.execute(decisions, persona)
    assert result == []
