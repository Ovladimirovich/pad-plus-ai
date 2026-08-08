# PAD+ AI — План дальнейших действий (Two-Stream Strategy)

**Дата:** Июль 2026  
**Статус:** Phase A ✅ | Phase B ✅ | Phase C 🔄 (in progress)  
**Решено:** Не переходить сразу к Phase D / Cognitive Context. Ввести **Research Stream** после Phase C.

---

## 🎯 Стратегия: Two-Stream Development

```
┌─────────────────────────────────────────────────────────────────┐
│  STREAM 1 — Engineering (последовательно, без риска)            │
├─────────────────────────────────────────────────────────────────┤
│  Phase A: Architecture Cleanup        ✅ DONE                   │
│  Phase B: Pipeline Stabilization      ✅ DONE                   │
│  Phase C: Session Isolation           🔄 IN PROGRESS            │
│       ├─ C1 Unified session identity   ✅                       │
│       ├─ C2 EmotionEngine per-session  ✅                       │
│       ├─ C3 ImpulseCore per-session    ✅                       │
│       ├─ C4 SessionManager ↔ Supabase  ✅                       │
│       └─ C5 TTL/LRU eviction           ✅                       │
│  ┌─────────────────────────────────────────────────────────────┤
│  │ STOP: Phase C done. Не переходим к Phase D сразу.           │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  STREAM 2 — Research (параллельно, без кода в проде)            │
├─────────────────────────────────────────────────────────────────┤
│  Research: "What is the next abstraction?"                      │
│  Директория: research/cognitive_workspace/                      │
│       ├─ 001_problem.md           — что именно болит сейчас     │
│       ├─ 002_examples.md          — как выглядит в других системах│
│       ├─ 003_requirements.md      — что должно решить абстракция │
│       ├─ 004_design_options.md    — 3-5 вариантов (Workspace,    │
│       │                              Context, State, Mind)       │
│       ├─ 005_prototype.md         — минимальный PoC (не в прод-500 LOC)  │
│       ├─ 006_comparison.md        — сравнение вариантов          │
│       └─ 007_adr.md               — Architecture Decision Record │
│  Срок: 2-3 недели探索, потом Decision.                           │
└─────────────────────────────────────────────────────────────────┘
                              ↓
                              Decision → Implementation (новая Phase D+)
```

---

## 📋 Подробный план Stream 1 (Engineering)

### Phase C — Session Isolation (завершение)

| Task | Status | Notes |
|------|--------|-------|
| C1 Unified session identity | ✅ | `ctx.session_id` flows API → executor → phases |
| C2 EmotionEngine per-session | ✅ | `SessionEmotionStore` в emotion phases |
| C3 ImpulseCore per-session | ✅ | `SessionImpulseStore` в impulse phases |
| C4 SessionManager ↔ Supabase | ✅ | `user_id` = `session_id` для auth users; SessionManager = кэш с валидацией против Supabase |
| C5 TTL/LRU eviction | ✅ | 24h TTL, max 500 sessions в обоих stores |

**Definition of Done Phase C:**
- [ ] Все 5 подзадач зелёные
- [ ] Интеграционный тест: 2 пользователя параллельно → изоляция эмоций/импульсов
- [ ] Load test: 50 concurrent sessions → нет утечек памяти
- [ ] Лог: `Pipeline: ... | state=HEALTHY` без degradation

---

### После Phase C — Пауза перед Phase D

**НЕ начинать:**
- Phase D (Learning Unification) — 4 MetaLearner'а ждут, но *чего* они учатся, непонятно без workspace-а
- Cognitive Context (Phase E) — абстракция не исследована
- Conversation State / Decision Engine — зависят от workspace-а

**ДЕЛАТЬ:**
1. Зафиксировать текущее состояние: `git tag phase-c-complete`
2. Запустить Stream 2 (Research)
3. В paralelo — баг-фиксы, observability, hardening текущего кода

---

## 📋 Подробный план Stream 2 (Research)

### Директория: `research/cognitive_workspace/`

```
research/
└── cognitive_workspace/
    ├── 001_problem.md
    ├── 002_examples.md
    ├── 003_requirements.md
    ├── 004_design_options.md
    ├── 005_prototype.md
    ├── 006_comparison.md
    ├── 007_adr.md
    └── prototypes/           # throw-away code, не в проде
```

### 001_problem.md — Что болит сейчас?

| Symptom | Root Cause (hypothesis) |
|---------|-------------------------|
| Pipeline ctx — мешок `Dict[str, Any]` без типов | Нет единого workspace-а для turno/weшления |
| 4 MetaLearner'а независимы | Нет unified learning bus — не знают *что* учить |
| Emotion/Impulse global singletons | Session Isolation (Phase C) фиксит, но не даёт workspace |
| Truth Loop / Reflection / Dreams — изолированы | Нет shared workspace для cross-phase reasoning |
| Conversation state разбросан (dialog_id, session_id, request_id) | Нет single source of truth для "что происходит сейчас" |

**Ключевой вопрос:** *Что должно находиться в "working mind" системы в момент обработки одного юзер-сообщения?*

---

### 002_examples.md — Референсы

