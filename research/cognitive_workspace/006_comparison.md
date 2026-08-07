# 006_comparison.md — Design Options Comparison & Decision Matrix

**Status:** Draft  
**Feeds into:** 007_adr.md (Architecture Decision Record)  
**Based on:** 004_design_options.md + 005_prototype.md

---

## Comparison Methodology

| Weight | Criterion | Rationale |
|--------|-----------|-----------|
| 30% | **Solves 001 Problems** | Directly addresses pain points from 001_problem.md |
| 20% | **Implementation Complexity** | Effort to build + maintain (lower = better) |
| 20% | **Fits PAD+ Architecture** | Aligns with existing pipeline, contracts, X-Ray |
| 15% | **Enables Unified Learning** | Phase D readiness (single learning signal) |
| 10% | **Observability / Debugging** | X-Ray, time-travel, contract validation |
| 5% | **Extensibility** | Future-proof for Phase E/F/G |

Score: 1 (poor) → 5 (excellent)

---

## Cluster A: Turn Workspace + Persistence

| Criterion | Weight | A1: LangGraph Checkpointer | A2: Custom Lightweight | A3: Hybrid |
|-----------|--------|---------------------------|------------------------|------------|
| Solves 001 | 30% | 5 | **5** | 4 |
| Complexity | 20% | 2 | **4** | 2 |
| PAD+ Fit | 20% | 2 | **5** | 3 |
| Learning | 15% | 4 | **4** | 4 |
| Observability | 10% | 5 | **4** | 4 |
| Extensibility | 5% | 4 | **4** | 4 |
| **Weighted Score** | | **3.7** | **4.4** | **3.5** |

**Winner: A2 — Custom Lightweight Checkpointer**

---

## Cluster B: Conversation Workspace

| Criterion | Weight | B1: Memory Stream (Emergent) | B2: Structured Core | B3: Hybrid Core + LLM |
|-----------|--------|------------------------------|---------------------|----------------------|
| Solves 001 | 30% | 4 | **5** | 4 |
| Complexity | 20% | 3 | **5** | 2 |
| PAD+ Fit | 20% | 2 | **5** | 3 |
| Learning | 15% | 3 | **4** | 3 |
| Observability | 10% | 2 | **5** | 3 |
| Extensibility | 5% | 3 | **4** | 3 |
| **Weighted Score** | | **2.9** | **4.8** | **3.2** |

**Winner: B2 — Structured Core**

---

## Cluster C: Working Memory / Scratchpad

| Criterion | Weight | C1: Free-Form Text | C2: Structured Evidence/Hypothesis |
|-----------|--------|-------------------|-----------------------------------|
| Solves 001 | 30% | 2 | **5** |
| Complexity | 20% | 5 | 3 |
| PAD+ Fit | 20% | 2 | **5** |
| Learning | 15% | 2 | **4** |
| Observability | 10% | 2 | **5** |
| Extensibility | 5% | 3 | **4** |
| **Weighted Score** | | **2.7** | **4.4** |

**Winner: C2 — Structured Evidence/Hypothesis Graph**

---

## Cluster D: Memory Hierarchy

| Criterion | Weight | D1: Three-Tier (MemGPT) | D2: Two-Tier + Conversation (PAD+ Adapted) |
|-----------|--------|-------------------------|--------------------------------------------|
| Solves 001 | 30% | 4 | **5** |
| Complexity | 20% | 2 | **4** |
| PAD+ Fit | 20% | 2 | **5** |
| Learning | 15% | 3 | **4** |
| Observability | 10% | 3 | **4** |
| Extensibility | 5% | 3 | **4** |
| **Weighted Score** | | **3.0** | **4.4** |

**Winner: D2 — Two-Tier + Conversation (Reuses Existing Stores)**

---

## Cluster E: Goal Stack

| Criterion | Weight | E1: ACT-R Hierarchical | E2: Flat Task List | E3: Hybrid with Suspend/Resume |
|-----------|--------|------------------------|-------------------|--------------------------------|
| Solves 001 | 30% | 4 | 2 | **5** |
| Complexity | 20% | 2 | 5 | 3 |
| PAD+ Fit | 20% | 3 | 3 | **4** |
| Learning | 15% | 3 | 2 | **4** |
| Observability | 10% | 3 | 2 | **4** |
| Extensibility | 5% | 3 | 3 | **4** |
| **Weighted Score** | | **3.1** | **2.7** | **4.0** |

**Winner: E3 — Hybrid Goal Stack with Suspend/Resume**

---

## Cluster F: Reflection Engine

