# 03_lifecycle.md — Memory Lifecycle Diagrams (Auto-Generated)

**Phase:** 1 — Memory Lifecycle  
**Status:** Auto-generated from code scan  
**Scan date:** 2026-07-31  
**Source:** `scripts/lifecycle_scanner.py`

---

## Purpose

Визуализировать циклы жизни каждого объекта памяти: от создания до удаления/консолидации.

---

## 1. Episode (EpisodicMemory)

### Lifecycle
```
Created (SaveEpisodePhase.add_episode)
    ↓
Active (available for recall)
    ↓
Consolidated (Consolidation.consolidate_all) ──→ Semantic Fact/Procedure
    ↓
Archived (after consolidation)
    ↓
Deleted (NOT IMPLEMENTED)
```

### Transitions

| From → To | Trigger | Actor | Conditions |
|-----------|---------|-------|------------|
| Created → Active | `SaveEpisodePhase.add_episode()` | SaveEpisodePhase | После генерации ответа |
| Active → Consolidated | `Consolidation.consolidate_all()` | MemoryConsolidator | Каждые 10 диалогов |
| Consolidated → Archived | После консолидации | MemoryConsolidator | После извлечения фактов |
| Archived → Deleted | (не реализовано) | — | — |

### Time in State

| State | Avg Duration | Max | Notes |
|-------|--------------|-----|-------|
| Active | ~10 диалогов | ∞ | До консолидации |
| Consolidated | мгновенно | мгновенно | Мгновенный переход |
| Archived | ∞ | ∞ | Никогда не удаляется |

### Invariants
- ✅ Episode создаётся ровно один раз за диалог
- ✅ Consolidation происходит ровно один раз за Episode
- ❌ Нет Deleted состояния (накопление бесконечно)
- ❌ Нет TTL для Active эпизодов

---

## 2. Fact (SemanticMemory — Facts)

### Lifecycle
```
Created (Consolidation.add_fact)
    ↓
Active (доступен для RAG)
    ↓
Consolidated → Roots (опционально)
    ↓
Archived / Deleted (не реализовано)
```

### Transitions

| From → To | Trigger | Actor |
|-----------|---------|-------|
| Created → Active | `Consolidation.add_fact()` | Consolidation |
| Active → Consolidated → Roots | `Consolidation.consolidate_semantic_to_roots()` | Consolidation |
| Active → Archived | (не реализовано) | — |

### Invariants
- ❌ Нет deduplication при создании
- ❌ Нет TTL / forgetting
- ❌ Нет importance-based eviction

---

## 3. Procedure (SemanticMemory — Procedures)

### Lifecycle
```
Created (Consolidation.add_procedure)
    ↓
Active (доступен для SemanticPhase)
    ↓
Обновление / Удаление (не реализовано)
```

### Problems
- ❌ Нет обновления процедур после создания
- ❌ Нет TTL / versioning

---

## 4. EmotionState (EmotionEngine)

### Lifecycle
```
Created (per session, SessionEmotionStore)
    ↓
Active (live updates via apply_event)
    ↓
Decay (каждую минуту, к нулю)
    ↓
Persisted (SessionEmotionStore.save)
    ↓
Restored (SessionEmotionStore.get_or_create)
    ↓
Evicted (TTL 24h / LRU 500)
```

### Transitions

| From → To | Trigger | Actor |
|-----------|---------|-------|
| Created → Active | `SessionEmotionStore.get_or_create()` | Pipeline |
| Active → Decay | Timer (каждую минуту) | `_decay_loop` |
| Active → Persisted | `SessionEmotionStore.save()` | EmotionUpdatePhase |
| Persisted → Restored | `SessionEmotionStore.get_or_create()` | Next Pipeline turn |
| Active → Evicted | TTL 24h / LRU 500 | `SessionEmotionStore._evict_*` |

### Decay Details
- **Rate**: 0.001/sec (6% в минуту к нулю)
- **Interval**: 60 сек
- **Target**: все PAD параметры → 0.0

### Invariants
- ✅ Session isolation (per user_id)
- ✅ Auto-decay работает
- ✅ TTL / LRU eviction работает
- ❌ Decay rate захардкожен
- ❌ Нет per-user настройки decay rate

---

## 5. ImpulseCore

### Lifecycle
```
Created (ImpulseManager.start / get_impulse_core)
    ↓
Active (updates via ImpulseUpdatePhase)
    ↓
Stack operations (push/pop)
    ↓
Persisted (ImpulseManager.save)
    ↓
Restored (ImpulseManager.load)
```

