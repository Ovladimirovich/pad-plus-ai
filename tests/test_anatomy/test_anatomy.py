"""Тесты Living Anatomy (backend)."""

import os

os.environ.setdefault("TEST_MODE", "true")
os.environ.setdefault("USE_PG_STORAGE", "false")

from core.anatomy import get_module_detail, get_module_status


def test_anatomy_root_structure():
    data = get_module_status()
    assert "brain" in data
    assert "timestamp" in data
    brain = data["brain"]
    assert brain["label"] == "Brain"
    assert "children" in brain
    assert len(brain["children"]) == 11


def test_anatomy_modules_present():
    data = get_module_status()
    children = data["brain"]["children"]
    for key in ["memory", "reasoning", "identity", "emotion", "reflection",
                "dreams", "truth", "safety", "healer", "research", "xray"]:
        assert key in children
        assert "status" in children[key]
        assert "metrics" in children[key]


def test_anatomy_memory_children():
    data = get_module_status()
    memory = data["brain"]["children"]["memory"]
    assert "children" in memory


def test_anatomy_module_detail_brain():
    detail = get_module_detail("brain")
    assert detail["label"] == "Brain"


def test_anatomy_module_detail_child():
    detail = get_module_detail("emotion")
    assert detail["label"] == "Emotion"
    assert "metrics" in detail


def test_anatomy_module_detail_has_component():
    detail = get_module_detail("reasoning")
    assert "component" in detail
    assert detail["component"] == "strategy_selector"
    assert "decision_count" in detail


def test_anatomy_module_detail_brain_no_component():
    detail = get_module_detail("brain")
    assert detail["label"] == "Brain"
    assert "component" in detail


def test_anatomy_module_detail_not_found():
    assert get_module_detail("nonexistent") is None
