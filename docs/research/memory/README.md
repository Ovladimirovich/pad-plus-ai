# Memory Research Initiative (MRI)

**Status:** Active  
**Started:** 2026-07-31  
**Lead:** Research Stream  
**Related:** [Phase C — Session Isolation Complete](../PHASE_PLAN_TWO_STREAMS.md)

---

## What is MRI?

**Memory Research Initiative (MRI)** — инженерная программа исследования когнитивной памяти PAD+ AI.

> **MRI = Memory Research Initiative**  
> Аналогия с медицинским МРТ: мы «сканируем» внутреннее устройство памяти системы, не меняя её, а понимая.

---

## Почему MRI?

После Phase C (Session Isolation) PAD+ уперся в два фундаментальных ограничения:

1. **Память теряется** — после ~30 сообщений модель забывает контекст, путает темы, не помнит решения
2. **Нет непрерывности разговора** — каждый запрос обрабатывается почти заново, нет ощущения «мы продолжаем мысль»

Это не баги. Это архитектурные ограничения текущей памяти.

---

## Методология MRI

```
Проблема
    ↓
Наблюдение (Inventory)
    ↓
Исследование (Flow Mapping, Metrics, Trace)
    ↓
Понимание (Problem Analysis, Hypotheses)
    ↓
Новая архитектура (Proposal, Experiments)
```

**Никакого кода до фазы 3.** Сначала понимание.

---

## Структура исследования

```
docs/research/memory/
├── README.md
├── 00_research_program.md
│
├── Phase 1 — What exists?
│   ├── 01_inventory.md
│   ├── 02_ownership.md
│   └── 03_lifecycle.md
│
├── Phase 2 — How does it work?
│   ├── 04_flow_mapping.md
│   ├── 05_operations.md
│   └── 06_trace_model.md
│
├── Phase 3 — What do measurements show?
│   ├── 07_metrics.md
│   ├── 08_problem_analysis.md
│   └── 09_design_principles.md
│
├── Phase 4 — What should be built?
│   └── 10_architecture_proposal.md
│
├── 11_hypotheses.md
└── 12_experiments.md
```

---

## Фазы

| Phase | Focus | Output |
|-------|-------|--------|
| **1 — What exists?** | Inventory, Ownership, Lifecycle | Полная карта памяти |
| **2 — How it works?** | Flows, Operations, Trace Model | Flow maps, Trace model |
| **3 — Measurements** | Metrics, Problem Analysis, Principles | Данные, Проблемы, Принципы |
| **4 — Architecture** | Proposal, Principles | ARD, Implementation Plan |

---

## Главный принцип MRI

> **Сначала понимание. Потом архитектура. Потом код.**

Никаких новых абстракций до понимания текущего состояния.

---

## Связь с X-Ray

Memory Trace интегрируется в **X-Ray** как новый тип событий:

```
X-Ray
├── Pipeline Trace
├── Cognitive Trace
├── Memory Trace   ← новый модуль (MemoryEvent)
├── Session Trace
└── Replay
```

Memory Event становится новым типом события в существующей инфраструктуре наблюдаемости.

---

## Hypotheses & Experiments

После появления Trace — формулируем и проверяем гипотезы:

- **H-001:** Episode Memory почти никогда не перечитывается
- **H-002:** Semantic используется чаще Episodic
- **H-003:** Emotion влияет на генерацию сильнее Memory
- **H-004:** Большая часть записей никогда не используется
- **H-005:** Session Memory может заменить часть Working Memory

---

## MRI != Memory Refactoring

| MRI | Memory Refactoring |
|-----|-------------------|
| Сначала измерение | Сначала код |
| Понимание проблемы | Предположение о решении |
| Данные → Архитектура | Архитектура → Данные |
| MRI = Research Program | Refactoring = Engineering |

---

## Timeline

| Week | Focus |
|------|-------|
| 1 | Phase 1: Inventory, Ownership, Lifecycle |
| 2 | Phase 2: Flows, Operations, Trace Model |
| 3 | Phase 3: Metrics, Problem Analysis, Hypotheses |
| 4 | Phase 4: Architecture Proposal + Experiments Plan |

---

*MRI начинается здесь. Первым шагом — Inventory.*