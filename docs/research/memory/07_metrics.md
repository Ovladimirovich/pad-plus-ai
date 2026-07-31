# 07_metrics.md — Memory Metrics Catalog

**Phase:** 7 — Metrics  
**Status:** Draft  
**Based on:** 01–06

---

## Purpose

Определить **все метрики памяти**, которые должны собираться для исследования и алертинга.

---

## Metric Categories

| Category | Prefix | Purpose |
|----------|--------|---------|
| **Throughput** | `memory_ops_` | READ/WRITE/DELETE rate |
| **Latency** | `memory_latency_` | p50/p95/p99 per operation |
| **Errors** | `memory_errors_` | Error rate by type |
| **Health** | `memory_health_` | Hit rate, staleness, fragmentation |
| **Capacity** | `memory_capacity_` | Size, count, growth rate |
| **Quality** | `memory_quality_` | Duplicates, orphans, staleness |
| **Consolidation** | `memory_consol_` | Consolidation pipeline health |

---

## Core Metrics (P0 — Must Have)

### Throughput

| Metric | Type | Labels | Target |
|--------|------|--------|--------|
| `memory_ops_total` | Counter | component, operation, status | — |
| `memory_reads_total` | Counter | component, phase | — |
| `memory_writes_total` | Counter | component, phase | — |
| `memory_deletes_total` | Counter | component | — |

### Latency

| Metric | Type | Labels | Target |
|--------|------|--------|--------|
| `memory_operation_latency_seconds` | Histogram | component, operation | p50<10ms, p99<100ms |
| `memory_read_latency_seconds` | Histogram | component | p50<5ms |
| `memory_write_latency_seconds` | Histogram | component | p50<10ms |
| `memory_consolidation_latency_seconds` | Histogram | type (ep2sem, sem2roots) | p95<30s |

### Errors

| Metric | Type | Labels | Target |
|--------|------|--------|--------|
| `memory_errors_total` | Counter | component, operation, error_type | <0.1% |
| `memory_timeouts_total` | Counter | component, operation | 0 |

---

## Health Metrics (P1 — Should Have)

### Hit Rate / Efficiency

| Metric | Formula | Target |
|--------|---------|--------|
| `memory_hit_rate` | hits / (hits + misses) | > 0.8 |
| `memory_miss_rate` | misses / (hits + misses) | < 0.2 |
| `memory_cache_hit_rate` | cache_hits / (cache_hits + cache_misses) | > 0.9 |

### Staleness / Freshness

| Metric | Definition | Alert Threshold |
|--------|------------|-----------------|
| `memory_max_age_seconds` | max(now - created_at) | > 30d warning |
| `memory_avg_age_seconds` | avg(now - created_at) | > 7d warning |
| `memory_staleness_ratio` | stale_items / total_items | > 0.5 warning |

### Capacity / Growth

| Metric | Alert Threshold |
|--------|-----------------|
| `memory_total_items` | > 1M warning |
| `memory_size_bytes` | > 10GB warning |
| `memory_growth_rate_per_day` | > 10% warning |
| `memory_session_count` | > 10k warning |

### Quality / Hygiene

| Metric | Definition | Alert Threshold |
|--------|------------|-----------------|
| `memory_duplicate_ratio` | duplicates / total | > 0.1 warning |
| `memory_orphan_ratio` | orphans / total | > 0.05 warning |
| `memory_dead_ratio` | never_accessed / total | > 0.3 warning |
| `memory_fragmentation_ratio` | fragmented_bytes / total_bytes | > 0.3 warning |

---

## Consolidation Metrics (P1)

| Metric | Definition | Target |
|--------|------------|--------|
| `consolidation_runs_total` | Counter | — |
| `consolidation_duration_seconds` | Histogram | p95 < 30s |
| `consolidation_ep2sem_items` | Gauge | — |
| `consolidation_sem2roots_items` | Gauge | — |
| `consolidation_rag_topics` | Gauge | — |
| `consolidation_forgotten_items` | Counter | — |
| `consolidation_merged_facts` | Counter | — |
| `consolidation_errors_total` | Counter | 0 |
| `consolidation_lag_turns` | Gauge | < 20 turns |

---

## Session Isolation Metrics (P1)