### Transitions
| From → To | Trigger | Actor |
|-----------|---------|-------|
| Created → Active | `ImpulseManager.start()` | Startup |
| Active → Updated | `ImpulseUpdatePhase.apply_deltas()` | Pipeline |
| Active → Pushed | `ImpulseCore.push()` | ImpulseUpdatePhase |
| Active → Popped | `ImpulseCore.pop()` | ImpulseUpdatePhase |
| Active → Persisted | `ImpulseManager.save()` | Background |

### Problems
- ❌ Нет session isolation (глобальный singleton)
- ❌ Нет TTL / auto-decay
- ❌ Stack может расти бесконечно (нет max size)

---

## 5. PersonaMemory

### Lifecycle
```
Created (init / load)
    ↓
Active (adjust_trait, add_reflection, evolve_from_dialog)
    ↓
Persisted (save → PG + JSON)
    ↓
Restored (load)
```

### Transitions
| From → To | Trigger | Actor |
|-----------|---------|-------|
| Created → Active | `PersonaMemory()` init | Startup |
| Active → Updated | `adjust_trait()`, `evolve_from_dialog()` | Pipeline / EmotionUpdate |
| Active → Persisted | `_save()` (after each change) | PersonaMemory |
| Persisted → Restored | `PersonaMemory()` init | Startup |

### Problems
- ❌ Duplicate with `UserPersona` (per-user)
- ❌ Global singleton — no session isolation
- ❌ No TTL for reflections/traits

---

## 6. UserPersona (per-user)

### Lifecycle
```
Created (UserPersonaManager.create_persona)
    ↓
Active (adjust_style, record_interaction)
    ↓
Persisted (save → PG)
    ↓
Restored (get_persona)
    ↓
Evicted (TTL / LRU — NOT IMPLEMENTED)
```

### Problems
- ❌ No TTL / eviction
- ❌ Separate from PersonaMemory (duplication)

---

## 7. RootsMemory

### Lifecycle
```
Created (init / load)
    ↓
Active (immutable after init)
    ↓
Persisted (save → PG + JSON)
    ↓
Restored (load)
```

### Problems
- ❌ Static, never evolves
- ❌ No versioning

---

## 7. RAGMemory

### Lifecycle
```
Created (init / get_rag)
    ↓
Active (add_dialog, search)
    ↓
Persisted (auto-save to PG)
    ↓
Consolidated → Episodic/Semantic (via Consolidation)
```

### Problems
- ❌ No TTL for dialogs
- ❌ No cleanup of old dialogs
- ❌ `get_recent` param mismatch (`limit` vs `n_results`) — FIXED

---

## 8. Working Memory / PipelineContext

### Lifecycle
```
Created (PipelineExecutor.execute)
    ↓
Mutated (all phases read/write ctx.context)
    ↓
Checkpointed (X-Ray trace)
    ↓
Discarded (end of turn)
```

### Key Keys in ctx.context
| Key | Written By | Read By | Lifetime |
|-----|------------|---------|----------|
| `strategy` | PipelineExecutor | All phases | Turn |
| `intent` | IntentPhase | RAG, Semantic, Generate | Turn |
| `rag_context` | RAGPhase | Generate | Turn |
| `episodic_context` | EpisodicPhase | Generate | Turn |
| `procedure_context` | SemanticPhase | Generate | Turn |
| `emotion_state` | EmotionPhase | Generate, EmotionUpdate | Turn |
| `impulse_bias` | ImpulsePhase | Generate | Turn |
| `response` | GeneratePhase | Evaluation, SaveEpisode | Turn |
| `truth_confidence` | TruthLoop | SaveEpisode | Turn |

### Problems
- ❌ Untyped `Dict[str, Any]` — no contracts
- ❌ Duplication: `emotion_state` vs `emotion_style`
- ❌ `pipeline_result` duplicated in `ctx.context["pipeline_result"]`

---

## 8. X-Ray / TraceCollector

### Lifecycle
```
Created (TraceCollector.start_session)
    ↓
Recorded (record_event per phase)
    ↓
Completed (TraceCollector.complete_session)
    ↓
Persisted (HistoryRecorder → PG)
```

### Problems
- ❌ No MemoryEvent type
- ❌ No integration with memory components

---

## Cross-Cutting Concerns

| Aspect | Status |
|--------|--------|
| **Single Owner per State** | ❌ (Emotion, Impulse, Persona, RAG) |
| **Session Isolation** | ✅ Emotion only |
| **TTL / Eviction** | ✅ Emotion only |
| **Deduplication** | ❌ (Semantic, Episodic) |
| **Importance Scoring** | ❌ |
| **Audit Trail** | ❌ (no MemoryEvent) |
| **Typed Contracts** | ❌ (Dict[str, Any]) |

---

## Next: Phase 2 — Flow Mapping

*04_flow_mapping.md — как память течёт через Pipeline*