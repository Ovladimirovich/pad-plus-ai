"""Тесты cross-integration (Фаза 4): Snapshot ↔ Decision Log."""

import os

os.environ.setdefault("TEST_MODE", "true")
os.environ.setdefault("USE_PG_STORAGE", "false")

from experiments.snapshot import capture_snapshot, get_snapshot_decisions
from core.decisions import get_decision_recorder


def test_snapshot_decision_count_field():
    snaps = __import__("experiments.snapshot", fromlist=["list_snapshots"]).list_snapshots(limit=5)
    assert len(snaps) >= 1
    assert "decision_count" in snaps[0]


def test_snapshot_decisions_returns_list():
    snap = capture_snapshot("cross_test")
    decisions = get_snapshot_decisions(snap.id)
    assert isinstance(decisions, list)


def test_decision_recorded_after_snapshot_counts():
    snap = capture_snapshot("cross_count_test")
    rec = get_decision_recorder()
    rec.record(
        component="provider_selector",
        decision_type="provider_selection",
        selected="openrouter",
        confidence=0.8,
        reason="test",
    )
    decisions = get_snapshot_decisions(snap.id)
    assert len(decisions) >= 1
    assert any(d["component"] == "provider_selector" for d in decisions)
