# 06_trace_model.md — Memory Trace Model (X-Ray Extension)

**Phase:** 1 — Trace Model Design  
**Status:** Draft  
**Based on:** 01–05, 07_metrics.md, 07_adr.md

---

## Purpose

Определить **MemoryEvent** — новый тип события в X-Ray для полной наблюдаемости памяти.

---

## Architecture

```
X-Ray
├── Pipeline Trace (existing)
├── Cognitive Trace (existing)
├── Session Trace (existing)
├── Memory Trace   ← NEW MODULE
│   ├── MemoryEvent
│   ├── MemoryTraceService
│   └── MemoryEventHandler
├── Replay
└── History
```

---

## MemoryEvent Schema

```python
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Literal, Optional
from uuid import uuid4


class MemoryOperation(str, Enum):
    """Тип операции над памятью"""
    READ = "READ"
    WRITE = "WRITE"
    DELETE = "DELETE"
    DECAY = "DECAY"
    CONSOLIDATE = "CONSOLIDATE"
    MERGE = "MERGE"
    VERIFY = "VERIFY"
    SUMMARIZE = "SUMMARIZE"
    RECALL = "RECALL"
    REINDEX = "REINDEX"
    RESTORE = "RESTORE"
    CONFLICT = "CONFLICT"
    INVALIDATE = "INVALIDATE"
    EVICT = "EVICT"
    BACKUP = "BACKUP"
    RESTORE = "RESTORE"
    SNAPSHOT = "SNAPSHOT"


class MemoryResult(str, Enum):
    """Результат операции"""
    FOUND = "FOUND"
    NOT_FOUND = "NOT_FOUND"
    CREATED = "CREATED"
    UPDATED = "UPDATED"
    DELETED = "DELETED"
    MERGED = "MERGED"
    CONSOLIDATED = "CONSOLIDATED"
    SKIPPED = "SKIPPED"
    ERROR = "ERROR"
    PARTIAL = "PARTIAL"
    CONFLICT = "CONFLICT"
    STALE = "STALE"
    EXPIRED = "EXPIRED"
    EVICTED = "EVICTED"
    REJECTED = "REJECTED"
    VERIFIED = "VERIFIED"
    INVALIDATED = "INVALIDATED"


class MemoryComponent(str, Enum):
    """Компонент памяти (Owner)"""
    EPISODIC_MEMORY = "EpisodicMemory"
    SEMANTIC_MEMORY = "SemanticMemory"
    RAG_MEMORY = "RAGMemory"
    ROOTS_MEMORY = "RootsMemory"
    EMOTION_ENGINE = "EmotionEngine"
    IMPULSE_CORE = "ImpulseCore"
    PERSONA_MEMORY = "PersonaMemory"
    USER_PERSONA = "UserPersonaManager"
    WORKING_MEMORY = "WorkingMemory"
    XRAY_TRACE = "XRayTrace"
    META_LEARNER = "MetaLearner"
    CONSOLIDATION = "Consolidation"
    SESSION_MANAGER = "SessionManager"
    UNKNOWN = "Unknown"


class MemoryObjectType(str, Enum):
    """Тип объекта памяти"""
    EPISODE = "Episode"
    FACT = "Fact"
    PROCEDURE = "Procedure"
    ROOT = "Root"
    EMOTION_STATE = "EmotionState"
    IMPULSE_STATE = "ImpulseState"
    PERSONA_TRAITS = "PersonaTraits"
    USER_PERSONA = "UserPersona"
    DIALOG = "Dialog"
    SESSION = "Session"
    WORKING_MEMORY = "WorkingMemory"
    CONTEXT = "Context"
    UNKNOWN = "Unknown"


@dataclass
class MemoryEvent:
    """Событие памяти для X-Ray"""
    
    # Identity
    event_id: str = field(default_factory=lambda: uuid4().hex[:16])
    timestamp: datetime = field(default_factory=datetime.now)
    
    # Context
    session_id: Optional[str] = None
    dialog_id: Optional[str] = None
    turn_id: Optional[int] = None
    phase: Optional[str] = None
    request_id: Optional[str] = None
    
    # Operation
    operation: MemoryOperation = MemoryOperation.READ
    component: MemoryComponent = MemoryComponent.UNKNOWN
    object_type: MemoryObjectType = MemoryObjectType.UNKNOWN
    object_id: Optional[str] = None
    
    # Result
    result: MemoryResult = MemoryResult.FOUND
    error: Optional[str] = None
    
    # Timing
    duration_ms: float = 0.0
    queue_time_ms: float = 0.0
    lock_wait_ms: float = 0.0
    
    # Payload
    payload_size_bytes: int = 0
    payload_preview: Optional[str] = None
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Trace context
    trace_id: Optional[str] = None
    span_id: Optional[str] = None
    parent_span_id: Optional[str] = None
    
    def to_xray_dict(self) -> Dict[str, Any]:
        """Serialize for X-Ray ingestion"""
        return {
            "event_type": "memory_event",
            "event_id": self.event_id,
            "timestamp": self.timestamp.isoformat(),
            "session_id": self.session_id,
            "dialog_id": self.dialog_id,
            "turn_id": self.turn_id,
            "phase": self.phase,
            "request_id": self.request_id,
            "operation": self.operation.value,
            "component": self.component.value,
            "object_type": self.object_type.value,
            "object_id": self.object_id,
            "result": self.result.value,
            "error": self.error,
            "duration_ms": self.duration_ms,
            "queue_time_ms": self.queue_time_ms,
            "lock_wait_ms": self.lock_wait_ms,
            "payload_size_bytes": self.payload_size_bytes,
            "payload_preview": self.payload_preview,
            "metadata": self.metadata,
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "parent_span_id": self.parent_span_id,
        }
```