| Metric | Definition | Alert |
|--------|------------|-------|
| `memory_active_sessions` | Active sessions in stores | > 1000 warning |
| `memory_session_leakage` | Cross-session reads | > 0 critical |
| `memory_session_isolation_ok` | Boolean | = 1 always |

---

## Component-Specific Metrics

### EpisodicMemory
| Metric | Target |
|--------|--------|
| `episodic_episodes_total` | — |
| `episodic_size_bytes` | < 5GB |
| `episodic_avg_episodes_per_session` | — |
| `episodic_consolidation_rate` | > 0.8 |

### SemanticMemory
| Metric | Target |
|--------|--------|
| `semantic_facts_total` | — |
| `semantic_procedures_total` | — |
| `semantic_duplicate_ratio` | < 0.1 |
| `semantic_search_latency_p99` | < 50ms |

### EmotionEngine
| Metric | Target |
|--------|--------|
| `emotion_active_sessions` | < 10000 |
| `emotion_decay_rate` | 0.001/sec |
| `emotion_persist_latency_p99` | < 10ms |

### ImpulseEngine
| Metric | Target |
|--------|--------|
| `impulse_active_sessions` | — |
| `impulse_stack_depth_avg` | < 10 |
| `impulse_update_latency_p99` | < 5ms |

---

## Dashboards

| Dashboard | Panels |
|-----------|--------|
| **Memory Overview** | Throughput, Latency, Errors, Health |
| **Memory Capacity** | Size, Growth, Capacity planning |
| **Memory Quality** | Duplicates, Orphans, Staleness |
| **Consolidation** | Runs, Duration, Items, Lag |
| **Session Isolation** | Active sessions, Leakage, Isolation OK |
| **Component Deep Dive** | Per-component: Episodic, Semantic, Emotion, Impulse |

---

## Alert Rules (P1)

| Alert | Condition | Severity | Runbook |
|-------|-----------|----------|---------|
| MemoryHighErrorRate | `memory_errors_total > 0.01 * memory_ops_total` | Critical | Check component logs |
| MemoryHighLatency | `memory_operation_latency_seconds{p99} > 100ms` | Warning | Check component |
| MemoryHighDuplication | `memory_duplicate_ratio > 0.2` | Warning | Run dedup |
| MemoryHighStaleness | `memory_staleness_ratio > 0.5` | Warning | Run cleanup |
| MemorySessionLeakage | `memory_session_leakage > 0` | Critical | Check isolation |
| ConsolidationLagHigh | `consolidation_lag_turns > 20` | Warning | Check consolidator |
| MemorySessionLeak | `memory_active_sessions > 10000` | Warning | Check TTL/eviction |

---

## Implementation

```python
# core/metrics/memory_metrics.py

from prometheus_client import Counter, Histogram, Gauge

# Throughput
MEMORY_OPS_TOTAL = Counter(
    'memory_ops_total',
    'Total memory operations',
    ['component', 'operation', 'status']
)

# Latency
MEMORY_OP_LATENCY = Histogram(
    'memory_operation_latency_seconds',
    'Memory operation latency',
    ['component', 'operation'],
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0]
)

# Health
MEMORY_HIT_RATE = Gauge('memory_hit_rate', 'Memory hit rate', ['component'])
MEMORY_DUPLICATE_RATIO = Gauge('memory_duplicate_ratio', 'Duplicate ratio', ['component'])

# Capacity
MEMORY_TOTAL_ITEMS = Gauge('memory_total_items', 'Total items', ['component'])
MEMORY_SIZE_BYTES = Gauge('memory_size_bytes', 'Size in bytes', ['component'])

# Consolidation
CONSOLIDATION_RUNS = Counter('consolidation_runs_total', 'Consolidation runs', ['type'])
CONSOLIDATION_LAG = Gauge('consolidation_lag_turns', 'Consolidation lag in turns')

# Session Isolation
MEMORY_SESSION_LEAKAGE = Gauge('memory_session_leakage', 'Cross-session memory leakage detected')
MEMORY_ACTIVE_SESSIONS = Gauge('memory_active_sessions', 'Active sessions in store', ['component'])
```

---

*Next: 08_problem_analysis.md — Problem Classification*