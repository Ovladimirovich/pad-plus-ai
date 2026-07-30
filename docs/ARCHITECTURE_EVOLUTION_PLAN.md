# PAD+ AI Architecture Evolution Plan

**Version:** 1.0  
**Date:** July 2026  
**Status:** Draft — defines the sequence of architectural development for PAD+ AI v4.x  
**Based on:** Architectural Audit — Cognitive State (`docs/COGNITIVE_STATE_AUDIT.md`)

---

## Table of Contents

1. [Purpose](#purpose)
2. [Current State Assessment](#current-state-assessment)
3. [Architectural Constraints](#architectural-constraints)
4. [Evolution Roadmap](#evolution-roadmap)
5. [Phase Details](#phase-details)
6. [Dependency Graph](#dependency-graph)
7. [What Is Forbidden by Phase](#what-is-forbidden-by-phase)
8. [Success Criteria & Measurement](#success-criteria--measurement)
9. [Appendix: Evolution Logic](#appendix-evolution-logic)

---

## Purpose

PAD+ AI evolved organically: each subsystem (X-Ray, HEALER, Research Platform) was born from a real constraint in the previous layer. This document formalizes that process for the next stages of evolution.

**This is not a feature roadmap.** It defines the architectural sequence: what must be stabilized before the next layer can be built. Violating this order creates technical debt that compounds.

---

## Current State Assessment

### What Is Stable

| Subsystem | Status | Evidence |
|-----------|--------|----------|
| Pipeline v5.0 (25 phases) | Stable | Hot/Background split works. 380+ tests pass. |
| X-Ray (observability) | Stable | Trace collection, history, visualization work. |
| HEALER (diagnostics) | Stable | Monitoring mode works. Auto-remediation exists but not in production. |
| Research Platform | Stable | Snapshots, analytics, data collection work. |
| RAG memory | Stable | PostgreSQL-backed, keyword + recency search. |

### What Is Fragile

| Subsystem | Status | Evidence |
|-----------|--------|----------|
| EmotionEngine | Fragile | Global singleton, no session isolation, dual storage (PG + JSON) |
| ImpulseCore | Fragile | Global singleton, no decay mechanism, triple storage (PG + JSON + .txt) |
| PersonaMemory | Fragile | `PersonaMemory.users` duplicates `UserPersona`, two independent update paths |
| MetaLearner | Fragmented | 4 independent implementations with no coordination |
| Pipeline contracts | Brittle | `execution_time_ms`, `procedure_used`, `result_dict` — keys read but never written |
| Session identity | Fractured | Managed across 4+ systems (SessionManager, Supabase, X-Ray, dialog_id) |

### What Is Dead / Orphaned

| Component | Reason |
|-----------|--------|
| `MemoryMaintenancePhase` | Defined, implemented, never registered in pipeline |
| `MemoryHygiene.run_cleanup()` | Simulated — reports duplicates but never deletes |
| `ImpulseState` DTO | Defined, exported, never instantiated |
| `RAGMemory._topic_stats` | Initialized, never written or read |
| `Consolidator._history` | Appended, never exposed, lost on restart |

---

## Architectural Constraints

These are NOT bugs. They are structural limitations that block further evolution.

| # | Constraint | Affected Subsystems | Blocks |
|---|-----------|---------------------|--------|
| C1 | **Dual Source of Truth** — `PersonaMemory.users` and `UserPersona` store overlapping per-user state via independent update paths | Persona | Any new memory feature (will diverge further) |
| C2 | **Global singletons** — EmotionEngine, ImpulseCore are process-wide, not per-session | Emotion, Impulse | Session isolation, multi-user support, truthful memory |
| C3 | **Fragmented learning** — 4 MetaLearners track strategy outcomes independently | X-Ray, Evolution, Experience, HEALER | Learning Layer, unified strategy optimization |
| C4 | **Broken pipeline contracts** — 3 keys read but never written, 1 orphaned phase | Pipeline | Predictable phase behavior, debugging |
| C5 | **Fractured session identity** — session_id, dialog_id, JWT, request_id all represent the same concept differently | Session, X-Ray, Experience, Auth | Any cross-subsystem feature |
| C6 | **No Cognitive Context** — no single object answers "what state is the system in right now?" | All | Cognitive Context Layer, Conversation State, Decision Engine |

---

## Evolution Roadmap

```
CURRENT
    │
    ▼
┌──────────────────────────────────────────────────────┐
│ Phase A: Architecture Cleanup                         │
│ "Fix what is broken before building new"              │
│                                                        │
│ Fix: C4 (broken contracts), dead code, dual SOF       │
└──────────────────────────────────────────────────────┘
    │
    ▼
┌──────────────────────────────────────────────────────┐
│ Phase B: Pipeline Stabilization                       │
│ "Make the pipeline contractually sound"               │
│                                                        │
│ Fix: typed PipelineContext, bg_data consistency       │
└──────────────────────────────────────────────────────┘
    │
    ▼
┌──────────────────────────────────────────────────────┐
│ Phase C: Session Isolation                             │
│ "One user's state must not leak to another"           │
│                                                        │
│ Fix: C2 (global singletons → per-session state),      │
│      C5 (unified session identity)                    │
└──────────────────────────────────────────────────────┘
    │
    ▼
┌──────────────────────────────────────────────────────┐
│ Phase D: Learning Unification                         │
│ "One learning layer, not four"                        │
│                                                        │
│ Fix: C3 (4 MetaLearners → Learning Services)          │
└──────────────────────────────────────────────────────┘
    │
    ▼
┌──────────────────────────────────────────────────────┐
│ Phase E: Cognitive Context Layer                       │
│ "The system knows what state it is in"                │
│                                                        │
│ New: ICognitiveContextProvider, immutable snapshot,    │
│      context_load phase                               │
└──────────────────────────────────────────────────────┘
    │
    ▼
┌──────────────────────────────────────────────────────┐
│ Phase F: Conversation State Engine                    │
│ "The system knows what it is doing and why"           │
│                                                        │
│ New: topic tracking, goal management, open questions,  │
│      state evolution across turns                     │
└──────────────────────────────────────────────────────┘
    │
    ▼
┌──────────────────────────────────────────────────────┐
│ Phase G: Decision Engine                              │
│ "The system decides how to respond, not just reacts"  │
│                                                        │
│ New: strategy selection, cognitive resource mgmt,     │
│      meta-cognitive layer                             │
└──────────────────────────────────────────────────────┘
    │
    ▼
┌──────────────────────────────────────────────────────┐
│ Phase H: Learning Layer                               │
│ "The system learns from experience across sessions"   │
│                                                        │
│ New: unified learning bus, cross-session patterns,    │
│      automated strategy optimization                  │
└──────────────────────────────────────────────────────┘
    │
    ▼
┌──────────────────────────────────────────────────────┐
│ Phase I: Cognitive OS                                 │
│ "The system manages its own cognitive resources"      │
│                                                        │
│ New: self-scheduling, resource-aware processing,      │
│      autonomous goal setting                          │
└──────────────────────────────────────────────────────┘
```

---

## Phase Details

### Phase A: Architecture Cleanup

**Goal:** Eliminate all defects and dead code found in the audit. No new features.

**Tasks:**

| # | Task | Constraint | Verification |
|---|------|-----------|-------------|
| A1 | Fix `execution_time_ms` — write it before EvaluationPhase reads it | C4 | EvaluationPhase receives correct value |
| A2 | Fix `procedure_used` — align key name between SemanticPhase and SaveEpisodePhase | C4 | SaveEpisode significance bonus triggers correctly |
| A3 | Fix `result_dict` — write it before ReflectionPhase reads it | C4 | ReflectionPhase receives pipeline result |
| A4 | Register `MemoryMaintenancePhase` in pipeline or remove it | C4 | Phase executes or file is deleted |
| A5 | Fix `MemoryHygiene` — either execute actual deletions or remove simulation | C4 | Cleanup produces real effects |
| A6 | Remove `PersonaMemory.users` — all per-user data lives in `UserPersona` only | C1 | Single Source of Truth for per-user state |
| A7 | Remove dead code: `_topic_stats`, `_history`, `ImpulseState` DTO | C4 | Cleanup audit passes |
| A8 | Remove `social_connection` from EmotionState if genuinely unused, or wire it into a prompt | — | No orphan fields |

**What is forbidden during Phase A:**
- Building any new subsystem (no Cognitive Context, no Conversation State, no new memory)
- Adding new pipeline phases
- Changing Emotion, Impulse, or Persona behavior
- Session isolation work

**Completion criteria:**
- Pipeline contracts: no read-before-write defects in ctx keys
- All orphaned code either registered or removed
- `PersonaMemory.users` eliminated — `UserPersona` is the only per-user store
- Cleanup audit passes (re-run COGNITIVE_STATE_AUDIT methodology)

---

### Phase B: Pipeline Stabilization

**Goal:** Make the pipeline contractually sound so phases communicate through typed contracts, not convention.

**Tasks:**

| # | Task | Constraint | Verification |
|---|------|-----------|-------------|
| B1 | Define typed schemas for PipelineContext.context sections | C4 | Each phase knows what keys exist and their types |
| B2 | Align `bg_data` assembly with actual keys written by foreground phases | C4 | Background phases don't silently get `None` |
| B3 | Eliminate `PipelineResult` / `ctx.context` value duplication | C4 | Single source of truth for each value |
| B4 | Add pre/post execution hooks for validation (all required keys exist / no unexpected keys remain) | C4 | Pipeline fails fast on contract violation |

**What is forbidden during Phase B:**
- Adding new phases without updating `bg_data` assembly
- Session isolation work
- Cognitive Context work

**Completion criteria:**
- `PipelineContext` has typed sections (dataclass or TypedDict) for at least: memory, emotion, impulse, strategy
- `bg_data` is auto-generated from typed context, not manually assembled
- `PipelineResult` values derive from context, not duplicate it
- Pre-flight validation passes for all phase combinations (including simple strategy)

---

### Phase C: Session Isolation

**Goal:** No state leaks between independent sessions. Emotion, Impulse, and Persona are scoped per-session.

**Tasks:**

| # | Task | Constraint | Verification |
|---|------|-----------|-------------|
| C1 | Unified session identity — define single `session_id` that all subsystems use | C5 | SessionManager, X-Ray, Emotion, Impulse all reference the same ID |
| C2 | EmotionEngine scoped per-session instead of global singleton | C2 | User A's praise does not affect User B's emotional state |
| C3 | ImpulseCore scoped per-session | C2 | User A's "understand" weight does not leak to User B |
| C4 | SessionManager deduplicate with Supabase auth sessions | C5 | One session lifecycle, not two |
| C5 | Add eviction policy for session-scoped state (TTL + LRU) | C2 | Old sessions are cleaned up |

**What is forbidden during Phase C:**
- Cognitive Context work (depends on stable session scope)
- Conversation State work (depends on session scope)
- Global state additions (any new global singleton)

**Completion criteria:**
- `EmotionState` is created per-session, loaded at session start, persisted per-session
- `ImpulseCore` is created per-session, decays independently
- `SessionManager._sessions` is the single source of truth for session identity
- TTL-based eviction works for all session-scoped state
- Load test: 100 concurrent sessions do not leak state between each other

---

### Phase D: Learning Unification

**Goal:** One learning layer, not four independent implementations.

**Tasks:**

| # | Task | Constraint | Verification |
|---|------|-----------|-------------|
| D1 | Audit the 4 MetaLearners for overlapping concerns | C3 | Clear mapping of what each tracks |
| D2 | Define `LearningService` contract (or `LearningBus`) that all learners publish to | C3 | Single event type for strategy outcomes |
| D3 | Consolidate strategy outcome tracking | C3 | One source of truth for strategy success rates |
| D4 | Keep domain-specific learning (personality evolution, healing meta) separate but connected | C3 | Sharing of strategy data without sharing internal state |

**What is forbidden during Phase D:**
- Conversation State work (depends on Cognitive Context)
- Decision Engine work (depends on unified learning)
- New independent MetaLearner implementations

**Completion criteria:**
- Exactly one component owns strategy outcome data
- All 4 original MetaLearners either consolidated or explicitly scoped
- Learning events flow through a single bus/channel
- No duplicate strategy counting

---

### Phase E: Cognitive Context Layer

The original concept from the audit, now built on stable foundations.

- `ICognitiveContextProvider` — interface for building context snapshot
- `CognitiveContextSnapshot` — immutable frozen dataclass
- `context_load` phase — runs first in pipeline, builds snapshot
- **No ownership** — snapshot is a view, not a new source of truth
- **No logic** — aggregation only

See `docs/COGNITIVE_STATE_AUDIT.md` section "Candidate Context Analysis" for v0.1 contract.

---

### Phase F: Conversation State Engine

Only after Cognitive Context proves stable and session isolation works.

- Topic tracking across turns (current, previous, derived topics)
- Goal management (active goal, goal completion, goal switching)
- Open questions tracking
- Working concepts (what was just introduced)
- Conversation summary (compressed, not raw history)

---

### Phase G: Decision Engine

- Strategy selection based on Cognitive Context + Conversation State
- Cognitive resource management (when to use expensive vs cheap LLM calls)
- Meta-cognitive layer: the system decides HOW to think, not just WHAT to think

---

### Phase H: Learning Layer

- Unified learning bus connecting all learning signals
- Cross-session pattern detection
- Automated strategy optimization
- Feedback loops from HEALER and Research Platform into learning

---

### Phase I: Cognitive OS

- Self-scheduling of cognitive resources
- Autonomous goal setting
- Resource-aware processing (decide which pipeline phases to run based on cognitive load)
- Long-term adaptation

---

## Dependency Graph

```
Phase A (Cleanup)
    │
    ▼
Phase B (Pipeline Stabilization)
    │
    ▼
Phase C (Session Isolation)
    │
    ├────────────────────┐
    ▼                    ▼
Phase D (Learning)    Phase E (Cognitive Context)
    │                    │
    └────────┬───────────┘
             ▼
     Phase F (Conversation State)
             │
             ▼
     Phase G (Decision Engine)
             │
             ▼
     Phase H (Learning Layer)
             │
             ▼
     Phase I (Cognitive OS)
```

**Key dependency rules:**
- Phase C (Session Isolation) must precede both D and E — without session scope, neither learning nor context can be correct
- Phase E (Cognitive Context) must precede F (Conversation State) — CSE aggregates context over turns
- Phase D (Learning Unification) should precede G (Decision Engine) — the engine needs unified learning signals
- Phases D and E are independent and can be parallelized

---

## What Is Forbidden by Phase

For each phase, the following developments are prohibited until the phase is completed:

| Phase | Forbidden |
|-------|-----------|
| **Phase A** | All new subsystems, all new pipeline phases, any changes to Emotion/Impulse/Persona behavior |
| **Phase B** | Adding new phases without bg_data update, any session isolation work, any Cognitive Context work |
| **Phase C** | Any new global singleton, any Conversation State work, any Cognitive Context work |
| **Phase D** | Any new independent MetaLearner, any Conversation State work, any Decision Engine work |
| **Phase E** | Any Conversation State Engine work, any Decision Engine work |
| **Phase F** | Any Decision Engine work, any Learning Layer work |
| **Phase G** | Any Learning Layer work that depends on unconsolidated learning signals |
| **Phase H** | Any Cognitive OS work |
| **Phase I** | — (terminal phase) |

---

## Success Criteria & Measurement

### Quantitative Metrics

| Metric | Current | Target (Phase A-C) | Target (Phase E+) | Measurement |
|--------|---------|-------------------|-------------------|-------------|
| Pipeline contract violations | 3 (ctx keys) | 0 | 0 | `rg "\.get\(['\"]" phases/` cross-reference |
| Orphaned phases | 1 | 0 | 0 | Pipeline registry check |
| Dual SOF instances | 1 | 0 | 0 | Code review |
| Global singletons with session-level data | 2 (Emotion, Impulse) | 2 | 0 | Audit |
| Independent MetaLearners | 4 | 4 | 1 | Module count |
| Session identity systems | 4+ | 4 | 1 | ID flow trace |
| Tests passing | 380+ | 380+ | 380+ | `pytest -v` |

### Qualitative Gates

- After Phase A: audit re-run shows zero CRITICAL and zero HIGH smells
- After Phase B: adding a new pipeline phase requires only adding a typed section, not manual bg_data editing
- After Phase C: 100 concurrent users produce no emotion/impulse cross-contamination in tests
- After Phase D: one API call returns authoritative strategy success data
- After Phase E: pipeline executor can be refactored to read from CognitiveContext instead of 5 different singletons

---

## Appendix: Evolution Logic

This roadmap follows the same pattern that produced X-Ray, HEALER, and Research Platform:

```
Phase A: "Pipeline has contract defects" → Cleanup
Phase B: "Pipeline contracts are fragile" → Typed contracts
Phase C: "State leaks between users" → Session isolation
Phase D: "Learning is fragmented" → Unified learning
Phase E: "No single cognitive state view" → Cognitive Context
Phase F: "Context is stateless across turns" → Conversation State
Phase G: "System reacts but doesn't decide" → Decision Engine
Phase H: "Learning is passive" → Active Learning Layer
Phase I: "System needs resource autonomy" → Cognitive OS
```

Each phase answers:
> "What constraint in the current architecture prevents the next logical evolution?"
