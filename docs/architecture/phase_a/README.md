# Phase A: Architecture Cleanup

**Goal:** Eliminate all defects and dead code found in the audit. No new features.

**Hypothesis:** After eliminating defects, the pipeline becomes deterministic — phased execution with known inputs and outputs produces predictable results.

**Metric:** Broken Contract count: 6 → 0

**Experiment:** Regression suite (360+ tests) passes with zero regressions.

---

## Research Questions

| RQ | Question | Metric | Current | Target |
|----|----------|--------|---------|--------|
| RQ-001 | Does fixing `execution_time_ms` improve evaluation accuracy? | EvaluationPhase receives correct duration | None passed | Duration ≥ 0 |
| RQ-002 | Does removing `PersonaMemory.users` eliminate state drift between user and system persona? | Cross-read consistency | Two independent update paths | Single source of truth |
| RQ-003 | Does registering `MemoryMaintenancePhase` reduce memory growth rate? | Memory item count over 1000 dialogs | Monotonic growth | Stabilized |
| RQ-004 | Does cleaning written-but-never-read ctx keys reduce confusion? | ctx namespace pollution | 2 orphaned keys | Clean ctx |

---

## Task Dependency Matrix

```
A1 ──► A5
 │
 A2 ──► ──► A8
 │
 A3 ──► A6 ──► A7
 │
 A4
 │
 A9 (independent cleanup)
```

**Legend:**
- **A1, A2, A3, A4, A9** — independent (can be done in parallel)
- **A5** — depends on A1 (hygiene test uses execution_time validation)
- **A6** — depends on A2, A3 (PersonaMemory.users removal frees ctx keys)
- **A7** — depends on A6 (dead code removal after interface change)
- **A8** — independent (social_connection audit)

---

## File Impact Matrix

| Task | Files Modified | Files Tested | Risk |
|------|---------------|--------------|------|
| A1 | `executor.py` | `test_evaluation_phase.py` | Low |
| A2 | `phases/save_episode.py` | `test_save_episode.py` | Low |
| A3 | `executor.py` | `test_reflection.py` | Low |
| A4 | `phases/memory_maintenance.py`, `phases/__init__.py` | `test_orchestrator.py` | Low |
| A5 | `memory/hygiene.py` | `test_hygiene.py` | Medium |
| A6 | `memory/persona.py` | `test_persona.py` | **High** |
| A7 | `memory/consolidation.py`, `impulse/core.py`, `impulse/__init__.py`, `memory/rag.py`, `scripts/impulse.py`, `tests/test_impulse_core.py` | Various | Medium |
| A8 | `emotion/pad_model.py`, `api/persona_routes.py` | `test_emotion.py` | Low |
| A9 | `phases/emotion_update.py` | `test_emotion_update.py` | Low |

---

## Definition of Done (Phase A)

1. **All A1-A9 tasks completed** with code changes merged
2. **Pipeline contract validation passes:**
   - `execution_time_ms` is written to `ctx.context` before EvaluationPhase reads it (and updated after every phase)
   - `procedure_name` is read by SaveEpisodePhase (not `procedure_used`)
   - `result_dict` is written before ReflectionPhase reads it
3. **MemoryMaintenancePhase** is registered as foreground phase (order=19) in pipeline
4. **MemoryHygiene.run_cleanup** produces honest zeros (no simulated deletions); real cleanup delegated to MemoryMaintenancePhase
5. **PersonaMemory.users** is removed — UserPersona is the sole per-user store
6. **Dead code eliminated:** `_topic_stats`, `Consolidator._history` (capped at 100), `ImpulseState` DTO, `InteractionMemory` dataclass
7. **`social_connection`** is removed from EmotionState (was never read by any consumer)
8. **Written-but-never-read ctx keys** cleaned: `emotion_event`, `emotion_intensity` removed from emotion_update output
9. **No regressions:** full test suite passes (`pytest -v` shows 360+ tests, zero new failures)
10. **Cleanup audit re-run** shows ZERO CRITICAL and ZERO HIGH smells (use `docs/COGNITIVE_STATE_AUDIT.md` methodology)
