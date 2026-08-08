"""
Тест на изоляцию Impulse Core между сессиями (Phase C3).
Проверяет, что изменение веса/импульса в сессии А не влияет на состояние сессии Б.
"""

import pytest
from core.impulse.session_store import get_session_impulse_store, reset_impulse_store
from core.impulse import apply_deltas


@pytest.fixture(autouse=True)
def clean_store():
    reset_impulse_store()
    yield
    reset_impulse_store()


def test_impulse_session_isolation():
    store = get_session_impulse_store()

    core_a = store.get_or_create("session-A")
    core_b = store.get_or_create("session-B")

    # Начальное состояние одинаково
    label_a_before = core_a.get_primary_label()
    label_b_before = core_b.get_primary_label()
    assert label_a_before == label_b_before

    # Применяем дельты только к сессии А
    apply_deltas(core_a, "deep_insight", 0.99)
    label_a_after = core_a.get_primary_label()
    label_b_after = core_b.get_primary_label()

    # Сессия А должна измениться, сессия Б должна остаться неизменной
    assert store.get_or_create("session-A").get_primary_label() == label_a_after
    assert store.get_or_create("session-B").get_primary_label() == label_b_before
