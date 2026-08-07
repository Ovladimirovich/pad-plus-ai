# 003_requirements.md — Cognitive Workspace Requirements

**Derived from:** 001_problem.md (symptoms + root causes) + 002_examples.md (10 system analysis)  
**Status:** Draft — feeds into 004_design_options.md

---

## 📋 Requirements Classification

| Priority | Code | Meaning |
|----------|------|---------|
| **P0** | Must Have | Blocker for any viable workspace |
| **P1** | Should Have | Significant value, workaround exists |
| **P2** | Nice to Have | Future extension, not blocking |

---

## 🎯 Functional Requirements

### FR-001: Turn Workspace (Per-Turn Scratchpad)
| ID | Requirement | Priority | Source |
|----|-------------|----------|--------|
| FR-001.1 | Create isolated workspace per pipeline turn | P0 | 001: context bag; 002: ReAct scratchpad, LangGraph state |
| FR-001.2 | Typed schema (not `Dict[str, Any]`) | P0 | 001: contract violations; 002: LangGraph typed state |
| FR-001.3 | Auto-populated by pipeline phases (immutable after phase) | P0 | 001: write-before-read defects |
| FR-001.4 | Includes: evidence, hypotheses, intermediate computations | P1 | 002: ReAct scratchpad, Generative Agents working memory |
| FR-001.5 | Auto-saved to persistent store after turn | P0 | 002: LangGraph checkpointer, time-travel debugging |
| FR-001.6 | Readable by any phase in same turn | P0 | 001: phase communication via ctx |

### FR-002: Conversation Workspace (Cross-Turn Continuity)
| ID | Requirement | Priority | Source |
|----|-------------|----------|--------|
| FR-002.1 | Persists across turns within same session | P0 | 001: fractured session identity |
| FR-002.2 | Topic stack (current + parent topics) | P1 | 001: no conversation state; 002: Generative Agents topic tracking |
| FR-002.3 | Goal stack with suspend/resume (hierarchical) | P1 | 002: ACT-R goal stack, AutoGPT task list |
| FR-002.4 | Key entities / concepts introduced in conversation | P1 | 002: Generative Agents entities, MemGPT working memory |
| FR-002.5 | Conversation summary (compressed, not raw history) | P1 | 002: MemGPT recall storage, Generative Agents reflections |
| FR-002.6 | Session isolation (no cross-user leakage) | P0 | 001: Phase C session isolation |

### FR-003: Working Memory (Active Reasoning Buffer)
| ID | Requirement | Priority | Source |
|----|-------------|----------|--------|
| FR-003.1 | Scratchpad for current reasoning (evidence, hypotheses, candidates) | P0 | 002: ReAct scratchpad, MemGPT working memory |
| FR-003.2 | Bounded size (token budget aware) | P1 | 002: MemGPT working memory limit |
| FR-003.3 | Explicit evidence → hypothesis → conclusion links | P1 | 002: ReAct trajectory, X-Ray trace |
| FR-003.4 | Clearable per turn, preservable across turns for multi-step | P1 | 002: ACT-R working memory |

### FR-004: Long-Term Memory (Cross-Session)
| ID | Requirement | Priority | Source |
|----|-------------|----------|--------|
| FR-004.1 | Semantic memory (facts, concepts, embeddings) | P1 | 002: MemGPT archival, Generative Agents stream, LlamaIndex |
| FR-004.2 | Episodic memory (past turns, decisions, outcomes) | P1 | 002: Generative Agents memory stream, LlamaIndex chat history |
| FR-004.3 | Reflection memory (high-level insights, patterns) | P1 | 002: Generative Agents reflections, Reflexion verbal reflection |
| FR-004.4 | Procedural memory (skills, strategies, procedures) | P2 | 002: ACT-R procedural memory, Semantic Kernel planners |
| FR-004.4 | Cross-session retrieval (recency + importance + relevance) | P1 | 002: Generative Agents retrieval (recency + importance + relevance) |

### FR-005: Goal & Task Management
| ID | Requirement | Priority | Source |
|----|-------------|----------|--------|
| FR-005.1 | Hierarchical goal stack (push/pop/suspend/resume) | P1 | 002: ACT-R goal stack, AutoGPT task decomposition |
| FR-005.2 | Explicit task decomposition (parent → subtasks) | P1 | 002: AutoGPT task list, BabyAGI |
| FR-005.3 | Task status tracking (pending → in_progress → done/failed) | P1 | 002: AutoGPT task status |
| FR-005.3 | Goal suspension/resumption with context preservation | P1 | 002: ACT-R goal suspension |

### FR-006: Reflection Engine
| ID | Requirement | Priority | Source |
|----|-------------|----------|--------|
| FR-006.1 | Periodic reflection (configurable interval) | P1 | 002: Generative Agents periodic reflection |
| FR-006.2 | Failure-triggered reflection (auto on error/low confidence) | P1 | 002: Reflexion verbal reflection |
| FR-006.3 | Reflection output → procedural memory update | P1 | 002: Reflexion policy update, ACT-R production compilation |
| FR-006.4 | Reflection output → long-term memory (reflection stream) | P1 | 002: Generative Agents reflection stream |

### FR-007: Planning Engine
| ID | Requirement | Priority | Source |
|----|-------------|----------|--------|
| FR-007.1 | Generate plan from goal + context | P1 | 002: Semantic Kernel planner, Generative Agents daily plan |
| FR-007.2 | Dynamic replanning on failure/new info | P1 | 002: Reflexion retry, ACT-R production firing |
| FR-007.2 | Plan as first-class object (versioned, branchable) | P1 | 002: Semantic Kernel Plan, LangGraph state |

