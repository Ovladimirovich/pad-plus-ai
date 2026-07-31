# 05_operations.md — Memory Operation Catalog

**Phase:** 5 — Operation Catalog  
**Status:** Draft  
**Based on:** 01_inventory, 02_ownership, 03_lifecycle, 04_flow_mapping

---

## Purpose

Полный каталог **всех операций** с памятью в PAD+ AI.

> Цель: каждая операция имеет владельца, триггер, и метрику.

---

## Operation Categories

| Category | Operations |
|----------|------------|
| **CRUD** | READ, WRITE, DELETE, UPDATE |
| **Lifecycle** | CREATE, ARCHIVE, RESTORE, EXPIRE, PURGE |
| **Maintenance** | DECAY, CONSOLIDATE, MERGE, DEDUP, COMPRESS, SUMMARIZE, REINDEX |
| **Verification** | VERIFY, VALIDATE, AUDIT, RECONCILE |
| **Query** | SEARCH, RECALL, LOOKUP, SCAN, STREAM |
| **Transformation** | TRANSFORM, ENRICH, DENORMALIZE, NORMALIZE, PROJECT |
| **Meta** | VERIFY, AUDIT, SNAPSHOT, CHECKPOINT, RESTORE |

---

## Complete Operation Catalog

### 1. Episodic Memory (EpisodicMemory)

| Op | Trigger | Owner | Phase | Metric |
|----|---------|-------|-------|--------|
| **CREATE** | SaveEpisodePhase | EpisodicMemory | SaveEpisode | `episodes_created_total` |
| **READ (recent)** | Consolidation, Pipeline | EpisodicMemory | Consolidation, various | `episodes_read_recent_count` |
| **READ (by id)** | Research, Pipeline | EpisodicMemory | various | `episodes_read_by_id_count` |
| **READ (search)** | RAG fallback, Consolidation | EpisodicMemory | various | `episodes_searched_count` |
| **READ (all)** | Consolidation | EpisodicMemory | Consolidation | `episodes_read_all_count` |
| **DELETE** | TTL expiry, Manual | EpisodicMemory | Background | `episodes_deleted_count` |
| **ARCHIVE** | TTL threshold | EpisodicMemory | Background | `episodes_archived_count` |
| **VERIFY** | Audit, Repair | EpisodicMemory | Manual/Scheduled | `episodes_verified_count` |

---

### 2. Semantic Memory (SemanticMemory)

| Op | Trigger | Owner | Phase | Metric |
|----|---------|-------|-------|--------|
| **CREATE (fact)** | Consolidation, Pipeline | SemanticMemory | Consolidation, SemanticPhase | `facts_created_total` |
| **CREATE (procedure)** | Consolidation, Pipeline | SemanticMemory | Consolidation, SemanticPhase | `procedures_created_total` |
| **READ (by id)** | SemanticPhase, Pipeline | SemanticMemory | various | `facts_read_by_id_count` |
| **READ (search)** | SemanticPhase, Pipeline | SemanticMemory | various | `facts_searched_count` |
| **READ (get_all)** | Consolidation | SemanticMemory | Consolidation | `facts_get_all_count` |
| **UPDATE (confidence)** | Consolidation, Feedback | SemanticMemory | Consolidation, Feedback | `facts_updated_confidence_count` |
| **UPDATE (content)** | Consolidation, Correction | SemanticMemory | Consolidation | `facts_updated_content_count` |
| **DELETE** | TTL, Deduplication, Manual | SemanticMemory | Background, Dedup | `facts_deleted_count` |
| **MERGE** | Consolidation (dedup) | SemanticMemory | Consolidation | `facts_merged_count` |
| **DEDUPE** | Consolidation, Scheduled | SemanticMemory | Consolidation, Scheduled | `facts_deduped_count` |
| **VERIFY** | Audit | SemanticMemory | Manual/Scheduled | `facts_verified_count` |
| **REINDEX** | Schema change, Manual | SemanticMemory | Manual/Scheduled | `facts_reindexed_count` |

---

### 3. Emotion Engine (PADModel / SessionEmotionStore)

