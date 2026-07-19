"""Тесты для системы снэпшотов экспериментов."""

import sys
import os
import tempfile
import shutil

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.experiments.snapshot import (
    SystemSnapshot,
    capture_snapshot,
    load_snapshot,
    list_snapshots,
    _save,
)


def test_snapshot_dataclass():
    snap = SystemSnapshot(
        id="abc123",
        timestamp="2024-01-01T00:00:00",
        label="test",
        pipeline_phase_order=["safety", "intent", "generate"],
        pad={"pleasure": 0.5, "arousal": 0.3, "dominance": 0.1},
    )
    d = snap.to_dict()
    assert d["id"] == "abc123"
    assert d["pipeline_phase_order"] == ["safety", "intent", "generate"]
    assert d["pad"]["pleasure"] == 0.5


def test_save_and_load():
    snap = SystemSnapshot(
        id="test-save-1",
        timestamp="2024-01-01T00:00:00",
        label="save test",
        pipeline_phase_order=["safety"],
    )
    path = _save(snap)
    assert path.exists()

    loaded = load_snapshot("test-save-1")
    assert loaded is not None
    assert loaded.id == "test-save-1"
    assert loaded.pipeline_phase_order == ["safety"]


def test_load_missing():
    loaded = load_snapshot("nonexistent-id-xyz")
    assert loaded is None


def test_capture_snapshot():
    snap = capture_snapshot(label="integration test snapshot")
    assert snap.id
    assert snap.timestamp
    loaded = load_snapshot(snap.id)
    assert loaded is not None
    assert loaded.label == "integration test snapshot"


def test_list_snapshots():
    snaps = list_snapshots(limit=10)
    assert isinstance(snaps, list)
    assert len(snaps) > 0
    assert "id" in snaps[0]
    assert "timestamp" in snaps[0]
