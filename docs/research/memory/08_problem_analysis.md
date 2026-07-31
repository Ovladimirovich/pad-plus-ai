# 08_problem_analysis.md — Problem Classification & Analysis

**Phase:** 8 — Problem Analysis  
**Status:** Draft  
**Based on:** 01–07

---

## Purpose

Классифицировать все найденные проблемы памяти по типам, серьезности и влиянию, чтобы определить приоритеты для архитектуры.

---

## Problem Taxonomy

| Tier | Definition | SLA |
|------|------------|-----|
| **P0 — Critical** | Блокирует работу / теряет данные / нарушает изоляцию | Fix before D' |
| **P1 — High** | Значительно деградирует качество / растекается бесконтрольно | Fix in D' |
| **P2 — Medium** | Деградирует производительность / накапливает tech debt | Backlog |
| **P3 — Low** | Улучшение UX / tech debt / nice to have | Backlog |

---

## Problem Registry (from 01_inventory + 02_ownership + 03_lifecycle + 04_flow_mapping)

### P0 — Critical (Fix Before Phase D')

| ID | Problem | Component | Root Cause | Impact | Evidence |
|----|---------|-----------|------------|--------|----------|
| **P0-01** | **No session isolation for Impulse** | ImpulseCore | Global singleton | User A's impulses affect User B | Global singleton |
| **P0-02** | **No session isolation for Persona** | PersonaMemory | Global singleton | User A's traits leak to User B | Global singleton |
| **P0-03** | **No session isolation for RAG** | RAGMemory | Global singleton | User A's history contaminates User B | Global singleton |
| **P0-04** | **No session isolation for Semantic/Roots** | SemanticMemory, RootsMemory | Global singletons | Cross-user contamination | Global singletons |
| **P0-05** | **No TTL/forgetting except Emotion** | Episodic, Semantic, Persona, Roots, RAG, Impulse | Unbounded growth, OOM risk | Only Emotion has TTL |
| **P0-06** | **No deduplication in Semantic** | SemanticMemory | Duplicate facts, hallucinations | No dedup in add_fact |
| **P0-06** | **No deduplication in Episodic** | EpisodicMemory | Wasted space, noise in consolidation | No dedup in add_episode |
| **P0-07** | **Untyped Pipeline Context** | PipelineContext.context | Runtime errors, no contracts | Dict[str, Any] everywhere |
| **P0-08** | **Dual Persona Owners** | PersonaMemory + UserPersonaManager | Inconsistent state, race conditions | Two managers for same domain |
| **P0-09** | **No MemoryEvent audit trail** | All memory | Can't debug, no compliance | No MemoryEvent type in X-Ray |
| **P0-10** | **Dual write paths for Episodic/RAG** | EpisodicMemory + RAGMemory | Both store dialogs | RAG stores dialogs independently |

---

### P1 — High (Must Fix in D')

| ID | Problem | Component | Root Cause | Impact |
|----|---------|-----------|------------|--------|
| **P1-01** | No importance/utility scoring for forgetting | All stores | Can't prioritize eviction | Memory pressure |
| **P1-01** | No deduplication in Episodic | EpisodicMemory | Wasted space, noise in consolidation | No dedup logic |
| **P1-02** | Consolidation path one-way only | Consolidation | Can't correct errors, no feedback loop | Irreversible errors |
| **P1-03** | No audit trail / audit trail | All memory | Can't debug, no compliance | No MemoryEvent |
| **P1-04** | Pipeline context untyped Dict | PipelineContext.context | Runtime errors, no IDE support | Dict[str, Any] everywhere |
| **P1-05** | No session isolation for Semantic/RAG/Roots | Multiple | Cross-user contamination | Global singletons |
| **P1-06** | Emotion decay rate hardcoded | PADModel | Can't tune per user/session | Hardcoded 0.001/sec |
| **P1-07** | No unified forgetting mechanism | All stores | Each store invents own | Inconsistent |
| **P1-08** | RAG get_recent param mismatch | RAGMemory | `limit` vs `n_results` bug | Bug fixed in inventory |
| **P1-09** | Consolidation path one-way only | Consolidation | Can't correct errors, no feedback | Irreversible |
| **P1-10** | No unified forgetting API | All stores | Each store invents own | Inconsistent |
| **P1-11** | Consolidation not in Pipeline | Consolidation | Not in main path, background only | Not in Pipeline flow |

---

### P2 — Medium (Technical Debt)

