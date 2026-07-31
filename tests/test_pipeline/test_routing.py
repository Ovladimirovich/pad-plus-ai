from core.pipeline.routing import PROFILES, get_profile, get_effective_hot, INDEPENDENT_GROUP
from core.pipeline import PipelineContext
import core.pipeline.phases  # noqa: F401 — triggers @register_phase decorators


class MockCtx:
    user_message: str = ""
    context: dict = {}

    def __init__(self, user_message="", context=None):
        self.user_message = user_message
        self.context = context or {}


def test_all_strategies_have_profiles():
    expected = {"simple", "retrieval", "reasoning", "creative", "reflective", "learning"}
    assert set(PROFILES.keys()) == expected


def test_simple_profile_minimal():
    p = get_profile("simple")
    assert "rag" not in p.hot
    assert "knowledge_graph" not in p.hot
    assert "episodic" not in p.hot
    assert "semantic" not in p.hot
    assert "truth_loop" not in p.hot
    assert "evaluation" not in p.hot
    assert "safety" in p.hot
    assert "intent" in p.hot
    assert "generate" in p.hot
    assert "emotion" in p.hot
    assert "impulse" in p.hot
    assert "persona" in p.hot
    assert "roots" in p.hot
    assert "response_guard" in p.hot


def test_reasoning_profile_full():
    p = get_profile("reasoning")
    assert "rag" in p.hot
    assert "knowledge_graph" in p.hot
    assert "episodic" in p.hot
    assert "semantic" in p.hot
    assert "truth_loop" in p.hot
    assert "evaluation" in p.hot


def test_unknown_strategy_falls_back_to_reasoning():
    p = get_profile("nonexistent")
    assert p.name == "reasoning"


def test_simple_background_no_heavy_phases():
    p = get_profile("simple")
    assert "persona_evolution" not in p.background
    assert "reflection" not in p.background
    assert "dreams" not in p.background
    assert "health" not in p.background
    assert "extraction" not in p.background


def test_retrieval_background_includes_heavy():
    p = get_profile("retrieval")
    assert "persona_evolution" in p.background
    assert "reflection" in p.background
    assert "dreams" in p.background
    assert "health" in p.background
    assert "extraction" in p.background


def test_retrieval_conditional_knowledge_graph():
    ctx = MockCtx(user_message="расскажи что такое квантовая физика")
    hot = get_effective_hot("retrieval", ctx)
    assert "knowledge_graph" in hot


def test_retrieval_conditional_no_knowledge_graph():
    ctx = MockCtx(user_message="привет как дела")
    hot = get_effective_hot("retrieval", ctx)
    assert "knowledge_graph" not in hot


def test_retrieval_conditional_truth_loop_with_rag():
    ctx = MockCtx(
        user_message="вопрос про историю",
        context={"sources": {"rag": {"count": 2, "confidence": 0.8}}},
    )
    hot = get_effective_hot("retrieval", ctx)
    assert "truth_loop" in hot


def test_retrieval_conditional_truth_loop_no_rag():
    ctx = MockCtx(
        user_message="вопрос",
        context={"sources": {"rag": {"count": 0, "confidence": 0.0}}},
    )
    hot = get_effective_hot("retrieval", ctx)
    assert "truth_loop" not in hot


def test_independent_group():
    assert "rag" in INDEPENDENT_GROUP
    assert "knowledge_graph" in INDEPENDENT_GROUP
    assert "episodic" in INDEPENDENT_GROUP
    assert "semantic" in INDEPENDENT_GROUP
    assert "emotion" in INDEPENDENT_GROUP


def test_profile_phases_are_registered():
    from core.pipeline.registry import get_registry
    registry = get_registry()
    all_registered = set(registry.list_names())
    for name, profile in PROFILES.items():
        for p in profile.hot:
            assert p in all_registered, f"{name}: phase '{p}' not registered"
        for p in profile.background:
            assert p in all_registered, f"{name}: bg phase '{p}' not registered"
