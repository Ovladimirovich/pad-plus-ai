# MRI Research Program

**Program:** Memory Research Initiative (MRI)  
**Started:** 2026-07-31  
**Status:** Active  
**Lead:** Research Stream

---

## Program Charter

### Mission
Построить **инженерную инфраструктуру исследования памяти** PAD+ AI, которая позволит ответить на любой вопрос о памяти на основе данных, а не предположений.

### Vision
Через 4 недели мы должны иметь возможность ответить на любой вопрос о памяти на основе данных:
- «Почему Episode Memory почти не перечитывается?»
- «Почему 80% Semantic Memory никогда не читается?»
- «Почему Emotion влияет на генерацию сильнее Memory?»

### Non-Goals (Explicit)
- ❌ Новый MemoryManager
- ❌ ConversationState
- ❌ CognitiveContext
- ❌ CognitiveWorkspace
- ❌ Переписывание Pipeline
- ❌ Новые абстракции памяти

---

## Research Questions (The Big Questions)

| ID | Question | Priority |
|------|----------|----------|
| RQ-001 | Почему PAD+ теряет контекст после ~30 сообщений? | P0 |
| RQ-002 | Почему нет ощущения «мы продолжаем мысль» между запросами? | P0 |
| RQ-003 | Почему Episode Memory почти не перечитывается? | P1 |
| RQ-004 | Почему Semantic Memory используется чаще Episodic? | P1 |
| RQ-005 | Почему Emotion влияет на генерацию сильнее Memory? | P1 |
| RQ-005 | Почему большая часть записей никогда не используется? | P1 |
| RQ-006 | Может ли Session Memory заменить часть Working Memory? | P1 |

---

## Program Structure

```
Phase 1: What exists?     (Week 1)  → Inventory, Ownership, Lifecycle
Phase 2: How it works?    (Week 2)  → Flows, Operations, Trace Model
Phase 3: Measurements     (Week 3)  → Metrics, Problems, Principles
Phase 4: Architecture     (Week 4)  → Proposal, Experiments Plan
```

### Phase Gates

| Phase | Gate | Criteria |
|-------|------|----------|
| 1 → 2 | Inventory Complete | All components documented with owners |
| 2 → 3 | Trace Working | MemoryEvent flowing in X-Ray |
| 3 → 4 | Data Collected | 1000+ MemoryEvents, 10+ hypotheses tested |
| 4 → Done | ADR Signed | Architecture Proposal signed off |

---

## Deliverables

| Phase | Artifacts |
|-------|-----------|
| **Phase 1** | 01_inventory.md, 02_ownership.md, 03_lifecycle.md |
| **Phase 2** | 04_flow_mapping.md, 05_operations.md, 06_trace_model.md |
| **Phase 3** | 07_metrics.md, 08_problem_analysis.md, 09_design_principles.md |
| **Phase 4** | 10_architecture_proposal.md, 11_hypotheses.md, 12_experiments.md |

---

## Methodology

| Principle | Practice |
|-----------|----------|
| **Data over opinion** | Все утверждения подкрепляются trace'ами |
| **Measure first** | Сначала измерение, потом архитектура |
| **Minimal code** | Только trace instrumentation до Phase 3 |
| **Reproducible** | Все эксперименты воспроизводимы |
| **No new abstractions** | Работаем с существующей памятью |

---

## Team

| Role | Person | Responsibility |
|------|--------|----------------|
| Research Lead | Research Stream | Program design, analysis |
| Engineering Lead | Engineering Stream | Trace instrumentation, infra |
| Data Analyst | Research Stream | Metrics, experiments, hypotheses |

---

## Success Criteria (Program Level)

| Metric | Target |
|--------|--------|
| Memory components documented | 100% |
| Ownership assigned | 100% (single owner per state) |
| Trace coverage | 100% memory operations |
| Hypotheses tested | 5+ |
| Experiments run | 3+ |
| Architecture proposal | Signed off |

---

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Trace overhead > 10ms | Low | Async writes, batching |
| Data volume too high | Medium | Sampling, retention policies |
| Incomplete instrumentation | Medium | Code review gate |
| Hypotheses not validated | Low | Time-boxed experiments |

---

## Governance

| Event | Cadence | Participants |
|-------|---------|--------------|
| Weekly Sync | Weekly | Research + Engineering Leads |
| Phase Gate Review | End of Phase | Research + Engineering + Product |
| Hypothesis Review | Bi-weekly | Research Lead + Analyst |

---

## Definition of Done (Program)

- [ ] Все 12 документов созданы и заполнены данными
- [ ] MemoryEvent течет в X-Ray (100% coverage)
- [ ] 5+ гипотез проверены (confirmed/rejected)
- [ ] 3+ эксперимента проведены
- [ ] Architecture Proposal подписан
- [ ] MRI considerado complete → transition to implementation

---

*MRI Research Program v1.0 | Started 2026-07-31*