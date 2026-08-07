# 10_architecture_proposal.md — Memory Architecture Proposal

**Phase:** 4 — Architecture Proposal  
**Status:** Draft  
**Based on:** 01–09  
**Status:** Draft for Review

---

## Executive Summary

Based on MRI findings, we propose **Memory Evolution** — эволюция памяти PAD+ через 4 итеративных этапа.

> **Главный вывод:** Проблема не в отсутствии "Cognitive Workspace", а в **отсутствии наблюдаемости, изоляции и цикла жизни** у существующей памяти.

---

## Current State Summary

| Problem | Severity |
|---------|----------|
| No session isolation (5/7 components) | P0 |
| No TTL/forgetting (6/7 components) | P0 |
| No deduplication (Semantic, Episodic) | P0 |
| No audit trail (MemoryEvent) | P1 |
| Untyped PipelineContext | P1 |
| Dual Persona owners | P1 |

---

## Proposed Architecture: Memory Evolution

### Vision
```
┌─────────────────────────────────────────────────────────────┐
│                    MEMORY EVOLUTION                          │
├─────────────────────────────────────────────────────────────┤
│  Layer 1: Observability (MemoryEvent + X-Ray)               │
│  Layer 2: Session Isolation (Session Stores)                │
│  Layer 3: Lifecycle Management (TTL, Forgetting, Consol.)  │
│  Layer 4: Unified Memory API (Typed, Contracts)            │
└─────────────────────────────────────────────────────────────┘
```

---

## Phase D' Implementation Plan

### D'‑1: Memory Trace & Instrumentation (Week 1-2)
**Goal:** Full MemoryEvent coverage in X-Ray

| Component | Action |
|-----------|--------|
| `EpisodicMemory` | Instrument READ/WRITE/SEARCH |
| `SemanticMemory` | Instrument READ/WRITE/CONSOLIDATE |
| `RAGMemory` | Instrument READ/WRITE/SEARCH |
| `RootsMemory` | Instrument READ |
| `SessionEmotionStore` | Instrument READ/WRITE/DELETE/DECAY |
| `SessionImpulseStore` | Instrument READ/WRITE/DELETE/STACK |
| `PersonaMemory` | Instrument READ/WRITE |
| `UserPersonaManager` | Instrument READ/WRITE |
| `SessionManager` | Instrument CRUD |
| `MemoryConsolidator` | Instrument CONSOLIDATE |
| `PipelineExecutor` | Auto-instrument per phase |

**Deliverable**: `core/xray/memory_trace.py` + instrumentation in all components

---

### D'‑2: Session Isolation (Week 2-3)
**Goal:** Все сессионные данные → per-session stores

| Component | Before | After |
|-----------|--------|-------|
| Emotion | `SessionEmotionStore` ✅ | Keep |
| Impulse | `ImpulseCore` (global) | `SessionImpulseStore` (new) |
| Persona | `PersonaMemory` (global) | `UserPersonaManager` (per-user) |
| RAG | `RAGMemory` (global) | `SessionRAGStore` (new) |
| Semantic | `SemanticMemory` (global) | `SessionSemanticStore` (new, cache layer) |
| Episodic | `EpisodicMemory` (global) | `SessionEpisodicStore` (new, cache layer) |
| Roots | `RootsMemory` (global) | `RootsMemory` (read-only, shared) |
| RAG | `RAGMemory` | `SessionRAGStore` |

**Pattern**: Все сессионные stores наследуют базовый `SessionStore[State]` с TTL, LRU, per-session isolation.

---

### D'‑3: Lifecycle & Forgetting (Week 3-4)
**Goal:** Единый фреймворк TTL/forgetting для всех компонентов

```python
class MemoryLifecycleConfig:
    # Per-component TTL
    ttl_hours: Dict[MemoryComponent, int] = {
        EpisodicMemory: 30 * 24,      # 30 days
        SemanticMemory: 90 * 24,      # 90 days
        RAGMemory: 30 * 24,
        RootsMemory: None,            # forever
        EmotionEngine: 24,            # 24 hours (decay)
        ImpulseCore: 7 * 24,          # 7 days
        PersonaMemory: 90 * 24,
        RAGMemory: 30 * 24,
    }
    
    # Eviction policies
    max_items: Dict[MemoryComponent, int] = {
        EpisodicMemory: 100000,
        SemanticMemory: 50000,
        RAGMemory: 10000,
        EmotionEngine: 5000,
        ImpulseCore: 1000,
    }
    
    # Forgetting strategies
    forgetting_strategy: Dict[MemoryComponent, str] = {
        EpisodicMemory: "ttl+importance",
        SemanticMemory: "importance+access",
        RAGMemory: "ttl+access",
        ImpulseCore: "stack+ttl",
    }
```

**Components to update:**
- `EpisodicMemory`: TTL + importance-based eviction
- `SemanticMemory`: Importance + access-based eviction + dedup
- `RAGMemory`: TTL + access-based eviction
- `SessionImpulseStore`: TTL + stack limit (max 50)
- `SessionEmotionStore`: Already has TTL/LRU

---

### D'‑4: Unified Memory API (Week 4-5)
**Goal:** Typed, contract-driven API для всех фаз

