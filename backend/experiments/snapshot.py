"""
SystemSnapshot — заморозка состояния системы для воспроизводимости экспериментов.

Фиксирует: pipeline config, провайдер/модель, persona traits, PAD state,
MetaLearner stats, MetaController state + метаданные.

Хранится: experiments/snapshots/{uuid}/snapshot.json
"""

import json
import logging
import os
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("padplus.experiments.snapshot")

SNAPSHOTS_DIR = Path(__file__).resolve().parent.parent.parent / "experiments" / "snapshots"


@dataclass
class SystemSnapshot:
    id: str
    timestamp: str
    label: str

    # Pipeline
    pipeline_phase_order: List[str] = field(default_factory=list)
    pipeline_phase_details: List[Dict[str, Any]] = field(default_factory=list)
    pipeline_state: str = "unknown"

    # Provider / model
    provider: str = ""
    model: str = ""

    # Emotion
    pad: Dict[str, float] = field(default_factory=dict)

    # Persona
    persona_traits: Dict[str, Any] = field(default_factory=dict)

    # Meta
    meta_controller: Dict[str, Any] = field(default_factory=dict)
    meta_learner_stats: Dict[str, Any] = field(default_factory=dict)

    # Memory
    memory_fingerprint: str = ""

    # Impulse
    impulse: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def capture_snapshot(label: str = "") -> SystemSnapshot:
    """Захватывает текущее состояние системы."""
    snapshot_id = uuid.uuid4().hex[:12]
    timestamp = datetime.now().isoformat()

    pad = {}
    persona_traits = {}
    meta_controller_state = {}
    meta_learner_stats = {}
    pipeline_phase_order = []
    pipeline_phase_details = []
    pipeline_state = "unknown"
    impulse = {}

    # Pipeline registry
    try:
        from backend.core.pipeline.registry import get_registry
        reg = get_registry()
        details = reg.list_details()
        pipeline_phase_order = [d["name"] for d in details]
        pipeline_phase_details = details
    except Exception as e:
        logger.warning("Snapshot: pipeline registry error: %s", e)

    # Pipeline state
    try:
        from backend.core.pipeline import get_pipeline
        pl = get_pipeline()
        pipeline_state = pl._state.value if hasattr(pl, "_state") and pl._state else "unknown"
    except Exception as e:
        logger.warning("Snapshot: pipeline state error: %s", e)

    # PAD model
    try:
        from backend.emotion.pad_model import get_pad_model
        pm = get_pad_model()
        if pm and pm.current:
            pad = asdict(pm.current)
    except Exception as e:
        logger.warning("Snapshot: pad model error: %s", e)

    # Persona
    try:
        from backend.memory.persona import get_persona
        p = get_persona()
        if p:
            persona_traits = {
                t.name: {"value": t.value, "stability": t.stability, "description": t.description}
                for t in p._traits.values()
            } if hasattr(p, "_traits") else {}
    except Exception as e:
        logger.warning("Snapshot: persona error: %s", e)

    # Meta controller
    try:
        from backend.core.meta_controller import get_meta_controller
        mc = get_meta_controller()
        meta_controller_state = mc.get_stats()
    except Exception as e:
        logger.warning("Snapshot: meta controller error: %s", e)

    # Meta learner
    try:
        from backend.core.xray.meta_learner import get_meta_learner
        ml = get_meta_learner()
        meta_learner_stats = ml.get_all_stats() if hasattr(ml, "get_all_stats") else {}
    except Exception as e:
        logger.warning("Snapshot: meta learner error: %s", e)

    # Impulse
    try:
        from backend.core.impulse.manager import get_impulse_manager
        im = get_impulse_manager()
        if im and hasattr(im, "get_current"):
            impulse = im.get_current()
    except Exception as e:
        logger.warning("Snapshot: impulse error: %s", e)

    snapshot = SystemSnapshot(
        id=snapshot_id,
        timestamp=timestamp,
        label=label or f"snapshot-{snapshot_id[:8]}",
        pipeline_phase_order=pipeline_phase_order,
        pipeline_phase_details=pipeline_phase_details,
        pipeline_state=pipeline_state,
        pad=pad,
        persona_traits=persona_traits,
        meta_controller=meta_controller_state,
        meta_learner_stats=meta_learner_stats,
        impulse=impulse,
    )

    _save(snapshot)
    return snapshot


def _save(snapshot: SystemSnapshot) -> Path:
    """Сохраняет снэпшот на диск."""
    out = SNAPSHOTS_DIR / snapshot.id
    out.mkdir(parents=True, exist_ok=True)
    path = out / "snapshot.json"
    path.write_text(
        json.dumps(snapshot.to_dict(), ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )
    logger.info("Snapshot saved: %s", path)
    return path


def load_snapshot(snapshot_id: str) -> Optional[SystemSnapshot]:
    """Загружает снэпшот по ID."""
    path = SNAPSHOTS_DIR / snapshot_id / "snapshot.json"
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return SystemSnapshot(**data)
    except Exception as e:
        logger.error("Failed to load snapshot %s: %s", snapshot_id, e)
        return None


def list_snapshots(limit: int = 50) -> List[Dict[str, Any]]:
    """Список снэпшотов (метаданные, без полных данных)."""
    if not SNAPSHOTS_DIR.exists():
        return []
    snapshots = []
    for d in sorted(SNAPSHOTS_DIR.iterdir(), reverse=True):
        if not d.is_dir():
            continue
        path = d / "snapshot.json"
        if not path.exists():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            ts = data.get("timestamp", "")
            decision_count = _count_decisions_since(ts)
            snapshots.append({
                "id": data.get("id", d.name),
                "timestamp": ts,
                "label": data.get("label", d.name),
                "pipeline_state": data.get("pipeline_state", ""),
                "provider": data.get("provider", ""),
                "model": data.get("model", ""),
                "phase_count": len(data.get("pipeline_phase_order", [])),
                "decision_count": decision_count,
            })
        except Exception:
            continue
        if len(snapshots) >= limit:
            break
    return snapshots


def _count_decisions_since(snapshot_timestamp: str) -> int:
    """Считает количество решений, записанных после снэпшота."""
    try:
        from datetime import datetime as _dt
        from backend.core.decisions import get_decision_recorder
        snap_ts = _dt.fromisoformat(snapshot_timestamp).timestamp()
        recs = get_decision_recorder().query(since=snap_ts, limit=10000)
        return len(recs)
    except Exception:
        return 0


def get_snapshot_decisions(snapshot_id: str, limit: int = 100) -> List[Dict[str, Any]]:
    """Решения Decision Log, записанные после снэпшота (для кросс-ссылки)."""
    snap = load_snapshot(snapshot_id)
    if not snap:
        return []
    try:
        from datetime import datetime as _dt
        from backend.core.decisions import get_decision_recorder
        snap_ts = _dt.fromisoformat(snap.timestamp).timestamp()
        recs = get_decision_recorder().query(since=snap_ts, limit=limit)
        return [r.to_dict() for r in recs]
    except Exception:
        return []
