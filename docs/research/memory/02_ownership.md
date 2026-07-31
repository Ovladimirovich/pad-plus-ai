# 02_ownership.md — Memory Ownership

**Phase:** 1 — Ownership  
**Status:** Auto-generated from code scan  
**Scan date:** 2026-07-31

---

## Ownership Matrix

| State | Single Owner | Readers | Writers |
|-------|--------------|---------|---------|
| **Episodes** | `EpisodicMemory` | `Consolidation`, `Pipeline`, `Research` | `SaveEpisodePhase` |
| **Semantic Facts** | `SemanticMemory` | `SemanticPhase`, `Pipeline`, `Consolidation` | `Consolidation` |
| **Semantic Procedures** | `SemanticMemory` | `SemanticPhase`, `Pipeline` | `Consolidation` |
| **Emotion State** | `SessionEmotionStore` | `EmotionPhase`, `GeneratePhase`, `ImpulsePhase` | `EmotionUpdatePhase`, `SessionEmotionStore` |
| **Impulse State** | `ImpulseCore` (global) | `ImpulsePhase`, `ImpulseUpdatePhase`, `Pipeline` | `ImpulseUpdatePhase` |
| **Persona Traits** | `PersonaMemory` | `PersonaPhase`, `PersonaEvolution` | `PersonaEvolutionPhase` |
| **User Persona Data** | `UserPersonaManager` | `PersonaPhase`, `PersonaEvolution` | `UserPersonaManager` |
| **Roots** | `RootsMemory` | `RootsPhase`, `GeneratePhase`, `Pipeline` | — (init only) |
| **RAG Dialogs** | `RAGMemory` | `RAGPhase`, `Consolidation` | `RAGPhase` (implicit) |
| **Working Memory** | `PipelineExecutor` | All Phases | All Phases (via `ctx.context`) |
| **X-Ray Events** | `TraceCollector` | X-Ray API, Healer, Research | All Phases |
| **Meta Learner State** | `MetaLearner` | `ReflectionPhase`, `Experience` | `ReflectionPhase` |
| **Consolidation History** | `MemoryConsolidator` | — | `Consolidation` |
| **Session Context** | `SessionManager` | — | `SessionManager` |

---

## ✅ Ownership Verification

| Check | Status | Details |
|-------|--------|---------|
| Single Writer per State | ⚠️ 13/15 | See conflicts below |
| Conflicts Resolved | ⚠️ 3/5 | See conflicts below |
| States without Writer | 1 (Roots - init only) | Expected |
| Global Singletons with Session Data | 3 (ImpulseCore, PersonaMemory, RAGMemory) | Need migration |

---

## 🔴 Ownership Conflicts (Require Fix)

| State | Conflict | Current Writers | Resolution |
|-------|----------|-----------------|------------|
| **Emotion State** | `PADModel` (global) vs `SessionEmotionStore` (per-session) | `EmotionUpdatePhase`, `SessionEmotionStore` | **Owner: `SessionEmotionStore`** — per-session store owns state; global `PADModel` is fallback factory |
| **Persona Data** | `PersonaMemory` (global) + `UserPersonaManager` (per-user) | `PersonaEvolutionPhase`, `UserPersonaManager` | **Owner: `UserPersonaManager`** — per-user owns; `PersonaMemory` = global defaults only |
| **Impulse State** | `ImpulseCore` (global singleton) | `ImpulseUpdatePhase` | **Owner: `SessionImpulseStore`** (new) — needs per-session store |
| **RAG Dialogs** | `RAGMemory` + `EpisodicMemory` (both store dialogs) | `RAGPhase` (implicit), `SaveEpisodePhase` | **Owner: `EpisodicMemory`** — episodes = source of truth; `RAGMemory` = derived index |
| **Working Memory** | `PipelineContext.context` (Dict) — multi-writer | All Phases (via `ctx.context.update()`) | **Owner: `PipelineExecutor`** — phases return `PhaseResult.data`, executor merges |

---

## ✅ Ownership Action Items

| # | State | Action | Target Phase |
|---|-------|--------|--------------|
| 1 | Emotion State | Already fixed: `SessionEmotionStore` owns per-session state | Phase C (Done) |
| 2 | Persona Data | Deprecate `PersonaMemory` for user data; `UserPersonaManager` owns | Phase D' |
| 3 | Impulse State | Create `SessionImpulseStore` (per-session) | Phase D' |
| 4 | RAG Dialogs | `EpisodicMemory` = source of truth; `RAGMemory` = derived index | Phase D' |
| 5 | Working Memory | `PipelineExecutor` owns `ctx.context`; phases return `PhaseResult.data` | Phase D' |
| 6 | Roots/Semantic/RAG | Add per-session stores (`SessionSemanticStore`, `SessionRAGStore`) | Phase D' |

---

## 📋 Ownership Rules (Enforced by ContractValidator)

1. **Single Writer** — Only the Owner class may call WRITE/DELETE on its state
2. **Readers Never Write** — Readers must not mutate state
3. **Ownership Declared** — Each component docstring must declare `# Owner: ClassName`
4. **Session Scoped** — Session-scoped state must use `SessionStore` pattern
5. **Global State** — Only for truly global config/fallbacks (no user data)

---

*Generated: 2026-07-31 | Source: `scripts/ownership_v2.py` scan*