```python
# core/memory/memory_service.py

class MemoryService:
    """Единая точка доступа ко всей памяти"""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.episodic = get_session_episodic_store(session_id)
        self.semantic = get_session_semantic_store(session_id)
        self.emotion = get_session_emotion_store()
        self.impulse = get_session_impulse_store()
        self.persona = get_user_persona_manager()
        self.rag = get_session_rag_store()
        self.roots = get_roots_memory()
    
    # Typed reads
    def get_recent_episodes(self, n: int = 10) -> List[Episode]: ...
    def search_semantic(self, query: str, k: int = 10) -> List[Fact]: ...
    def get_emotion_state(self) -> EmotionState: ...
    def get_impulse_state(self) -> ImpulseState: ...
    def get_persona_context(self) -> str: ...
    def get_roots_context(self) -> str: ...
    
    # Typed writes
    def add_episode(self, episode: Episode) -> str: ...
    def add_fact(self, fact: Fact) -> str: ...
    def add_procedure(self, proc: Procedure) -> str: ...
    def apply_emotion_event(self, event: str, intensity: float): ...
    def apply_impulse_delta(self, delta: ImpulseDelta): ...
```

---

### D'‑5: Typed PipelineContext (Week 5)
**Goal:** Заменить `Dict[str, Any]` на типизированный контекст

```python
# core/pipeline/context.py

class PipelineContext:
    user_message: str
    session_id: Optional[str]
    api_key: Optional[str]
    provider: Optional[str]
    
    # Typed sections (replaces Dict[str, Any])
    strategy: StrategyContext
    execution: ExecutionContext
    session: SessionContext
    memory: MemoryContext
    emotion: EmotionContext
    impulse: ImpulseContext
    experience: ExperienceContext
    persona: PersonaContext
    # ...
```

---

### D'‑6: Contract Validation (Week 5-6)
**Goal:** ContractValidator в каждом pipeline turn

```python
# core/pipeline/contracts.py (already exists)
# Integration in PipelineExecutor.execute()

async def execute(self, ...):
    # ... setup ...
    for phase_name, phase in self._phases:
        # PRE-CHECK
        violations = self._contract_validator.pre_check(
            phase_name, set(ctx.context.keys())
        )
        if violations:
            logger.warning(f"Pre-check failed [{phase_name}]: {violations}")
        
        phase_result = await phase.execute(ctx)
        
        # POST-CHECK
        if phase_result.data:
            produced = set(phase_result.data.keys())
            violations = self._contract_validator.post_check(
                phase_name, produced
            )
            if violations:
                logger.warning(f"Post-check failed [{phase_name}]: {violations}")
```

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        Pipeline Turn                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  MemoryService(session_id)                                       │
│  ├── SessionEpisodicStore      ← EpisodicMemory                │
│  ├── SessionSemanticStore      ← SemanticMemory (cache)        │
│  ├── SessionEmotionStore       ← PADModel (per session)        │
│  ├── SessionImpulseStore       ← ImpulseCore (per session)     │
│  ├── UserPersonaManager        ← UserPersona (per user)        │
│  ├── SessionRAGStore           ← RAGMemory (per session)       │
│  ├── RootsMemory               ← (shared, read-only)           │
│  └── SessionManager            ← SessionContext                │
│                                                                  │
│  PipelineContext (typed)                                        │
│  ├── strategy: StrategyContext                                 │
│  ├── execution: ExecutionContext                               │
│  ├── session: SessionContext                                   │
│  ├── memory: MemoryContext                                     │
│  ├── emotion: EmotionContext                                   │
│  ├── impulse: ImpulseContext                                   │
│  ├── experience: ExperienceContext                             │
│  └── persona: PersonaContext                                   │
│                                                                  │
│  ContractValidator: pre_check / post_check per phase          │
│  MemoryTraceService: MemoryEvent → X-Ray                       │
└─────────────────────────────────────────────────────────────────┘
```

---

## Migration Strategy

| Phase | Migration | Risk | Rollback |
|-------|-----------|------|----------|
| D'‑1 | Add MemoryEvent instrumentation | Low | Feature flag |
| D'‑2 | Session stores (Emotion ✅, Impulse, RAG, Semantic) | Medium | Per-component rollback |
| D'‑3 | TTL/forgetting framework | Medium | Config rollback |
| D'‑4 | MemoryService API | Low | Feature flag |
| D'‑5 | Typed PipelineContext | Medium | Gradual typing |
| D'‑6 | ContractValidator integration | Low | Config toggle |

---

## Success Metrics (Post D')

| Metric | Target |
|--------|--------|
| Session isolation violations | 0 |
| MemoryEvent coverage | 100% operations |
| Checkpoint latency p99 | < 10ms |
| Session isolation violations | 0 |
| Memory growth rate | < 5%/month |
| Consolidation lag | < 5 turns |
| Pipeline context typing | 100% typed |

---

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Session store overhead | Medium | High | Async writes, batch, benchmark |
| Migration breaks existing | Low | Critical | Feature flags, gradual rollout |
| Consolidation breaks | Low | High | Integration tests |
| Trace overhead | Low | Medium | Sampling, async flush |

---

## Decision Required

| Decision | Options | Recommendation |
|----------|---------|----------------|
| **Session store pattern** | Per-component stores vs unified SessionStore | Per-component (isolation) |
| **TTL config** | Per-component YAML vs DB | YAML (versioned) |
| **Persona consolidation** | Deprecate PersonaMemory fully | Yes (UserPersonaManager only) |
| **Working Memory** | Typed PipelineContext vs Dict | Typed (contracts) |
| **MemoryEvent sampling** | 100% vs sampled | 100% (observability first) |

---

*Ready for Review → Approve → D' Implementation Sprint*