---

## MemoryEvent Emitters (Where to instrument)

| Component | Location | Operations to Emit |
|-----------|----------|-------------------|
| `EpisodicMemory` | `add_episode`, `get_recent`, `get_all`, `search` | WRITE, READ, READ, READ |
| `SemanticMemory` | `add_fact`, `add_procedure`, `find_facts`, `find_procedure` | WRITE, WRITE, READ, READ |
| `RAGMemory` | `add_dialog`, `search` | WRITE, READ |
| `RootsMemory` | `get_roots_context` | READ |
| `SessionEmotionStore` | `get_or_create`, `save`, `remove`, `get_active_count` | READ/WRITE, WRITE, DELETE, READ |
| `SessionImpulseStore` | `get_or_create`, `save`, `remove`, `get_active_count` | READ/WRITE, WRITE, DELETE, READ |
| `PersonaMemory` | `get_trait`, `adjust_trait`, `add_reflection`, `evolve_from_dialog` | READ, WRITE, WRITE, WRITE |
| `UserPersonaManager` | `get_persona`, `create_persona`, `save_persona` | READ, WRITE, WRITE |
| `SessionManager` | `create_session`, `get_session`, `end_session`, `get_or_create` | WRITE, READ, DELETE, READ/WRITE |
| `MemoryConsolidator` | `consolidate_all`, `run_scheduled_consolidation` | CONSOLIDATE, CONSOLIDATE |
| `PipelineExecutor` | `execute` (phases) | READ/WRITE (per phase) |
| `TraceCollector` | `record_event` | WRITE (X-Ray itself) |

---

## Instrumentation Pattern

```python
# В каждом компоненте памяти
class EpisodicMemory:
    def __init__(self):
        self._trace = get_memory_tracer()  # from core.xray
    
    def add_episode(self, episode: Episode) -> str:
        start = time.perf_counter()
        try:
            episode_id = self._do_add_episode(episode)
            self._trace.emit_memory_event(
                operation=MemoryOperation.WRITE,
                component=MemoryComponent.EPISODIC_MEMORY,
                object_type=MemoryObjectType.EPISODE,
                object_id=episode_id,
                result=MemoryResult.CREATED,
                duration_ms=(time.perf_counter() - start) * 1000,
                payload_size_bytes=len(str(episode)),
                session_id=self._current_session_id,
                phase="SaveEpisodePhase",
            )
            return episode_id
        except Exception as e:
            self._trace.emit_memory_event(
                operation=MemoryOperation.WRITE,
                component=MemoryComponent.EPISODIC_MEMORY,
                object_type=MemoryObjectType.EPISODE,
                result=MemoryResult.ERROR,
                error=str(e),
                duration_ms=(time.perf_counter() - start) * 1000,
            )
            raise
```

