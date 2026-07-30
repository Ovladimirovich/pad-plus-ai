# Architectural Audit: Cognitive State of PAD+ AI

**Date:** July 2026
**Version:** 1.0
**Scope:** Full inventory of cognitive state ownership, lifecycle, dependencies, and architecture smells across all subsystems. No code changes proposed.

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Stage 1-2: State Ownership & Lifecycle](#stage-1-2-state-ownership--lifecycle)
3. [Stage 3: Pipeline Dependency Map](#stage-3-pipeline-dependency-map)
4. [Stage 4: Cognitive Dependency Graph](#stage-4-cognitive-dependency-graph)
5. [Stage 5: Architecture Smells](#stage-5-architecture-smells)
6. [Candidate Context Analysis](#candidate-context-analysis)
7. [Critical Findings Summary](#critical-findings-summary)

---

## Executive Summary

PAD+ AI has **12+ independent subsystems**, each managing its own state with its own lifecycle, storage backend, and scope discipline. The system has **no unified representation of its own cognitive state** -- each pipeline execution reconstructs context from scratch by querying multiple singletons.

Three cross-cutting problems dominate:

| # | Problem | Impact |
|---|---------|--------|
| 1 | **7+ global singletons** where per-user or per-session scope is required | User A's praise activates Emotion dimension for User B; session isolation is impossible |
| 2 | **Dual/triple storage** for the same logical state (PG + JSON + SQLite) | No single source of truth; drift between backends guaranteed over time |
| 3 | **No lifecycle management** -- no shutdown, no cleanup, no eviction for most subsystems | Memory leaks, unbounded growth, stale state accumulation |

---

## Stage 1-2: State Ownership & Lifecycle

### 1.1 EmotionEngine

**File:** `backend/emotion/pad_model.py`

**Owned State:**

| Field | Range | Default | Persistence |
|-------|-------|---------|-------------|
| `pleasure` | [-1, +1] | 0.0 | PG (`emotion_state` singleton) + `data/emotion_state.json` |
| `arousal` | [-1, +1] | 0.0 | Same |
| `dominance` | [-1, +1] | 0.0 | Same |
| `curiosity` | [0, 1] | 0.5 | Same |
| `confidence` | [0, 1] | 0.5 | Same |
| `social_connection` | [-1, +1] | 0.0 | Same |

**Source of Truth:** Dual -- PG preferred, JSON fallback. Both written on every mutation.

**Readers:** EmotionPhase (order 7), GeneratePhase, IdentityPhase, SaveEpisodePhase, IntentRouter, WebSocket broadcast, Admin/Frontend API, X-Ray, Anatomy, Health, Dreams.

**Writers:** EmotionUpdatePhase (order 17, pipeline), EmotionLearner (from RAG histories), Event listener (`experience_captured` events), Admin API routes, Frontend API routes, Decay thread.

**Scope:** **Global singleton.** One `PADModel` per process. All users share the same emotional state.

**Lifecycle:**
- Created: On first `get_pad_model()` call. Loads from PG -> JSON -> defaults.
- Decay: Daemon thread every 60s, linear decay at 0.001/s toward neutral.
- Destroyed: **Never.** No teardown, no shutdown. Lives until process exit.

---

### 1.2 ImpulseCore

**File:** `backend/core/impulse/core.py`, `manager.py`

**Owned State:**

| Field | Type | Persistence |
|-------|------|-------------|
| `dimensions[4]` | Each: `{label, question, weight [0,1]}` | PG (`impulse_state`) + `data/impulse.json` + `data/current_impulse.txt` |
| `_stack` | `list[list[dict]]` | In-memory only |

Dimensions: `understand`, `improve`, `protect`, `create`.

**Source of Truth:** Triple -- PG + JSON + .txt file. All three written on every `save()`.

**Readers:** ImpulsePhase (order 8, reads + injects bias into context), X-Ray, Admin API, Anatomy, Deep Health.

**Writers:** ImpulseUpdatePhase (order 18, primary, via `apply_deltas()` + `save()`), Event listener (disabled by default), Admin API routes.

**Scope:** **Global singleton.** One ImpulseCore per process.

**Lifecycle:**
- Created: On first `get_impulse_core()` call. Loads PG -> JSON -> defaults.
- Modified: Every pipeline cycle via `ImpulseUpdatePhase`.
- Destroyed: **Never.** `reset_manager()` exists for tests only.
- Decay: **None.** Unlike EmotionEngine, impulse weights are monotonic -- they only increase via deltas, never decay.

---

### 1.3 PersonaMemory + UserPersona

**Files:** `backend/memory/persona.py`, `backend/memory/user_persona.py`

**Owned State:**

**PersonaMemory** (system-level "self"):
- `traits[7]`: curiosity, skepticism, empathy, creativity, caution, openness, humility
- `values[4]`, `principles[6]`
- `users: Dict[str, InteractionMemory]` -- **per-user data inside global singleton**
- `reflections[100]`, `style_preferences[7]`

**UserPersona** (per-user):
- `style_preferences[6]`: verbosity, formality, technical_level, humor_level, use_examples, use_analogies
- `interests`, `frequent_topics`, `total_interactions`, `evolution_history[10]`

**Source of Truth:**
- PersonaMemory: PG (`persona_state` singleton) + `data/persona.json`
- UserPersona: `data/user_personas.json` (dev) or PG `user_personas` table (prod)

**Scope:** **Mixed.** PersonaMemory is a global singleton. UserPersona is per-user (stored in `Dict[str, UserPersona]`). **Critical:** `PersonaMemory.users` stores per-user interaction data inside the global singleton, duplicating UserPersona.

**Key Smell:** `PersonaMemory.users` is written (by `record_interaction()`) but **never read by the pipeline**. It is only visible via admin API. The pipeline reads `UserPersona` instead. Two code paths update both structures on every interaction with no synchronization.

**Lifecycle:**
- PersonaMemory: Process lifetime. No teardown.
- UserPersona: Created on first access per user. **No cache eviction** -- dict grows unboundedly with unique users.

---

### 1.4 Memory Manager (RAG + Episodic + Semantic)

**Files:** `backend/memory/rag.py`, `episodic.py`, `semantic.py`, `consolidation.py`, `hygiene.py`

**Scope:** All five are **global singletons**. Despite having `user_id` fields, there is one database and one instance per process.

| Component | Backend | State | Cleanup |
|-----------|---------|-------|---------|
| RAGMemory | PostgreSQL (`rag_dialogs`) | Dialog pairs with keywords, topics, entities, embeddings | **None** (cleanup is simulated, not executed) |
| EpisodicMemory | SQLite (`data/episodic.db`) | Episodes with `continuation_of`, `related_episodes`, significance | **None** (significance never decays) |
| SemanticMemory | SQLite (`data/semantic.db`) | Typed knowledge (declarative, procedural, conceptual, metacognitive) | **None** |
| Consolidator | In-memory | `_history: List[ConsolidationResult]` (lost on restart) | **None** (runs every N dialogs but never prunes its own history) |
| Hygiene | In-memory | Config dict | **Simulated** -- reports duplicates but never deletes |

---

### 1.5 PipelineContext

**File:** `backend/core/pipeline/context.py`

**Owned State:**
```python
user_message: str
context: Dict[str, Any]       # Shared mutable dict between 30+ phases
session_id: Optional[str]
api_key: Optional[str]
provider: Optional[str]
```

**Scope:** **Per-request.** Created fresh for each `execute()` call. Lives milliseconds to seconds.

**Critical Design Choice:** The `context` dict is the sole communication mechanism between 30+ phases. It has no schema, no typing, no documentation of who reads/writes what. A phase reading a key written by another phase is coupled by convention only.

**Background phases** reconstruct a **separate** PipelineContext from a manually-assembled `bg_data` dict subset -- if a background phase reads a key not copied into `bg_data`, it silently gets `None`.

---

### 1.6 Session

**Files:** `backend/session_manager.py`, `backend/api/frontend_routes.py`

**Owned State:**
- `SessionManager._sessions: Dict[str, Session]` -- all active sessions
- Each `Session`: `session_id, created_at, last_active, ip_address, context, settings, message_count`
- Persisted to `data/sessions.json`

**Session Identity is Fractured Across 4+ Systems:**

| System | ID | Backend |
|--------|----|---------|
| SessionManager | `sess_{uuid}` | In-memory + JSON |
| Supabase Auth | JWT token | Supabase remote |
| X-Ray | `request_id` == `session_id` | In-memory + SQLite |
| Experience Store | `dialog_id` (mapped from `session_id`) | SQLite |
| Frontend | `dialog_id` | Supabase `dialogs` table |

The `experience/listener.py` line `dialog_id = data.get("session_id") or str(uuid.uuid4())` explicitly conflates these two concepts.

**Scope:** **Global singleton** -- all users' sessions in one `Dict`.

**Lifecycle:** TTL 24h. `cleanup_expired()` runs only on `get_stats()` call. Sessions accumulate in JSON file even after expiry.

---

### 1.7 X-Ray

**Files:** `backend/core/xray/` (10+ files)

| Component | State | Backend | Scope |
|-----------|-------|---------|-------|
| TraceCollector | `_sessions: Dict[str, TraceSession]` (max 100) | In-memory | Global singleton |
| XRayHistory | LRU cache (500) + SQLite table | `data/xray_traces.db` | Global singleton |
| MetaLearner | `stats: Dict[str, StrategyStats]` + `_recent_decisions[50]` | `data/xray_meta_learner.json` | Global singleton |
| SystemStateManager | `SystemState` (load, confidence, errors, sessions) | In-memory | Global singleton |
| CognitiveStateManager | `_active_states`, `_history` (max 100) | In-memory | Global singleton |
| latest_pipeline_result | Module-level `Optional[Dict]` | In-memory | **Global mutable variable** |

**Trace persistence is duplicated:** Both SQLite (`data/xray_traces.db`) and PostgreSQL (migration `015_xray_traces.sql`) store X-Ray traces -- with **different schemas**. PG has `strategy, intent, confidence, health_score, user_id`; SQLite has `thinking_mode`.

**MetaLearner stats accumulate forever** -- no decay mechanism for old strategy data.

---

### 1.8 HEALER

**Files:** `backend/healing/`, `HEALER/` (external)

| Component | State | Backend | Scope |
|-----------|-------|---------|-------|
| HealerListener | `_cycle_count`, `_last_reports` | In-memory | Global singleton |
| RemediationEngine | `_applied: list[dict]` | In-memory | Per-listener |
| HealingChangesStore | `_applied`, `_backups: dict[str, bytes]` | **In-memory** (file backups stored as RAM bytes) | Global singleton |
| External HEALER | Full runtime (separate MetaLearner, diagnostics) | Its own | Independent process |

**Backup data is stored in RAM** as raw bytes, not written to disk. No rollback() caller exists.

---

### 1.9 Research Platform

**Files:** `backend/experiments/`, `backend/analytics/`, `backend/learning/`

| Component | State | Backend | Cleanup |
|-----------|-------|---------|---------|
| SystemSnapshot | Full system freeze (all subsystems) | JSON files on disk | **None** (accumulates forever) |
| Analytics | Events + sessions | SQLite (`data/analytics.db`) | 30-day retention |
| ExperienceLearner | `_interactions[1000]`, strategy scores | `data/experience_learner.json` | **None** |
| DataCollector | Dialogs, feedback, rewards | JSONL files (daily) | **None** |
| SelfEvaluator | `_recent_responses[50]` | In-memory | Max 50 |
| ActiveLearningPolicy | Counters | In-memory | **None** |

---

### 1.10 MetaLearner / Reflection (Fragmented)

There are **four separate MetaLearner-like components**:

| # | Location | Purpose | State | Persistence |
|---|----------|---------|-------|-------------|
| A | `core/xray/meta_learner.py` | Strategy success tracking | Per-strategy stats + 50 recent decisions | `data/xray_meta_learner.json` |
| B | `core/evolution/meta_learner.py` | Personality evolution decisions | Stateless (pure function) | None |
| C | `backend/learning/experience.py` | Context-aware strategy scoring | Interactions[1000] + score dicts | `data/experience_learner.json` |
| D | `HEALER/healer/meta/meta_learner.py` | Healing meta-analysis | Independent (separate process) | Its own |

**All four independently track strategy-related outcomes with no cross-talk.**

---

## Stage 3: Pipeline Dependency Map

### 3.1 Phase Execution Order (25 registered + inline + background)

| # | Phase | Order | Reads from ctx | Writes to ctx | External Reads | External Writes | Strategy Skip |
|---|-------|-------|---------------|---------------|----------------|-----------------|---------------|
| 0 | anti_loop | inline | `user_message` | `blocked`, `warning` | `executor._check_anti_loop()` | `_anti_loop_history` | No |
| 1 | safety | 1 | `user_message` | `blocked`, `sanitized_message`, `warning`, `safety_passed` | `safety_layer.check_request()` | None | No |
| 2 | intent | 2 | `user_message` | `intent`, `pipeline_meta` | `intent_router.route()` | None | No |
| 3 | rag | 3 | `user_message`, `user_id` | `rag_context`, `rag_used`, `sources` | `rag.get_context()` | None | **Yes** |
| 4 | knowledge_graph | 4 | `user_message` | `concepts`, `graph_context`, `confidence` | `knowledge.find_related_triples()` | None | **Yes** |
| 5 | episodic | 5 | `user_message`, `user_id` | `episodic_context`, `count` | `episodic.search_episodes()` | None | **Yes** |
| 6 | semantic | 6 | `user_message` | `procedure_context`, `procedure_name`, `procedure_id` | `semantic.find_applicable_procedure()` | None | **Yes** |
| 7 | emotion | 7 | (none) | `emotion_state`, `emotion_style` | `pad_model.get_state()` | None | **Yes** |
| 8 | impulse | 8 | (none) | `impulse_state`, `impulse_bias`, `impulse_primary`, `impulse_prompt_line`, `impulse_active` | `impulse.to_dict()`, `.get_bias_block()`, `.get_primary_label()` | None | No |
| 9 | persona | 9 | `user_id`, `intent` | `persona_context` | `persona.get_persona_context()` / `user_persona.get_context_for_prompt()` | `persona.save()` / `user_persona.record_interaction()` | **Yes** |
| 10 | roots | 10 | (none) | `roots_context` | `roots.export_for_context()` | None | **Yes** |
| 11 | identity | 11 | `user_message`, `emotion_state`, `call_count` | `is_identity`, `response`, `skip_generate`, `provider`, `confidence`, `model` | `roots.count()`, `vector_memory.count()` | None | No |
| 12 | generate | 12 | `user_message`, `roots_context`, `persona_context`, `rag_context`, `episodic_context`, `procedure_context`, `graph_context`, `emotion_style`, `emotion_state`, `strategy`, `impulse_bias`, `impulse_primary`, `api_key`, `session_id`, `provider` | `response`, `provider`, `confidence`, `model`, `raw_llm_response`, `llm_metadata`, `impulse_used`, `impulse_primary` | `llm_service`, `provider_manager.generate()` | None | No |
| 13 | truth_loop | 13 | `response`, `sources` | `truth_confidence`, `claims_verified`, `sources_info`, `add_disclaimer` | `truth_loop.extract_claims()`, `.verify_claims()` | None | **Yes** |
| 14 | evaluation | 14 | `response`, `confidence`, `execution_time_ms`, `strategy`, `intent`, `provider`, `model` | `evaluation`, `evaluation_skipped`, `ask_feedback`, `feedback_prompt` | `evaluator.evaluate()`, `collector.record_dialog()`, `active_policy.should_ask_feedback()` | `collector.record_dialog()` | **Yes** |
| 15 | save_episode | 15 | `response`, `intent`, `rag_used`, `procedure_used`, `truth_confidence`, `emotion_state`, `user_id` | `episode_id` | `episodic.add_episode()` | **`episodic.add_episode()`** | **Yes** |
| 16 | extraction | 16 | `user_message` | `concepts_added`, `relations_added` | `knowledge.extract_and_add()` | **`extract_and_add()`** | **Yes** |
| 17 | emotion_update | 17 | `user_message`, `response` | `emotion_event`, `emotion_intensity` | `pad_model`, `emotion_learner` | **`pad.apply_event()` + `pad.save()`** | **Yes** |
| 18 | impulse_update | 18 | entire `context`, `user_message` | `impulse_updated`, `impulse_state`, `impulse_primary`, `experience_interaction_type`, `experience_significance` | `signals.ensure_experience_in_context()`, `impulse.apply_deltas()`, `impulse.get_manager().save()` | **`apply_deltas()` + `save()`** | No |
| 19 | events_broadcast | 22 | `confidence`, `rag_used`, `intent` | (none) | `event_bus.emit()` | **`bus.emit()`** | No |
| 20 | response_guard | 27 | `response`, `call_count`, `confidence` | `response`, `cognition` | `response_guard`, `self_healing`, `tone_engine`, `cognitive_layer` | **`self_healing.process_and_learn()`** | No |
| -- | persona_evolution | 21 (BG) | `user_id`, `response` | (none) | `user_persona`, `persona`, `evolution.*` | **`persona.save()`, `.evolve_from_dialog()`, `Constitution.execute()`** | **Background** |
| -- | health | 23 (BG) | `pipeline_success`, `rag_used` | (none) | `health_monitor` | **`health.record_event()`** | **Background** |
| -- | reflection | 24 (BG) | `result_dict`, `pipeline_result`, `experience_interaction_type`, `experience_significance`, `emotion_style`, `impulse_primary` | (none) | `reflection_loop`, `system_state_manager`, `meta_controller` | **`state_manager.update()`, `meta.adapt()`** | **Background** |
| -- | dreams | 25 (BG) | (none) | (none) | `dream_system` | **`dreams.record_activity()`** | **Background** |
| -- | metrics | 26 (BG) | `start_time`, `pipeline_result` | (none) | `metrics_collector` | **`metrics.increment()`, `record_duration()`, `set_gauge()`** | **Background** |
| -- | consolidation | inline (BG) | `user_id` (from bg_data) | (none) | `consolidator.run_scheduled_consolidation()` | **`consolidator.run()`** | **Background** |
| -- | procedure_success | inline (BG) | `intent` (from bg_data) | (none) | `semantic.record_procedure_success()` | **`semantic.record_procedure_success()`** | **Background** |

### 3.2 Orphaned Phase

**MemoryMaintenancePhase** (`phases/memory_maintenance.py`) is defined and fully implemented (fusion + forgetting logic) but **never imported** in `__init__.py`, **never registered** via `@register_phase`, and **never instantiated** in the executor. Dead code.

### 3.3 Buggy / Stale ctx Reads

| Key | Read By | Problem |
|-----|---------|---------|
| `execution_time_ms` | EvaluationPhase | Never written to ctx -- always returns `None`. Actual value is on `result.execution_time_ms`. |
| `procedure_used` | SaveEpisodePhase | Semantic phase writes `procedure_name`, not `procedure_used`. Branch never triggers. |
| `result_dict` | ReflectionPhase | No phase ever writes `result_dict` to ctx. Always returns empty dict. |

---

## Stage 4: Cognitive Dependency Graph

### 4.1 State-to-State Relationship Map

```
┌─────────────────────────────────────────────────────────────┐
│                      PIPELINE EXECUTOR                       │
│  Creates PipelineContext per-request, orchestrates phases    │
└─────────────────────────────────────────────────────────────┘
                              │
     ┌────────────────────────┼────────────────────────┐
     ▼                        ▼                        ▼
┌────────────┐        ┌──────────────┐        ┌──────────────┐
│  Emotion   │        │   Impulse    │        │   Persona    │
│  Engine    │◄──────►│    Core      │        │   Memory     │◄──────┐
│ (global)   │        │ (global)     │        │ (global+per- │       │
└─────┬──────┘        └──────┬───────┘        │ user)        │       │
      │                      │                └──────────────┘       │
      │                      │                       │               │
      ▼                      ▼                       ▼               │
┌──────────────────────────────────────────────────────────┐        │
│                     PIPELINE CONTEXT                       │        │
│            (per-request Dict[str, Any], ephemeral)         │        │
└──────────────────────────────────────────────────────────┘        │
      │                      │                       │               │
      ▼                      ▼                       ▼               │
┌────────────┐        ┌──────────────┐        ┌──────────────┐       │
│   Memory   │        │   X-Ray /   │        │   Research   │       │
│  Manager   │        │  MetaLearner │        │   Platform   │       │
│ (RAG,Epi,  │        │ (global)     │        │ (global)     │       │
│  Sem)      │        └──────────────┘        └──────────────┘       │
│ (global)   │               │                       │               │
└────────────┘               ▼                       ▼               │
                      ┌──────────────┐        ┌──────────────┐       │
                      │   HEALER    │        │  Experience  │       │
                      │  (global)   │        │   Learner    │       │
                      └──────────────┘        │  (global)    │───────┘
                                              └──────────────┘

                    ┌──────────────────┐
                    │  Session Manager │
                    │  (global, all    │
                    │   sessions)      │
                    └──────────────────┘
```

### 4.2 Cyclic Dependencies

```
EmotionUpdatePhase ──► EmotionEngine ──► EmotionPhase ──► GeneratePhase
      │                                                      │
      └────────────────── PipelineContext ◄──────────────────┘

ImpulseUpdatePhase ──► ImpulseCore ──► ImpulsePhase ──► GeneratePhase
      │                                                    │
      └──────────────── PipelineContext ◄──────────────────┘

SaveEpisodePhase ──► EpisodicMemory ──► EpisodicPhase ──► GeneratePhase
      │                                                  │
      └─────────────── PipelineContext ◄─────────────────┘
```

These are not bugs -- they are the designed write-then-read cycle within a single pipeline execution. The risk is **interleaving across concurrent requests** when multiple pipelines read and write the same global singleton.

### 4.3 Contention Map (Concurrent Access Risk)

| Subsystem | Phase (Read) | Phase (Write) | Sync/Async | Protection |
|-----------|-------------|---------------|------------|------------|
| EmotionEngine | EmotionPhase (7) | EmotionUpdatePhase (17) | Both sync | `threading.RLock()` within model only |
| ImpulseCore | ImpulsePhase (8) | ImpulseUpdatePhase (18) | Both sync | None across requests |
| KnowledgeGraph | KGPhase (4) | ExtractionPhase (16) | Both sync | None |
| UserPersona | PersonaPhase (9) | PersonaEvolutionPhase (21 BG) | Sync + BG | None |
| EpisodicMemory | EpisodicPhase (5) | SaveEpisodePhase (15) | Both sync | None |

**Risk level for all:** Moderate -- sequential within a single request, but concurrent requests interleave reads and writes to the same global state.

---

## Stage 5: Architecture Smells

### 5.1 Smell Severity Matrix

| Severity | Count | Examples |
|----------|-------|---------|
| **CRITICAL** | 4 | PersonaMemory.users duplicates UserPersona; 4 MetaLearners with no cross-talk; Emotion/Impulse globals with no session isolation; Session identity fractured across 4+ systems |
| **HIGH** | 8 | All memory modules are global singletons; mutable `Dict[str, Any]` as cross-phase contract; no lifecycle teardown; dual trace persistence (PG + SQLite with different schemas); backup bytes stored in RAM; 3 buggy ctx reads; orphaned MemoryMaintenancePhase; simulated cleanup |
| **MEDIUM** | 6 | Dual PipelineContext construction; no impulse decay; Exponential session JSON growth; 5 contention points; ~10 written-but-never-read ctx keys; no TTL-based eviction |
| **LOW** | 5 | `social_connection` written but never read; `current_impulse.txt` redundancy; `ImpulseState` dead DTO; `_topic_stats` dead accumulation; `_history` lost on restart |

### 5.2 CRITICAL Smells

#### CS-1: PersonaMemory.users duplicates UserPersona

`PersonaMemory` (global singleton) stores `users: Dict[str, InteractionMemory]` -- per-user interaction data. `UserPersona` (per-user managed separately) stores the same kind of information. On every pipeline cycle, **both** are updated via independent code paths with no synchronization. They can diverge.

#### CS-2: Four independent MetaLearners

`core/xray/meta_learner.py`, `core/evolution/meta_learner.py`, `backend/learning/experience.py`, and `HEALER/healer/meta/meta_learner.py` all independently track strategy outcomes, interaction patterns, or learning signals. None share data, none coordinate. The same interaction is analyzed four different ways.

#### CS-3: Global singletons where session isolation is needed

EmotionEngine and ImpulseCore are process-wide singletons. User A's interaction changes the emotional/cognitive state for User B. In a multi-user deployment, this is semantically broken.

#### CS-4: Session identity fractured across 4 systems

SessionManager (sess_{uuid}), Supabase Auth (JWT), X-Ray (request_id), and Experience Store / Frontend (dialog_id) all manage session-like identifiers with manual, error-prone mapping between them.

### 5.3 HIGH Smells

#### HS-1: Mutable Dict[str, Any] as cross-phase contract

PipelineContext.context has no schema, no typing, no documentation. 30+ phases communicate through a shared mutable dict by convention only.

#### HS-2: Dual trace persistence with different schemas

X-Ray traces stored in both SQLite and PostgreSQL with different column sets. No indication of which is authoritative.

#### HS-3: Backup bytes in RAM

HealingChangesStore stores file backup content as `dict[str, tuple[str, bytes]]` in memory instead of writing to disk. Could consume significant RAM.

#### HS-4: No lifecycle teardown

Zero subsystems implement `close()`, `shutdown()`, or `__exit__`. Open DB connections, daemon threads, and file handles leak on process exit.

---

## Candidate Context Analysis

### 5.1 What MUST be in CognitiveContext

| Component | Rationale | Current Scope | Proposed Scope |
|-----------|-----------|---------------|----------------|
| **Session ID** | Every pipeline execution needs identity | Fractured across 4 systems | Single `session_id` |
| **Emotion Snapshot** | Read by GeneratePhase, IdentityPhase, SaveEpisodePhase | Global singleton | Per-session |
| **Impulse Snapshot** | Read by GeneratePhase (bias injection) | Global singleton | Per-session |
| **Strategy** | Read by GeneratePhase, EvaluationPhase | Per-request (set by executor) | Per-request |
| **Topic** | Missing entirely -- no "current topic" concept | Not tracked | Per-session |

### 5.2 What MAY be in CognitiveContext (v1.5)

| Component | Rationale | Dependency |
|-----------|-----------|------------|
| **Persona traits** | Influences generation style | Persona subsystems unchanged |
| **Confidence** | Current system confidence level | MetaLearner unchanged |
| **Active goal** | Conversation direction | Not yet implemented |

### 5.3 What MUST NOT be in CognitiveContext

| Component | Reason |
|-----------|--------|
| Memory (RAG, Episodic, Semantic) | They are storage, not state. CognitiveContext is a snapshot, not a store. |
| Entire PersonaMemory | Only style/context needed, not full user history |
| MetaLearner stats | Accumulated statistics, not current context |
| HEALER status | Operational, not cognitive |
| Research Platform data | Experimental, not operational |
| X-Ray trace data | Observability, not cognition |
| Conversation History | Raw messages are storage, not state |

### 5.4 CognitiveContext v0.1 Contract (Draft)

```python
@dataclass(frozen=True)
class CognitiveContextSnapshot:
    session_id: str
    request_id: str
    timestamp: datetime

    # Per-session state (loaded from scoped stores)
    emotion: EmotionState
    impulse: ImpulseSnapshot
    current_topic: str
    previous_topic: str

    # Per-request state (computed by executor)
    strategy: str
    strategy_confidence: float
```

**Non-goals:** No persistence. No memory management. No decision making. No ownership transfer.

---

## Critical Findings Summary

### What to fix immediately (defects, not features)

| # | Finding | Location | Impact |
|---|---------|----------|--------|
| 1 | `execution_time_ms` read never written | `phases/evaluation.py:44` | Silent no-op in evaluation |
| 2 | `procedure_used` read never written | `phases/save_episode.py:23` | Dead code branch |
| 3 | `result_dict` read never written | `phases/reflection.py:22` | Reflection gets empty input |
| 4 | MemoryMaintenancePhase orphaned | `phases/memory_maintenance.py` | Fusion/forgetting logic never runs |
| 5 | Hygiene cleanup is simulated | `memory/hygiene.py` | No actual deduplication |
| 6 | Emotion update listener reads non-existent field "тревога" | `intent_router.py` | Silent no-op |

### What to discuss architecturally

| # | Question | Options |
|---|----------|---------|
| 1 | Should Emotion/Impulse be per-session or global? | Global (current) vs scoped by session_id |
| 2 | Should PersonaMemory.users be removed? | Yes -- UserPersona already owns this |
| 3 | Should 4 MetaLearners be unified? | Unify vs accept fragmentation |
| 4 | Should trace storage be PG-only or SQLite-only? | Current: both, different schemas |
| 5 | Should PipelineContext get a typed schema? | Typed dataclass vs continue with Dict |
| 6 | Should HEALER backups be on disk? | RAM (current) vs filesystem |

### Next: ADR-0002 decision

This audit provides the factual foundation. The next step is to decide whether Cognitive Context Layer (ADR-0002) addresses the right problems, and whether to proceed with implementation or address the critical defects first.
