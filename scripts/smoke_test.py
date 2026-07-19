"""
Smoke test — быстрая проверка, что проект работает.

Использование:
    python scripts/smoke_test.py
"""

import importlib
import logging
import os
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger("padplus.smoke")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

os.environ.setdefault("USE_PG_STORAGE", "false")

CHECKS = []


def check(name: str):
    def decorator(fn):
        CHECKS.append((name, fn))
        return fn
    return decorator


@check("Core config loads")
def test_config():
    from backend.core.config import USE_PG_STORAGE
    assert USE_PG_STORAGE is False


@check("Pipeline imports")
def test_pipeline():
    from backend.core.pipeline import get_pipeline
    p = get_pipeline()
    assert p is not None
    assert len(p._phases) >= 10


@check("PAD model loads")
def test_emotion():
    from backend.emotion.pad_model import get_pad_model
    m = get_pad_model()
    state = m.get_state()
    assert -1 <= state.pleasure <= 1
    assert -1 <= state.arousal <= 1


@check("Memory interfaces")
def test_memory():
    from backend.memory.base import MemoryInterface
    assert MemoryInterface is not None


@check("X-Ray tracer loads")
def test_xray():
    from backend.core.xray import get_xray_tracer, get_trace_collector, get_xray_history
    assert get_xray_tracer() is not None
    assert get_trace_collector() is not None
    assert get_xray_history() is not None


@check("X-Ray history persistence (SQLite)")
def test_xray_persistence():
    import tempfile
    from backend.core.xray.history_recorder import XRayHistory

    tmp = tempfile.mktemp(suffix=".db")

    try:
        h = XRayHistory(db_path=tmp)
        h.add_trace({
            "id": "test-trace",
            "user_message": "hello",
            "response": "world",
            "model": "test",
            "provider": "test",
            "thinking_mode": "",
            "total_ms": 100,
            "success": True,
            "timestamp": "2026-01-01T00:00:00",
            "spans": [],
        })
        loaded = h.get_trace("test-trace")
        assert loaded is not None
        assert loaded["user_message"] == "hello"

        sessions = h.list_sessions(limit=10)
        assert len(sessions) >= 1
    finally:
        try:
            os.unlink(tmp)
        except PermissionError:
            pass


@check("Experiment analysis module")
def test_analysis():
    from experiments.analysis import (
        ExperimentReport, ExperimentResult,
        analyze_keywords, compare_profiles, generate_report_md,
    )
    report = ExperimentReport(
        name="test", description="test",
        timestamp="now", provider="test", model="test",
        profiles_used=["baseline"],
    )
    report.results.append(ExperimentResult(
        profile="baseline", question_id="Q1",
        question="test", response="test response",
        success=True,
    ))
    assert len(report.results) == 1


@check("Experiment runner imports")
def test_runner():
    from experiments.runner import load_config, save_results, run_experiment
    assert callable(load_config)
    assert callable(run_experiment)


@check("Evals module")
def test_evals():
    from backend.evals import QualityEvaluator, RunComparison, compare_runs
    comp = compare_runs(
        {"success": True, "total_ms": 100, "response": "a", "confidence": 0.5},
        {"success": True, "total_ms": 80, "response": "b", "confidence": 0.7},
    )
    assert "latency_ms" in comp.metrics
    assert comp.metrics["latency_ms"]["delta"] == -20.0


@check("PhaseRegistry")
def test_registry():
    from backend.core.pipeline.registry import get_registry, register_phase
    reg = get_registry()
    names = reg.list_names()
    assert "safety" in names
    assert "generate" in names
    assert "response_guard" in names
    assert len(names) >= 25


@check("Module contracts (Protocols)")
def test_protocols():
    from backend.core.pipeline.base import (
        VerificationModule, EmotionStateProvider,
        PersonaProvider, TraceCollectorProtocol,
    )
    assert VerificationModule is not None
    assert EmotionStateProvider is not None


def main():
    passed = 0
    failed = 0

    for name, fn in CHECKS:
        try:
            fn()
            logger.info(f"  ✅ {name}")
            passed += 1
        except Exception as e:
            logger.error(f"  ❌ {name}: {e}")
            failed += 1

    logger.info("─" * 40)
    logger.info(f"Passed: {passed}, Failed: {failed}")
    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