---

## MemoryTraceService

```python
class MemoryTraceService:
    """Сервис сбора и анализа MemoryEvent"""
    
    def __init__(self, xray_client: XRayClient):
        self.xray = xray_client
        self._buffer: List[MemoryEvent] = []
        self._flush_interval = 100  # events
    
    def emit(self, event: MemoryEvent) -> None:
        self._buffer.append(event)
        if len(self._buffer) >= self._flush_interval:
            self.flush()
    
    def flush(self) -> None:
        if not self._buffer:
            return
        events = self._buffer
        self._buffer = []
        # Batch send to X-Ray
        self.xray.send_batch([e.to_xray_dict() for e in events])
    
    async def aemit(self, event: MemoryEvent) -> None:
        self.emit(event)
```

---

## X-Ray Schema Extension (PostgreSQL)

```sql
-- memory_events table
CREATE TABLE memory_events (
    event_id          VARCHAR(32) PRIMARY KEY,
    timestamp         TIMESTAMPTZ NOT NULL,
    session_id        VARCHAR(64),
    dialog_id         VARCHAR(64),
    turn_id           INTEGER,
    phase             VARCHAR(64),
    request_id        VARCHAR(64),
    
    operation         VARCHAR(32) NOT NULL,
    component         VARCHAR(64) NOT NULL,
    object_type       VARCHAR(32) NOT NULL,
    object_id         VARCHAR(128),
    result            VARCHAR(32) NOT NULL,
    error             TEXT,
    
    duration_ms       REAL NOT NULL,
    queue_time_ms     REAL DEFAULT 0,
    lock_wait_ms      REAL DEFAULT 0,
    
    payload_size      INTEGER DEFAULT 0,
    payload_preview   TEXT,
    
    trace_id          VARCHAR(64),
    span_id           VARCHAR(64),
    parent_span_id    VARCHAR(64),
    
    metadata          JSONB DEFAULT '{}',
    
    created_at        TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_memory_events_session_time 
    ON memory_events (session_id, timestamp DESC);

CREATE INDEX idx_memory_events_component_op 
    ON memory_events (component, operation, timestamp DESC);

CREATE INDEX idx_memory_events_object 
    ON memory_events (object_type, object_id, timestamp DESC);
```

---

## MemoryEvent Queries (for Research)

```sql
-- Top reads by component
SELECT component, operation, COUNT(*) as cnt
FROM memory_events
WHERE operation = 'READ' AND timestamp > NOW() - INTERVAL '24 hours'
GROUP BY component, operation
ORDER BY cnt DESC;

-- Memory leakage: objects never read after write
WITH writes AS (
    SELECT object_id, component, timestamp
    FROM memory_events
    WHERE operation = 'WRITE'
),
reads AS (
    SELECT object_id, component, timestamp
    FROM memory_events
    WHERE operation = 'READ'
)
SELECT w.object_id, w.component, w.timestamp as written_at
FROM writes w
LEFT JOIN reads r 
    ON w.object_id = r.object_id 
   AND w.component = r.component
   AND r.timestamp > w.timestamp
WHERE r.object_id IS NULL
  AND w.timestamp > NOW() - INTERVAL '7 days';

-- Memory churn rate
SELECT 
    DATE_TRUNC('hour', timestamp) as hour,
    component,
    COUNT(*) FILTER (WHERE operation = 'WRITE') as writes,
    COUNT(*) FILTER (WHERE operation = 'DELETE') as deletes,
    COUNT(*) FILTER (WHERE operation = 'EVICT') as evicts
FROM memory_events
WHERE timestamp > NOW() - INTERVAL '24 hours'
GROUP BY hour, component
ORDER BY hour DESC;
```