| Система | Абстракция | Ключевая идея |
|---------|------------|---------------|
| ACT-R / Soar | Working Memory / Goal Stack | Production rules + chunk retrieval |
| LangGraph / LangChain | StateGraph / Checkpointer | Graph state + persistence |
| AutoGPT / BabyAGI | Task List + Memory | Recursive task decomposition |
| MemGPT | Main Context + Recall Storage | Virtual memory management |
| ReAct / Reflexion | Scratchpad + Reflection | Explicit reasoning trace |
| Cognitive Architectures (CLARION, LIDA) | Global Workspace | Broadcast + competition |

**Критерии отбора:** production-ready, open source, documented architecture.

---

### 003_requirements.md — Что должна дать абстракция?

**Functional:**
- [ ] Единый "workspace" для текущего turn'а (вход → мышление → выход)
- [ ] Persistence across turns (conversation continuity)
- [ ] Explicit reasoning trace (для X-Ray, Reflection, Truth Loop)
- [ ] Isolation между сессиями (already Phase C)
- [ ] Versioning / snapshots (для Research Platform)

**Non-functional:**
- [ ] < 5ms overhead на turn
- [ ] Typed schema (Pydantic / TypedDict)
- [ ] Serializable (JSON / msgpack)
- [ ] Testable in isolation (unit tests без pipeline)

---

### 004_design_options.md — Варианты (3-5)

| Option | Name | Core Idea | Pros | Cons |
|--------|------|-----------|------|------|
| A | **Conversation Workspace** | Single object: history + working memory + goals | Simple, maps to dialog | May not fit multi-task reasoning |
| B | **Task Workspace** | Decompose → sub-tasks → each has workspace | Fits complex reasoning | Overhead for simple chat |
| C | **Working Mind** | Global workspace + specialized modules (Baars GWT) | Theoretically grounded | Complex implementation |
| D | **Cognitive Context** (current plan) | Immutable snapshot per phase | Pipeline-native | Read-only, no "working" state |
| E | **Thinking State** | Explicit reasoning trace + scratchpad | Transparent, debuggable | Verbose, storage cost |

**Критерий выбора:** какой вариант решает *проблемы из 001* с минимальной сложностью?

---

### 005_prototype.md — PoC план

- **Scope:** 1 file, < 500 LOC, zero deps outside stdlib + pydantic
- **API:** `workspace = Workspace(session_id); workspace.think(input) → output`
- **Tests:** unit tests для каждого метода, property-based для state transitions
- **Benchmarks:** 10k turns → latency, memory
- **Throw-away:** код НЕ вливается в main, только insights

---

### 006_comparison.md — Сравнение

| Criterion | Weight | A | B | C | D | E |
|-----------|--------|---|---|---|---|---|
| Solves 001 problems | 30% |   |   |   |   |   |
| Implementation complexity | 20% |   |   |   |   |   |
| Fits existing pipeline | 20% |   |   |   |   |   |
| Enables unified learning | 15% |   |   |   |   |   |
| Observability (X-Ray) | 10% |   |   |   |   |   |
| Extensibility | 5% |   |   |   |   |   |
| **TOTAL** | 100% |   |   |   |   |   |

---

### 007_adr.md — Architecture Decision Record

```markdown
# ADR-XXXX: Cognitive Workspace Abstraction

## Status
Proposed / Accepted / Superseded

## Context
[Summary from 001]

## Decision
[Chosen option from 006]

## Consequences
- Positive: ...
- Negative: ...
- Risks: ...

## Implementation Plan
- Phase D': ...
- Phase E': ...
```

---

## 🚦 Decision Gate (после Research)

| Outcome | Action |
|---------|--------|
| Один вариант явно лучше (score > 70%) | Внедрять как Phase D' (новая нумерация) |
| Два варианта близки | Спайк 1 неделя на каждом → ревью |
| Ничего не подходит | Back to drawing board, extend research |

**Никакого кода в проде до Accepted ADR.**

---

## 📅 Timeline (ориентировочный)

| Week | Stream 1 (Eng) | Stream 2 (Research) |
|------|----------------|---------------------|
| 1-2  | Phase C finish, hardening | 001, 002, 003 |
| 3-4  | Bug fixes, observability | 004, 005 (prototypes) |
| 5    | **STOP new features** | 006, 007 (ADR) |
| 6    | Review ADR | Decision meeting |
| 7+   | Implementation (new Phase D') | — |

---

## 📝 Правила работы

1. **Stream 1 не блокирует Stream 2** — они независимы
2. **Stream 2 не коммитит в main** — только `research/` + PR для обсуждения
3. **Decision делается командой** — не одним разработчиком
3. **После Decision — новый Phase Plan** (D', E', F'...) с понятными критериями
4. **Phase C = last "cleanup" phase** — после неё только research-driven development

---

## ✅ Checkpoint: Где мы сейчас

- [x] Phase A — Architecture Cleanup
- [x] Phase B — Pipeline Stabilization  
- [x] Phase C — Session Isolation (5/5 tasks)
- [ ] **Phase C Integration Tests** — following task
- [ ] **Research Stream kickoff** — create `research/cognitive_workspace/`

---

**Next Action:** Запустить Phase C integration tests + создать `research/cognitive_workspace/001_problem.md`