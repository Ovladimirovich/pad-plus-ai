# 09_design_principles.md — Memory Design Principles

**Phase:** 9 — Design Principles  
**Status:** Draft  
**Based on:** 01–08

---

## Purpose

Зафиксировать **принципы проектирования** новой архитектуры памяти, выведенные из проблем (08) и исследования (01–07).

---

## Core Principles

### 1. Single Source of Truth
> **У каждого куска состояния ровно один владелец.**

- Никаких dual writers
- Читатели никогда не пишут
- Владелец отвечает за: CREATE, READ, UPDATE, DELETE, TTL, Schema, Eviction

### 2. Session Isolation by Default
> **Любое состояние, относящееся к пользователю/сессии, изолировано по умолчанию.**

- Глобальные синглтоны только для read-only / shared / derived state
- Session-scoped stores по умолчанию для: Emotion, Impulse, RAG, Episodic, Semantic, Persona, Working Memory

### 3. Explicit Lifecycle
> **У каждого объекта памяти явный жизненный цикл.**

- CREATE → ACTIVE → [CONSOLIDATED] → ARCHIVED → DELETED
- Каждый переход имеет триггер, актора, условия
- Нет "вечного" Active без TTL/eviction

### 4. Typed Contracts
> **Никаких `Dict[str, Any]` в критических путях.**

- Все контексты, результаты фаз, события типизированы (Pydantic/dataclass)
- ContractValidator pre/post check на каждом pipeline turn
- Schema evolution: additive only, backward compatible

### 5. Full Observability
> **Никаких "черных ящиков" в памяти.**

- Каждая операция = MemoryEvent в X-Ray
- 100% покрытие: READ, WRITE, DELETE, DECAY, CONSOLIDATE, MERGE, EVICT
- Time-travel debugging: load any turn at any phase

### 6. Unified Forgetting
> **Единый механизм забывания для всех типов памяти.**

- Единый TTL/eviction framework
- Importance scoring (configurable per type)
- Graceful degradation: graceful degradation при давлении

### 6. Unified Forgetting
> **Единый механизм забывания для всех типов памяти.**

- Единый TTL/eviction framework
- Importance scoring (configurable per type)
- Graceful degradation под давлением

### 7. Single Write Path
> **У каждого состояния один путь записи.**

- Никаких dual write paths
- Writer = Owner
- Readers never write

### 7. Single Write Path
> **У каждого состояния один путь записи.**

- Никаких dual write paths
- Writer = Owner
- Readers never write

### 8. Consolidation as First-Class Citizen
> **Консолидация — не background job, а first-class операция.**

- В Pipeline / явный API
- Reversible / compensable
- Observable (MemoryEvent)

### 9. Session Isolation by Default
> **Изоляция сессий — не опция, а дефолт.**

- Глобальные синглтоны только для read-only / derived state
- Per-session stores по умолчанию

### 10. Memory as Observable
> **Память — это измерение в X-Ray, не скрытый state.**

- MemoryEvent = first-class X-Ray event
- Memory Trace = first-class X-Ray trace
- Time-travel debugging = first-class feature

---

## Anti-Patterns (What We Don't Do)

| Anti-Pattern | Instead |
|--------------|---------|
| Global singleton for session state | Per-session store |
| Dict[str, Any] context | Typed context sections |
| Dual writers | Single owner |
| Implicit lifecycle | Explicit lifecycle with TTL |
| Implicit consolidation | Explicit, observable consolidation |
| Implicit forgetting | Explicit TTL/importance |
| Implicit session isolation | Explicit session_id in all stores |
| Dual write paths | Single owner |
| Implicit consolidation | Explicit, observable consolidation |
| Implicit forgetting | Explicit TTL/importance |

---

## Decision Framework

| Decision | Principle | Example |
|----------|-----------|---------|
| Where to store X? | Single Owner | EpisodicMemory owns Episodes |
| Who writes X? | Single Writer | Only EpisodicMemory writes Episodes |
| When does X expire? | Explicit Lifecycle | TTL = 30d for Episodes |
| Who reads X? | Readers never write | SemanticPhase reads Episodic |
| How to forget? | Unified Forgetting | TTL + Importance scoring |
| Where to consolidate? | Explicit consolidation | Consolidation API in Pipeline |
| How to debug? | Full observability | MemoryEvent in X-Ray |

---

## Architecture Guardrails (Code Review Checklist)

- [ ] New state has single owner documented
- [ ] New state has explicit lifecycle (TTL, transitions)
- [ ] New state has session isolation (if user-facing)
- [ ] New state has typed schema (Pydantic)
- [ ] New state emits MemoryEvent on all ops
- [ ] No Dict[str, Any] in new critical paths
- [ ] No dual writers for same state
- [ ] No global singleton for session-scoped state
- [ ] Consolidation is explicit, not background magic
- [ ] TTL/forgetting defined for new state

---

## Evolution Rules

| Change | Process |
|--------|---------|
| New memory type | Add to Inventory → Ownership → Lifecycle → Trace → Metrics |
| Change lifecycle | Update Lifecycle doc → Update Trace → Update Metrics |
| Change ownership | Update Ownership doc → Migrate data → Deprecate old |
| Add operation | Add to Operations catalog → Instrument → Add metrics |
| New consolidation | Add to Flow Mapping → Add to Operations → Instrument |

---

*These principles are living. Update as MRI progresses.*