---

## Alert Rules (Prometheus)

```yaml
groups:
- name: memory_observability
  rules:
    - alert: MemoryWriteFailureRate
      expr: rate(memory_events_operation_total{result="ERROR"}[5m]) > 0.01
      for: 2m
      labels:
        severity: critical
      annotations:
        summary: "Memory write failure rate > 1%"
        
    - alert: MemoryReadMissRateHigh
      expr: |
        rate(memory_events_operation_total{result="NOT_FOUND"}[5m])
        /
        rate(memory_events_operation_total{operation="READ"}[5m]) > 0.5
      for: 5m
      labels:
        severity: warning
      annotations:
        summary: "Memory read miss rate > 50%"
        
    - alert: MemoryEventLatencyHigh
      expr: histogram_quantile(0.99, rate(memory_events_duration_ms_bucket[5m])) > 100
      for: 2m
      labels:
        severity: warning
      annotations:
        summary: "Memory event p99 latency > 100ms"
        
    - alert: SessionIsolationViolation
      expr: |
        count by (session_id) (
          memory_events{component=~"EmotionEngine|ImpulseCore|PersonaMemory", operation="READ|WRITE"}
        ) > 1
      for: 1m
      labels:
        severity: critical
      annotations:
        summary: "Multiple sessions sharing memory component"
```

---

## Dashboard Panels (Grafana)

| Panel | Query | Description |
|-------|-------|-------------|
| **Memory Ops/sec** | `rate(memory_events_total[1m])` | Throughput |
| **Read/Write Ratio** | `rate(READ)/rate(WRITE)` | Balance |
| **Error Rate** | `rate(result="ERROR")` | Health |
| **Latency p50/p95/p99** | `histogram_quantile(0.99, duration_ms)` | Latency |
| **Component Distribution** | `sum by (component) rate(memory_events_total[5m])` | Load |
| **Session Isolation** | `count by (session_id) (memory_events)` | Isolation check |
| **Memory Churn** | `rate(operation="EVICT" OR operation="DELETE")[5m]` | Turnover |
| **Consolidation Rate** | `rate(operation="CONSOLIDATE")[5m]` | Consolidation |

---

## Implementation Checklist

- [ ] Define `MemoryEvent` dataclass in `core/xray/memory_trace.py`
- [ ] Create `MemoryTraceService` in `core/xray/memory_trace.py`
- [ ] Add `emit_memory_event()` to `XRayBroadcaster` / `TraceCollector`
- [ ] Instrument `EpisodicMemory` (READ/WRITE)
- [ ] Instrument `SemanticMemory` (READ/WRITE/CONSOLIDATE)
- [ ] Instrument `RAGMemory` (READ/WRITE)
- [ ] Instrument `RootsMemory` (READ)
- [ ] Instrument `SessionEmotionStore` (READ/WRITE/DELETE)
- [ ] Instrument `SessionImpulseStore` (READ/WRITE/DELETE)
- [ ] Instrument `PersonaMemory` (READ/WRITE)
- [ ] Instrument `UserPersonaManager` (READ/WRITE)
- [ ] Instrument `SessionManager` (READ/WRITE/DELETE)
- [ ] Instrument `MemoryConsolidator` (CONSOLIDATE)
- [ ] Instrument `PipelineExecutor` (per-phase READ/WRITE)
- [ ] Add `memory_events` table migration
- [ ] Add Prometheus metrics for MemoryEvent
- [ ] Add Grafana dashboard panels
- [ ] Add alert rules

---

## Rollout Plan

| Phase | Scope | Risk |
|-------|-------|------|
| 1 | Core components (Episodic, Semantic, RAG, Roots) | Low |
| 2 | Emotion/Impulse/Persona stores | Medium (session isolation) |
| 3 | Pipeline phases (auto-instrument) | Medium |
| 4 | Consolidation | Low (background) |
| 5 | Dashboards + Alerts | Low |

---

*Next: 07_metrics.md — Memory Metrics Catalog*