| Op | Trigger | Owner | Phase | Metric |
|----|---------|-------|-------|--------|
| **READ** | EmotionPhase | SessionEmotionStore | EmotionPhase | `emotion_read_count` |
| **WRITE (apply_event)** | EmotionUpdatePhase | SessionEmotionStore | EmotionUpdatePhase | `emotion_events_applied_total` |
| **DECAY** | Background timer (1min) | PADModel | Background | `emotion_decay_events_total` |
| **PERSIST** | EmotionUpdatePhase | SessionEmotionStore | EmotionUpdatePhase | `emotion_persist_total` |
| **RESTORE** | Session start | SessionEmotionStore | Session init | `emotion_restore_count` |
| **DECAY_CONFIG** | Config change | PADModel | Config | `emotion_decay_config_changes` |

---

### 4. Impulse Engine (ImpulseCore / SessionImpulseStore)

| Op | Trigger | Owner | Phase | Metric |
|----|---------|-------|-------|--------|
| **READ** | ImpulsePhase | SessionImpulseStore | ImpulsePhase | `impulse_read_count` |
| **WRITE (apply_deltas)** | ImpulseUpdatePhase | SessionImpulseStore | ImpulseUpdatePhase | `impulse_deltas_applied_total` |
| **PUSH** | ImpulsePhase, Pipeline | ImpulseCore | ImpulsePhase, Pipeline | `impulse_stack_push_count` |
| **POP** | Pipeline, Manual | ImpulseCore | Pipeline | `impulse_stack_pop_count` |
| **SET_WEIGHTS** | ImpulsePhase, Manual | ImpulseCore | ImpulsePhase | `impulse_weights_set_count` |
| **RESET** | Session end, Manual | SessionImpulseStore | Session end | `impulse_reset_count` |
| **DECAY** | Not implemented | — | — | `impulse_decay_not_implemented` |

---

### 4. Persona (PersonaMemory / UserPersonaManager)

| Op | Trigger | Owner | Phase | Metric |
|----|---------|-------|-------|--------|
| **READ (traits)** | PersonaPhase, Pipeline | PersonaMemory | PersonaPhase | `persona_traits_read_count` |
| **WRITE (adjust_trait)** | PersonaEvolutionPhase | PersonaMemory | PersonaEvolutionPhase | `persona_traits_adjusted_count` |
| **WRITE (evolve)** | PersonaEvolutionPhase | PersonaMemory | PersonaEvolutionPhase | `persona_evolutions_total` |
| **READ (user style)** | PersonaPhase | UserPersonaManager | PersonaPhase | `user_persona_style_read_count` |
| **WRITE (adjust_style)** | PersonaPhase, PersonaEvolutionPhase | UserPersonaManager | PersonaPhase, PersonaEvolutionPhase | `user_persona_style_adjusted_count` |
| **PERSIST** | PersonaEvolutionPhase | UserPersonaManager | PersonaEvolutionPhase | `user_persona_persist_count` |
| **CREATE (new user)** | First interaction | UserPersonaManager | Session init | `user_persona_created_count` |

---

### 4. RAG Memory (RAGMemory)

| Op | Trigger | Owner | Phase | Metric |
|----|---------|-------|-------|--------|
| **SEARCH** | RAGPhase | RAGMemory | RAGPhase | `rag_searches_total` |
| **INSERT (add_dialog)** | Pipeline, RAGPhase | RAGMemory | Pipeline, RAGPhase | `rag_dialogs_inserted_total` |
| **GET_RECENT** | Consolidation, EmotionLearner | RAGMemory | Consolidation, EmotionLearner | `rag_recent_read_count` |
| **GET_STATS** | Consolidation, Monitoring | RAGMemory | Consolidation, Monitoring | `rag_stats_read_count` |
| **GET_TOPIC_STATS** | Consolidation | RAGMemory | Consolidation | `rag_topic_stats_read_count` |
| **DELETE** | TTL, Manual | RAGMemory | Background | `rag_dialogs_deleted_count` |

---

### 5. Roots Memory (RootsMemory)

| Op | Trigger | Owner | Phase | Metric |
|----|---------|-------|-------|--------|
| **READ** | RootsPhase, Pipeline | RootsMemory | RootsPhase, Pipeline | `roots_read_count` |
| **CREATE (init)** | Startup, Migration | RootsMemory | Startup | `roots_init_count` |
| **UPDATE** | Never (by design) | — | — | `roots_update_not_allowed` |

---

### 5. Pipeline Context / Working Memory

| Op | Trigger | Owner | Phase | Metric |
|----|---------|-------|-------|--------|
| **READ** | All Phases | PipelineContext | All Phases | `ctx_read_total` |
| **WRITE** | All Phases (via PhaseResult) | PipelineExecutor | All Phases | `ctx_write_total` |
| **CLEAR** | Turn end | PipelineExecutor | Turn end | `ctx_clear_count` |
| **SNAPSHOT** | X-Ray, Debug | PipelineExecutor | Turn end | `ctx_snapshot_count` |