| Criterion | Weight | F1: Generative Agents (Periodic LLM) | F2: Structured Only | F3: Hybrid (Structured + LLM) |
|-----------|--------|--------------------------------------|---------------------|------------------------------|
| Solves 001 | 30% | 4 | 2 | **5** |
| Complexity | 20% | 2 | 5 | 3 |
| PAD+ Fit | 20% | 3 | 3 | **4** |
| Learning | 15% | 4 | 2 | **5** |
| Observability | 10% | 2 | 5 | **4** |
| Extensibility | 5% | 3 | 3 | **4** |
| **Weighted Score** | | **3.0** | **3.2** | **4.1** |

**Winner: F3 — Hybrid (Structured + LLM for Deep Reflection)**

---

## Cluster G: Planning Engine

| Criterion | Weight | G1: Semantic Kernel Planner | G2: LLM-as-Planner (Structured Output) |
|-----------|--------|----------------------------|----------------------------------------|
| Solves 001 | 30% | 4 | **5** |
| Complexity | 20% | 2 | **4** |
| PAD+ Fit | 20% | 2 | **5** |
| Learning | 15% | 3 | **4** |
| Observability | 10% | 3 | **4** |
| Extensibility | 5% | 3 | **4** |
| **Weighted Score** | | **2.7** | **4.4** |

**Winner: G2 — LLM-as-Planner with Structured Output**

---

## Cluster H: Learning Bus

| Criterion | Weight | H1: Event Bus (Decoupled) | H2: Learning Coordinator (Centralized) |
|-----------|--------|---------------------------|----------------------------------------|
| Solves 001 | 30% | 3 | **5** |
| Complexity | 20% | 4 | **4** |
| PAD+ Fit | 20% | 2 | **5** |
| Learning | 15% | 3 | **5** |
| Observability | 10% | 2 | **5** |
| Extensibility | 5% | **5** | 3 |
| **Weighted Score** | | **3.1** | **4.4** |

**Winner: H2 — Learning Coordinator (Centralized)**

---

## Composite Winner Composition

| Cluster | Winner | Score | Notes |
|---------|--------|-------|-------|
| **A: Turn Workspace** | **A2: Custom Lightweight Checkpointer** | 4.4 | No LangGraph dep, phase-aware |
| **B: Conversation Workspace** | **B2: Structured Core** | 4.8 | Type-safe, contract-friendly |
| **C: Working Memory** | **C2: Structured Scratchpad** | 4.4 | Evidence→hypothesis links |
| **D: Memory Hierarchy** | **D2: Two-Tier + Conversation** | 4.4 | Reuses SessionEmotionStore, pgvector |
| **E: Goal Stack** | **E3: Hybrid with Suspend/Resume** | 4.0 | True suspend/resume |
| **F: Reflection** | **F3: Hybrid (Structured + LLM)** | 4.1 | Cost-controlled deep reflection |
| **G: Planning** | **G2: LLM-as-Planner (Structured)** | 4.4 | Dynamic replanning |
| **H: Learning Bus** | **H2: Learning Coordinator** | 4.4 | Single source of truth |

**Overall Composite Score: 4.35 / 5.0**

---

## Prototype Validation (005)

| Test | Result | Notes |
|------|--------|-------|
| TurnWorkspace checkpointing per phase | ✅ PASS | < 5ms per phase |
| ConversationWorkspace persistence | ✅ PASS | Persists across turns |
| Time-travel load at phase | ✅ PASS | < 3ms |
| Branching from checkpoint | ✅ PASS | < 10ms |
| Structured scratchpad ops | ✅ PASS | Evidence→hypothesis links |
| Conversation goal push/suspend/resume | ✅ PASS | True suspend/resume |
| Overhead per phase | ✅ PASS | < 5ms checkpoint |

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Checkpointer overhead > 10ms/phase | Low | Medium | Async writes, batch if needed |
| ConversationWorkspace grows unbounded | Medium | Medium | TTL + summarization every N turns |
| LLM planner hallucination | Medium | High | Structured output + validation |
| LLM reflection cost | Medium | Low | Structured first, LLM only deep |
| Session store contention | Low | Medium | Per-session stores, no global lock |

---

## Implementation Priority (Phased)

### Phase D' (Post-Research Implementation)

| Week | Deliverable | Based On |
|------|-------------|----------|
| 1-2 | Custom Checkpointer (A2) + TurnWorkspace (A2+C2) | A2, C2 |
| 2-3 | ConversationWorkspace (B2) + Goal Stack (E3) | B2, E3 |
| 3-4 | Memory Hierarchy (D2) + Reflection Engine (F3) | D2, F3 |
| 5-6 | Planner (G2) + Learning Coordinator (H2) | G2, H2 |
| 7 | Integration + Testing + ADR | All |

---

## Decision

**Recommended Architecture:** The composite of winners (A2+B2+C2+D2+E3+F3+G2+H2) scores **4.35/5.0** and directly addresses all 001 pain points while fitting PAD+ architecture.

**Next Step:** Write **007_adr.md** to formalize this decision.