### FR-008: State Persistence & Time Travel
| ID | Requirement | Priority | Source |
|----|-------------|----------|--------|
| FR-008.1 | Full state checkpoint after each turn | P0 | 002: LangGraph checkpointer |
| FR-008.2 | Point-in-time restore (any turn) | P1 | 002: LangGraph time-travel |
| FR-008.3 | Branch from checkpoint (what-if analysis) | P1 | 002: LangGraph branching |
| FR-008.4 | Structured export (JSON/Parquet) for Research Platform | P1 | 001: Research Platform snapshots |

---

## ⚙️ Non-Functional Requirements

### NFR-001: Performance
| ID | Requirement | Priority | Target |
|----|-------------|----------|--------|
| NFR-001.1 | Turn workspace creation < 5ms | P0 | 002: LangGraph overhead |
| NFR-001.2 | Conversation workspace ops < 10ms | P1 | |
| NFR-001.3 | Memory retrieval (vector) < 50ms p99 | P1 | 002: MemGPT, LangGraph |
| NFR-001.4 | Checkpoint save < 20ms | P0 | 002: LangGraph checkpoint |
| NFR-001.5 | Memory footprint per session < 50MB | P1 | |

### NFR-002: Type Safety & Contracts
| ID | Requirement | Priority | Source |
|----|-------------|----------|--------|
| NFR-002.1 | All workspace fields typed (TypedDict/Pydantic) | P0 | 001: Pipeline contracts |
| NFR-002.2 | Phase contracts auto-validated (pre/post) | P0 | 001: Phase B ContractValidator |
| NFR-002.3 | Schema evolution strategy (additive only) | P1 | 001: Pipeline evolution |

### NFR-003: Observability & Debugging
| ID | Requirement | Priority | Source |
|----|-------------|----------|--------|
| NFR-003.1 | Full turn trace (input → workspace → output) | P0 | 001: X-Ray integration |
| NFR-003.2 | Workspace diff between turns | P1 | 002: LangGraph time-travel |
| NFR-003.3 | Workspace serialization for Research Platform | P1 | 001: Research snapshots |

### NFR-004: Isolation & Security
| ID | Requirement | Priority | Source |
|----|-------------|----------|--------|
| NFR-004.1 | Session isolation (Phase C verified) | P0 | 001: Phase C |
| NFR-004.2 | No cross-user data in shared memory tiers | P0 | 001: Session isolation |
| NFR-004.3 | TTL/LRU eviction on all memory tiers | P1 | 002: MemGPT, SessionEmotionStore |

### NFR-005: Extensibility
| ID | Requirement | Priority | Source |
|----|-------------|----------|--------|
| NFR-005.1 | New workspace sections additive (no breaking changes) | P1 | 001: Pipeline evolution |
| NFR-005.2 | Custom memory backends pluggable (interface) | P2 | 002: LangGraph checkpointer interface |
| NFR-005.3 | Custom reflection/planning strategies pluggable | P2 | 002: Semantic Kernel planners |

---

## 🎯 Acceptance Criteria (Definition of Done)

### Workspace v0.1 (MVP)
- [ ] TurnWorkspace created per turn, typed, checkpointed
- [ ] ConversationWorkspace persists across turns, topic stack
- [ ] WorkingMemory scratchpad per turn, bounded
- [ ] Checkpoint after each turn (PostgreSQL)
- [ ] Time-travel restore working
- [ ] ContractValidator passes for all phases
- [ ] Phase C session isolation still passes

### Workspace v0.2 (Memory + Reflection)
- [ ] Long-term memory (semantic + episodic + reflection)
- [ ] Vector retrieval integrated
- [ ] Periodic reflection running
- [ ] Failure-triggered reflection
- [ ] Goal stack with suspend/resume

### Workspace v0.3 (Planning + Advanced)
- [ ] Hierarchical goal stack
- [ ] Dynamic replanning
- [ ] Branch-from-checkpoint (what-if)
- [ ] Reflection → procedural memory update

---

## 🔗 Traceability Matrix

| Requirement | Problem (001) | Example System (002) | Design Option (004) |
|-------------|---------------|----------------------|---------------------|
| FR-001.1..6 | ctx bag, contracts | LangGraph, ReAct | A: Typed TurnWorkspace |
| FR-002.1..6 | Fractured session | Generative Agents, MemGPT | B: ConversationWorkspace |
| FR-003.1..4 | No scratchpad | ReAct, MemGPT, ACT-R | A: WorkingMemory |
| FR-004.1..4 | No cross-session | Generative Agents, MemGPT | C: Memory Hierarchy |
| FR-005.1..3 | No goals | ACT-R, AutoGPT | B: GoalStack |
| FR-006.1..3 | No reflection | Generative Agents, Reflexion | D: ReflectionEngine |
| FR-007.1..2 | No planning | Semantic Kernel, Generative Agents | E: Planner |
| FR-008.1..4 | No time-travel | LangGraph checkpointer | A: Checkpointer |
| NFR-001 | Performance | All | Benchmark each tier |
| NFR-002 | Type safety | Pipeline contracts | TypedDict + ContractValidator |
| NFR-003 | Observability | X-Ray | Workspace traces |
| NFR-004 | Isolation | Phase C | Per-session stores |
| NFR-005 | Extensibility | LangGraph | Plugin interfaces |

---

## 📝 Next: 004_design_options.md

For each requirement cluster, define 3-5 concrete design options with trade-offs.