---

### 6. X-Ray / Trace

| Op | Trigger | Owner | Phase | Metric |
|----|---------|-------|-------|--------|
| **WRITE (event)** | All Phases | TraceCollector | All Phases | `trace_events_written_total` |
| **READ (session)** | X-Ray API, Replay | TraceCollector | API | `trace_sessions_read_count` |
| **REPLAY** | Debug, Healer | TraceCollector | Manual | `trace_replay_count` |
| **EXPORT** | Export API | TraceCollector | Manual | `trace_export_count` |

---

### 7. Consolidation (MemoryConsolidator)

| Op | Trigger | Owner | Phase | Metric |
|----|---------|-------|-------|--------|
| **EPISODIC→SEMANTIC** | ControlTick (every 10) | MemoryConsolidator | Background | `consolidation_ep_to_sem_count` |
| **SEMANTIC→ROOTS** | ControlTick (every 10) | MemoryConsolidator | Background | `consolidation_sem_to_roots_count` |
| **RAG→TOPIC_STATS** | ControlTick (every 10) | MemoryConsolidator | Background | `consolidation_rag_topic_count` |
| **FORGET** | TTL, Importance | MemoryConsolidator | Background | `consolidation_forget_count` |
| **MERGE** | SemanticFusion | SemanticMemory | Consolidation | `consolidation_merge_count` |

---

### 7. Session Management (SessionManager)

| Op | Trigger | Owner | Phase | Metric |
|----|---------|-------|-------|--------|
| **CREATE** | New session, API | SessionManager | Session init | `sessions_created_total` |
| **GET** | Pipeline, API | SessionManager | Pipeline, API | `sessions_get_total` |
| **GET_OR_CREATE** | Pipeline, API | SessionManager | Pipeline, API | `sessions_get_or_create_total` |
| **END** | Timeout, Manual | SessionManager | Session end | `sessions_ended_total` |
| **TOUCH** | Activity | SessionManager | Activity | `sessions_touched_total` |
| **EVICT** | TTL, LRU | SessionManager | Background | `sessions_evicted_total` |
| **RECORD_MESSAGE** | Pipeline | SessionManager | Pipeline | `sessions_messages_recorded` |

---

## Operation Summary Matrix

| Component | READ | WRITE | DELETE | DECAY | MERGE | CONSOLIDATE | VERIFY |
|-----------|------|-------|--------|-------|-------|-------------|--------|
| EpisodicMemory | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ✅ |
| SemanticMemory | ✅ | ✅ | ✅ | ❌ | ✅ | ❌ | ✅ |
| RAGMemory | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| RootsMemory | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Emotion (SessionEmotionStore) | ✅ | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ |
| Impulse (SessionImpulseStore) | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| PersonaMemory | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| UserPersonaManager | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| RAGMemory | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| RootsMemory | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Consolidation | ❌ | ✅ | ✅ | ❌ | ✅ | ✅ | ❌ |
| SessionManager | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |

---

## Operation Properties (Standard)

Каждая операция должна иметь:

```python
@dataclass
class MemoryOperation:
    # Identity
    name: str                    # "EpisodicMemory.CREATE"
    category: str                # "CRUD", "LIFECYCLE", etc.
    
    # Ownership
    owner: str                   # "EpisodicMemory"
    phase: str                   # "SaveEpisodePhase"
    
    # Trigger
    trigger: str                 # "SaveEpisodePhase.execute()"
    async: bool                  # True/False
    
    # Contracts
    preconditions: List[str]     # ["session_id exists", "episode valid"]
    postconditions: List[str]    # ["episode stored", "index updated"]
    invariants: List[str]        # ["no duplicate episodes", "ttl > 0"]
    
    # Contracts
    input_schema: Type           # Pydantic model
    output_schema: Type          # Pydantic model
    
    # Metrics
    latency_p99_ms: float
    throughput_qps: float
    error_rate: float
    
    # Observability
    trace: bool                  # True = emit X-Ray event
    alert_on_failure: bool
    
    # Guarantees
    consistency: str             # "strong" | "eventual"
    durability: str              # "sync" | "async"
    isolation: str               # "session" | "global"
```

---

## Next: Phase 6 — Trace Model (MemoryEvent for X-Ray)

*06_trace_model.md — MemoryEvent schema для X-Ray*