| ID | Problem | Component |
|----|---------|-----------|
| **P2-01** | RAG `_topic_stats` unused | RAGMemory |
| **P2-02** | Semantic `_topic_stats` unused | SemanticMemory |
| **P2-03** | Persona traits don't evolve (values/principles static) | PersonaMemory |
| **P2-04** | Impulse stack unbounded (no max size) | ImpulseCore |
| **P2-04** | No session isolation for Working Memory | PipelineContext |
| **P2-05** | Dual Persona owners (PersonaMemory + UserPersonaManager) | PersonaMemory + UserPersonaManager |
| **P2-05** | No unified forgetting API | All stores |
| **P2-06** | No MemoryEvent audit trail | All stores |
| **P2-06** | Emotion `_topic_stats` unused | EmotionEngine |
| **P2-06** | RAG `get_recent` param mismatch (`limit` vs `n_results`) | RAGMemory |
| **P2-06** | Persona traits don't evolve (values/principles static) | PersonaMemory |
| **P2-06** | No session isolation for Working Memory | PipelineContext |

---

### P3 — Low (Nice to Have)

| ID | Problem |
|----|---------|
| **P3-01** | No versioning for Persona traits |
| **P3-02** | No versioning for Roots |
| **P3-03** | No semantic versioning for Semantic facts |
| **P3-04** | No compression for old episodes |
| **P3-04** | No summary generation for old episodes |
| **P3-05** | No importance decay curves (only linear) |

---

## Problem → Root Cause Mapping

| Problem | Root Cause |
|---------|------------|
| No session isolation | Architecture evolved per-component, no cross-cutting session layer |
| No TTL/forgetting | Never needed before (small scale); now OOM risk |
| No importance scoring | Never needed before; now can't prioritize eviction |
| Dual Persona owners | UserPersona added later, PersonaMemory not deprecated |
| Untyped context | Rapid prototyping, no schema evolution |
| No audit trail | Never needed for debugging; now can't debug |
| Dual write paths | Organic growth, no ownership assignment |

---

## Problem → Component Matrix

| Problem | Episodic | Semantic | Emotion | Impulse | Persona | UserPersona | Roots | RAG | WorkingMem | Consolidation |
|---------|----------|----------|---------|---------|---------|-------------|-------|-----|------------|---------------|
| No session isolation | ✅ | ✅ | ✅ | ❌ | ✅ | ❌ | ✅ | ✅ | ✅ | ❌ |
| No TTL/forgetting | ✅ | ✅ | ✅ (has) | ❌ | ✅ | ❌ | ✅ | ✅ | N/A | ❌ |
| No dedup | ❌ | ✅ | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| No importance | ✅ | ✅ | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| Dual owners | ❌ | ❌ | N/A | N/A | ✅ | ✅ | N/A | N/A | N/A | N/A |
| No audit trail | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Untyped context | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | ✅ | N/A |

---

## Problem → Phase Mapping

| Problem | Phase to Fix | Effort |
|---------|--------------|--------|
| P0-01..04 Session isolation | D'‑1, D'‑2 | High |
| P0-05 TTL/forgetting | D'‑2, D'‑3 | High |
| P0-06 Dedup | D'‑2 | Medium |
| P0-07 Untyped context | D'‑5 | Medium |
| P0-08 Dual owners | D'‑2 | Medium |
| P0-09 MemoryEvent | D'‑1 | Medium |
| P1-01 Importance scoring | D'‑3 | High |
| P1-02 Episodic dedup | D'‑2 | Medium |
| P1-02 Consolidation one-way | D'‑3 | Medium |
| P1-03 No audit trail | D'‑1 | Medium |

---

## Root Cause Analysis (5 Whys)

### Why no session isolation?
1. Why? Components evolved independently
2. Why? No cross-cutting session layer existed
3. Why? Architecture grew organically, no upfront design
4. Why? PAD+ started as monolith, evolved piecemeal
5. Why? **Root: No architectural governance for cross-cutting concerns**

### Why no TTL/forgetting?
1. Why? Never needed before (small scale)
2. Why? Scale grew, but memory layer didn't evolve
3. Why? No ownership for "memory lifecycle"
4. Why? No single owner for memory lifecycle
5. Why? **Root: No memory lifecycle owner**

### Why untyped context?
1. Why? Dict[str, Any] easiest for prototyping
2. Why? No schema evolution process
3. Why? No schema registry / contract enforcement
4. Why? No architectural governance for data contracts

---

## Prioritization Framework

| Priority | Criteria | Action |
|----------|----------|--------|
| **P0** | Blocks correctness / data loss / isolation | Fix immediately, block D' |
| **P1** | Degrades quality significantly / unbounded growth | Fix in D' |
| **P2** | Tech debt, limits future | Schedule in D'+1 |
| **P3** | Nice to have | Backlog |

---

## Next: 09_design_principles.md

*Derive design principles from problems*